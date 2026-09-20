from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class TraceInitiateRequest(BaseModel):
    case_id: str
    root_wallet: str = Field(..., json_schema_extra={"example": "0x71c8901b2c45e89d1234a567b8901234cde56781"})
    max_hops: int = Field(4, ge=1, le=8)
    chain: str = "ethereum"
    person_id: Optional[str] = None

class TraceNode(BaseModel):
    id: str
    label: str
    category: str  # SUSPECT_WALLET, INTERMEDIARY, MIXER, BRIDGE, VASP
    risk_score: float
    cluster_id: Optional[str] = None
    hop: int

class TraceEdge(BaseModel):
    source: str
    target: str
    value: float
    token_symbol: str
    tx_hash: str
    timestamp: Optional[str] = None
    risk_flag: Optional[str] = None

class TraceGraphResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trace_id: str
    case_id: str
    root_wallet: str
    chain: str
    status: str
    nodes: List[TraceNode]
    edges: List[TraceEdge]
    total_nodes: int
    total_edges: int
    created_at: Optional[datetime] = None
