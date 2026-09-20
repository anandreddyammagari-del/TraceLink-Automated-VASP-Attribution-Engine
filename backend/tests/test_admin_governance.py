import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.services.datapack_updater import datapack_service
from backend.core.database import init_db, AsyncSessionLocal
from backend.core.seed import seed_initial_data

@pytest.fixture(autouse=True)
async def setup_database():
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed_initial_data(session)

def test_datapack_service_inspection_and_reload():
    status = datapack_service.get_datapack_status()
    assert "datapack_version" in status
    assert "vasp_directory" in status["packages"]
    assert status["packages"]["vasp_directory"]["status"] == "LOADED_AND_VERIFIED"

    reload_res = datapack_service.reload_all_packs()
    assert reload_res["status"] == "RELOADED_SUCCESSFULLY"
    assert reload_res["indexed_vasp_count"] >= 5

@pytest.mark.asyncio
async def test_admin_governance_api_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Login as L3 Admin Director (ACP Vikram Rathore)
        admin_login = await client.post("/api/auth/login", json={
            "badge_number": "IND-CYBER-8841",
            "password": "Police@Secure2026"
        })
        admin_token = admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 2. Login as L1 Investigator (Insp. Anita Sharma)
        l1_login = await client.post("/api/auth/login", json={
            "badge_number": "IND-CYBER-4412",
            "password": "Police@Secure2026"
        })
        l1_token = l1_login.json()["access_token"]
        l1_headers = {"Authorization": f"Bearer {l1_token}"}

        # Test RBAC: L1 investigator should be DENIED (403 Forbidden)
        forbidden_res = await client.get("/api/admin/officers", headers=l1_headers)
        assert forbidden_res.status_code == 403

        # Test L3 Admin: should be ALLOWED (200 OK)
        officers_res = await client.get("/api/admin/officers", headers=admin_headers)
        assert officers_res.status_code == 200
        assert len(officers_res.json()) >= 2

        # Provision a new officer with unique badge
        import uuid
        unique_badge = f"IND-CYBER-{uuid.uuid4().hex[:6].upper()}"
        prov_res = await client.post("/api/admin/officers", json={
            "badge_number": unique_badge,
            "full_name": "SI Sunil Rao",
            "rank": "Sub-Inspector",
            "police_station": "Cyber Cell South",
            "clearance_level": "L1_INVESTIGATOR",
            "password": "Police@Secure2026"
        }, headers=admin_headers)
        assert prov_res.status_code == 200
        assert prov_res.json()["status"] == "OFFICER_PROVISIONED"

        # Check datapacks
        dp_res = await client.get("/api/admin/datapacks", headers=admin_headers)
        assert dp_res.status_code == 200
        assert "datapack_version" in dp_res.json()

        # Create cryptographic backup snapshot
        snap_res = await client.post("/api/admin/backup/create", headers=admin_headers)
        assert snap_res.status_code == 200
        assert snap_res.json()["status"] == "SNAPSHOT_SEALED"
        assert "sha256_integrity_seal" in snap_res.json()
