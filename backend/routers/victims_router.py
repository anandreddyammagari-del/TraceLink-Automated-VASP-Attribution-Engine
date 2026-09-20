from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List
from backend.core.security import get_current_officer
from backend.services.ncrp_ingestion import ncrp_service

router = APIRouter(prefix="/api/victims", tags=["Victim Registry & NCRP Ingestion"])

# In-memory store for active session complaints (initialized with fixtures)
_complaints_store: List[dict] = ncrp_service.load_fixture_complaints()

@router.get("", response_model=List[dict])
async def list_registered_complaints(
    officer: dict = Depends(get_current_officer)
):
    """List all registered NCRP victim complaints."""
    return _complaints_store

@router.post("/upload-ncrp")
async def upload_ncrp_complaints_csv(
    file: UploadFile = File(...),
    officer: dict = Depends(get_current_officer)
):
    """Ingest CSV complaint export from NCRP portal."""
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV complaint datasets are supported.")

    content = await file.read()
    text = content.decode("utf-8", errors="replace")
    parsed = ncrp_service.parse_complaints(text)

    # Append to store avoiding duplicate complaint refs
    existing_refs = {c["complaint_ref"] for c in _complaints_store}
    new_added = 0
    for comp in parsed:
        if comp["complaint_ref"] not in existing_refs:
            _complaints_store.append(comp)
            existing_refs.add(comp["complaint_ref"])
            new_added += 1

    return {
        "status": "SUCCESS",
        "total_parsed": len(parsed),
        "new_complaints_registered": new_added,
        "total_registered": len(_complaints_store)
    }

@router.post("/correlate-wallet")
async def correlate_destination_wallet(
    address: str,
    officer: dict = Depends(get_current_officer)
):
    """Find victim complaints reporting a specific destination wallet."""
    addr = address.strip().lower()
    matches = [c for c in _complaints_store if c.get("destination_wallet", "").lower() == addr]
    total_loss = sum(c.get("loss_amount_inr", 0.0) for c in matches)

    return {
        "address": address,
        "victim_count": len(matches),
        "total_claimed_loss_inr": total_loss,
        "linked_complaints": matches
    }
