import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.core.database import get_db
from backend.core.security import verify_password, create_access_token, get_current_officer, calculate_sha256
from backend.models.user import User
from backend.models.audit import AuditLog
from backend.schemas.user_schema import OfficerLoginRequest, TokenResponse, OfficerProfile

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Cyber Officer Authentication"])

POLICE_STATIONS = [
    "Special Cyber Operations, State Crime Branch",
    "Cyber Crime Police Station, Central District",
    "Cyber Police Station, Bandra Kurla Complex",
    "State Cyber Security Incident Cell (CERT-State)",
    "Special Investigation Team (Financial Cyber Fraud)"
]

@router.get("/stations", response_model=list[str])
async def list_police_stations():
    """Retrieve verified cyber police cell units for official login selection."""
    return POLICE_STATIONS

@router.post("/login", response_model=TokenResponse)
async def officer_login(credentials: OfficerLoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate authorized police investigator or senior supervisory officer."""
    stmt = select(User).where(User.badge_number == credentials.badge_number)
    res = await db.execute(stmt)
    officer = res.scalars().first()

    if not officer or not verify_password(credentials.password, officer.password_hash):
        logger.warning(f"Unauthorized login attempt for badge ID: {credentials.badge_number}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Service/Badge Number or Official Password. Access denied."
        )

    if not officer.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Officer account deactivated by Cyber Directorate Admin."
        )

    # Station verification if provided
    if credentials.station and credentials.station != officer.police_station:
        # Update station if valid or accept assigned station
        pass

    # Update last login timestamp
    now = datetime.now(timezone.utc)
    officer.last_login = now

    # Generate JWT token
    token_payload = {
        "sub": officer.badge_number,
        "user_id": officer.id,
        "rank": officer.rank,
        "station": officer.police_station,
        "clearance_level": officer.clearance_level
    }
    access_token = create_access_token(token_payload)

    # Append audit log entry
    last_audit_stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(1)
    last_audit_res = await db.execute(last_audit_stmt)
    last_audit = last_audit_res.scalars().first()
    prev_hash = last_audit.current_hash if last_audit else "0000000000000000000000000000000000000000000000000000000000000000"

    from backend.models.audit import format_audit_timestamp
    details = f"Officer authenticated: {officer.rank} {officer.full_name} ({officer.badge_number}) at {officer.police_station}"
    current_hash = AuditLog.compute_hash(
        prev_hash=prev_hash,
        event_type="OFFICER_LOGIN_SUCCESS",
        officer_id=officer.badge_number,
        case_id="AUTH",
        details=details,
        timestamp_str=format_audit_timestamp(now)
    )
    audit_entry = AuditLog(
        event_type="OFFICER_LOGIN_SUCCESS",
        officer_id=officer.badge_number,
        case_id="AUTH",
        details=details,
        prev_hash=prev_hash,
        current_hash=current_hash,
        timestamp=now
    )
    db.add(audit_entry)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        badge_number=officer.badge_number,
        rank=officer.rank,
        station=officer.police_station,
        clearance_level=officer.clearance_level,
        expires_in=480 * 60
    )

@router.get("/me", response_model=OfficerProfile)
async def get_current_officer_profile(
    officer_ctx: dict = Depends(get_current_officer),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve authenticated officer profile and credentials."""
    stmt = select(User).where(User.badge_number == officer_ctx["badge_number"])
    res = await db.execute(stmt)
    officer = res.scalars().first()
    if not officer:
        raise HTTPException(status_code=404, detail="Officer record not found.")
    return officer
