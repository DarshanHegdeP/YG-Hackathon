from datetime import datetime, timezone
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models import (
    Control, ControlAssignment, Review, ReviewStatus,
    EvidenceRequest, EvidenceRequestStatus, Scope, User, UserRole
)
from app.schemas import DashboardSummaryOut, OverdueRequestOut, EvidenceRequestOut
from app.api.deps import get_current_user, get_reviewer_user
from app.services.reminders.reminder_engine import reminder_engine

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/summary", response_model=DashboardSummaryOut)
def get_dashboard_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    owner_dashboard = current_user.role == UserRole.BUSINESS_OWNER
    if owner_dashboard:
        total_controls = (
            db.query(func.count(func.distinct(ControlAssignment.control_id)))
            .join(Scope)
            .filter(Scope.owner_user_id == current_user.id)
            .scalar()
        )
        active_assignments = (
            db.query(ControlAssignment)
            .join(Scope)
            .filter(
                Scope.owner_user_id == current_user.id,
                ControlAssignment.status == "ACTIVE",
            )
            .count()
        )
        active_reviews_query = (
            db.query(Review)
            .join(ControlAssignment)
            .join(Scope)
            .filter(Scope.owner_user_id == current_user.id)
        )
        request_query = (
            db.query(EvidenceRequest)
            .join(Review)
            .join(ControlAssignment)
            .join(Scope)
            .filter(Scope.owner_user_id == current_user.id)
        )
        scope_query = db.query(Scope).filter(Scope.owner_user_id == current_user.id)
    else:
        total_controls = db.query(Control).count()
        active_assignments = db.query(ControlAssignment).filter(ControlAssignment.status == "ACTIVE").count()
        active_reviews_query = db.query(Review)
        request_query = db.query(EvidenceRequest)
        scope_query = db.query(Scope)

    active_reviews = active_reviews_query.filter(
        Review.status.in_([ReviewStatus.OPEN, ReviewStatus.IN_PROGRESS])
    ).count()
    total_requests = request_query.count()
    complete_requests = request_query.filter(EvidenceRequest.status == EvidenceRequestStatus.COMPLETE).count()
    pending_requests = request_query.filter(EvidenceRequest.status == EvidenceRequestStatus.PENDING).count()
    incomplete_requests = request_query.filter(EvidenceRequest.status == EvidenceRequestStatus.INCOMPLETE).count()
    overdue_requests = request_query.filter(EvidenceRequest.status == EvidenceRequestStatus.OVERDUE).count()

    # Status distribution
    status_counts = (
        request_query.with_entities(EvidenceRequest.status, func.count(EvidenceRequest.id))
        .group_by(EvidenceRequest.status)
        .all()
    )
    status_distribution = {s.value: count for s, count in status_counts}

    # Scope distribution
    scope_counts = (
        scope_query.with_entities(Scope.type, func.count(Scope.id))
        .group_by(Scope.type)
        .all()
    )
    scope_distribution = {s.value: count for s, count in scope_counts}

    return DashboardSummaryOut(
        total_controls=total_controls,
        active_assignments=active_assignments,
        active_reviews=active_reviews,
        total_requests=total_requests,
        complete_requests=complete_requests,
        pending_requests=pending_requests,
        incomplete_requests=incomplete_requests,
        overdue_requests=overdue_requests,
        status_distribution=status_distribution,
        scope_distribution=scope_distribution
    )

@router.get("/overdue", response_model=List[OverdueRequestOut])
def get_overdue_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    overdue_query = db.query(EvidenceRequest).filter(
        EvidenceRequest.status == EvidenceRequestStatus.OVERDUE
    )
    if current_user.role == UserRole.BUSINESS_OWNER:
        overdue_query = overdue_query.join(Review).join(ControlAssignment).join(Scope).filter(
            Scope.owner_user_id == current_user.id
        )
    overdue_reqs = overdue_query.all()

    out = []
    for req in overdue_reqs:
        due_date = req.due_date.replace(tzinfo=timezone.utc) if req.due_date.tzinfo is None else req.due_date
        days = max(1, (now - due_date).days)
        review = req.review
        assignment = review.assignment if review else None
        control = assignment.control if assignment else None
        scope = assignment.scope if assignment else None

        out.append(OverdueRequestOut(
            id=req.id,
            request_code=req.request_code,
            control_name=control.name if control else "Unknown",
            scope_name=scope.name if scope else "Unknown",
            recipient=scope.email if scope else "Unknown",
            due_date=req.due_date,
            days_overdue=days,
            reminder_count=req.reminder_count
        ))
    return out

@router.post("/trigger-reminders")
def trigger_reminders_manually(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reviewer_user)
):
    """
    Allows reviewers to manually invoke the reminder & escalation engine.
    Great for hackathon demonstrations!
    """
    results = reminder_engine.process_reminders(db)
    return {"message": "Reminder engine executed successfully", "results": results}
