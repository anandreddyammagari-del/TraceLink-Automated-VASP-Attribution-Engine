import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.core.database import init_db, AsyncSessionLocal
from backend.core.seed import seed_initial_data
from backend.services.dataset_ingestion import DatasetIngestionService
from backend.services.covalent_service import CovalentService

@pytest.fixture(autouse=True)
async def setup_database():
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed_initial_data(session)

@pytest.mark.asyncio
async def test_csv_canonical_ingestion():
    h1 = f"0x{uuid.uuid4().hex}"
    h2 = f"0x{uuid.uuid4().hex}"
    csv_data = f"""tx_hash,person_id,from_address,to_address,value,timestamp,token_symbol,chain,risk_flag,attributed_entity
{h1},SUSP-INGEST-01,0xaaaabbbbccccddddeeeeffff0000111122223333,0xbbbbccccddddeeeeffff00001111222233334444,10.5,2026-09-18T10:00:00Z,ETH,ethereum,STRUCTURING,Intermediary Mule
{h2},SUSP-INGEST-01,0xbbbbccccddddeeeeffff00001111222233334444,0x503828976d22510aad0201ac7ec88293211d23dc,10.2,2026-09-18T14:30:00Z,ETH,ethereum,VASP_DEPOSIT,WazirX Deposit
"""
    async with AsyncSessionLocal() as session:
        result = await DatasetIngestionService.ingest_csv_content(
            content=csv_data,
            case_id="FIR-2026-DEL-CY-0042",
            officer_badge="TEST-BADGE-01",
            db=session
        )
        assert result["total_rows_received"] == 2
        assert result["inserted"] == 2
        assert len(result["errors"]) == 0

@pytest.mark.asyncio
async def test_csv_alias_headers_ingestion():
    h = f"0x{uuid.uuid4().hex}"
    csv_data = f"""hash,suspect,from,to,amount,date,token
{h},SUSP-ALIAS-02,0xccccddddeeeeffff000011112222333344445555,0xddddeeeeffff0000111122223333444455556666,5.25,2026-09-17 12:00:00,ETH
"""
    async with AsyncSessionLocal() as session:
        result = await DatasetIngestionService.ingest_csv_content(
            content=csv_data,
            case_id="FIR-2026-DEL-CY-0042",
            officer_badge="TEST-BADGE-01",
            db=session
        )
        assert result["total_rows_received"] == 1
        assert result["inserted"] == 1
        assert result["sample_records"][0]["value"] == 5.25
        assert result["sample_records"][0]["person_id"] == "SUSP-ALIAS-02"

@pytest.mark.asyncio
async def test_json_array_ingestion():
    h = f"0x{uuid.uuid4().hex}"
    json_data = f"""[
      {{
        "tx_hash": "{h}",
        "person_id": "SUSP-JSON-03",
        "from_address": "0xeeeeffff00001111222233334444555566667777",
        "to_address": "0xffff000011112222333344445555666677778888",
        "value": 3.75,
        "timestamp": "2026-09-18T18:00:00Z"
      }}
    ]"""
    async with AsyncSessionLocal() as session:
        result = await DatasetIngestionService.ingest_json_content(
            content=json_data,
            case_id="FIR-2026-DEL-CY-0042",
            officer_badge="TEST-BADGE-01",
            db=session
        )
        assert result["total_rows_received"] == 1
        assert result["inserted"] == 1

@pytest.mark.asyncio
async def test_malformed_and_duplicate_handling():
    h_valid = f"0x{uuid.uuid4().hex}"
    # Contains 1 valid row, 1 missing field, 1 invalid numeric value
    csv_data = f"""tx_hash,from_address,to_address,value
{h_valid},0x1111,0x2222,4.5
,0xmissinghash,0x2222,1.0
0xinvalidval,0x1111,0x2222,NOT_A_NUMBER
"""
    async with AsyncSessionLocal() as session:
        result = await DatasetIngestionService.ingest_csv_content(
            content=csv_data,
            case_id="FIR-2026-DEL-CY-0042",
            officer_badge="TEST-BADGE-01",
            db=session
        )
        assert result["total_rows_received"] == 3
        assert result["inserted"] == 1
        assert len(result["errors"]) == 2

        # Re-ingest exact same content to test duplicate suppression
        dup_result = await DatasetIngestionService.ingest_csv_content(
            content=csv_data,
            case_id="FIR-2026-DEL-CY-0042",
            officer_badge="TEST-BADGE-01",
            db=session
        )
        assert dup_result["inserted"] == 0
        assert dup_result["skipped_duplicates"] == 1

@pytest.mark.asyncio
async def test_covalent_offline_fixture_fallback():
    txs = await CovalentService.fetch_wallet_transactions(
        address="0x71c8901b2c45e89d1234a567b8901234cde56781",
        chain="ethereum"
    )
    assert len(txs) >= 2
    assert any("0x" in t["tx_hash"] for t in txs)
    assert all("value" in t and "from_address" in t and "to_address" in t for t in txs)

@pytest.mark.asyncio
async def test_upload_dataset_api_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Officer login
        login = await client.post("/api/auth/login", json={
            "badge_number": "IND-CYBER-8841",
            "password": "Police@Secure2026"
        })
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        h_api = f"0x{uuid.uuid4().hex}"
        csv_bytes = f"""tx_hash,person_id,from_address,to_address,value,timestamp
{h_api},SUSP-API-99,0xaaaabbbb1111,0xbbbbcccc2222,9.99,2026-09-19T00:00:00Z
""".encode("utf-8")

        files = {"file": ("test_run_txs.csv", csv_bytes, "text/csv")}
        res = await client.post("/api/transactions/upload-dataset", headers=headers, files=files)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"
        assert data["summary"]["inserted"] == 1
