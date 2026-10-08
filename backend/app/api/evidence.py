import os
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db
from app.models import (
    Evidence, EvidenceRequest, EvidenceRequestStatus, EvidenceProcessingStatus,
    AIValidation, AIValidationStatus, AIRelevance, User, CommunicationType
)
from app.schemas import EvidenceOut, AIValidationOut
from app.api.deps import get_current_user
from app.services.storage.storage_service import storage_service
from app.services.documents.extractor import document_extractor
from app.services.ai.gemini import gemini_service
from app.services.email.resend_service import email_service
from app.utils.audit import log_audit

router = APIRouter(prefix="/api/evidence", tags=["evidence"])

ALLOWED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".docx", ".csv", ".txt"}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB

async def process_and_validate_evidence_task(evidence_id: int, db: Session):
    """
    Core document extraction and AI validation pipeline.
    """
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        return

    req = evidence.request
    control = req.review.assignment.control
    scope = req.review.assignment.scope
    review = req.review

    try:
        evidence.processing_status = EvidenceProcessingStatus.PROCESSING
        db.commit()

        # 1. Download file bytes from storage
        file_bytes = await storage_service.download_file(evidence.storage_path)

        # 2. Extract structured text
        extracted_text = document_extractor.extract_text(
            file_bytes=file_bytes,
            file_name=evidence.file_name,
            file_type=evidence.file_type
        )
        evidence.extracted_text = extracted_text
        evidence.processing_status = EvidenceProcessingStatus.PROCESSED
        evidence.processed_at = datetime.now(timezone.utc)
        db.commit()

        # 3. AI Validation with Gemini
        requirements_data = [
            {"name": r.name, "description": r.description, "mandatory": r.mandatory}
            for r in control.evidence_requirements
        ]
        period_start_str = review.period_start.strftime("%Y-%m-%d")
        period_end_str = review.period_end.strftime("%Y-%m-%d")

        ai_result = await gemini_service.validate_evidence(
            control_code=control.control_code,
            control_name=control.name,
            control_description=control.description,
            requirements=requirements_data,
            period_start=period_start_str,
            period_end=period_end_str,
            extracted_text=extracted_text
        )

        validation = AIValidation(
            evidence_id=evidence.id,
            status=AIValidationStatus(ai_result.get("status", "LOW_CONFIDENCE")),
            relevance=AIRelevance(ai_result.get("relevance", "MEDIUM")),
            confidence=float(ai_result.get("confidence", 0.0)),
            findings=ai_result.get("findings", []),
            missing_information=ai_result.get("missingInformation", []),
            reason=ai_result.get("reason", ""),
            model=ai_result.get("model", settings.GEMINI_MODEL),
            raw_response=ai_result.get("raw_response", "")
        )
        db.add(validation)
        db.flush()

        # 4. Authority rule: Update request status and send automated communication
        submission_url = f"{settings.FRONTEND_URL}/submit/{req.secure_token}"

        if validation.status == AIValidationStatus.COMPLETE:
            req.status = EvidenceRequestStatus.COMPLETE
            req.completed_at = datetime.now(timezone.utc)
            email_service.send_completion(
                db=db,
                request=req,
                recipient_email=scope.email
            )
        elif validation.status in [AIValidationStatus.INCOMPLETE, AIValidationStatus.IRRELEVANT]:
            req.status = EvidenceRequestStatus.INCOMPLETE
            missing_items = validation.missing_information or ["Supporting control records"]
            email_service.send_missing_evidence(
                db=db,
                request=req,
                recipient_email=scope.email,
                missing_items=missing_items,
                reason=validation.reason,
                submission_url=submission_url
            )
        else:
            req.status = EvidenceRequestStatus.SUBMITTED

        db.commit()

        log_audit(
            db,
            action="EVIDENCE_PROCESSED_AND_VALIDATED",
            entity_type="evidence",
            entity_id=evidence.id,
            metadata_json={"validation_status": validation.status.value, "confidence": validation.confidence}
        )

    except Exception as e:
        print(f"[Evidence Pipeline Error] {e}")
        evidence.processing_status = EvidenceProcessingStatus.FAILED
        db.commit()

@router.post("/upload", response_model=EvidenceOut)
async def upload_evidence(
    file: UploadFile = File(...),
    request_id: Optional[int] = Form(None),
    secure_token: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # Authenticate request via either token or request_id
    evidence_req = None
    if secure_token:
        evidence_req = db.query(EvidenceRequest).filter(EvidenceRequest.secure_token == secure_token).first()
    elif request_id:
        evidence_req = db.query(EvidenceRequest).filter(EvidenceRequest.id == request_id).first()

    if not evidence_req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence request could not be identified with the provided token or request_id."
        )

    # Validate file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read bytes and check size
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE // (1024*1024)} MB."
        )

    # Upload to storage service (Supabase or local fallback)
    storage_path, sha256_hash, file_size = await storage_service.upload_file(
        file_bytes=file_bytes,
        file_name=file.filename,
        content_type=file.content_type or "application/octet-stream"
    )

    # Create Evidence database record
    evidence = Evidence(
        request_id=evidence_req.id,
        file_name=file.filename,
        file_type=ext,
        storage_path=storage_path,
        file_size=file_size,
        sha256=sha256_hash,
        processing_status=EvidenceProcessingStatus.UPLOADED,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    log_audit(
        db,
        action="EVIDENCE_UPLOADED",
        entity_type="evidence",
        entity_id=evidence.id,
        metadata_json={"file_name": file.filename, "sha256": sha256_hash, "size": file_size}
    )

    # Run processing and validation synchronously so UI immediately has the result
    await process_and_validate_evidence_task(evidence.id, db)
    db.refresh(evidence)

    return evidence

@router.get("/{id}", response_model=EvidenceOut)
def get_evidence(id: int, db: Session = Depends(get_db)):
    ev = db.query(Evidence).filter(Evidence.id == id).first()
    if not ev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    return ev

@router.post("/{id}/process", response_model=EvidenceOut)
async def trigger_process(id: int, db: Session = Depends(get_db)):
    ev = db.query(Evidence).filter(Evidence.id == id).first()
    if not ev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    await process_and_validate_evidence_task(ev.id, db)
    db.refresh(ev)
    return ev
