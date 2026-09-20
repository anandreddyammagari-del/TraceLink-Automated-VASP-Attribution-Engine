import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.core.database import Base

class Trace(Base):
    __tablename__ = "traces"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=False)
    root_wallet = Column(String(120), nullable=False, index=True)
    max_hops = Column(Integer, default=4, nullable=False)
    chain = Column(String(50), default="ethereum", nullable=False)
    status = Column(String(50), default="QUEUED", nullable=False)  # QUEUED, PROCESSING, COMPLETED, FAILED
    total_nodes = Column(Integer, default=0)
    total_edges = Column(Integer, default=0)
    graph_json = Column(Text, nullable=True)  # Serialized node/edge topology for D3
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    case = relationship("Case", back_populates="traces")
    attributions = relationship("VASPAttribution", back_populates="trace", cascade="all, delete-orphan")
