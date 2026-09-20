import json
import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from backend.core.database import AsyncSessionLocal
from backend.core.kafka_client import event_bus
from backend.core.config import settings
from backend.models.trace import Trace
from backend.models.transaction import Transaction
from backend.models.attribution import VASPAttribution
from backend.models.wallet import Wallet
from backend.services.covalent_service import CovalentService
from backend.services.chainalysis_service import known_entity_service
from backend.services.graph_algorithms import (
    build_networkx_graph,
    bfs_nearest_vasp,
    dijkstra_confidence_weighted_path,
    calculate_centrality_metrics
)

logger = logging.getLogger(__name__)

async def process_trace_event(message: dict):
    """Worker processing function for an individual trace event."""
    trace_id = message.get("trace_id")
    root_wallet = message.get("root_wallet", "").lower()
    chain = message.get("chain", "ethereum")
    max_hops = message.get("max_hops", 4)
    case_id = message.get("case_id")

    logger.info(f"[TraceWorker] Processing trace task: ID {trace_id} for root wallet {root_wallet}")

    async with AsyncSessionLocal() as db:
        stmt = select(Trace).where(Trace.id == trace_id)
        res = await db.execute(stmt)
        trace = res.scalars().first()
        if not trace:
            logger.error(f"[TraceWorker] Trace record {trace_id} not found.")
            return

        trace.status = "PROCESSING"
        await db.commit()

        try:
            # 1. Look for existing transactions in database for this root wallet
            tx_stmt = select(Transaction).where(
                or_(
                    Transaction.from_address == root_wallet,
                    Transaction.to_address == root_wallet,
                    Transaction.case_id == case_id
                )
            )
            tx_res = await db.execute(tx_stmt)
            txs = tx_res.scalars().all()

            # If none exist, query Covalent service (or offline fixtures)
            if not txs:
                logger.info(f"[TraceWorker] Querying multi-chain provider for {root_wallet}")
                fetched = await CovalentService.fetch_wallet_transactions(root_wallet, chain)
                new_tx_objs = []
                for f in fetched:
                    # Categorize destination
                    cat_info = known_entity_service.categorize_address(f["to_address"])
                    risk_flag = "VASP_DEPOSIT" if cat_info["category"] == "VASP" else f.get("risk_flag", "UNVERIFIED")

                    tx_obj = Transaction(
                        tx_hash=f["tx_hash"],
                        case_id=case_id,
                        person_id=message.get("person_id", "DISCOVERED_WALLET"),
                        from_address=f["from_address"].lower(),
                        to_address=f["to_address"].lower(),
                        value=f["value"],
                        token_symbol=f["token_symbol"],
                        value_inr=round(f["value"] * 280000.0, 2),
                        timestamp=f["timestamp"],
                        chain=chain,
                        risk_flag=risk_flag,
                        attributed_entity=cat_info["label"],
                        hop_level=1
                    )
                    db.add(tx_obj)
                    new_tx_objs.append(tx_obj)
                await db.commit()
                txs = new_tx_objs

            # 2. Construct Graph Topology
            nodes_dict = {}
            edges = []

            # Root Node
            root_info = known_entity_service.categorize_address(root_wallet, default_category="SUSPECT_WALLET")
            nodes_dict[root_wallet] = {
                "id": root_wallet,
                "label": f"Root ({root_wallet[:6]}...{root_wallet[-4:]})",
                "category": "SUSPECT_WALLET",
                "risk_score": 92.0,
                "hop": 0
            }

            for tx in txs:
                from_k = tx.from_address.lower()
                to_k = tx.to_address.lower()

                if from_k not in nodes_dict:
                    cat_from = known_entity_service.categorize_address(from_k)
                    nodes_dict[from_k] = {
                        "id": from_k,
                        "label": cat_from["label"],
                        "category": cat_from["category"],
                        "risk_score": cat_from["risk_score"],
                        "hop": 1
                    }

                if to_k not in nodes_dict:
                    cat_to = known_entity_service.categorize_address(to_k)
                    nodes_dict[to_k] = {
                        "id": to_k,
                        "label": cat_to["label"],
                        "category": cat_to["category"],
                        "risk_score": cat_to["risk_score"],
                        "hop": tx.hop_level or 2
                    }

                edges.append({
                    "source": from_k,
                    "target": to_k,
                    "value": tx.value,
                    "token_symbol": tx.token_symbol,
                    "tx_hash": tx.tx_hash,
                    "timestamp": tx.timestamp.isoformat() if tx.timestamp else None,
                    "risk_flag": tx.risk_flag
                })

            # 3. Execute Graph Algorithms (BFS & Dijkstra)
            nx_graph = build_networkx_graph(list(nodes_dict.values()), edges)
            known_vasps = known_entity_service.get_known_vasp_addresses()
            
            bfs_result = bfs_nearest_vasp(nx_graph, root_wallet, known_vasps, max_hops=max_hops)
            
            if bfs_result["found"]:
                vasp_addr = bfs_result["vasp_address"]
                vasp_details = known_entity_service.identify_vasp(vasp_addr) or {}
                vasp_name = vasp_details.get("vasp_name", "Identified VASP Cluster")

                from backend.services.ml_scoring import ml_confidence_engine

                # Calculate volume metrics
                initial_vol = sum(e["value"] for e in edges if e["source"] == root_wallet) or 1.0
                inflow_vol = sum(e["value"] for e in edges if e["target"] == vasp_addr) or 0.1
                mixer_count = sum(1 for e in edges if "mixer" in str(e.get("risk_flag", "")).lower())
                peel_depth = max(0, bfs_result["hop_distance"] - 1)

                ml_res = ml_confidence_engine.calculate_confidence(
                    hop_count=bfs_result["hop_distance"],
                    initial_volume=initial_vol,
                    arriving_volume=inflow_vol,
                    time_delta_hours=24.0,
                    mixer_hops=mixer_count,
                    peel_layer_depth=peel_depth,
                    is_known_cluster=bool(vasp_details)
                )

                conf_score = ml_res["confidence_score"]
                tier = ml_res["confidence_tier"]
                evidence_factors = ml_res["evidence_breakdown"]

                # Create or update attribution record
                attrib = VASPAttribution(
                    trace_id=trace.id,
                    target_vasp_name=vasp_name,
                    vasp_deposit_address=vasp_addr,
                    hop_distance=bfs_result["hop_distance"],
                    total_volume=round(inflow_vol, 4),
                    token_symbol="ETH",
                    confidence_score=conf_score,
                    confidence_tier=tier,
                    evidence_breakdown_json=json.dumps(evidence_factors)
                )
                db.add(attrib)

            graph_payload = {
                "nodes": list(nodes_dict.values()),
                "edges": edges
            }

            trace.graph_json = json.dumps(graph_payload)
            trace.total_nodes = len(nodes_dict)
            trace.total_edges = len(edges)
            trace.status = "COMPLETED"
            trace.completed_at = datetime.now(timezone.utc)
            await db.commit()
            logger.info(f"[TraceWorker] Trace {trace_id} completed successfully with {len(nodes_dict)} nodes and {len(edges)} edges.")

        except Exception as e:
            logger.error(f"[TraceWorker] Failed to process trace {trace_id}: {e}", exc_info=True)
            trace.status = "FAILED"
            await db.commit()

async def start_trace_worker():
    """Subscribe trace worker to kafka/in-memory event queue."""
    event_bus.subscribe(settings.KAFKA_TRACE_TOPIC, process_trace_event)
    logger.info("[TraceWorker] Subscribed to trace dispatch events.")
