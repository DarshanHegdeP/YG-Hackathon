import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.config import settings
from app.models import Communication, CommunicationType, EvidenceRequest

class EmailService:
    def __init__(self):
        self.api_key = settings.RESEND_API_KEY
        self.sender = settings.EMAIL_FROM
        self.resend_client = None

        if self.api_key and self.api_key != "re_your_resend_api_key":
            try:
                import resend
                resend.api_key = self.api_key
                self.resend_client = resend
            except Exception as e:
                print(f"[EmailService] Failed to initialize Resend: {e}")

    def _record_communication(
        self,
        db: Session,
        request_id: int,
        comm_type: CommunicationType,
        recipient: str,
        subject: str,
        status: str,
        provider_message_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Communication:
        comm = Communication(
            request_id=request_id,
            type=comm_type,
            recipient=recipient,
            subject=subject,
            provider_message_id=provider_message_id,
            status=status,
            sent_at=datetime.now(timezone.utc),
            metadata_json=metadata or {}
        )
        db.add(comm)
        db.commit()
        db.refresh(comm)
        return comm

    def _send_email_raw(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> (str, Optional[str]):
        """
        Sends email via Resend or logs locally if Resend is unconfigured.
        Returns (status, provider_message_id).
        """
        if self.resend_client:
            try:
                params = {
                    "from": self.sender,
                    "to": [to_email],
                    "subject": subject,
                    "html": html_content
                }
                response = self.resend_client.Emails.send(params)
                message_id = response.get("id") if isinstance(response, dict) else str(response)
                return "SENT", message_id
            except Exception as e:
                print(f"[EmailService] Resend delivery error to {to_email}: {e}")
                return "FAILED", None
        else:
            print(f"\n[EmailService MOCK SEND] To: {to_email} | Subject: {subject}\n--- Content Preview ---\n{html_content[:200]}...\n")
            return "SENT", "mock_msg_" + str(int(datetime.now(timezone.utc).timestamp()))

    def send_initial_request(
        self,
        db: Session,
        request: EvidenceRequest,
        recipient_email: str,
        control_name: str,
        control_code: str,
        period_str: str,
        requirements: List[str],
        submission_url: str
    ) -> Communication:
        subject = f"Action Required: LOD2 Evidence Request {request.request_code}"
        req_list_html = "".join([f"<li><strong>{r}</strong></li>" for r in requirements])
        html = f"""
        <div style="font-family: Arial, sans-serif; color: #1e293b; max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px;">
            <div style="border-bottom: 2px solid #3b82f6; padding-bottom: 12px; margin-bottom: 20px;">
                <h2 style="color: #1e40af; margin: 0;">LOD2 Internal Control Evidence Request</h2>
                <span style="font-size: 13px; color: #64748b;">Ref: {request.request_code}</span>
            </div>
            <p>Hello,</p>
            <p>You have been requested to provide evidence for the following second line of defense (LOD2) control assessment:</p>
            <div style="background-color: #f8fafc; padding: 16px; border-radius: 6px; margin: 16px 0;">
                <p style="margin: 4px 0;"><strong>Control:</strong> {control_code} - {control_name}</p>
                <p style="margin: 4px 0;"><strong>Review Period:</strong> {period_str}</p>
                <p style="margin: 4px 0;"><strong>Submission Due Date:</strong> <span style="color: #dc2626; font-weight: bold;">{request.due_date.strftime('%Y-%m-%d')}</span></p>
            </div>
            <p><strong>Required Evidence Items:</strong></p>
            <ul>{req_list_html}</ul>
            <div style="margin: 28px 0; text-align: center;">
                <a href="{submission_url}" style="background-color: #2563eb; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                    Upload & Submit Evidence
                </a>
            </div>
            <p style="font-size: 12px; color: #64748b;">Or copy this secure link into your browser: <br/><a href="{submission_url}">{submission_url}</a></p>
            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 24px 0;" />
            <p style="font-size: 11px; color: #94a3b8;">This is an automated request generated by the AI-Powered Evidence Collection Bot.</p>
        </div>
        """
        status, msg_id = self._send_email_raw(recipient_email, subject, html)
        return self._record_communication(
            db=db,
            request_id=request.id,
            comm_type=CommunicationType.INITIAL_REQUEST,
            recipient=recipient_email,
            subject=subject,
            status=status,
            provider_message_id=msg_id,
            metadata={"submission_url": submission_url}
        )

    def send_missing_evidence(
        self,
        db: Session,
        request: EvidenceRequest,
        recipient_email: str,
        missing_items: List[str],
        reason: str,
        submission_url: str
    ) -> Communication:
        subject = f"Additional Evidence Required — {request.request_code}"
        missing_html = "".join([f"<li style='color: #dc2626;'><strong>{item}</strong></li>" for item in missing_items])
        html = f"""
        <div style="font-family: Arial, sans-serif; color: #1e293b; max-width: 600px; margin: 0 auto; border: 1px solid #fed7aa; border-radius: 8px; padding: 24px;">
            <div style="border-bottom: 2px solid #f97316; padding-bottom: 12px; margin-bottom: 20px;">
                <h2 style="color: #c2410c; margin: 0;">Missing Evidence Notice</h2>
                <span style="font-size: 13px; color: #64748b;">Ref: {request.request_code}</span>
            </div>
            <p>Hello,</p>
            <p>Our automated AI evidence verification analyzed your recent submission and determined that critical required items are missing or incomplete.</p>
            <div style="background-color: #fff7ed; padding: 16px; border-radius: 6px; border-left: 4px solid #f97316; margin: 16px 0;">
                <p style="margin: 0 0 8px 0; font-weight: bold; color: #9a3412;">Audit Findings:</p>
                <p style="margin: 0; color: #431407;">{reason}</p>
            </div>
            <p><strong>Missing Information Needed:</strong></p>
            <ul>{missing_html}</ul>
            <p>Please upload the supplementary documents as soon as possible before the due date (<span style="color: #dc2626; font-weight: bold;">{request.due_date.strftime('%Y-%m-%d')}</span>).</p>
            <div style="margin: 28px 0; text-align: center;">
                <a href="{submission_url}" style="background-color: #ea580c; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                    Upload Supplementary Evidence
                </a>
            </div>
            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 24px 0;" />
            <p style="font-size: 11px; color: #94a3b8;">AI-Powered Evidence Collection Bot</p>
        </div>
        """
        status, msg_id = self._send_email_raw(recipient_email, subject, html)
        return self._record_communication(
            db=db,
            request_id=request.id,
            comm_type=CommunicationType.MISSING_EVIDENCE,
            recipient=recipient_email,
            subject=subject,
            status=status,
            provider_message_id=msg_id,
            metadata={"missing_items": missing_items, "submission_url": submission_url}
        )

    def send_reminder(
        self,
        db: Session,
        request: EvidenceRequest,
        recipient_email: str,
        reminder_num: int,
        submission_url: str
    ) -> Communication:
        comm_type = CommunicationType.REMINDER_1 if reminder_num == 1 else CommunicationType.REMINDER_2
        subject = f"Reminder #{reminder_num}: LOD2 Evidence Request {request.request_code}"
        html = f"""
        <div style="font-family: Arial, sans-serif; color: #1e293b; max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px;">
            <h2 style="color: #1e40af; margin-top: 0;">Evidence Submission Reminder #{reminder_num}</h2>
            <p>This is a reminder that evidence for <strong>{request.request_code}</strong> is due on <strong>{request.due_date.strftime('%Y-%m-%d')}</strong>.</p>
            <div style="margin: 24px 0; text-align: center;">
                <a href="{submission_url}" style="background-color: #2563eb; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                    View & Submit Evidence
                </a>
            </div>
        </div>
        """
        status, msg_id = self._send_email_raw(recipient_email, subject, html)
        return self._record_communication(
            db=db,
            request_id=request.id,
            comm_type=comm_type,
            recipient=recipient_email,
            subject=subject,
            status=status,
            provider_message_id=msg_id
        )

    def send_final_reminder(
        self,
        db: Session,
        request: EvidenceRequest,
        recipient_email: str,
        submission_url: str
    ) -> Communication:
        subject = f"FINAL REMINDER: Evidence Due Today — {request.request_code}"
        html = f"""
        <div style="font-family: Arial, sans-serif; color: #1e293b; max-width: 600px; margin: 0 auto; border: 2px solid #ef4444; border-radius: 8px; padding: 24px;">
            <h2 style="color: #dc2626; margin-top: 0;">Final Reminder: Due Today</h2>
            <p>Your evidence submission for <strong>{request.request_code}</strong> is due <strong>TODAY</strong>.</p>
            <div style="margin: 24px 0; text-align: center;">
                <a href="{submission_url}" style="background-color: #dc2626; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                    Submit Now To Avoid Escalation
                </a>
            </div>
        </div>
        """
        status, msg_id = self._send_email_raw(recipient_email, subject, html)
        return self._record_communication(
            db=db,
            request_id=request.id,
            comm_type=CommunicationType.FINAL_REMINDER,
            recipient=recipient_email,
            subject=subject,
            status=status,
            provider_message_id=msg_id
        )

    def send_escalation(
        self,
        db: Session,
        request: EvidenceRequest,
        escalation_email: str,
        original_recipient: str,
        submission_url: str
    ) -> Communication:
        subject = f"ESCALATION: Overdue Evidence Request {request.request_code}"
        html = f"""
        <div style="font-family: Arial, sans-serif; color: #1e293b; max-width: 600px; margin: 0 auto; border: 2px solid #b91c1c; border-radius: 8px; padding: 24px;">
            <h2 style="color: #991b1b; margin-top: 0;">LOD2 Control Evidence Escalation</h2>
            <p>Evidence request <strong>{request.request_code}</strong> originally assigned to <strong>{original_recipient}</strong> is now overdue (due date was {request.due_date.strftime('%Y-%m-%d')}).</p>
            <p>As the designated escalation contact, please ensure the required control evidence is provided promptly.</p>
            <div style="margin: 24px 0; text-align: center;">
                <a href="{submission_url}" style="background-color: #991b1b; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                    Review Overdue Request
                </a>
            </div>
        </div>
        """
        status, msg_id = self._send_email_raw(escalation_email, subject, html)
        return self._record_communication(
            db=db,
            request_id=request.id,
            comm_type=CommunicationType.ESCALATION,
            recipient=escalation_email,
            subject=subject,
            status=status,
            provider_message_id=msg_id
        )

    def send_completion(
        self,
        db: Session,
        request: EvidenceRequest,
        recipient_email: str
    ) -> Communication:
        subject = f"Evidence Accepted: Complete — {request.request_code}"
        html = f"""
        <div style="font-family: Arial, sans-serif; color: #1e293b; max-width: 600px; margin: 0 auto; border: 1px solid #10b981; border-radius: 8px; padding: 24px;">
            <h2 style="color: #059669; margin-top: 0;">Evidence Review Complete</h2>
            <p>The evidence submitted for <strong>{request.request_code}</strong> has been successfully validated and accepted.</p>
            <p>Thank you for your timely cooperation with the LOD2 control testing process.</p>
        </div>
        """
        status, msg_id = self._send_email_raw(recipient_email, subject, html)
        return self._record_communication(
            db=db,
            request_id=request.id,
            comm_type=CommunicationType.COMPLETION,
            recipient=recipient_email,
            subject=subject,
            status=status,
            provider_message_id=msg_id
        )

email_service = EmailService()
