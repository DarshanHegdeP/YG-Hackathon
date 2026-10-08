import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db
from app.models import (
    EvidenceRequest, EvidenceRequestStatus, Review, User, Scope, Control,
    CommunicationType
)
from app.schemas import (
    EvidenceRequestCreate, EvidenceRequestUpdate, EvidenceRequestOut,
    EvidenceRequestPublicOut, EvidenceRequirementOut, EvidenceOut, AIValidationOut
)
from app.api.deps import get_reviewer_or_admin, get_current_user
from app.services.email.resend_service import email_service
from app.utils.audit import log_audit

router = APIRouter(prefix="/api/evidence-requests", tags=["evidence-requests"])

def generate_request_code(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    count = db.query(EvidenceRequest).count() + 1
    return f"REQ-{year}-{count:04d}"

@router.get("", response_model=List[EvidenceRequestOut])
def list_requests(
    status_filter: Optional[EvidenceRequestStatus] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    scope_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(EvidenceRequest)
    if status_filter:
        query = query.filter(EvidenceRequest.status == status_filter)
    if search:
        s = f"%{search}%"
        query = query.filter(EvidenceRequest.request_code.ilike(s))

    requests = query.order_by(EvidenceRequest.created_at.desc()).all()

    if scope_type:
        requests = [
            r for r in requests
            if r.review and r.review.assignment and r.review.assignment.scope and r.review.assignment.scope.type.value == scope_type
        ]

    return requests

@router.post("", response_model=EvidenceRequestOut)
def create_request(
    payload: EvidenceRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reviewer_or_admin)
):
    review = db.query(Review).filter(Review.id == payload.review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    due_date = payload.due_date or review.due_date
    req_code = generate_request_code(db)
    secure_token = str(uuid.uuid4())

    req = EvidenceRequest(
        review_id=review.id,
        request_code=req_code,
        status=EvidenceRequestStatus.PENDING,
        requested_at=datetime.now(timezone.utc),
        due_date=due_date,
        reminder_count=0,
        secure_token=secure_token
    )
    db.add(req)
    db.flush()

    # Send initial email
    assignment = review.assignment
    scope = assignment.scope
    control = assignment.control
    requirements = [r.name for r in control.evidence_requirements]
    period_str = f"{review.period_start.strftime('%Y-%m-%d')} to {review.period_end.strftime('%Y-%m-%d')}"
    submission_url = f"{settings.FRONTEND_URL}/submit/{secure_token}"

    email_service.send_initial_request(
        db=db,
        request=req,
        recipient_email=scope.email,
        control_name=control.name,
        control_code=control.control_code,
        period_str=period_str,
        requirements=requirements,
        submission_url=submission_url
    )

    db.commit()
    db.refresh(req)

    log_audit(
        db,
        action="EVIDENCE_REQUEST_CREATED",
        entity_type="evidence_request",
        entity_id=req.id,
        user_id=current_user.id,
        metadata_json={"request_code": req_code, "recipient": scope.email}
    )

    return req

# PUBLIC ENDPOINT FOR EVIDENCE RECIPIENT
@router.get("/token/{token}", response_model=EvidenceRequestPublicOut)
def get_request_by_token(token: str, db: Session = Depends(get_db)):
    req = db.query(EvidenceRequest).filter(EvidenceRequest.secure_token == token).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid submission link or token expired")

    review = req.review
    assignment = review.assignment if review else None
    control = assignment.control if assignment else None
    scope = assignment.scope if assignment else None

    if not control or not scope:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Associated control or scope missing")

    req_list = [
        EvidenceRequirementOut.model_validate(r) for r in control.evidence_requirements
    ]
    uploaded_evidences = [
        EvidenceOut.model_validate(e) for e in req.evidences
    ]

    latest_val = None
    if req.evidences:
        latest_ev = req.evidences[-1]
        if latest_ev.validations:
            latest_val = AIValidationOut.model_validate(latest_ev.validations[-1])

    return EvidenceRequestPublicOut(
        request_code=req.request_code,
        secure_token=req.secure_token,
        status=req.status,
        due_date=req.due_date,
        requested_at=req.requested_at,
        control_code=control.control_code,
        control_name=control.name,
        control_description=control.description,
        scope_name=scope.name,
        scope_type=scope.type.value,
        recipient_email=scope.email,
        period_start=review.period_start,
        period_end=review.period_end,
        required_evidence=req_list,
        uploaded_evidences=uploaded_evidences,
        latest_validation=latest_val
    )

@router.get("/{id}", response_model=EvidenceRequestOut)
def get_request(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    req = db.query(EvidenceRequest).filter(EvidenceRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence request not found")
    return req

@router.put("/{id}", response_model=EvidenceRequestOut)
def update_request(
    id: int,
    payload: EvidenceRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reviewer_or_admin)
):
    req = db.query(EvidenceRequest).filter(EvidenceRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence request not found")

    if payload.due_date is not None:
        req.due_date = payload.due_date
    if payload.status is not None:
        req.status = payload.status
        if payload.status == EvidenceRequestStatus.COMPLETE:
            req.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(req)

    log_audit(
        db,
        action="EVIDENCE_REQUEST_UPDATED",
        entity_type="evidence_request",
        entity_id=req.id,
        user_id=current_user.id
    )

    return req

@router.post("/{id}/remind", response_model=EvidenceRequestOut)
def send_manual_reminder(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reviewer_or_admin)
):
    req = db.query(EvidenceRequest).filter(EvidenceRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence request not found")

    review = req.review
    scope = review.assignment.scope
    submission_url = f"{settings.FRONTEND_URL}/submit/{req.secure_token}"

    email_service.send_reminder(
        db=db,
        request=req,
        recipient_email=scope.email,
        reminder_num=req.reminder_count + 1,
        submission_url=submission_url
    )

    req.reminder_count += 1
    req.last_reminder_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(req)

    log_audit(
        db,
        action="MANUAL_REMINDER_SENT",
        entity_type="evidence_request",
        entity_id=req.id,
        user_id=current_user.id,
        metadata_json={"recipient": scope.email}
    )

    return req

@router.post("/{id}/escalate", response_model=EvidenceRequestOut)
def send_manual_escalation(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reviewer_or_admin)
):
    req = db.query(EvidenceRequest).filter(EvidenceRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence request not found")

    review = req.review
    scope = review.assignment.scope
    escalation_email = scope.escalation_user.email if scope.escalation_user else scope.email
    submission_url = f"{settings.FRONTEND_URL}/submit/{req.secure_token}"

    email_service.send_escalation(
        db=db,
        request=req,
        escalation_email=escalation_email,
        original_recipient=scope.email,
        submission_url=submission_url
    )

    req.status = EvidenceRequestStatus.OVERDUE
    req.reminder_count += 1
    req.last_reminder_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(req)

    log_audit(
        db,
        action="MANUAL_ESCALATION_SENT",
        entity_type="evidence_request",
        entity_id=req.id,
        user_id=current_user.id,
        metadata_json={"escalation_email": escalation_email}
    )

    return req

@router.post("/{id}/mark-complete", response_model=EvidenceRequestOut)
def mark_request_complete(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reviewer_or_admin)
):
    req = db.query(EvidenceRequest).filter(EvidenceRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence request not found")

    req.status = EvidenceRequestStatus.COMPLETE
    req.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(req)

    scope = req.review.assignment.scope
    email_service.send_completion(db=db, request=req, recipient_email=scope.email)

    log_audit(
        db,
        action="REQUEST_MARKED_COMPLETE",
        entity_type="evidence_request",
        entity_id=req.id,
        user_id=current_user.id
    )

    return req
