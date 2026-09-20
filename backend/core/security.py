import hashlib
import os
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.core.config import settings

# Clearance hierarchy
CLEARANCE_LEVELS = {
    "L1_INVESTIGATOR": 1,
    "L2_SENIOR_OFFICER": 2,
    "L3_ADMIN_DIRECTOR": 3
}

security_bearer = HTTPBearer(auto_error=False)

def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Securely hash password using PBKDF2-HMAC-SHA256 with 100,000 iterations."""
    if not salt:
        salt = os.urandom(16).hex()
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return f"{salt}:{hashed}"

def verify_password(plain_password: str, stored_hash: str) -> bool:
    """Verify password against stored salt:hash."""
    try:
        parts = stored_hash.split(":")
        if len(parts) != 2:
            return False
        salt, expected_hash = parts
        actual_hash = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        return hmac.compare_digest(actual_hash, expected_hash)
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate cryptographically signed JWT token for cyber officer."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "iat": now,
        "iss": "tracelink-auth-gateway"
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    """Decode and validate officer JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Officer session token has expired. Re-authentication required.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid cyber officer credentials or signature token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

def calculate_sha256(data: str) -> str:
    """Compute SHA-256 digest for audit logs and tamper-evident chaining."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

async def get_current_officer(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)
) -> dict:
    """FastAPI dependency to extract and verify the current cyber officer."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Official police credentials required. Access restricted.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    payload = decode_token(credentials.credentials)
    badge_number = payload.get("sub")
    if not badge_number:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing badge identifier."
        )
    return {
        "user_id": payload.get("user_id"),
        "badge_number": badge_number,
        "rank": payload.get("rank"),
        "station": payload.get("station"),
        "clearance_level": payload.get("clearance_level", "L1_INVESTIGATOR")
    }

def require_clearance(min_level: str):
    """Enforce minimum officer clearance level (L1, L2, L3)."""
    min_rank = CLEARANCE_LEVELS.get(min_level, 1)
    
    async def clearance_dependency(officer: dict = Depends(get_current_officer)):
        officer_rank = CLEARANCE_LEVELS.get(officer.get("clearance_level", "L1_INVESTIGATOR"), 1)
        if officer_rank < min_rank:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action requires minimum clearance '{min_level}'. Access denied."
            )
        return officer
        
    return clearance_dependency
