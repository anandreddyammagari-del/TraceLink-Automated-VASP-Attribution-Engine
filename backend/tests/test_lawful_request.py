import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.core.database import init_db, AsyncSessionLocal
from backend.core.seed import seed_initial_data
from backend.models.case import Case
from backend.models.attribution import VASPAttribution
from backend.services.request_generator import LawfulRequestGenerator
from sqlalchemy import select

@pytest.fixture(autouse=True)
async def setup_database():
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed_initial_data(session)

@pytest.mark.asyncio
async def test_section_94_notice_generation():
    async with AsyncSessionLocal() as session:
        case = (await session.execute(select(Case).limit(1))).scalars().first()
        attrib = (await session.execute(select(VASPAttribution).limit(1))).scalars().first()
        
        officer = {
            "rank": "ACP",
            "badge_number": "IND-CYBER-8841",
            "station": "Special Cyber Cell, State Crime Branch"
        }

        notice = LawfulRequestGenerator.generate_section_94_notice(
            case_record=case,
            attribution=attrib,
            officer=officer,
            custom_instructions="Preserve IP connection logs for port 443."
        )

        assert "Section 94" in notice["statutory_clause"]
        assert "BNSS" in notice["statutory_clause"]
        assert "Section 79(3)(b)" in notice["statutory_clause"]
        assert attrib.target_vasp_name in notice["notice_body"]
        assert attrib.vasp_deposit_address in notice["notice_body"]
        assert "MANDATORY INSTITUTIONAL SAFETY NOTICE" in notice["notice_body"]
        assert "Direct electronic submission to external portals is deactivated" in notice["notice_body"]
        assert "Preserve IP connection logs for port 443" in notice["notice_body"]

@pytest.mark.asyncio
async def test_notice_drafting_and_signing_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Officer login
        login = await client.post("/api/auth/login", json={
            "badge_number": "IND-CYBER-8841",
            "password": "Police@Secure2026"
        })
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Fetch case and attribution ID
        cases_res = await client.get("/api/cases", headers=headers)
        case_id = cases_res.json()[0]["id"]

        # Get existing traces for attribution ID
        async with AsyncSessionLocal() as session:
            attrib = (await session.execute(select(VASPAttribution).limit(1))).scalars().first()
            attrib_id = attrib.id
            target_vasp = attrib.target_vasp_name
            target_addr = attrib.vasp_deposit_address

        # Draft notice via API
        draft_res = await client.post("/api/requests/draft", headers=headers, json={
            "attribution_id": attrib_id,
            "case_id": case_id,
            "target_vasp_name": target_vasp,
            "target_deposit_wallet": target_addr,
            "custom_remarks": "Immediate freeze requested."
        })
        assert draft_res.status_code == 200
        draft_data = draft_res.json()
        assert "id" in draft_data
        assert draft_data["status"] == "DRAFT"
        notice_id = draft_data["id"]

        # Officer digital sign-off
        sign_res = await client.post(f"/api/requests/{notice_id}/sign", headers=headers, json={
            "confirm_local_review_only": True,
            "officer_notes": "Forensically verified against WazirX deposit gateway."
        })
        assert sign_res.status_code == 200
        assert sign_res.json()["status"] == "APPROVED_PRINT_READY"

        # Verify updated status
        detail_res = await client.get(f"/api/requests/{notice_id}", headers=headers)
        assert detail_res.status_code == 200
        assert detail_res.json()["status"] == "APPROVED_PRINT_READY"
        assert detail_res.json()["is_external_submission_deactivated"] is True
