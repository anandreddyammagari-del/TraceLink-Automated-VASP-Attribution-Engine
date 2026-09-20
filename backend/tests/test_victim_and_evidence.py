import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.services.ncrp_ingestion import ncrp_service
from backend.services.valuation_service import valuation_service
from backend.services.evidence_locker import evidence_locker
from backend.services.seizure_memo_generator import seizure_memo_generator
from backend.core.database import init_db, AsyncSessionLocal
from backend.core.seed import seed_initial_data

@pytest.fixture(autouse=True)
async def setup_database():
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed_initial_data(session)

def test_ncrp_complaint_ingestion():
    csv_data = """complaint_ref,complainant_name,contact_phone,destination_wallet_reported,loss_amount_inr,fraud_modality,incident_date
NCRP/2026/TEST/001,Amit Verma,9800000001,0x71c8901b2c45e89d1234a567b8901234cde56781,250000.0,Telegram Crypto Fraud,2026-09-15
"""
    complaints = ncrp_service.parse_complaints(csv_data)
    assert len(complaints) == 1
    assert complaints[0]["complaint_ref"] == "NCRP/2026/TEST/001"
    assert complaints[0]["loss_amount_inr"] == 250000.0
    assert complaints[0]["destination_wallet"] == "0x71c8901b2c45e89d1234a567b8901234cde56781"

def test_historical_inr_valuation():
    # Test valuation of 2.5 ETH on 2026-09-14 (from fixture rate 280,000 INR)
    inr_val = valuation_service.calculate_valuation_inr(2.5, "ETH", "2026-09-14T10:00:00Z")
    assert inr_val == 700000.0

    # Test BTC valuation
    btc_val = valuation_service.calculate_valuation_inr(1.0, "BTC", "2026-09-14T10:00:00Z")
    assert btc_val == 5350000.0

def test_evidence_locker_custody_and_integrity():
    sample_evidence = b"TRANSACTION_EXPORT_BLOCK_18920412_FORENSIC_HASH"
    entry = evidence_locker.register_evidence(
        filename="chain_export.bin",
        file_bytes=sample_evidence,
        case_id="FIR-2026-DEL-CY-0042",
        officer_badge="IND-CYBER-8841",
        item_description="Cold wallet storage extraction raw binary dump"
    )
    assert entry["sha256_checksum"] is not None
    assert entry["md5_checksum"] is not None
    assert entry["custody_status"] == "SECURED_IN_DIGITAL_VAULT"

    # Integrity verification
    assert evidence_locker.verify_evidence_integrity(sample_evidence, entry["sha256_checksum"]) is True
    assert evidence_locker.verify_evidence_integrity(b"TAMPERED_DATA", entry["sha256_checksum"]) is False

def test_section_105_bnss_seizure_memo():
    memo = seizure_memo_generator.generate_seizure_memo(
        fir_number="FIR-2026-DEL-CY-0042",
        police_station="Special Cyber Operations Branch",
        crime_sections="Section 66D IT Act r/w Section 318(4) BNS",
        seized_assets_description="1x Trezor Model T Hardware Wallet, 1x Seed Card with 12 words",
        custody_officer={"rank": "ACP", "badge_number": "IND-CYBER-8841"},
        suspect_name="Rohan Malhotra"
    )
    assert "SEIZURE-MEMO/BNSS105" in memo["memo_reference"]
    assert "Section 105 Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023" in memo["memo_body"]
    assert "Trezor Model T" in memo["memo_body"]

@pytest.mark.asyncio
async def test_victims_and_evidence_api_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post("/api/auth/login", json={
            "badge_number": "IND-CYBER-8841",
            "password": "Police@Secure2026"
        })
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Check victims list
        v_res = await client.get("/api/victims", headers=headers)
        assert v_res.status_code == 200
        assert len(v_res.json()) >= 1

        # Check wallet correlation
        correlate_res = await client.post(
            "/api/victims/correlate-wallet?address=0x71c8901b2c45e89d1234a567b8901234cde56781",
            headers=headers
        )
        assert correlate_res.status_code == 200
        assert correlate_res.json()["victim_count"] >= 1

        # Test seizure memo API endpoint
        m_res = await client.post(
            "/api/evidence/seizure-memo",
            data={
                "fir_number": "FIR-2026-DEL-CY-0042",
                "police_station": "Special Cyber Operations Branch",
                "crime_sections": "Section 66D IT Act r/w BNS",
                "seized_assets_description": "1x Ledger Nano X Hardware Wallet"
            },
            headers=headers
        )
        assert m_res.status_code == 200
        assert "SEIZURE-MEMO/BNSS105" in m_res.json()["memo_reference"]
