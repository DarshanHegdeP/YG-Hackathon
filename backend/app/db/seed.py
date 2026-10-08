import uuid
from datetime import datetime, timezone, timedelta
from app.db.session import SessionLocal, engine, Base
from app.config import settings
from app.models import (
    User, UserRole, Scope, ScopeType, Control, ControlEvidenceRequirement,
    ControlAssignment, Review, ReviewStatus, EvidenceRequest, EvidenceRequestStatus,
    Communication, CommunicationType, AuditLog, Evidence, EvidenceProcessingStatus,
    AIValidation, AIValidationStatus, AIRelevance
)
from app.utils.security import get_password_hash

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(User).filter(User.email == "reviewer@example.com").first():
            print("[Seed] Database already seeded. Skipping.")
            return

        print("[Seed] Seeding database with realistic LOD2 control testing demo data...")
        now = datetime.now(timezone.utc)
        demo_password_hash = get_password_hash("Password123!")

        # 1. Users
        reviewer_user = User(
            name="Alice Reviewer",
            email="reviewer@example.com",
            password_hash=demo_password_hash,
            role=UserRole.REVIEWER,
            is_active=True
        )
        business_owner = User(
            name="Bob Business Owner",
            email="business@example.com",
            password_hash=demo_password_hash,
            role=UserRole.BUSINESS_OWNER,
            is_active=True
        )
        escalation_contact = User(
            name="Edward Escalation",
            email="escalation@example.com",
            password_hash=demo_password_hash,
            role=UserRole.BUSINESS_OWNER,
            is_active=True
        )

        db.add_all([reviewer_user, business_owner, escalation_contact])
        db.flush()

        # 2. Scopes
        scope_it_ops = Scope(
            type=ScopeType.TEAM,
            name="IT Operations Team",
            description="Core infrastructure and system administration team",
            owner_user_id=business_owner.id,
            email="it-ops@example.com",
            escalation_user_id=escalation_contact.id,
            metadata_json={"tier": 1, "lead": "Bob Business"}
        )
        scope_finance = Scope(
            type=ScopeType.TEAM,
            name="Finance Team",
            description="Corporate accounting and financial controllership",
            owner_user_id=business_owner.id,
            email="finance-team@example.com",
            escalation_user_id=escalation_contact.id,
            metadata_json={"cost_center": "CC-904"}
        )
        scope_john = Scope(
            type=ScopeType.PERSON,
            name="Jai Ram",
            description="Senior Database Administrator & Access Custodian",
            owner_user_id=business_owner.id,
            email="jairam@gmail.com",
            escalation_user_id=escalation_contact.id,
            metadata_json={"employee_id": "EMP-4401"}
        )
        scope_payments = Scope(
            type=ScopeType.APPLICATION,
            name="Payments Application",
            description="Core real-time payment processing platform",
            owner_user_id=business_owner.id,
            email="payments-app-owner@example.com",
            escalation_user_id=escalation_contact.id,
            metadata_json={"criticality": "TIER_0", "repo": "payments-core"}
        )

        db.add_all([scope_it_ops, scope_finance, scope_john, scope_payments])
        db.flush()

        # 3. Controls & Requirements
        ctrl_access = Control(
            control_code="C001",
            name="Periodic User Access Review",
            description="Evidence must demonstrate that user access was reviewed for the specified period and approved by an authorized reviewer.",
            frequency="QUARTERLY",
            status="ACTIVE"
        )
        ctrl_changes = Control(
            control_code="C002",
            name="Production Change Management Authorization",
            description="Evidence must demonstrate that all production code deployments were formally requested, peer-reviewed, and authorized prior to release.",
            frequency="MONTHLY",
            status="ACTIVE"
        )
        db.add_all([ctrl_access, ctrl_changes])
        db.flush()

        # Requirements for C001
        c1_r1 = ControlEvidenceRequirement(control_id=ctrl_access.id, name="Access Review Report", description="Listing of active users and granted privileges exported from authoritative source", mandatory=True)
        c1_r2 = ControlEvidenceRequirement(control_id=ctrl_access.id, name="Reviewer Confirmation", description="Attestation from department manager confirming access appropriateness", mandatory=True)
        c1_r3 = ControlEvidenceRequirement(control_id=ctrl_access.id, name="Approval Evidence", description="Timestamped approval email or ticket signoff", mandatory=True)
        c1_r4 = ControlEvidenceRequirement(control_id=ctrl_access.id, name="Exception Report", description="Documentation of revoked access or authorized exceptions", mandatory=True)

        # Requirements for C002
        c2_r1 = ControlEvidenceRequirement(control_id=ctrl_changes.id, name="Change Request Ticket with Peer Review", description="PR or JIRA ticket showing 2 peer reviews", mandatory=True)
        c2_r2 = ControlEvidenceRequirement(control_id=ctrl_changes.id, name="Automated Test Results Summary", description="Passing CI/CD pipeline pipeline report", mandatory=True)
        c2_r3 = ControlEvidenceRequirement(control_id=ctrl_changes.id, name="Production Release Authorization Sign-off", description="Change Advisory Board (CAB) approval signoff", mandatory=True)

        db.add_all([c1_r1, c1_r2, c1_r3, c1_r4, c2_r1, c2_r2, c2_r3])
        db.flush()

        # 4. Control Assignments
        assign_1 = ControlAssignment(
            control_id=ctrl_access.id,
            scope_id=scope_it_ops.id,
            reviewer_id=reviewer_user.id,
            frequency="QUARTERLY",
            effective_from=now - timedelta(days=90),
            status="ACTIVE"
        )
        assign_2 = ControlAssignment(
            control_id=ctrl_access.id,
            scope_id=scope_finance.id,
            reviewer_id=reviewer_user.id,
            frequency="QUARTERLY",
            effective_from=now - timedelta(days=90),
            status="ACTIVE"
        )
        assign_3 = ControlAssignment(
            control_id=ctrl_changes.id,
            scope_id=scope_payments.id,
            reviewer_id=reviewer_user.id,
            frequency="MONTHLY",
            effective_from=now - timedelta(days=60),
            status="ACTIVE"
        )
        assign_4 = ControlAssignment(
            control_id=ctrl_access.id,
            scope_id=scope_john.id,
            reviewer_id=reviewer_user.id,
            frequency="QUARTERLY",
            effective_from=now - timedelta(days=90),
            status="ACTIVE"
        )
        db.add_all([assign_1, assign_2, assign_3, assign_4])
        db.flush()

        # 5. Reviews
        # Review 1: Open / In Progress
        rev_1 = Review(
            control_assignment_id=assign_1.id,
            period_start=now - timedelta(days=90),
            period_end=now,
            due_date=now + timedelta(days=5),
            status=ReviewStatus.IN_PROGRESS
        )
        # Review 2: Overdue Review
        rev_2 = Review(
            control_assignment_id=assign_2.id,
            period_start=now - timedelta(days=120),
            period_end=now - timedelta(days=30),
            due_date=now - timedelta(days=3),
            status=ReviewStatus.OVERDUE
        )
        # Review 3: Completed Review
        rev_3 = Review(
            control_assignment_id=assign_3.id,
            period_start=now - timedelta(days=60),
            period_end=now - timedelta(days=30),
            due_date=now - timedelta(days=10),
            status=ReviewStatus.COMPLETED
        )
        # Review 4: Open Review for John Smith
        rev_4 = Review(
            control_assignment_id=assign_4.id,
            period_start=now - timedelta(days=90),
            period_end=now,
            due_date=now + timedelta(days=1),
            status=ReviewStatus.OPEN
        )
        db.add_all([rev_1, rev_2, rev_3, rev_4])
        db.flush()

        # 6. Evidence Requests
        # Request 1: Pending (Active demo request for IT Ops)
        token_1 = "demo-token-itops-2026-0001"
        req_1 = EvidenceRequest(
            review_id=rev_1.id,
            request_code="REQ-2026-0001",
            status=EvidenceRequestStatus.PENDING,
            requested_at=now - timedelta(days=2),
            due_date=now + timedelta(days=5),
            reminder_count=0,
            secure_token=token_1
        )
        # Request 2: Overdue Request (Finance Team)
        token_2 = "demo-token-finance-2026-0002"
        req_2 = EvidenceRequest(
            review_id=rev_2.id,
            request_code="REQ-2026-0002",
            status=EvidenceRequestStatus.OVERDUE,
            requested_at=now - timedelta(days=14),
            due_date=now - timedelta(days=3),
            reminder_count=3,
            last_reminder_at=now - timedelta(days=1),
            secure_token=token_2
        )
        # Request 3: Complete Request (Payments App)
        token_3 = "demo-token-payments-2026-0003"
        req_3 = EvidenceRequest(
            review_id=rev_3.id,
            request_code="REQ-2026-0003",
            status=EvidenceRequestStatus.COMPLETE,
            requested_at=now - timedelta(days=25),
            due_date=now - timedelta(days=10),
            reminder_count=1,
            completed_at=now - timedelta(days=12),
            secure_token=token_3
        )
        # Request 4: Incomplete Request (John Smith)
        token_4 = "demo-token-john-2026-0004"
        req_4 = EvidenceRequest(
            review_id=rev_4.id,
            request_code="REQ-2026-0004",
            status=EvidenceRequestStatus.INCOMPLETE,
            requested_at=now - timedelta(days=4),
            due_date=now + timedelta(days=1),
            reminder_count=1,
            last_reminder_at=now - timedelta(days=1),
            secure_token=token_4
        )
        db.add_all([req_1, req_2, req_3, req_4])
        db.flush()

        # 7. Communications history
        comm_1 = Communication(
            request_id=req_1.id,
            type=CommunicationType.INITIAL_REQUEST,
            recipient=scope_it_ops.email,
            subject=f"Action Required: LOD2 Evidence Request {req_1.request_code}",
            provider_message_id="msg_resend_demo_001",
            status="SENT",
            sent_at=now - timedelta(days=2),
            metadata_json={"submission_url": f"{settings.FRONTEND_URL}/submit/{token_1}"}        )
        comm_2_1 = Communication(
            request_id=req_2.id,
            type=CommunicationType.INITIAL_REQUEST,
            recipient=scope_finance.email,
            subject=f"Action Required: LOD2 Evidence Request {req_2.request_code}",
            provider_message_id="msg_resend_demo_002",
            status="SENT",
            sent_at=now - timedelta(days=14),
            metadata_json={"submission_url": f"{settings.FRONTEND_URL}/submit/{token_2}"}        )
        comm_2_2 = Communication(
            request_id=req_2.id,
            type=CommunicationType.REMINDER_1,
            recipient=scope_finance.email,
            subject=f"Reminder #1: LOD2 Evidence Request {req_2.request_code}",
            provider_message_id="msg_resend_demo_003",
            status="SENT",
            sent_at=now - timedelta(days=5)
        )
        comm_2_3 = Communication(
            request_id=req_2.id,
            type=CommunicationType.ESCALATION,
            recipient=escalation_contact.email,
            subject=f"ESCALATION: Overdue Evidence Request {req_2.request_code}",
            provider_message_id="msg_resend_demo_004",
            status="SENT",
            sent_at=now - timedelta(days=1)
        )
        comm_4_1 = Communication(
            request_id=req_4.id,
            type=CommunicationType.MISSING_EVIDENCE,
            recipient=scope_john.email,
            subject=f"Additional Evidence Required — {req_4.request_code}",
            provider_message_id="msg_resend_demo_005",
            status="SENT",
            sent_at=now - timedelta(days=1),
            metadata_json={"missing_items": ["Exception Report", "Approval Evidence"]}
        )
        db.add_all([comm_1, comm_2_1, comm_2_2, comm_2_3, comm_4_1])
        db.flush()

        # 8. Sample Evidence and AI Validations for Complete and Incomplete requests
        ev_complete = Evidence(
            request_id=req_3.id,
            file_name="Payment_Gateway_CAB_Release_Bundle.pdf",
            file_type=".pdf",
            storage_path="mock_payment_bundle.pdf",
            file_size=204850,
            sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            processing_status=EvidenceProcessingStatus.PROCESSED,
            extracted_text="=== PAGE 1 ===\nProduction Change Request #PR-892\nPeer Reviews: 2 Approved by Lead Architect and QA Lead\nAutomated Test Results: 142/142 tests passed in CI/CD pipeline\nCAB Approval: Signed off by Operations Director on 2026-09-15",
            uploaded_at=now - timedelta(days=13),
            processed_at=now - timedelta(days=13)
        )
        db.add(ev_complete)
        db.flush()

        val_complete = AIValidation(
            evidence_id=ev_complete.id,
            status=AIValidationStatus.COMPLETE,
            relevance=AIRelevance.HIGH,
            confidence=0.96,
            findings=[
                "Change Request ticket contains verified peer review approvals.",
                "Automated test pipeline report verified with 100% pass rate.",
                "CAB Director approval signature and timestamp verified."
            ],
            missing_information=[],
            reason="The submitted evidence demonstrates all mandatory release criteria, testing verifications, and authorized CAB sign-offs.",
            model="gemini-1.5-flash",
            raw_response='{"status": "COMPLETE", "relevance": "HIGH", "confidence": 0.96}'
        )
        db.add(val_complete)

        # Incomplete evidence for John Smith
        ev_incomplete = Evidence(
            request_id=req_4.id,
            file_name="Database_User_List_Export.xlsx",
            file_type=".xlsx",
            storage_path="mock_user_list.xlsx",
            file_size=65400,
            sha256="c54c3b53c156f0e213322a3cfef9d3a7c6f09e25d25e0c5218d6e32155799a4c",
            processing_status=EvidenceProcessingStatus.PROCESSED,
            extracted_text="=== SHEET: Users ===\nColumns: user_id, username, role, active\n1 | db_admin | DBA | True\n2 | read_only | Analyst | True\nRow count: 2",
            uploaded_at=now - timedelta(days=1),
            processed_at=now - timedelta(days=1)
        )
        db.add(ev_incomplete)
        db.flush()

        val_incomplete = AIValidation(
            evidence_id=ev_incomplete.id,
            status=AIValidationStatus.INCOMPLETE,
            relevance=AIRelevance.HIGH,
            confidence=0.91,
            findings=[
                "User access roster is present with accounts and roles."
            ],
            missing_information=[
                "Reviewer Confirmation",
                "Approval Evidence",
                "Exception Report"
            ],
            reason="The submitted user list covers account inventories, but lacks required formal reviewer attestation, management approval signoff, and exception documentation.",
            model="gemini-1.5-flash",
            raw_response='{"status": "INCOMPLETE", "relevance": "HIGH", "confidence": 0.91}'
        )
        db.add(val_incomplete)

        # 9. Audit Logs
        log_1 = AuditLog(
            user_id=reviewer_user.id,
            action="CONTROL_CREATED",
            entity_type="control",
            entity_id=ctrl_access.id,
            metadata_json={"control_code": "C001"},
            timestamp=now - timedelta(days=90)
        )
        log_2 = AuditLog(
            user_id=reviewer_user.id,
            action="REVIEW_CREATED",
            entity_type="review",
            entity_id=rev_1.id,
            metadata_json={"period": "Q3 2026"},
            timestamp=now - timedelta(days=2)
        )
        log_3 = AuditLog(
            user_id=reviewer_user.id,
            action="EVIDENCE_REQUEST_CREATED",
            entity_type="evidence_request",
            entity_id=req_1.id,
            metadata_json={"request_code": "REQ-2026-0001"},
            timestamp=now - timedelta(days=2)
        )
        db.add_all([log_1, log_2, log_3])

        db.commit()
        print("[Seed] Successfully seeded demo users, controls, scopes, assignments, reviews, requests, and validations!")

    except Exception as e:
        db.rollback()
        print(f"[Seed] Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
