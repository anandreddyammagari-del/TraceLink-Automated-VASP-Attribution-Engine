import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from backend.core.database import Base

class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    wallet_address = Column(String(120), unique=True, nullable=False, index=True)
    chain = Column(String(50), default="ethereum", nullable=False)
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=True)
    suspect_name = Column(String(150), nullable=True)
    alert_threshold_usd = Column(String(50), default="1000.0")
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
