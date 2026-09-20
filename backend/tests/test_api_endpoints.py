import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.core.database import init_db, AsyncSessionLocal
from backend.core.seed import seed_initial_data

@pytest.fixture(autouse=True)
async def setup_database():
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed_initial_data(session)

@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "OPERATIONAL"
        assert "TraceLink" in data["app_name"]

@pytest.mark.asyncio
async def test_officer_login_success_and_failure():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Invalid credentials
        fail_res = await client.post("/api/auth/login", json={
            "badge_number": "IND-CYBER-8841",
            "password": "WrongPassword123"
        })
        assert fail_res.status_code == 401

        # Correct credentials
        success_res = await client.post("/api/auth/login", json={
            "badge_number": "IND-CYBER-8841",
            "password": "Police@Secure2026"
        })
        assert success_res.status_code == 200
        token_data = success_res.json()
        assert "access_token" in token_data
        assert token_data["badge_number"] == "IND-CYBER-8841"
        assert token_data["clearance_level"] == "L3_ADMIN_DIRECTOR"

@pytest.mark.asyncio
async def test_master_transaction_stream_and_search():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post("/api/auth/login", json={
            "badge_number": "IND-CYBER-8841",
            "password": "Police@Secure2026"
        })
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Fetch all transactions
        res = await client.get("/api/transactions", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 5
        assert len(data["transactions"]) >= 5

        # Search specifically for suspect SUSP-IND-9021
        filter_res = await client.get("/api/transactions?person_id=SUSP-IND-9021", headers=headers)
        assert filter_res.status_code == 200
        filtered_data = filter_res.json()
        assert filtered_data["total"] >= 2
        for tx in filtered_data["transactions"]:
            assert tx["person_id"] == "SUSP-IND-9021"

@pytest.mark.asyncio
async def test_cases_and_trace_back():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post("/api/auth/login", json={
            "badge_number": "IND-CYBER-8841",
            "password": "Police@Secure2026"
        })
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Cases list
        cases_res = await client.get("/api/cases", headers=headers)
        assert cases_res.status_code == 200
        cases = cases_res.json()
        assert len(cases) >= 2
        assert any("ShadowChain" in c["title"] for c in cases)

        # Trace back by Person ID
        pivot_res = await client.get("/api/traces/by-person/SUSP-IND-9021", headers=headers)
        assert pivot_res.status_code == 200
        graph_data = pivot_res.json()
        assert "nodes" in graph_data
        assert "edges" in graph_data
        assert len(graph_data["nodes"]) >= 2

@pytest.mark.asyncio
async def test_audit_chain_verification():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post("/api/auth/login", json={
            "badge_number": "IND-CYBER-8841",
            "password": "Police@Secure2026"
        })
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Verify cryptographic chain
        verify_res = await client.get("/api/audit/verify-chain", headers=headers)
        assert verify_res.status_code == 200
        assert verify_res.json()["verified"] is True
        assert verify_res.json()["status"] == "CHAIN_INTEGRITY_VERIFIED_AUTHENTIC"
