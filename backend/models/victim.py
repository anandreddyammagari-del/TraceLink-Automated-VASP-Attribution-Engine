import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text
from backend.core.database import Base

class Victim(Base):
    __tablename__ = "victims"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    complaint_ref = Column(String(100), unique=True, nullable=False, index=True)  # NCRP / National Cyber Crime Portal Ack No.
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=True)
    complainant_name = Column(String(150), nullable=False)
    contact_phone = Column(String(50), nullable=True)
    destination_wallet_reported = Column(String(120), nullable=False, index=True)
    loss_amount_inr = Column(Float, default=0.0)
    fraud_modality = Column(String(150), nullable=True)  # Crypto Staking Fraud, Job Scam, Sextortion, Fake Exchange
    incident_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
