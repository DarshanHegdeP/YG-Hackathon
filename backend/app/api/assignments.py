from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import ControlAssignment, Control, Scope, User, UserRole
from app.schemas import ControlAssignmentCreate, ControlAssignmentUpdate, ControlAssignmentOut
from app.api.deps import get_reviewer_user, get_current_user
from app.utils.audit import log_audit

router = APIRouter(prefix="/api/control-assignments", tags=["assignments"])

@router.get("", response_model=List[ControlAssignmentOut])
def list_assignments(
    control_id: Optional[int] = None,
    scope_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(ControlAssignment)
    if current_user.role == UserRole.BUSINESS_OWNER:
        query = query.join(Scope).filter(Scope.owner_user_id == current_user.id)
    if control_id:
        query = query.filter(ControlAssignment.control_id == control_id)
    if scope_id:
        query = query.filter(ControlAssignment.scope_id == scope_id)
    return query.order_by(ControlAssignment.id.desc()).all()

@router.post("", response_model=ControlAssignmentOut)
def create_assignment(
    payload: ControlAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reviewer_user)
):
    # Verify control, scope, reviewer exist
    control = db.query(Control).filter(Control.id == payload.control_id).first()
    if not control:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Control not found")

    scope = db.query(Scope).filter(Scope.id == payload.scope_id).first()
    if not scope:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scope not found")

    reviewer = db.query(User).filter(User.id == payload.reviewer_id).first()
    if not reviewer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reviewer user not found")

    assignment = ControlAssignment(
        control_id=payload.control_id,
        scope_id=payload.scope_id,
        reviewer_id=payload.reviewer_id,
        frequency=payload.frequency,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        status=payload.status,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    log_audit(
        db,
        action="ASSIGNMENT_CREATED",
        entity_type="control_assignment",
        entity_id=assignment.id,
        user_id=current_user.id,
        metadata_json={
            "control_code": control.control_code,
            "scope_name": scope.name,
            "reviewer_email": reviewer.email
        }
    )

    return assignment

@router.get("/{id}", response_model=ControlAssignmentOut)
def get_assignment(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    assignment = db.query(ControlAssignment).filter(ControlAssignment.id == id).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Control assignment not found")
    if assignment.scope.owner_user_id != current_user.id and current_user.role != UserRole.REVIEWER:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Control assignment not found")
    return assignment

@router.put("/{id}", response_model=ControlAssignmentOut)
def update_assignment(
    id: int,
    payload: ControlAssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reviewer_user)
):
    assignment = db.query(ControlAssignment).filter(ControlAssignment.id == id).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Control assignment not found")

    if payload.frequency is not None:
        assignment.frequency = payload.frequency
    if payload.reviewer_id is not None:
        assignment.reviewer_id = payload.reviewer_id
    if payload.effective_from is not None:
        assignment.effective_from = payload.effective_from
    if payload.effective_to is not None:
        assignment.effective_to = payload.effective_to
    if payload.status is not None:
        assignment.status = payload.status

    db.commit()
    db.refresh(assignment)

    log_audit(
        db,
        action="ASSIGNMENT_UPDATED",
        entity_type="control_assignment",
        entity_id=assignment.id,
        user_id=current_user.id
    )

    return assignment
