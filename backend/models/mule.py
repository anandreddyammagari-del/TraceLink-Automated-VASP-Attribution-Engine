import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, Text
from backend.core.database import Base

class MuleNetwork(Base):
    __tablename__ = "mule_networks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    network_label = Column(String(150), nullable=False)
    funnel_wallet_address = Column(String(120), unique=True, nullable=False, index=True)
    contributing_source_count = Column(Integer, default=0)
    total_volume_inr = Column(Float, default=0.0)
    layering_hops_to_vasp = Column(Integer, default=1)
    associated_fir_numbers = Column(Text, default="[]")  # JSON array of linked FIRs
    risk_level = Column(String(50), default="CRITICAL")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
