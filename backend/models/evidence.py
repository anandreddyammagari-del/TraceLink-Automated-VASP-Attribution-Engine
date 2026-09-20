import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from backend.core.database import Base

class EvidenceItem(Base):
    __tablename__ = "evidence_locker"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # CSV, JSON, PNG, PDF, RAW_LOG
    file_size_bytes = Column(Integer, nullable=False)
    sha256_hash = Column(String(64), nullable=False, index=True)
    uploaded_by_officer_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    storage_path = Column(String(500), nullable=False)
    custody_transfers = Column(Text, default="[]")  # JSON log of custody changes
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
