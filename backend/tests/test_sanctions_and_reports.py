import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.services.sanctions_service import sanctions_service
from backend.services.bridge_resolver import bridge_resolver
from backend.services.report_generator import report_generator
from backend.core.database import init_db, AsyncSessionLocal
from backend.core.seed import seed_initial_data

@pytest.fixture(autouse=True)
async def setup_database():
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed_initial_data(session)

@pytest.mark.asyncio
async def test_sanctions_screening_service():
    # Test known OFAC SDN address from snapshot
    lazarus_addr = "0x1da5821544e25c636c1417ba96ade4cf6d2f9b5a"
    match = sanctions_service.check_address(lazarus_addr)
    assert match is not None
    assert "Lazarus" in match["entity_name"]
    assert match["list_source"] == "OFAC_SDN"

    # Test clean address
    clean_addr = "0x0000000000000000000000000000000000000001"
    assert sanctions_service.check_address(clean_addr) is None

@pytest.mark.asyncio
async def test_bridge_resolver_contract_identification():
    # Test Wormhole portal
    wormhole_addr = "0x98f3c9e6e3face36baad05fe09d375eff1764732"
    bridge_info = bridge_resolver.identify_bridge_contract(wormhole_addr)
    assert bridge_info is not None
    assert bridge_info["protocol"] == "Wormhole Portal"

    # Test Stargate router
    stargate_addr = "0xaf5191b0de27e10945d34f1949dd11565560cb6"
    assert bridge_resolver.identify_bridge_contract(stargate_addr) is not None

@pytest.mark.asyncio
async def test_pdf_report_generation_binary():
    case_dict = {
        "fir_number": "FIR-2026-DEL-CY-0042",
        "title": "Operation ShadowChain",
        "police_station": "Special Cyber Operations Branch",
        "crime_sections": "Sec 66D IT Act r/w BNS",
        "total_disputed_inr": 48500000.0
    }
    attrib_dict = {
        "target_vasp_name": "WazirX (Zanmai Labs Pvt Ltd)",
        "vasp_deposit_address": "0x503828976d22510aad0201ac7ec88293211d23dc",
        "confidence_score": 89.4,
        "confidence_tier": "HIGH",
        "total_volume": 8.2,
        "token_symbol": "ETH",
        "hop_distance": 3,
        "evidence_breakdown": [
            "Direct 3-hop topological connection",
            "Conserved fund flow ratio > 65%"
        ]
    }
    pdf_bytes = report_generator.generate_case_dossier_pdf(
        case_dict=case_dict,
        attribution_dict=attrib_dict,
        transactions=[],
        officer={"rank": "ACP", "badge_number": "IND-CYBER-8841"},
        audit_chain_head="a" * 64
    )
    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 2000

@pytest.mark.asyncio
async def test_sanctions_and_report_api_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Officer login
        login = await client.post("/api/auth/login", json={
            "badge_number": "IND-CYBER-8841",
            "password": "Police@Secure2026"
        })
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Check sanctions endpoint
        s_res = await client.get("/api/sanctions/check/0x1da5821544e25c636c1417ba96ade4cf6d2f9b5a", headers=headers)
        assert s_res.status_code == 200
        assert s_res.json()["sanctioned"] is True

        # Check court dossier PDF download endpoint
        p_res = await client.get("/api/reports/case/FIR-2026-DEL-CY-0042/pdf", headers=headers)
        assert p_res.status_code == 200
        assert p_res.headers["content-type"] == "application/pdf"
        assert p_res.content.startswith(b"%PDF-")
