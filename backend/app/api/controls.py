from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Control, ControlEvidenceRequirement, User
from app.schemas import ControlCreate, ControlUpdate, ControlOut
from app.api.deps import get_reviewer_user, get_current_user
from app.utils.audit import log_audit

router = APIRouter(prefix="/api/controls", tags=["controls"])

@router.get("", response_model=List[ControlOut])
def list_controls(
    search: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Control)
    if search:
        s = f"%{search}%"
        query = query.filter((Control.name.ilike(s)) | (Control.control_code.ilike(s)) | (Control.description.ilike(s)))
    if status_filter:
        query = query.filter(Control.status == status_filter)
    return query.order_by(Control.control_code.asc()).all()

@router.post("", response_model=ControlOut)
def create_control(
    payload: ControlCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reviewer_user)
):
    existing = db.query(Control).filter(Control.control_code == payload.control_code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Control code '{payload.control_code}' already exists."
        )

    control = Control(
        control_code=payload.control_code,
        name=payload.name,
        description=payload.description,
        frequency=payload.frequency,
        status=payload.status,
    )
    db.add(control)
    db.flush()

    for req in payload.requirements:
        evidence_req = ControlEvidenceRequirement(
            control_id=control.id,
            name=req.name,
            description=req.description,
            mandatory=req.mandatory,
        )
        db.add(evidence_req)

    db.commit()
    db.refresh(control)

    log_audit(
        db,
        action="CONTROL_CREATED",
        entity_type="control",
        entity_id=control.id,
        user_id=current_user.id,
        metadata_json={"control_code": control.control_code, "name": control.name}
    )

    return control

@router.get("/{id}", response_model=ControlOut)
def get_control(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    control = db.query(Control).filter(Control.id == id).first()
    if not control:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Control not found")
    return control

@router.put("/{id}", response_model=ControlOut)
def update_control(
    id: int,
    payload: ControlUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reviewer_user)
):
    control = db.query(Control).filter(Control.id == id).first()
    if not control:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Control not found")

    if payload.name is not None:
        control.name = payload.name
    if payload.description is not None:
        control.description = payload.description
    if payload.frequency is not None:
        control.frequency = payload.frequency
    if payload.status is not None:
        control.status = payload.status

    if payload.requirements is not None:
        # Replace requirements
        db.query(ControlEvidenceRequirement).filter(ControlEvidenceRequirement.control_id == control.id).delete()
        for req in payload.requirements:
            evidence_req = ControlEvidenceRequirement(
                control_id=control.id,
                name=req.name,
                description=req.description,
                mandatory=req.mandatory,
            )
            db.add(evidence_req)

    db.commit()
    db.refresh(control)

    log_audit(
        db,
        action="CONTROL_UPDATED",
        entity_type="control",
        entity_id=control.id,
        user_id=current_user.id
    )

    return control
