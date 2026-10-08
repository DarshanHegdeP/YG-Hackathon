from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Scope, User
from app.schemas import ScopeCreate, ScopeUpdate, ScopeOut
from app.api.deps import get_reviewer_or_admin, get_current_user
from app.utils.audit import log_audit

router = APIRouter(prefix="/api/scopes", tags=["scopes"])

def _format_scope_out(scope: Scope) -> ScopeOut:
    owner_name = scope.owner.name if scope.owner else None
    esc_name = scope.escalation_user.name if scope.escalation_user else None
    return ScopeOut(
        id=scope.id,
        type=scope.type,
        name=scope.name,
        description=scope.description,
        owner_user_id=scope.owner_user_id,
        email=scope.email,
        escalation_user_id=scope.escalation_user_id,
        metadata_json=scope.metadata_json,
        created_at=scope.created_at,
        updated_at=scope.updated_at,
        owner_name=owner_name,
        escalation_name=esc_name
    )

@router.get("", response_model=List[ScopeOut])
def list_scopes(
    type_filter: Optional[str] = Query(None, alias="type"),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Scope)
    if type_filter:
        query = query.filter(Scope.type == type_filter)
    if search:
        s = f"%{search}%"
        query = query.filter((Scope.name.ilike(s)) | (Scope.email.ilike(s)))
    scopes = query.order_by(Scope.name.asc()).all()
    return [_format_scope_out(sc) for sc in scopes]

@router.post("", response_model=ScopeOut)
def create_scope(
    payload: ScopeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reviewer_or_admin)
):
    scope = Scope(
        type=payload.type,
        name=payload.name,
        description=payload.description,
        owner_user_id=payload.owner_user_id,
        email=payload.email,
        escalation_user_id=payload.escalation_user_id,
        metadata_json=payload.metadata_json,
    )
    db.add(scope)
    db.commit()
    db.refresh(scope)

    log_audit(
        db,
        action="SCOPE_CREATED",
        entity_type="scope",
        entity_id=scope.id,
        user_id=current_user.id,
        metadata_json={"type": scope.type.value, "name": scope.name, "email": scope.email}
    )

    return _format_scope_out(scope)

@router.get("/{id}", response_model=ScopeOut)
def get_scope(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    scope = db.query(Scope).filter(Scope.id == id).first()
    if not scope:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scope not found")
    return _format_scope_out(scope)

@router.put("/{id}", response_model=ScopeOut)
def update_scope(
    id: int,
    payload: ScopeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_reviewer_or_admin)
):
    scope = db.query(Scope).filter(Scope.id == id).first()
    if not scope:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scope not found")

    if payload.type is not None:
        scope.type = payload.type
    if payload.name is not None:
        scope.name = payload.name
    if payload.description is not None:
        scope.description = payload.description
    if payload.owner_user_id is not None:
        scope.owner_user_id = payload.owner_user_id
    if payload.email is not None:
        scope.email = payload.email
    if payload.escalation_user_id is not None:
        scope.escalation_user_id = payload.escalation_user_id
    if payload.metadata_json is not None:
        scope.metadata_json = payload.metadata_json

    db.commit()
    db.refresh(scope)

    log_audit(
        db,
        action="SCOPE_UPDATED",
        entity_type="scope",
        entity_id=scope.id,
        user_id=current_user.id
    )

    return _format_scope_out(scope)
