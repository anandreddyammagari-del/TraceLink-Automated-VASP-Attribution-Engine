from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from backend.core.security import get_current_officer
from backend.services.sanctions_service import sanctions_service

router = APIRouter(prefix="/api/sanctions", tags=["OFAC SDN & Sanctions Intelligence"])

@router.get("/check/{address}")
async def check_address_sanctions(
    address: str,
    officer: dict = Depends(get_current_officer)
):
    """Check a single blockchain address against OFAC SDN and global sanctions registers."""
    match = sanctions_service.check_address(address)
    if match:
        return {
            "sanctioned": True,
            "address": address,
            "details": match
        }
    return {
        "sanctioned": False,
        "address": address,
        "details": None
    }

@router.post("/batch-check")
async def batch_check_sanctions(
    addresses: List[str],
    officer: dict = Depends(get_current_officer)
):
    """Check multiple wallet addresses simultaneously."""
    matches = sanctions_service.check_addresses_batch(addresses)
    return {
        "total_checked": len(addresses),
        "total_flagged": len(matches),
        "matches": matches
    }

@router.get("/stats")
async def sanctions_stats(
    officer: dict = Depends(get_current_officer)
):
    """Statistics on loaded offline sanctions fixtures."""
    return {
        "total_sanctioned_entities": sanctions_service.total_indexed(),
        "sources": ["OFAC_SDN", "CHAINABUSE", "UN_CONSOLIDATED"],
        "mode": "OFFLINE_LOCAL_CACHE"
    }
