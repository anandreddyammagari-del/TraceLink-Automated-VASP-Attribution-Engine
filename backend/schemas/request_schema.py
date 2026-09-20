from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class LawfulRequestDraftCreate(BaseModel):
    attribution_id: str
    case_id: str
    target_vasp_name: str
    target_deposit_wallet: str
    statutory_clause: Optional[str] = (
        "Section 94 Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023 "
        "r/w Section 79(3)(b) Information Technology Act, 2000"
    )
    custom_remarks: Optional[str] = None

class LawfulRequestUpdate(BaseModel):
    notice_body: str
    status: Optional[str] = None

class LawfulRequestSignOff(BaseModel):
    officer_notes: Optional[str] = None
    confirm_local_review_only: bool = Field(
        ...,
        description="Must confirm draft is for local review only; external portal transmission is disabled."
    )

class LawfulRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    attribution_id: str
    case_id: str
    notice_reference_number: str
    statutory_clause: str
    target_vasp_name: str
    target_deposit_wallet: str
    notice_body: str
    status: str
    signed_by_officer_id: Optional[str] = None
    is_external_submission_deactivated: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
