import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.core.database import Base

class LawfulRequest(Base):
    __tablename__ = "requests_drafted"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    attribution_id = Column(String(36), ForeignKey("vasp_attributions.id"), nullable=False)
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=False)
    notice_reference_number = Column(String(100), unique=True, nullable=False)
    statutory_clause = Column(
        String(255),
        default="Section 94 Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023 r/w Section 79(3)(b) Information Technology Act, 2000"
    )
    target_vasp_name = Column(String(100), nullable=False)
    target_deposit_wallet = Column(String(120), nullable=False)
    notice_body = Column(Text, nullable=False)
    status = Column(String(50), default="DRAFT", nullable=False)  # DRAFT, OFFICER_REVIEWED, PENDING_SENIOR_APPROVAL, APPROVED_PRINT_READY
    signed_by_officer_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    is_external_submission_deactivated = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    attribution = relationship("VASPAttribution", back_populates="lawful_requests")
    signed_by_officer = relationship("User", foreign_keys=[signed_by_officer_id])
