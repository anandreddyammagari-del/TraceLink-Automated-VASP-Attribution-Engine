import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from backend.core.database import Base

class TieredApproval(Base):
    __tablename__ = "approvals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=False)
    request_id = Column(String(36), ForeignKey("requests_drafted.id"), nullable=True)
    required_clearance = Column(String(50), default="L2_SENIOR_OFFICER", nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, APPROVED, REJECTED
    requesting_officer_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    reviewing_officer_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    officer_remarks = Column(Text, nullable=True)
    decided_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
