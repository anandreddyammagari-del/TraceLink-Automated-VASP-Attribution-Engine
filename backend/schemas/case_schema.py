from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from backend.schemas.suspect_schema import SuspectResponse

class CaseCreate(BaseModel):
    fir_number: str = Field(..., json_schema_extra={"example": "FIR-2026-DEL-CY-0042"})
    title: str
    police_station: str = "Special Cyber Cell, Crime Branch"
    crime_sections: str = "Section 66D IT Act, 2000 r/w Section 318(4) BNS, 2023"
    priority: str = "HIGH"
    total_disputed_inr: float = 0.0
    description: Optional[str] = None

class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    fir_number: str
    title: str
    police_station: str
    crime_sections: str
    investigating_officer_id: str
    status: str
    priority: str
    total_disputed_inr: float
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    suspects: Optional[List[SuspectResponse]] = []
