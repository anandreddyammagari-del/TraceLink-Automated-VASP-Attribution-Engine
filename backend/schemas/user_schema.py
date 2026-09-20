from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class OfficerLoginRequest(BaseModel):
    badge_number: str = Field(..., json_schema_extra={"example": "IND-CYBER-8841"})
    password: str = Field(..., min_length=6)
    station: Optional[str] = None
    totp_code: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    badge_number: str
    rank: str
    station: str
    clearance_level: str
    expires_in: int

class OfficerProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    badge_number: str
    full_name: str
    rank: str
    police_station: str
    clearance_level: str
    is_active: bool
    created_at: Optional[datetime] = None
