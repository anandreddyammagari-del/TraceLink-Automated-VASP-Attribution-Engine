import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text
from backend.core.database import Base

class SanctionsMatch(Base):
    __tablename__ = "sanctions_matches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    wallet_address = Column(String(120), nullable=False, index=True)
    list_source = Column(String(100), nullable=False)  # OFAC_SDN, CHAINABUSE, INTERPOL_RED_NOTICE
    entity_name = Column(String(200), nullable=False)
    program = Column(String(100), nullable=True)  # CYBER2, DPRK, TERRORISM
    match_score = Column(Float, default=1.0)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
