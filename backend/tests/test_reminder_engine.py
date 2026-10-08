import uuid
from datetime import datetime, timezone, timedelta
from app.models import (
    User, UserRole, Scope, ScopeType, Control, ControlAssignment,
    Review, ReviewStatus, EvidenceRequest, EvidenceRequestStatus,
    Communication, CommunicationType
)
from app.services.reminders.reminder_engine import reminder_engine

def test_reminder_engine_escalation_and_idempotency(db_session, reviewer_user):
    now = datetime.now(timezone.utc)

    # Setup Scope
    scope = Scope(
        type=ScopeType.TEAM,
        name="Security Ops",
        email="secops@example.com",
        escalation_user_id=reviewer_user.id
    )
    db_session.add(scope)
    db_session.flush()

    # Setup Control
    control = Control(
        control_code="C010",
        name="Log Monitoring",
        description="Verify weekly logs",
        frequency="WEEKLY",
        status="ACTIVE"
    )
    db_session.add(control)
    db_session.flush()

    # Setup Assignment
    assignment = ControlAssignment(
        control_id=control.id,
        scope_id=scope.id,
        reviewer_id=reviewer_user.id,
        frequency="WEEKLY",
        effective_from=now - timedelta(days=30),
        status="ACTIVE"
    )
    db_session.add(assignment)
    db_session.flush()

    # Setup Overdue Review (due 2 days ago)
    review = Review(
        control_assignment_id=assignment.id,
        period_start=now - timedelta(days=10),
        period_end=now - timedelta(days=3),
        due_date=now - timedelta(days=2),
        status=ReviewStatus.OPEN
    )
    db_session.add(review)
    db_session.flush()

    # Setup Evidence Request
    req = EvidenceRequest(
        review_id=review.id,
        request_code="REQ-TEST-0001",
        status=EvidenceRequestStatus.PENDING,
        requested_at=now - timedelta(days=5),
        due_date=now - timedelta(days=2),
        reminder_count=0,
        secure_token=str(uuid.uuid4())
    )
    db_session.add(req)
    db_session.commit()

    # 1. Run reminder engine
    res1 = reminder_engine.process_reminders(db_session)
    assert res1["escalations_sent"] == 1
    assert res1["marked_overdue"] == 1

    db_session.refresh(req)
    assert req.status == EvidenceRequestStatus.OVERDUE
    assert req.reminder_count == 1

    # Check communication recorded
    comms = db_session.query(Communication).filter(Communication.request_id == req.id).all()
    assert len(comms) == 1
    assert comms[0].type == CommunicationType.ESCALATION

    # 2. Run reminder engine AGAIN — must be idempotent and NOT send another duplicate escalation
    res2 = reminder_engine.process_reminders(db_session)
    assert res2["escalations_sent"] == 0
    assert res2["reminders_sent"] == 0
