import logging
from typing import Dict, List, Any, Optional

from backend.core.config import settings

logger = logging.getLogger(__name__)

class Neo4jGraphService:
    """
    Neo4j Graph Database Service for long-term multi-case linkage and community detection.
    Provides graceful offline fallback when Neo4j is not running in the environment.
    """
    def __init__(self):
        self.driver = None
        self.is_connected = False
        self._local_edges = []
        self._local_nodes = {}

    def connect(self):
        """Attempt connection to Neo4j bolt driver."""
        if settings.OFFLINE_MODE:
            logger.info("Neo4j: Operating with in-memory graph repository (offline lab mode).")
            return

        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                connection_timeout=2.0
            )
            with self.driver.session() as session:
                session.run("RETURN 1")
            self.is_connected = True
            logger.info("Connected to Neo4j graph cluster successfully.")
        except Exception as e:
            self.is_connected = False
            logger.info(f"Neo4j unreachable ({e}). Using local in-memory graph fallback.")

    def close(self):
        if self.driver and self.is_connected:
            self.driver.close()

    def save_wallet_node(self, address: str, category: str, risk_score: float, case_id: Optional[str] = None):
        """Upsert a Wallet node into Neo4j graph."""
        clean_addr = address.lower()
        self._local_nodes[clean_addr] = {
            "address": clean_addr,
            "category": category,
            "risk_score": risk_score,
            "case_id": case_id
        }

        if not self.is_connected or not self.driver:
            return

        query = """
        MERGE (w:Wallet {address: $address})
        SET w.category = $category,
            w.risk_score = $risk_score,
            w.last_updated = timestamp()
        WITH w
        WHERE $case_id IS NOT NULL
        MERGE (c:Case {id: $case_id})
        MERGE (w)-[:ASSOCIATED_WITH]->(c)
        """
        try:
            with self.driver.session() as session:
                session.run(query, address=clean_addr, category=category, risk_score=risk_score, case_id=case_id)
        except Exception as e:
            logger.warning(f"Neo4j save_wallet_node failed: {e}")

    def save_transaction_edge(
        self,
        from_address: str,
        to_address: str,
        value: float,
        tx_hash: str,
        token_symbol: str = "ETH",
        risk_flag: str = "NORMAL",
        case_id: Optional[str] = None
    ):
        """Create a DIRECTED transaction relationship between wallets in Neo4j."""
        from_clean = from_address.lower()
        to_clean = to_address.lower()
        edge = {
            "from": from_clean,
            "to": to_clean,
            "value": value,
            "tx_hash": tx_hash,
            "token": token_symbol,
            "risk_flag": risk_flag,
            "case_id": case_id
        }
        self._local_edges.append(edge)

        if not self.is_connected or not self.driver:
            return

        query = """
        MERGE (src:Wallet {address: $from_address})
        MERGE (dst:Wallet {address: $to_address})
        MERGE (src)-[r:TRANSFERRED {tx_hash: $tx_hash}]->(dst)
        SET r.value = $value,
            r.token = $token,
            r.risk_flag = $risk_flag,
            r.case_id = $case_id,
            r.timestamp = timestamp()
        """
        try:
            with self.driver.session() as session:
                session.run(
                    query,
                    from_address=from_clean,
                    to_address=to_clean,
                    tx_hash=tx_hash,
                    value=value,
                    token=token_symbol,
                    risk_flag=risk_flag,
                    case_id=case_id
                )
        except Exception as e:
            logger.warning(f"Neo4j save_transaction_edge failed: {e}")

    def find_cross_case_wallets(self) -> List[Dict[str, Any]]:
        """Identify wallets shared across multiple independent cases / FIRs."""
        if self.is_connected and self.driver:
            query = """
            MATCH (w:Wallet)-[:ASSOCIATED_WITH]->(c:Case)
            WITH w, count(DISTINCT c) AS case_count, collect(c.id) AS case_ids
            WHERE case_count > 1
            RETURN w.address AS address, w.category AS category, case_count, case_ids
            """
            try:
                with self.driver.session() as session:
                    res = session.run(query)
                    return [record.data() for record in res]
            except Exception as e:
                logger.warning(f"Neo4j cross-case query failed: {e}")

        # Local fallback
        address_cases = {}
        for edge in self._local_edges:
            cid = edge.get("case_id")
            if cid:
                for addr in [edge["from"], edge["to"]]:
                    if addr not in address_cases:
                        address_cases[addr] = set()
                    address_cases[addr].add(cid)

        return [
            {"address": addr, "case_count": len(cases), "case_ids": list(cases)}
            for addr, cases in address_cases.items()
            if len(cases) > 1
        ]

neo4j_service = Neo4jGraphService()
