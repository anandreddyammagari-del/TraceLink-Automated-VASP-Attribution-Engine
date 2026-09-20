import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from backend.core.database import Base

class Case(Base):
    __tablename__ = "cases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fir_number = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    police_station = Column(String(200), nullable=False)
    crime_sections = Column(String(255), nullable=False)  # e.g., Sec 66D IT Act, Sec 318(4) BNS
    investigating_officer_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    status = Column(String(50), default="OPEN", nullable=False)  # OPEN, UNDER_REVIEW, CHARGESHEET_FILED, CLOSED
    priority = Column(String(50), default="HIGH", nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    total_disputed_inr = Column(Float, default=0.0)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    investigating_officer = relationship("User", foreign_keys=[investigating_officer_id])
    suspects = relationship("Suspect", back_populates="case", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="case", cascade="all, delete-orphan")
    traces = relationship("Trace", back_populates="case", cascade="all, delete-orphan")
