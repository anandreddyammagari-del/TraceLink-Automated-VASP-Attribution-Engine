import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.services.temporal_analysis import temporal_service
from backend.services.peel_chain_detector import peel_chain_detector
from backend.services.poisoning_detector import poisoning_detector
from backend.core.database import init_db, AsyncSessionLocal
from backend.core.seed import seed_initial_data

@pytest.fixture(autouse=True)
async def setup_database():
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed_initial_data(session)

def test_temporal_burst_and_dormancy_detection():
    now = datetime.now(timezone.utc)
    # Rapid burst sequence: 3 transactions within 15 seconds
    burst_txs = [
        {"tx_hash": "0x1", "timestamp": (now - timedelta(seconds=20)).isoformat(), "from_address": "0xa", "to_address": "0xb", "value": 10.0},
        {"tx_hash": "0x2", "timestamp": (now - timedelta(seconds=12)).isoformat(), "from_address": "0xb", "to_address": "0xc", "value": 9.5},
        {"tx_hash": "0x3", "timestamp": (now - timedelta(seconds=2)).isoformat(), "from_address": "0xc", "to_address": "0xd", "value": 9.0}
    ]
    report = temporal_service.detect_velocity_anomalies(burst_txs)
    assert report["burst_count_sub_30s"] == 2
    assert report["velocity_profile"] == "AUTOMATED_BOT_SCRIPT"

    # Dormancy sequence: 40 days gap
    dormant_txs = [
        {"tx_hash": "0x1", "timestamp": (now - timedelta(days=45)).isoformat(), "from_address": "0xa", "to_address": "0xb", "value": 10.0},
        {"tx_hash": "0x2", "timestamp": now.isoformat(), "from_address": "0xb", "to_address": "0xc", "value": 10.0}
    ]
    dormant_report = temporal_service.detect_velocity_anomalies(dormant_txs)
    assert dormant_report["dormant_drain_count"] == 1
    assert dormant_report["velocity_profile"] == "DORMANT_COLD_DRAIN"

def test_peel_chain_detection():
    # Construct a classic 2-hop peel chain
    # Root A -> (peel 1.0 to D1, change 9.0 to B)
    # B -> (peel 1.0 to D2, change 8.0 to C)
    txs = [
        {"tx_hash": "0xp1", "from_address": "0xaaaa", "to_address": "0xd1", "value": 1.0},
        {"tx_hash": "0xp2", "from_address": "0xaaaa", "to_address": "0xbbbb", "value": 9.0},
        {"tx_hash": "0xp3", "from_address": "0xbbbb", "to_address": "0xd2", "value": 1.0},
        {"tx_hash": "0xp4", "from_address": "0xbbbb", "to_address": "0xcccc", "value": 8.0}
    ]
    res = peel_chain_detector.detect_peel_sequence(txs)
    assert res["peel_chains_detected"] >= 1
    chain = res["chains"][0]
    assert chain["depth"] == 2
    assert chain["total_peeled_amount"] == 2.0

def test_address_poisoning_vanity_matching():
    # Legitimate victim counterparty
    legit = "0x71c8901b2c45e89d1234a567b8901234cde56781"
    # Attacker crafted vanity: same prefix (0x71c8) and suffix (6781), middle random
    poison_vanity = "0x71c8ffffffffffffffffffffffffffffffcde56781"

    sim = poisoning_detector.calculate_vanity_similarity(poison_vanity, legit)
    assert sim["is_spoofed_vanity"] is True
    assert sim["prefix_match_len"] >= 4
    assert sim["suffix_match_len"] >= 4

    # Test poisoning transaction evaluation
    dust_tx = {
        "tx_hash": "0xpoison1",
        "from_address": "0xattacker",
        "to_address": poison_vanity,
        "value": 0.00005
    }
    is_poison, reason = poisoning_detector.is_poisoning_transaction(dust_tx, [legit])
    assert is_poison is True
    assert "Address poisoning vanity match" in reason

@pytest.mark.asyncio
async def test_analytics_api_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post("/api/auth/login", json={
            "badge_number": "IND-CYBER-8841",
            "password": "Police@Secure2026"
        })
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Query temporal analytics for seeded case
        res = await client.get("/api/analytics/temporal/FIR-2026-DEL-CY-0042", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "velocity_profile" in data
        assert "burst_count_sub_30s" in data
