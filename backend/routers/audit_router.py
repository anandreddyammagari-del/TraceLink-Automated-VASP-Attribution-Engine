from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.core.database import get_db
from backend.core.security import get_current_officer, require_clearance
from backend.models.audit import AuditLog

router = APIRouter(prefix="/api/audit", tags=["Tamper-Evident Audit Trail"])

@router.get("", response_model=list[dict])
async def list_audit_trail(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    officer: dict = Depends(get_current_officer)
):
    """Retrieve cryptographically linked audit trail entries."""
    stmt = select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit)
    res = await db.execute(stmt)
    entries = res.scalars().all()

    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "officer_id": e.officer_id,
            "case_id": e.case_id,
            "details": e.details,
            "prev_hash": e.prev_hash,
            "current_hash": e.current_hash,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None
        }
        for e in entries
    ]

@router.get("/verify-chain", response_model=dict)
async def verify_audit_chain(
    db: AsyncSession = Depends(get_db),
    officer: dict = Depends(require_clearance("L2_SENIOR_OFFICER"))
):
    """
    Cryptographically verify the entire SHA-256 audit chain from Genesis to head.
    Any modified row immediately triggers a chain break failure.
    """
    stmt = select(AuditLog).order_by(AuditLog.timestamp.asc())
    res = await db.execute(stmt)
    entries = res.scalars().all()

    if not entries:
        return {"verified": True, "entries_checked": 0, "status": "NO_ENTRIES"}

    expected_prev = "0000000000000000000000000000000000000000000000000000000000000000"
    for i, entry in enumerate(entries):
        if i == 0:
            if entry.prev_hash != expected_prev:
                return {
                    "verified": False,
                    "tamper_detected_at_step": i,
                    "entry_id": entry.id,
                    "error": "Genesis block prev_hash mismatch."
                }
        else:
            if entry.prev_hash != entries[i-1].current_hash:
                return {
                    "verified": False,
                    "tamper_detected_at_step": i,
                    "entry_id": entry.id,
                    "error": f"Chain broken: Row {i} prev_hash does not match Row {i-1} current_hash."
                }

        from backend.models.audit import format_audit_timestamp
        recalculated = AuditLog.compute_hash(
            prev_hash=entry.prev_hash,
            event_type=entry.event_type,
            officer_id=entry.officer_id,
            case_id=entry.case_id,
            details=entry.details,
            timestamp_str=format_audit_timestamp(entry.timestamp)
        )
        if recalculated != entry.current_hash:
            return {
                "verified": False,
                "tamper_detected_at_step": i,
                "entry_id": entry.id,
                "error": f"Block hash invalid at entry {entry.id}. Data has been altered!"
            }

    return {
        "verified": True,
        "entries_checked": len(entries),
        "chain_head_hash": entries[-1].current_hash,
        "status": "CHAIN_INTEGRITY_VERIFIED_AUTHENTIC"
    }
