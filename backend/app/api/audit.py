from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import AuditLog, User
from app.schemas import AuditLogOut
from app.api.deps import get_reviewer_user

router = APIRouter(prefix="/api/audit-logs", tags=["audit"])

@router.get("", response_model=List[AuditLogOut])
def get_audit_logs(
    entity_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reviewer_user)
):
    query = db.query(AuditLog)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if action:
        query = query.filter(AuditLog.action == action)

    logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()

    out = []
    for log in logs:
        out.append(AuditLogOut(
            id=log.id,
            user_id=log.user_id,
            user_name=log.user.name if log.user else "System / Anonymous",
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            metadata_json=log.metadata_json,
            timestamp=log.timestamp
        ))
    return out
