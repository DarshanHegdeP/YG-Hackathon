from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import AuditLog

def log_audit(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    user_id: Optional[int] = None,
    metadata_json: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """Helper to record an audit log event consistently."""
    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=metadata_json or {},
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry
