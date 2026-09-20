import pytest
from datetime import datetime, timezone
from sqlalchemy import select, update
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.core.database import init_db, AsyncSessionLocal
from backend.core.seed import seed_initial_data
from backend.models.audit import AuditLog, format_audit_timestamp

@pytest.fixture(autouse=True)
async def setup_database():
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed_initial_data(session)

@pytest.mark.asyncio
async def test_audit_log_append_and_chain_validity():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Officer login to generate audit row
        login = await client.post("/api/auth/login", json={
            "badge_number": "IND-CYBER-8841",
            "password": "Police@Secure2026"
        })
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Verify chain is authentic
        res = await client.get("/api/audit/verify-chain", headers=headers)
        assert res.status_code == 200
        assert res.json()["verified"] is True
        assert res.json()["status"] == "CHAIN_INTEGRITY_VERIFIED_AUTHENTIC"

@pytest.mark.asyncio
async def test_tamper_detection_on_altered_audit_row():
    """
    Directly mutate a historical row's details in the database to simulate malicious tampering.
    The verification routine MUST detect the corrupted hash and report chain failure!
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post("/api/auth/login", json={
            "badge_number": "IND-CYBER-8841",
            "password": "Police@Secure2026"
        })
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Tamper with the database row directly
        original_details = None
        entry_id = None
        async with AsyncSessionLocal() as session:
            stmt = select(AuditLog).order_by(AuditLog.timestamp.asc()).limit(1)
            entry = (await session.execute(stmt)).scalars().first()
            assert entry is not None
            entry_id = entry.id
            original_details = entry.details
            # Alter details maliciously
            entry.details = "TAMPERED DETAILS BY UNAUTHORIZED INTRUDER"
            await session.commit()

        # Run verification
        verify_res = await client.get("/api/audit/verify-chain", headers=headers)
        assert verify_res.status_code == 200
        data = verify_res.json()
        assert data["verified"] is False
        assert "Data has been altered!" in data["error"] or "Block hash invalid" in data["error"]

        # Restore original details so DB integrity remains valid
        async with AsyncSessionLocal() as session:
            stmt = select(AuditLog).where(AuditLog.id == entry_id)
            entry = (await session.execute(stmt)).scalars().first()
            entry.details = original_details
            await session.commit()
