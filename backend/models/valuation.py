import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime
from backend.core.database import Base

class AssetValuation(Base):
    __tablename__ = "asset_valuations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    token_symbol = Column(String(20), nullable=False, index=True)  # BTC, ETH, USDT, USDC, MATIC
    price_date = Column(DateTime, nullable=False, index=True)
    rate_usd = Column(Float, nullable=False)
    rate_inr = Column(Float, nullable=False)
    source = Column(String(50), default="OFFLINE_PRICE_TABLE")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
