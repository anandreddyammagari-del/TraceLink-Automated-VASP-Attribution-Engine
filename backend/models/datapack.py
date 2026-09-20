import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Boolean
from backend.core.database import Base

class DataPack(Base):
    __tablename__ = "datapacks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pack_name = Column(String(100), nullable=False)  # VASP_DIRECTORY, OFAC_SANCTIONS, PRICE_HISTORY
    version = Column(String(50), nullable=False)
    record_count = Column(Integer, default=0)
    signature_sha256 = Column(String(64), nullable=False)
    is_verified = Column(Boolean, default=True)
    installed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
