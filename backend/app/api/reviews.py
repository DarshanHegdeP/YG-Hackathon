import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db
from app.models import Review, ReviewStatus, ControlAssignment, EvidenceRequest, EvidenceRequestStatus, User
from app.schemas import ReviewCreate, ReviewUpdate, ReviewOut
from app.api.deps import get_reviewer_or_admin, get_current_user
from app.services.email.resend_service import email_service
from app.utils.audit import log_audit

router = APIRouter(prefix="/api/reviews", tags=["reviews"])

def generate_request_code(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    count = db.query(EvidenceRequest).count() + 1
    return f"REQ-{year}-{count:04d}"

@router.get("", response_model=List[ReviewOut])
def list_reviews(
    status_filter: Optional[ReviewStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Review)
    if status_filter:
        query = query.filter(Review.status == status_filter)
    return query.order_by(Review.due_date.asc()).all()

@router.post("", response_model=ReviewOut)
def create_review(
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reviewer_or_admin)
):
    assignment = db.query(ControlAssignment).filter(ControlAssignment.id == payload.control_assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Control assignment not found")

    review = Review(
        control_assignment_id=payload.control_assignment_id,
        period_start=payload.period_start,
        period_end=payload.period_end,
        due_date=payload.due_date,
        status=payload.status,
    )
    db.add(review)
    db.flush()

    # Automatically create Evidence Request if requested
    if payload.create_request:
        req_code = generate_request_code(db)
        secure_token = str(uuid.uuid4())
        evidence_req = EvidenceRequest(
            review_id=review.id,
            request_code=req_code,
            status=EvidenceRequestStatus.PENDING,
            requested_at=datetime.now(timezone.utc),
            due_date=payload.due_date,
            reminder_count=0,
            secure_token=secure_token
        )
        db.add(evidence_req)
        db.flush()

        # Send initial request email
        scope = assignment.scope
        control = assignment.control
        requirements = [r.name for r in control.evidence_requirements]
        period_str = f"{review.period_start.strftime('%Y-%m-%d')} to {review.period_end.strftime('%Y-%m-%d')}"
        submission_url = f"{settings.FRONTEND_URL}/submit/{secure_token}"

        email_service.send_initial_request(
            db=db,
            request=evidence_req,
            recipient_email=scope.email,
            control_name=control.name,
            control_code=control.control_code,
            period_str=period_str,
            requirements=requirements,
            submission_url=submission_url
        )

        log_audit(
            db,
            action="EVIDENCE_REQUEST_CREATED",
            entity_type="evidence_request",
            entity_id=evidence_req.id,
            user_id=current_user.id,
            metadata_json={"request_code": req_code, "recipient": scope.email}
        )

    db.commit()
    db.refresh(review)

    log_audit(
        db,
        action="REVIEW_CREATED",
        entity_type="review",
        entity_id=review.id,
        user_id=current_user.id
    )

    return review

@router.get("/{id}", response_model=ReviewOut)
def get_review(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    review = db.query(Review).filter(Review.id == id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return review

@router.put("/{id}", response_model=ReviewOut)
def update_review(
    id: int,
    payload: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reviewer_or_admin)
):
    review = db.query(Review).filter(Review.id == id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    if payload.period_start is not None:
        review.period_start = payload.period_start
    if payload.period_end is not None:
        review.period_end = payload.period_end
    if payload.due_date is not None:
        review.due_date = payload.due_date
    if payload.status is not None:
        review.status = payload.status

    db.commit()
    db.refresh(review)

    log_audit(
        db,
        action="REVIEW_UPDATED",
        entity_type="review",
        entity_id=review.id,
        user_id=current_user.id
    )

    return review
