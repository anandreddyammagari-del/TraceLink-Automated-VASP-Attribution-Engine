from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from backend.core.database import get_db
from backend.core.security import get_current_officer
from backend.models.transaction import Transaction
from backend.models.case import Case
from backend.services.temporal_analysis import temporal_service
from backend.services.peel_chain_detector import peel_chain_detector
from backend.services.poisoning_detector import poisoning_detector

router = APIRouter(prefix="/api/analytics", tags=["Advanced Forensic Analytics"])

@router.get("/temporal/{case_id}")
async def analyze_case_temporal_velocity(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    officer: dict = Depends(get_current_officer)
):
    """Analyze transaction velocity, sub-30s burst transfers, and dormancy periods for a case."""
    stmt = select(Case).where(or_(Case.id == case_id, Case.fir_number == case_id))
    case_rec = (await db.execute(stmt)).scalars().first()
    if not case_rec:
        raise HTTPException(status_code=404, detail="Case record not found.")

    tx_stmt = select(Transaction).where(Transaction.case_id == case_rec.id)
    txs = (await db.execute(tx_stmt)).scalars().all()
    tx_dicts = [
        {
            "tx_hash": t.tx_hash,
            "from_address": t.from_address,
            "to_address": t.to_address,
            "value": t.value,
            "token_symbol": t.token_symbol,
            "timestamp": t.timestamp.isoformat() if t.timestamp else None
        }
        for t in txs
    ]

    return temporal_service.detect_velocity_anomalies(tx_dicts)

@router.post("/peel-chain")
async def analyze_peel_chains(
    transactions: list[dict],
    officer: dict = Depends(get_current_officer)
):
    """Detect sequential peel chain shaving patterns in a provided set of transactions."""
    return peel_chain_detector.detect_peel_sequence(transactions)

@router.post("/check-poisoning")
async def check_address_poisoning(
    payload: dict,
    officer: dict = Depends(get_current_officer)
):
    """Evaluate whether a transaction or candidate address is a zero-value vanity poisoning attack."""
    tx = payload.get("transaction", {})
    legit_addrs = payload.get("legitimate_addresses", [])
    is_poison, reason = poisoning_detector.is_poisoning_transaction(tx, legit_addrs)
    return {
        "is_poisoning_attack": is_poison,
        "rationale": reason
    }
