import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship
from app.db.session import Base

def utc_now():
    return datetime.now(timezone.utc)

class UserRole(str, enum.Enum):
    REVIEWER = "REVIEWER"
    BUSINESS_OWNER = "BUSINESS_OWNER"

class ScopeType(str, enum.Enum):
    PERSON = "PERSON"
    TEAM = "TEAM"
    DEPARTMENT = "DEPARTMENT"
    BUSINESS_UNIT = "BUSINESS_UNIT"
    APPLICATION = "APPLICATION"
    SYSTEM_OWNER = "SYSTEM_OWNER"
    OTHER = "OTHER"

class ReviewStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"

class EvidenceRequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    INCOMPLETE = "INCOMPLETE"
    COMPLETE = "COMPLETE"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"

class EvidenceProcessingStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"

class AIValidationStatus(str, enum.Enum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    IRRELEVANT = "IRRELEVANT"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"

class AIRelevance(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class CommunicationType(str, enum.Enum):
    INITIAL_REQUEST = "INITIAL_REQUEST"
    REMINDER_1 = "REMINDER_1"
    REMINDER_2 = "REMINDER_2"
    FINAL_REMINDER = "FINAL_REMINDER"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    ESCALATION = "ESCALATION"
    COMPLETION = "COMPLETION"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.BUSINESS_OWNER, nullable=False)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    manager = relationship("User", remote_side=[id], backref="subordinates")

class Scope(Base):
    __tablename__ = "scopes"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(SQLEnum(ScopeType), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    email = Column(String(255), nullable=False)
    escalation_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    owner = relationship("User", foreign_keys=[owner_user_id])
    escalation_user = relationship("User", foreign_keys=[escalation_user_id])
    assignments = relationship("ControlAssignment", back_populates="scope")

class Control(Base):
    __tablename__ = "controls"

    id = Column(Integer, primary_key=True, index=True)
    control_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    frequency = Column(String(50), default="QUARTERLY", nullable=False)
    status = Column(String(50), default="ACTIVE", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    evidence_requirements = relationship(
        "ControlEvidenceRequirement",
        back_populates="control",
        cascade="all, delete-orphan"
    )
    assignments = relationship("ControlAssignment", back_populates="control")

class ControlEvidenceRequirement(Base):
    __tablename__ = "control_evidence_requirements"

    id = Column(Integer, primary_key=True, index=True)
    control_id = Column(Integer, ForeignKey("controls.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    mandatory = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    control = relationship("Control", back_populates="evidence_requirements")

class ControlAssignment(Base):
    __tablename__ = "control_assignments"

    id = Column(Integer, primary_key=True, index=True)
    control_id = Column(Integer, ForeignKey("controls.id"), nullable=False, index=True)
    scope_id = Column(Integer, ForeignKey("scopes.id"), nullable=False, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    frequency = Column(String(50), default="QUARTERLY", nullable=False)
    effective_from = Column(DateTime, default=utc_now, nullable=False)
    effective_to = Column(DateTime, nullable=True)
    status = Column(String(50), default="ACTIVE", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    control = relationship("Control", back_populates="assignments")
    scope = relationship("Scope", back_populates="assignments")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    reviews = relationship("Review", back_populates="assignment")

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    control_assignment_id = Column(Integer, ForeignKey("control_assignments.id"), nullable=False, index=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    status = Column(SQLEnum(ReviewStatus), default=ReviewStatus.OPEN, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    assignment = relationship("ControlAssignment", back_populates="reviews")
    evidence_requests = relationship("EvidenceRequest", back_populates="review")

class EvidenceRequest(Base):
    __tablename__ = "evidence_requests"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False, index=True)
    request_code = Column(String(100), unique=True, index=True, nullable=False)
    status = Column(SQLEnum(EvidenceRequestStatus), default=EvidenceRequestStatus.PENDING, nullable=False)
    requested_at = Column(DateTime, default=utc_now, nullable=False)
    due_date = Column(DateTime, nullable=False)
    reminder_count = Column(Integer, default=0, nullable=False)
    last_reminder_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    secure_token = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    review = relationship("Review", back_populates="evidence_requests")
    evidences = relationship("Evidence", back_populates="request", cascade="all, delete-orphan")
    communications = relationship("Communication", back_populates="request", cascade="all, delete-orphan")

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("evidence_requests.id"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    sha256 = Column(String(64), index=True, nullable=False)
    processing_status = Column(SQLEnum(EvidenceProcessingStatus), default=EvidenceProcessingStatus.UPLOADED, nullable=False)
    extracted_text = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=utc_now, nullable=False)
    processed_at = Column(DateTime, nullable=True)

    request = relationship("EvidenceRequest", back_populates="evidences")
    validations = relationship("AIValidation", back_populates="evidence", cascade="all, delete-orphan")

class AIValidation(Base):
    __tablename__ = "ai_validations"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False, index=True)
    status = Column(SQLEnum(AIValidationStatus), default=AIValidationStatus.LOW_CONFIDENCE, nullable=False)
    relevance = Column(SQLEnum(AIRelevance), default=AIRelevance.MEDIUM, nullable=False)
    confidence = Column(Float, default=0.0, nullable=False)
    findings = Column(JSON, nullable=True)
    missing_information = Column(JSON, nullable=True)
    reason = Column(Text, nullable=False)
    model = Column(String(100), nullable=False)
    raw_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    evidence = relationship("Evidence", back_populates="validations")

class Communication(Base):
    __tablename__ = "communications"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("evidence_requests.id"), nullable=False, index=True)
    type = Column(SQLEnum(CommunicationType), nullable=False)
    recipient = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    provider_message_id = Column(String(255), nullable=True)
    status = Column(String(50), default="SENT", nullable=False)
    sent_at = Column(DateTime, default=utc_now, nullable=False)
    metadata_json = Column(JSON, nullable=True)

    request = relationship("EvidenceRequest", back_populates="communications")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(Integer, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)

    user = relationship("User", foreign_keys=[user_id])
