from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List, Optional
from backend.core.security import get_current_officer
from backend.services.evidence_locker import evidence_locker
from backend.services.seizure_memo_generator import seizure_memo_generator

router = APIRouter(prefix="/api/evidence", tags=["Evidence Custody Locker & Section 105 BNSS"])

# In-memory session registry for evidence deposits
_evidence_vault: List[dict] = []

@router.post("/deposit")
async def deposit_evidence_file(
    file: UploadFile = File(...),
    case_id: str = Form("FIR-2026-DEL-CY-0042"),
    item_description: str = Form("Cryptocurrency ledger export / digital evidence item"),
    officer: dict = Depends(get_current_officer)
):
    """
    Deposit digital evidence file into the cryptographic locker.
    Calculates SHA-256 and MD5 checksums for immutable Chain of Custody.
    """
    file_bytes = await file.read()
    entry = evidence_locker.register_evidence(
        filename=file.filename,
        file_bytes=file_bytes,
        case_id=case_id,
        officer_badge=officer["badge_number"],
        item_description=item_description
    )
    _evidence_vault.append(entry)
    return {
        "status": "EVIDENCE_SEALED",
        "evidence_id": entry["evidence_id"],
        "sha256_checksum": entry["sha256_checksum"],
        "md5_checksum": entry["md5_checksum"],
        "item_description": entry["item_description"]
    }

@router.get("/case/{case_id}")
async def list_case_evidence(
    case_id: str,
    officer: dict = Depends(get_current_officer)
):
    """List all secured evidence items for a case."""
    items = [e for e in _evidence_vault if e["case_id"] == case_id]
    return {
        "case_id": case_id,
        "total_evidence_items": len(items),
        "items": items
    }

@router.post("/seizure-memo")
async def generate_seizure_memo_endpoint(
    fir_number: str = Form("FIR-2026-DEL-CY-0042"),
    police_station: str = Form("Special Cyber Operations Branch"),
    crime_sections: str = Form("Section 66D IT Act r/w Sec 318(4) BNS"),
    seized_assets_description: str = Form("1x Ledger Nano X Hardware Wallet (SN: LN-9941), 1x Encrypted USB flash drive containing recovery phrases"),
    suspect_name: Optional[str] = Form("Rohan Malhotra (SUSP-IND-9021)"),
    officer: dict = Depends(get_current_officer)
):
    """Generate formal Section 105 BNSS (2023) Seizure Memo / Panchnama."""
    memo = seizure_memo_generator.generate_seizure_memo(
        fir_number=fir_number,
        police_station=police_station,
        crime_sections=crime_sections,
        seized_assets_description=seized_assets_description,
        custody_officer=officer,
        suspect_name=suspect_name
    )
    return memo
