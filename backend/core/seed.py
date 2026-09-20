import json
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.user import User
from backend.models.case import Case
from backend.models.suspect import Suspect
from backend.models.wallet import Wallet
from backend.models.transaction import Transaction
from backend.models.audit import AuditLog
from backend.models.trace import Trace
from backend.models.attribution import VASPAttribution
from backend.core.security import hash_password

logger = logging.getLogger(__name__)

async def seed_initial_data(session: AsyncSession):
    """Seed the database with standard Cyber Police officers, cases, suspects, and multi-entity transactions."""
    # Check if data already exists
    res = await session.execute(select(User).limit(1))
    if res.scalars().first():
        logger.info("Database already seeded with forensic officer accounts.")
        return

    logger.info("Seeding institutional forensic accounts and multi-entity ledger...")

    # 1. Officers
    officer_admin = User(
        badge_number="IND-CYBER-8841",
        full_name="ACP Vikram Rathore",
        rank="Assistant Commissioner of Police (ACP)",
        police_station="Special Cyber Operations, State Crime Branch",
        clearance_level="L3_ADMIN_DIRECTOR",
        password_hash=hash_password("Police@Secure2026"),
        is_active=True
    )
    officer_l1 = User(
        badge_number="IND-CYBER-4412",
        full_name="Insp. Anita Sharma",
        rank="Inspector (Cyber Forensics)",
        police_station="Cyber Crime Police Station, Central District",
        clearance_level="L1_INVESTIGATOR",
        password_hash=hash_password("Police@Secure2026"),
        is_active=True
    )
    session.add_all([officer_admin, officer_l1])
    await session.flush()

    # 2. Cases
    case_1 = Case(
        fir_number="FIR-2026-DEL-CY-0042",
        title="Operation ShadowChain — Crypto Investment Syndicate & Layering",
        police_station="Special Cyber Operations, State Crime Branch",
        crime_sections="Section 66D IT Act, 2000 r/w Section 318(4), 336(3), 61(2) BNS, 2023",
        investigating_officer_id=officer_admin.id,
        status="OPEN",
        priority="CRITICAL",
        total_disputed_inr=48500000.0,
        description="Mass fraudulent Telegram trading bot funneling victim deposits through layering wallets to VASP cash-out points."
    )
    case_2 = Case(
        fir_number="FIR-2026-MUM-CY-0119",
        title="Operation BitLaundering — Multi-State Pig Butchering Syndicate",
        police_station="Cyber Police Station, Bandra Kurla Complex",
        crime_sections="Section 66C & 66D IT Act, 2000 r/w Section 318(4) BNS, 2023",
        investigating_officer_id=officer_l1.id,
        status="UNDER_REVIEW",
        priority="HIGH",
        total_disputed_inr=19200000.0,
        description="Fictitious algorithmic yield platform siphoning retail victim funds across Tron and Ethereum bridges."
    )
    session.add_all([case_1, case_2])
    await session.flush()

    # 3. Suspects
    susp_1 = Suspect(
        person_id="SUSP-IND-9021",
        full_name="Rohan Malhotra",
        aliases="CryptoKing, RH_Alpha",
        national_id="PAN: BMQPM1928K",
        case_id=case_1.id,
        risk_category="SEVERE",
        notes="Primary kingpin running Telegram recruitment groups and orchestrating initial collection wallets."
    )
    susp_2 = Suspect(
        person_id="SUSP-IND-9022",
        full_name="Dinesh Verma",
        aliases="LayerMaster, D_Verma09",
        national_id="PAN: CZKPV8841L",
        case_id=case_1.id,
        risk_category="HIGH_RISK",
        notes="Technical operator managing mixer splitting, peel chains, and bridging intermediary wallets."
    )
    susp_3 = Suspect(
        person_id="SUSP-IND-9023",
        full_name="Sanjay Joshi",
        aliases="Mule_SJ, PuneMule",
        national_id="PAN: APXPK5512M",
        case_id=case_2.id,
        risk_category="MONITORED",
        notes="Mule account aggregator receiving fragmented deposits and liquidating on local P2P desks."
    )
    session.add_all([susp_1, susp_2, susp_3])
    await session.flush()

    # 4. Suspect Wallets
    wallet_1 = Wallet(
        address="0x71c8901b2c45e89d1234a567b8901234cde56781",
        chain="ethereum",
        suspect_id=susp_1.id,
        cluster_id="CLUSTER-MALT-01",
        known_entity_label="Rohan Malhotra Collection Wallet",
        entity_category="SUSPECT_WALLET",
        risk_score=94.5
    )
    wallet_2 = Wallet(
        address="0x3a918273645bcef890123456789abcdef1234567",
        chain="ethereum",
        suspect_id=susp_2.id,
        cluster_id="CLUSTER-VERM-02",
        known_entity_label="Dinesh Verma Layering Intermediary 1",
        entity_category="INTERMEDIARY",
        risk_score=82.0
    )
    wallet_3 = Wallet(
        address="0x89ab12cd34ef5678901234567890abcdef123456",
        chain="ethereum",
        suspect_id=susp_2.id,
        cluster_id="CLUSTER-VERM-02",
        known_entity_label="Dinesh Verma Layering Intermediary 2",
        entity_category="INTERMEDIARY",
        risk_score=78.5
    )
    wallet_vasp = Wallet(
        address="0x28c6c06298d514db089934071355e5743bf21d60",
        chain="ethereum",
        suspect_id=None,
        cluster_id="CLUSTER-BINANCE-HOT",
        known_entity_label="Binance 14: Exchange Hot Wallet",
        entity_category="VASP",
        risk_score=10.0
    )
    wallet_wazirx = Wallet(
        address="0x503828976d22510aad0201ac7ec88293211d23dc",
        chain="ethereum",
        suspect_id=None,
        cluster_id="CLUSTER-WAZIRX-DEP",
        known_entity_label="WazirX: Nodal Deposit Gateway",
        entity_category="VASP",
        risk_score=5.0
    )
    session.add_all([wallet_1, wallet_2, wallet_3, wallet_vasp, wallet_wazirx])
    await session.flush()

    # 5. Multi-Entity Transactions
    now = datetime.now(timezone.utc)
    txs = [
        Transaction(
            tx_hash="0xaa12894cd87123efb67192834019283019283019283019283019283019283011",
            case_id=case_1.id,
            suspect_id=susp_1.id,
            person_id="SUSP-IND-9021",
            from_address="0x1111111111111111111111111111111111111111",  # Victim
            to_address=wallet_1.address,
            value=18.5,
            token_symbol="ETH",
            value_inr=5180000.0,
            timestamp=now - timedelta(days=5, hours=4),
            chain="ethereum",
            risk_flag="FRAUD_COLLECTION",
            attributed_entity="Suspect Primary Collection",
            hop_level=0
        ),
        Transaction(
            tx_hash="0xbb23905de98234fac78203945120394120394120394120394120394120394122",
            case_id=case_1.id,
            suspect_id=susp_1.id,
            person_id="SUSP-IND-9021",
            from_address=wallet_1.address,
            to_address=wallet_2.address,
            value=12.0,
            token_symbol="ETH",
            value_inr=3360000.0,
            timestamp=now - timedelta(days=4, hours=22),
            chain="ethereum",
            risk_flag="LAYERING_HOP_1",
            attributed_entity="Intermediary Splitter",
            hop_level=1
        ),
        Transaction(
            tx_hash="0xcc34016ef09345abd89314056231405231405231405231405231405231405233",
            case_id=case_1.id,
            suspect_id=susp_2.id,
            person_id="SUSP-IND-9022",
            from_address=wallet_2.address,
            to_address=wallet_3.address,
            value=8.5,
            token_symbol="ETH",
            value_inr=2380000.0,
            timestamp=now - timedelta(days=3, hours=18),
            chain="ethereum",
            risk_flag="PEEL_CHAIN",
            attributed_entity="Intermediary Peel Wallet",
            hop_level=2
        ),
        Transaction(
            tx_hash="0xdd45127fa10456bce90425167342516342516342516342516342516342516344",
            case_id=case_1.id,
            suspect_id=susp_2.id,
            person_id="SUSP-IND-9022",
            from_address=wallet_3.address,
            to_address=wallet_wazirx.address,
            value=8.2,
            token_symbol="ETH",
            value_inr=2296000.0,
            timestamp=now - timedelta(days=2, hours=10),
            chain="ethereum",
            risk_flag="VASP_DEPOSIT",
            attributed_entity="WazirX Nodal Cluster",
            hop_level=3
        ),
        Transaction(
            tx_hash="0xee56238ab21567cde01536278453627453627453627453627453627453627455",
            case_id=case_2.id,
            suspect_id=susp_3.id,
            person_id="SUSP-IND-9023",
            from_address="0x4444444444444444444444444444444444444444",
            to_address="0x5555555555555555555555555555555555555555",
            value=5.0,
            token_symbol="ETH",
            value_inr=1400000.0,
            timestamp=now - timedelta(days=1, hours=6),
            chain="ethereum",
            risk_flag="STRUCTURING",
            attributed_entity="P2P Mule Aggregator",
            hop_level=1
        ),
        Transaction(
            tx_hash="0xff67349bc32678def12647389564738564738564738564738564738564738566",
            case_id=case_2.id,
            suspect_id=susp_3.id,
            person_id="SUSP-IND-9023",
            from_address="0x5555555555555555555555555555555555555555",
            to_address=wallet_vasp.address,
            value=4.95,
            token_symbol="ETH",
            value_inr=1386000.0,
            timestamp=now - timedelta(hours=14),
            chain="ethereum",
            risk_flag="VASP_DEPOSIT",
            attributed_entity="Binance Hot Cluster",
            hop_level=2
        )
    ]
    session.add_all(txs)
    await session.flush()

    # 6. Sample Trace and Attribution
    trace_demo = Trace(
        case_id=case_1.id,
        root_wallet=wallet_1.address,
        max_hops=3,
        chain="ethereum",
        status="COMPLETED",
        total_nodes=4,
        total_edges=3,
        graph_json=json.dumps({
            "nodes": [
                {"id": wallet_1.address, "label": "Rohan Malhotra (Primary)", "category": "SUSPECT_WALLET", "risk_score": 94.5, "hop": 0},
                {"id": wallet_2.address, "label": "Layering Hop 1", "category": "INTERMEDIARY", "risk_score": 82.0, "hop": 1},
                {"id": wallet_3.address, "label": "Peel Node Hop 2", "category": "INTERMEDIARY", "risk_score": 78.5, "hop": 2},
                {"id": wallet_wazirx.address, "label": "WazirX Deposit Cluster", "category": "VASP", "risk_score": 5.0, "hop": 3}
            ],
            "edges": [
                {"source": wallet_1.address, "target": wallet_2.address, "value": 12.0, "token_symbol": "ETH", "tx_hash": txs[1].tx_hash, "risk_flag": "LAYERING_HOP_1"},
                {"source": wallet_2.address, "target": wallet_3.address, "value": 8.5, "token_symbol": "ETH", "tx_hash": txs[2].tx_hash, "risk_flag": "PEEL_CHAIN"},
                {"source": wallet_3.address, "target": wallet_wazirx.address, "value": 8.2, "token_symbol": "ETH", "tx_hash": txs[3].tx_hash, "risk_flag": "VASP_DEPOSIT"}
            ]
        }),
        completed_at=now - timedelta(hours=8)
    )
    session.add(trace_demo)
    await session.flush()

    attrib_demo = VASPAttribution(
        trace_id=trace_demo.id,
        target_vasp_name="WazirX (Zanmai Labs Pvt Ltd)",
        vasp_deposit_address=wallet_wazirx.address,
        hop_distance=3,
        total_volume=8.2,
        token_symbol="ETH",
        confidence_score=89.4,
        confidence_tier="HIGH",
        evidence_breakdown_json=json.dumps([
            "Shortest hop distance: 3 hops from suspect collection address",
            "High volume retention: 68.3% of primary stolen funds conserved through peel chain",
            "Direct attribution to verified WazirX nodal deposit hot wallet",
            "Temporal velocity: Transfer sequence executed within 62 hours (automated layering pattern)",
            "Zero mixer / coinjoin obfuscation detected along the primary routing path"
        ])
    )
    session.add(attrib_demo)
    await session.flush()

    # 7. Genesis Audit Log entry with SHA-256 chain initialization
    from backend.models.audit import format_audit_timestamp
    genesis_prev = "0000000000000000000000000000000000000000000000000000000000000000"
    ts_str = format_audit_timestamp(now)
    genesis_details = "Forensic workstation initialized. Cryptographic audit chain anchored with Genesis block."
    genesis_hash = AuditLog.compute_hash(
        prev_hash=genesis_prev,
        event_type="GENESIS_SYSTEM_INIT",
        officer_id=officer_admin.badge_number,
        case_id="SYSTEM",
        details=genesis_details,
        timestamp_str=ts_str
    )
    
    audit_init = AuditLog(
        event_type="GENESIS_SYSTEM_INIT",
        officer_id=officer_admin.badge_number,
        case_id="SYSTEM",
        details=genesis_details,
        prev_hash=genesis_prev,
        current_hash=genesis_hash,
        timestamp=now
    )
    session.add(audit_init)
    await session.commit()
    logger.info("Forensic database seeded successfully with tamper-evident audit root.")
