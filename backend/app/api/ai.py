from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import (
    Evidence, AIValidation, AIValidationStatus, AIRelevance,
    EvidenceRequestStatus, User, UserRole
)
from app.schemas import AIValidationOut
from app.api.deps import get_reviewer_user, get_current_user
from app.services.ai.gemini import gemini_service
from app.services.email.resend_service import email_service
from app.config import settings
from app.utils.audit import log_audit

router = APIRouter(prefix="/api/evidence", tags=["ai"])

@router.get("/{id}/validation", response_model=AIValidationOut)
def get_validation(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ev = db.query(Evidence).filter(Evidence.id == id).first()
    if not ev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    if (
        current_user.role == UserRole.BUSINESS_OWNER
        and ev.request.review.assignment.scope.owner_user_id != current_user.id
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    val = db.query(AIValidation).filter(AIValidation.evidence_id == id).order_by(AIValidation.created_at.desc()).first()
    if not val:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No AI validation found for this evidence")
    return val

@router.post("/{id}/revalidate", response_model=AIValidationOut)
async def revalidate_evidence(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reviewer_user)
):
    ev = db.query(Evidence).filter(Evidence.id == id).first()
    if not ev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    if not ev.extracted_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Evidence text has not been extracted yet")

    req = ev.request
    control = req.review.assignment.control
    review = req.review
    scope = req.review.assignment.scope

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
        extracted_text=ev.extracted_text
    )

    validation = AIValidation(
        evidence_id=ev.id,
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

    # Authority rule: update request status
    submission_url = f"{settings.FRONTEND_URL}/submit/{req.secure_token}"
    if validation.status == AIValidationStatus.COMPLETE:
        req.status = EvidenceRequestStatus.COMPLETE
    elif validation.status in [AIValidationStatus.INCOMPLETE, AIValidationStatus.IRRELEVANT]:
        req.status = EvidenceRequestStatus.INCOMPLETE

    db.commit()
    db.refresh(validation)

    log_audit(
        db,
        action="EVIDENCE_REVALIDATED",
        entity_type="ai_validation",
        entity_id=validation.id,
        user_id=current_user.id,
        metadata_json={"validation_status": validation.status.value, "confidence": validation.confidence}
    )

    return validation
