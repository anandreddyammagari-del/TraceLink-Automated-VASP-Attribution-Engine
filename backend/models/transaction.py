import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from backend.core.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tx_hash = Column(String(120), unique=True, nullable=False, index=True)
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=True)
    suspect_id = Column(String(36), ForeignKey("suspects.id"), nullable=True)
    person_id = Column(String(50), nullable=True, index=True)  # Denormalized for rapid ledger query
    from_address = Column(String(120), nullable=False, index=True)
    to_address = Column(String(120), nullable=False, index=True)
    value = Column(Float, nullable=False)
    token_symbol = Column(String(20), default="ETH", nullable=False)
    value_inr = Column(Float, default=0.0)
    timestamp = Column(DateTime, nullable=False)
    chain = Column(String(50), default="ethereum", nullable=False)
    risk_flag = Column(String(50), default="UNVERIFIED")  # CLEAN, STRUCTURING, MIXER_TRAVERSED, VASP_DEPOSIT, PEELING
    attributed_entity = Column(String(150), nullable=True)
    hop_level = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    case = relationship("Case", back_populates="transactions")
    suspect = relationship("Suspect", back_populates="transactions")
