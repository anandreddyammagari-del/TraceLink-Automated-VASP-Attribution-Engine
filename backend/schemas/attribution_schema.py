from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class AttributionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    trace_id: str
    target_vasp_name: str
    vasp_deposit_address: str
    hop_distance: int
    total_volume: float
    token_symbol: str
    confidence_score: float
    confidence_tier: str  # HIGH, MEDIUM, LOW
    evidence_breakdown: Optional[List[str]] = []
    created_at: Optional[datetime] = None
