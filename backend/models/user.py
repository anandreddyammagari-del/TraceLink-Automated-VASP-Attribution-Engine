import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime
from backend.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    badge_number = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(150), nullable=False)
    rank = Column(String(100), nullable=False)  # e.g. Inspector, ACP, DySP, Cyber Forensics Specialist
    police_station = Column(String(200), nullable=False)
    clearance_level = Column(String(50), nullable=False, default="L1_INVESTIGATOR")  # L1_INVESTIGATOR, L2_SENIOR_OFFICER, L3_ADMIN_DIRECTOR
    password_hash = Column(String(255), nullable=False)
    totp_secret = Column(String(64), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime, nullable=True)
