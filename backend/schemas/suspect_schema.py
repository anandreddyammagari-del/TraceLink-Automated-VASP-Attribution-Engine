from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class SuspectCreate(BaseModel):
    person_id: str = Field(..., json_schema_extra={"example": "SUSP-IND-9021"})
    full_name: str
    aliases: Optional[str] = None
    national_id: Optional[str] = None
    case_id: str
    risk_category: str = "HIGH_RISK"
    notes: Optional[str] = None

class SuspectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    person_id: str
    full_name: str
    aliases: Optional[str] = None
    national_id: Optional[str] = None
    case_id: str
    risk_category: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
