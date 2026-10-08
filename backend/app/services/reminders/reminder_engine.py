from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.config import settings
from app.models import (
    EvidenceRequest, EvidenceRequestStatus, Communication, CommunicationType,
    Review, ControlAssignment, Scope, Control, AuditLog, User
)
from app.services.email.resend_service import email_service
from app.utils.audit import log_audit

class ReminderEngine:
    @staticmethod
    def process_reminders(db: Session) -> Dict[str, Any]:
        """
        Runs automated evaluation of all open evidence requests,
        sending reminders or escalations idempotently based on PostgreSQL database state.
        """
        now = datetime.now(timezone.utc)
        active_statuses = [EvidenceRequestStatus.PENDING, EvidenceRequestStatus.INCOMPLETE]

        requests = db.query(EvidenceRequest).filter(
            EvidenceRequest.status.in_(active_statuses)
        ).all()

        results = {
            "evaluated_count": len(requests),
            "reminders_sent": 0,
            "escalations_sent": 0,
            "marked_overdue": 0,
            "actions": []
        }

        for req in requests:
            # Resolve scope and recipient
            review = req.review
            if not review or not review.assignment:
                continue

            assignment = review.assignment
            scope = assignment.scope
            if not scope:
                continue

            recipient_email = scope.email
            escalation_email = None
            if scope.escalation_user:
                escalation_email = scope.escalation_user.email
            elif scope.escalation_user_id:
                esc_user = db.query(User).filter(User.id == scope.escalation_user_id).first()
                if esc_user:
                    escalation_email = esc_user.email
            if not escalation_email:
                escalation_email = recipient_email

            submission_url = f"{settings.FRONTEND_URL}/submit/{req.secure_token}"

            # Calculate time difference
            # Due date is UTC
            due_date = req.due_date.replace(tzinfo=timezone.utc) if req.due_date.tzinfo is None else req.due_date
            time_to_due = due_date - now
            days_to_due = time_to_due.total_seconds() / 86400.0

            # Get past communication types for this request
            past_comm_types = set(
                db.query(Communication.type)
                .filter(Communication.request_id == req.id)
                .all()
            )
            past_comm_types = {t[0] for t in past_comm_types}

            # 1. Escalation: overdue past escalation threshold
            if days_to_due <= -settings.ESCALATION_DAYS_AFTER:
                # Mark as overdue if not already
                if req.status != EvidenceRequestStatus.OVERDUE:
                    req.status = EvidenceRequestStatus.OVERDUE
                    results["marked_overdue"] += 1

                if CommunicationType.ESCALATION not in past_comm_types:
                    email_service.send_escalation(
                        db=db,
                        request=req,
                        escalation_email=escalation_email,
                        original_recipient=recipient_email,
                        submission_url=submission_url
                    )
                    req.reminder_count += 1
                    req.last_reminder_at = now
                    results["escalations_sent"] += 1
                    results["actions"].append(f"Escalation sent for {req.request_code} to {escalation_email}")

                    log_audit(
                        db=db,
                        action="ESCALATION_SENT",
                        entity_type="evidence_request",
                        entity_id=req.id,
                        metadata_json={"recipient": escalation_email, "days_overdue": abs(round(days_to_due, 1))}
                    )

            # 2. Final Reminder: on or just past due date
            elif days_to_due <= 0.0 and days_to_due > -settings.ESCALATION_DAYS_AFTER:
                if CommunicationType.FINAL_REMINDER not in past_comm_types:
                    email_service.send_final_reminder(
                        db=db,
                        request=req,
                        recipient_email=recipient_email,
                        submission_url=submission_url
                    )
                    req.reminder_count += 1
                    req.last_reminder_at = now
                    results["reminders_sent"] += 1
                    results["actions"].append(f"Final reminder sent for {req.request_code}")

                    log_audit(
                        db=db,
                        action="FINAL_REMINDER_SENT",
                        entity_type="evidence_request",
                        entity_id=req.id,
                        metadata_json={"recipient": recipient_email}
                    )

            # 3. Reminder 2: 1 day before due date
            elif days_to_due <= settings.REMINDER_2_DAYS_BEFORE and days_to_due > 0.0:
                if CommunicationType.REMINDER_2 not in past_comm_types:
                    email_service.send_reminder(
                        db=db,
                        request=req,
                        recipient_email=recipient_email,
                        reminder_num=2,
                        submission_url=submission_url
                    )
                    req.reminder_count += 1
                    req.last_reminder_at = now
                    results["reminders_sent"] += 1
                    results["actions"].append(f"Reminder 2 sent for {req.request_code}")

                    log_audit(
                        db=db,
                        action="REMINDER_2_SENT",
                        entity_type="evidence_request",
                        entity_id=req.id,
                        metadata_json={"recipient": recipient_email}
                    )

            # 4. Reminder 1: 2 days before due date
            elif days_to_due <= settings.REMINDER_1_DAYS_BEFORE and days_to_due > settings.REMINDER_2_DAYS_BEFORE:
                if CommunicationType.REMINDER_1 not in past_comm_types:
                    email_service.send_reminder(
                        db=db,
                        request=req,
                        recipient_email=recipient_email,
                        reminder_num=1,
                        submission_url=submission_url
                    )
                    req.reminder_count += 1
                    req.last_reminder_at = now
                    results["reminders_sent"] += 1
                    results["actions"].append(f"Reminder 1 sent for {req.request_code}")

                    log_audit(
                        db=db,
                        action="REMINDER_1_SENT",
                        entity_type="evidence_request",
                        entity_id=req.id,
                        metadata_json={"recipient": recipient_email}
                    )

            db.commit()

        return results

reminder_engine = ReminderEngine()
