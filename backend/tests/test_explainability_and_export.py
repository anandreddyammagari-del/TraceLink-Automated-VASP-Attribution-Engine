import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.services.explainability import explainability_service
from backend.services.case_export import case_export_service
from backend.core.database import init_db, AsyncSessionLocal
from backend.core.seed import seed_initial_data

@pytest.fixture(autouse=True)
async def setup_database():
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed_initial_data(session)

def test_explainability_waterfall_decomposition():
    # Test a clean direct attribution
    res = explainability_service.explain_score(
        hop_count=1,
        volume_ratio=0.85,
        is_known_cluster=True,
        has_mixer=False,
        peel_depth=1,
        anomaly_score=0.1
    )
    assert res["final_confidence_score"] >= 80.0
    assert res["confidence_tier"] == "HIGH"
    assert len(res["waterfall_contributions"]) >= 5

    # Test mixer penalty
    mixer_res = explainability_service.explain_score(
        hop_count=4,
        volume_ratio=0.3,
        is_known_cluster=False,
        has_mixer=True,
        peel_depth=4,
        anomaly_score=0.8
    )
    assert mixer_res["final_confidence_score"] < 50.0
    assert mixer_res["confidence_tier"] == "LOW"
    # Find mixer contribution
    mixer_contrib = next(c for c in mixer_res["waterfall_contributions"] if "Mixer" in c["feature"])
    assert mixer_contrib["contribution"] == -40.0

def test_case_bundle_export_and_tamper_detection():
    case_meta = {"fir_number": "FIR-2026-DEL-CY-0042", "title": "Test Operation"}
    suspects = [{"person_id": "SUSP-1"}]
    bundle = case_export_service.export_case_bundle(
        case_data=case_meta,
        suspects=suspects,
        transactions=[],
        attributions=[],
        audit_trail=[],
        exporting_officer={"badge_number": "IND-CYBER-8841"}
    )
    assert "archive_metadata" in bundle
    assert "hmac_sha256_signature" in bundle["archive_metadata"]

    # Valid import
    valid, msg, payload = case_export_service.verify_and_import_bundle(bundle)
    assert valid is True
    assert "verified authentic" in msg

    # Malicious tampering: alter title
    bundle["bundle_payload"]["case"]["title"] = "CORRUPTED ALTERED TITLE"
    tampered_valid, tampered_msg, _ = case_export_service.verify_and_import_bundle(bundle)
    assert tampered_valid is False
    assert "signature mismatch" in tampered_msg.lower() or "tampered" in tampered_msg.lower()

@pytest.mark.asyncio
async def test_explainability_and_export_api_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post("/api/auth/login", json={
            "badge_number": "IND-CYBER-8841",
            "password": "Police@Secure2026"
        })
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Query explain-attribution
        exp_res = await client.get("/api/cases/FIR-2026-DEL-CY-0042/explain-attribution", headers=headers)
        assert exp_res.status_code == 200
        assert "explanation" in exp_res.json()
        assert "waterfall_contributions" in exp_res.json()["explanation"]

        # Export bundle
        exp_bundle_res = await client.get("/api/cases/FIR-2026-DEL-CY-0042/export-bundle", headers=headers)
        assert exp_bundle_res.status_code == 200
        bundle = exp_bundle_res.json()
        assert "archive_metadata" in bundle

        # Import bundle
        imp_res = await client.post("/api/cases/import-bundle", json=bundle, headers=headers)
        assert imp_res.status_code == 200
        assert imp_res.json()["status"] == "BUNDLE_IMPORTED_AUTHENTIC"
