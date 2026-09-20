from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class TransactionCreate(BaseModel):
    tx_hash: str
    case_id: Optional[str] = None
    suspect_id: Optional[str] = None
    person_id: Optional[str] = None
    from_address: str
    to_address: str
    value: float
    token_symbol: str = "ETH"
    value_inr: Optional[float] = 0.0
    timestamp: datetime
    chain: str = "ethereum"
    risk_flag: Optional[str] = "UNVERIFIED"
    attributed_entity: Optional[str] = None
    hop_level: Optional[int] = 0

class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tx_hash: str
    case_id: Optional[str] = None
    suspect_id: Optional[str] = None
    person_id: Optional[str] = None
    from_address: str
    to_address: str
    value: float
    token_symbol: str
    value_inr: float
    timestamp: datetime
    chain: str
    risk_flag: str
    attributed_entity: Optional[str] = None
    hop_level: int
    created_at: Optional[datetime] = None

class LedgerFilterQuery(BaseModel):
    person_id: Optional[str] = None
    wallet_address: Optional[str] = None
    tx_hash: Optional[str] = None
    case_id: Optional[str] = None
    chain: Optional[str] = None
    risk_flag: Optional[str] = None
    limit: int = 100
    offset: int = 0
