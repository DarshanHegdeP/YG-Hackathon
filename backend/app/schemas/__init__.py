from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, EmailStr, Field
from app.models import (
    UserRole, ScopeType, ReviewStatus, EvidenceRequestStatus,
    EvidenceProcessingStatus, AIValidationStatus, AIRelevance, CommunicationType
)

# --- Auth & User ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: UserRole = UserRole.BUSINESS_USER
    manager_id: Optional[int] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Scope ---
class ScopeBase(BaseModel):
    type: ScopeType
    name: str
    description: Optional[str] = None
    owner_user_id: Optional[int] = None
    email: str
    escalation_user_id: Optional[int] = None
    metadata_json: Optional[Dict[str, Any]] = None

class ScopeCreate(ScopeBase):
    pass

class ScopeUpdate(BaseModel):
    type: Optional[ScopeType] = None
    name: Optional[str] = None
    description: Optional[str] = None
    owner_user_id: Optional[int] = None
    email: Optional[str] = None
    escalation_user_id: Optional[int] = None
    metadata_json: Optional[Dict[str, Any]] = None

class ScopeOut(ScopeBase):
    id: int
    created_at: datetime
    updated_at: datetime
    owner_name: Optional[str] = None
    escalation_name: Optional[str] = None

    class Config:
        from_attributes = True

# --- Control & Evidence Requirement ---
class EvidenceRequirementBase(BaseModel):
    name: str
    description: Optional[str] = None
    mandatory: bool = True

class EvidenceRequirementCreate(EvidenceRequirementBase):
    pass

class EvidenceRequirementOut(EvidenceRequirementBase):
    id: int
    control_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ControlBase(BaseModel):
    control_code: str
    name: str
    description: str
    frequency: str = "QUARTERLY"
    status: str = "ACTIVE"

class ControlCreate(ControlBase):
    requirements: List[EvidenceRequirementCreate] = []

class ControlUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    frequency: Optional[str] = None
    status: Optional[str] = None
    requirements: Optional[List[EvidenceRequirementCreate]] = None

class ControlOut(ControlBase):
    id: int
    created_at: datetime
    updated_at: datetime
    evidence_requirements: List[EvidenceRequirementOut] = []

    class Config:
        from_attributes = True

# --- Control Assignment ---
class ControlAssignmentBase(BaseModel):
    control_id: int
    scope_id: int
    reviewer_id: int
    frequency: str = "QUARTERLY"
    effective_from: datetime
    effective_to: Optional[datetime] = None
    status: str = "ACTIVE"

class ControlAssignmentCreate(ControlAssignmentBase):
    pass

class ControlAssignmentUpdate(BaseModel):
    frequency: Optional[str] = None
    reviewer_id: Optional[int] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    status: Optional[str] = None

class ControlAssignmentOut(ControlAssignmentBase):
    id: int
    created_at: datetime
    control: Optional[ControlOut] = None
    scope: Optional[ScopeOut] = None
    reviewer: Optional[UserOut] = None

    class Config:
        from_attributes = True

# --- Review ---
class ReviewBase(BaseModel):
    control_assignment_id: int
    period_start: datetime
    period_end: datetime
    due_date: datetime
    status: ReviewStatus = ReviewStatus.OPEN

class ReviewCreate(ReviewBase):
    create_request: bool = True

class ReviewUpdate(BaseModel):
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    due_date: Optional[datetime] = None
    status: Optional[ReviewStatus] = None

class ReviewOut(ReviewBase):
    id: int
    created_at: datetime
    updated_at: datetime
    assignment: Optional[ControlAssignmentOut] = None
    evidence_requests: List["EvidenceRequestSummaryOut"] = []

    class Config:
        from_attributes = True

# --- AI Validation ---
class AIValidationResult(BaseModel):
    status: AIValidationStatus
    relevance: AIRelevance
    confidence: float
    missingInformation: List[str] = []
    findings: List[str] = []
    reason: str

class AIValidationOut(BaseModel):
    id: int
    evidence_id: int
    status: AIValidationStatus
    relevance: AIRelevance
    confidence: float
    findings: Optional[List[str]] = None
    missing_information: Optional[List[str]] = None
    reason: str
    model: str
    raw_response: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- Evidence ---
class EvidenceBase(BaseModel):
    file_name: str
    file_type: str
    storage_path: str
    file_size: int
    sha256: str
    processing_status: EvidenceProcessingStatus = EvidenceProcessingStatus.UPLOADED

class EvidenceOut(EvidenceBase):
    id: int
    request_id: int
    extracted_text: Optional[str] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    validations: List[AIValidationOut] = []

    class Config:
        from_attributes = True

# --- Communication ---
class CommunicationOut(BaseModel):
    id: int
    request_id: int
    type: CommunicationType
    recipient: str
    subject: str
    provider_message_id: Optional[str] = None
    status: str
    sent_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

# --- Evidence Request ---
class EvidenceRequestBase(BaseModel):
    review_id: int
    due_date: datetime
    status: EvidenceRequestStatus = EvidenceRequestStatus.PENDING

class EvidenceRequestCreate(BaseModel):
    review_id: int
    due_date: Optional[datetime] = None

class EvidenceRequestUpdate(BaseModel):
    due_date: Optional[datetime] = None
    status: Optional[EvidenceRequestStatus] = None

class EvidenceRequestSummaryOut(BaseModel):
    id: int
    review_id: int
    request_code: str
    status: EvidenceRequestStatus
    requested_at: datetime
    due_date: datetime
    reminder_count: int
    last_reminder_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    secure_token: str
    created_at: datetime

    class Config:
        from_attributes = True

class EvidenceRequestOut(EvidenceRequestSummaryOut):
    updated_at: datetime
    review: Optional[ReviewOut] = None
    evidences: List[EvidenceOut] = []
    communications: List[CommunicationOut] = []

    class Config:
        from_attributes = True

# --- Public Submission Page Schema ---
class EvidenceRequestPublicOut(BaseModel):
    request_code: str
    secure_token: str
    status: EvidenceRequestStatus
    due_date: datetime
    requested_at: datetime
    control_code: str
    control_name: str
    control_description: str
    scope_name: str
    scope_type: str
    recipient_email: str
    period_start: datetime
    period_end: datetime
    required_evidence: List[EvidenceRequirementOut]
    uploaded_evidences: List[EvidenceOut]
    latest_validation: Optional[AIValidationOut] = None

# --- Dashboard & Audit ---
class DashboardSummaryOut(BaseModel):
    total_controls: int
    active_assignments: int
    active_reviews: int
    total_requests: int
    complete_requests: int
    pending_requests: int
    incomplete_requests: int
    overdue_requests: int
    status_distribution: Dict[str, int]
    scope_distribution: Dict[str, int]

class OverdueRequestOut(BaseModel):
    id: int
    request_code: str
    control_name: str
    scope_name: str
    recipient: str
    due_date: datetime
    days_overdue: int
    reminder_count: int

class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    metadata_json: Optional[Dict[str, Any]] = None
    timestamp: datetime

    class Config:
        from_attributes = True
