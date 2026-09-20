import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.core.database import Base

class VASPAttribution(Base):
    __tablename__ = "vasp_attributions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trace_id = Column(String(36), ForeignKey("traces.id"), nullable=False)
    target_vasp_name = Column(String(100), nullable=False, index=True)  # e.g., WazirX, CoinDCX, Binance, Kraken
    vasp_deposit_address = Column(String(120), nullable=False)
    hop_distance = Column(Integer, nullable=False)
    total_volume = Column(Float, nullable=False)
    token_symbol = Column(String(20), default="ETH")
    confidence_score = Column(Float, nullable=False)  # 0.0 - 100.0
    confidence_tier = Column(String(20), nullable=False)  # HIGH, MEDIUM, LOW
    evidence_breakdown_json = Column(Text, nullable=True)  # JSON-encoded factor list
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    trace = relationship("Trace", back_populates="attributions")
    lawful_requests = relationship("LawfulRequest", back_populates="attribution", cascade="all, delete-orphan")
