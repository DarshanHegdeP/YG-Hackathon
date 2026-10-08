from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Communication, EvidenceRequest, User
from app.schemas import CommunicationOut
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/evidence-requests", tags=["communications"])

@router.get("/{id}/communications", response_model=List[CommunicationOut])
def get_request_communications(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    req = db.query(EvidenceRequest).filter(EvidenceRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence request not found")

    comms = (
        db.query(Communication)
        .filter(Communication.request_id == id)
        .order_by(Communication.sent_at.asc())
        .all()
    )
    return comms
