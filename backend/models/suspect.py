import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.core.database import Base

class Suspect(Base):
    __tablename__ = "suspects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    person_id = Column(String(50), unique=True, nullable=False, index=True)  # e.g., SUSP-IND-9021
    full_name = Column(String(150), nullable=False)
    aliases = Column(String(255), nullable=True)
    national_id = Column(String(100), nullable=True)  # PAN, Aadhaar ref, Passport
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=False)
    risk_category = Column(String(50), default="HIGH_RISK")  # SEVERE, HIGH_RISK, MEDIUM_RISK, MONITORED
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    case = relationship("Case", back_populates="suspects")
    wallets = relationship("Wallet", back_populates="suspect", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="suspect")
