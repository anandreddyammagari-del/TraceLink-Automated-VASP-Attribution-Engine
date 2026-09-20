import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime
from backend.core.database import Base

class BridgeHop(Base):
    __tablename__ = "bridge_hops"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_chain = Column(String(50), nullable=False)
    source_tx_hash = Column(String(120), nullable=False, index=True)
    bridge_protocol = Column(String(100), nullable=False)  # Wormhole, Stargate, Multichain, Across
    destination_chain = Column(String(50), nullable=False)
    destination_tx_hash = Column(String(120), nullable=True, index=True)
    destination_recipient = Column(String(120), nullable=True)
    transferred_volume = Column(Float, nullable=False)
    token_symbol = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
