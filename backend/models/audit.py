import uuid
import hashlib
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime
from backend.core.database import Base

def format_audit_timestamp(dt: datetime) -> str:
    """Consistently format datetime to standard ISO8601 UTC string for hashing."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # Format to seconds precision for database storage invariance across SQLite & Postgres
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(100), nullable=False, index=True)
    officer_id = Column(String(50), nullable=False, index=True)
    case_id = Column(String(50), nullable=True, index=True)
    details = Column(Text, nullable=False)
    prev_hash = Column(String(64), nullable=False)
    current_hash = Column(String(64), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    @staticmethod
    def compute_hash(prev_hash: str, event_type: str, officer_id: str, case_id: str, details: str, timestamp_str: str) -> str:
        """Calculate cryptographically secure SHA-256 block hash for tamper-evident chaining."""
        payload = f"{prev_hash}|{event_type}|{officer_id}|{case_id or 'GLOBAL'}|{details}|{timestamp_str}"
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()
