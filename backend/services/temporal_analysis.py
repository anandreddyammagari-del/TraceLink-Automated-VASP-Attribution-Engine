import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional

logger = logging.getLogger("tracelink.temporal")

class TemporalAnalysisService:
    """
    Forensic engine for analyzing transaction time series, hop transfer latency,
    detecting rapid robotic bursts (<30s) and dormancy-then-drain patterns.
    """
    @staticmethod
    def parse_dt(ts) -> Optional[datetime]:
        if not ts:
            return None
        if isinstance(ts, datetime):
            return ts
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        if isinstance(ts, str):
            try:
                clean = ts.replace("Z", "+00:00")
                return datetime.fromisoformat(clean)
            except Exception:
                return None
        return None

    @classmethod
    def calculate_hop_latencies(cls, transactions: List[dict]) -> List[dict]:
        """
        Sorts transactions chronologically and calculates latency between consecutive hops.
        """
        parsed_txs = []
        for tx in transactions:
            dt = cls.parse_dt(tx.get("timestamp"))
            if dt:
                parsed_txs.append((dt, tx))

        parsed_txs.sort(key=lambda x: x[0])
        results = []
        prev_dt = None

        for idx, (dt, tx) in enumerate(parsed_txs):
            latency_sec = 0.0
            if prev_dt:
                latency_sec = max(0.0, (dt - prev_dt).total_seconds())

            is_burst = 0.0 < latency_sec < 30.0
            is_dormant_drain = latency_sec > (30 * 86400.0)  # > 30 days gap

            results.append({
                "index": idx,
                "tx_hash": tx.get("tx_hash"),
                "from_address": tx.get("from_address"),
                "to_address": tx.get("to_address"),
                "value": tx.get("value"),
                "token_symbol": tx.get("token_symbol", "ETH"),
                "timestamp": dt.isoformat(),
                "latency_seconds": round(latency_sec, 2),
                "latency_hours": round(latency_sec / 3600.0, 2),
                "is_burst_transfer": is_burst,
                "is_dormant_drain": is_dormant_drain
            })
            prev_dt = dt

        return results

    @classmethod
    def detect_velocity_anomalies(cls, transactions: List[dict]) -> dict:
        """
        Returns structured summary of temporal anomalies (burst count, max dormancy, velocity flag).
        """
        latencies = cls.calculate_hop_latencies(transactions)
        burst_count = sum(1 for item in latencies if item["is_burst_transfer"])
        dormant_drains = sum(1 for item in latencies if item["is_dormant_drain"])

        total_txs = len(latencies)
        velocity_profile = "STANDARD_MANUAL"
        if burst_count >= 2 or (total_txs > 2 and burst_count / total_txs > 0.4):
            velocity_profile = "AUTOMATED_BOT_SCRIPT"
        elif dormant_drains >= 1:
            velocity_profile = "DORMANT_COLD_DRAIN"

        return {
            "total_transactions_analyzed": total_txs,
            "burst_count_sub_30s": burst_count,
            "dormant_drain_count": dormant_drains,
            "velocity_profile": velocity_profile,
            "hops": latencies
        }

temporal_service = TemporalAnalysisService()
