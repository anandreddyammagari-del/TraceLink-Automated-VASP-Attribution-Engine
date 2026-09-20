import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.core.database import Base

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    address = Column(String(120), unique=True, nullable=False, index=True)
    chain = Column(String(50), nullable=False, default="ethereum")  # ethereum, bitcoin, polygon, bsc, arbitrum, tron
    suspect_id = Column(String(36), ForeignKey("suspects.id"), nullable=True)
    cluster_id = Column(String(100), nullable=True, index=True)
    known_entity_label = Column(String(150), nullable=True)  # e.g., Binance Deposit, Tornado Cash Mixer, Suspect Primary
    entity_category = Column(String(50), default="SUSPECT_WALLET")  # SUSPECT_WALLET, INTERMEDIARY, MIXER, BRIDGE, VASP
    risk_score = Column(Float, default=50.0)  # 0 to 100
    is_sanctioned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    suspect = relationship("Suspect", back_populates="wallets")
