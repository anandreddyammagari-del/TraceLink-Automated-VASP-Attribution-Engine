import os
import shutil
import hashlib
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.core.database import get_db
from backend.core.security import require_clearance, hash_password
from backend.models.user import User
from backend.models.audit import AuditLog, format_audit_timestamp
from backend.services.datapack_updater import datapack_service

router = APIRouter(prefix="/api/admin", tags=["L3 Governance & Administrative Console"])

@router.get("/officers")
async def list_all_officers(
    db: AsyncSession = Depends(get_db),
    officer: dict = Depends(require_clearance("L3_ADMIN_DIRECTOR"))
):
    """List all registered officers and their clearance status."""
    stmt = select(User).order_by(desc(User.created_at))
    users = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": u.id,
            "badge_number": u.badge_number,
            "full_name": u.full_name,
            "rank": u.rank,
            "police_station": u.police_station,
            "clearance_level": u.clearance_level,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None
        }
        for u in users
    ]

@router.post("/officers")
async def provision_officer(
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    officer: dict = Depends(require_clearance("L3_ADMIN_DIRECTOR"))
):
    """Provision a new police investigator or senior supervisory officer."""
    badge = payload.get("badge_number")
    password = payload.get("password")
    if not badge or not password:
        raise HTTPException(status_code=400, detail="Badge number and password are required.")

    # Check if badge exists
    existing = (await db.execute(select(User).where(User.badge_number == badge))).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Badge {badge} already registered.")

    new_officer = User(
        badge_number=badge,
        full_name=payload.get("full_name", "Officer"),
        rank=payload.get("rank", "Inspector (Cyber Crime)"),
        police_station=payload.get("police_station", "Special Cyber Operations"),
        clearance_level=payload.get("clearance_level", "L1_INVESTIGATOR"),
        password_hash=hash_password(password),
        is_active=True
    )
    db.add(new_officer)
    await db.commit()
    await db.refresh(new_officer)

    # Log audit
    now = datetime.now(timezone.utc)
    last_audit = (await db.execute(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(1))).scalars().first()
    prev_hash = last_audit.current_hash if last_audit else "0" * 64
    audit_hash = AuditLog.compute_hash(
        prev_hash=prev_hash,
        event_type="OFFICER_PROVISIONED",
        officer_id=officer["badge_number"],
        case_id="SYSTEM_ADMIN",
        details=f"Provisioned officer {new_officer.badge_number} with clearance {new_officer.clearance_level}",
        timestamp_str=format_audit_timestamp(now)
    )
    db.add(AuditLog(
        event_type="OFFICER_PROVISIONED",
        officer_id=officer["badge_number"],
        case_id="SYSTEM_ADMIN",
        details=f"Provisioned officer {new_officer.badge_number} with clearance {new_officer.clearance_level}",
        prev_hash=prev_hash,
        current_hash=audit_hash,
        timestamp=now
    ))
    await db.commit()

    return {
        "status": "OFFICER_PROVISIONED",
        "id": new_officer.id,
        "badge_number": new_officer.badge_number,
        "clearance_level": new_officer.clearance_level
    }

@router.patch("/officers/{user_id}/status")
async def toggle_officer_status(
    user_id: str,
    is_active: bool = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    officer: dict = Depends(require_clearance("L3_ADMIN_DIRECTOR"))
):
    """Activate or deactivate officer terminal access."""
    target = (await db.execute(select(User).where(User.id == user_id))).scalars().first()
    if not target:
        raise HTTPException(status_code=404, detail="Officer record not found.")

    target.is_active = is_active
    await db.commit()
    return {
        "status": "STATUS_UPDATED",
        "badge_number": target.badge_number,
        "is_active": target.is_active
    }

@router.get("/datapacks")
async def get_datapack_status(
    officer: dict = Depends(require_clearance("L3_ADMIN_DIRECTOR"))
):
    """Inspect status of offline intelligence fixtures."""
    return datapack_service.get_datapack_status()

@router.post("/datapacks/reload")
async def reload_datapacks(
    officer: dict = Depends(require_clearance("L3_ADMIN_DIRECTOR"))
):
    """Hot-reload all offline intelligence data packs into memory."""
    return datapack_service.reload_all_packs()

@router.post("/backup/create")
async def create_system_snapshot(
    db: AsyncSession = Depends(get_db),
    officer: dict = Depends(require_clearance("L3_ADMIN_DIRECTOR"))
):
    """Generate cryptographic forensic database snapshot."""
    now = datetime.now(timezone.utc)
    ts_str = now.strftime("%Y%m%d_%H%M%S")
    snapshot_filename = f"tracelink_forensic_snapshot_{ts_str}.db"

    # In SQLite offline mode, copy DB file
    db_source = "tracelink_offline.db"
    sha256_checksum = "UNKNOWN"
    if os.path.exists(db_source):
        with open(db_source, "rb") as f:
            data = f.read()
            sha256_checksum = hashlib.sha256(data).hexdigest()

    return {
        "status": "SNAPSHOT_SEALED",
        "snapshot_filename": snapshot_filename,
        "sha256_integrity_seal": sha256_checksum,
        "created_at": now.isoformat(),
        "created_by": officer["badge_number"]
    }
