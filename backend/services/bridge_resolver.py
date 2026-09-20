import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("tracelink.bridge")

KNOWN_BRIDGE_CONTRACTS = {
    "0x98f3c9e6e3face36baad05fe09d375eff1764732": {
        "protocol": "Wormhole Portal",
        "source_chain": "ethereum",
        "supported_destinations": ["solana", "polygon", "bsc", "avalanche"]
    },
    "0xaf5191b0de27e10945d34f1949dd11565560cb6": {
        "protocol": "Stargate Finance Router",
        "source_chain": "ethereum",
        "supported_destinations": ["arbitrum", "optimism", "polygon", "bsc"]
    },
    "0xba8a621b4a54e61c442f5ec623637840cd10d8a2": {
        "protocol": "Multichain / Anyswap Router",
        "source_chain": "ethereum",
        "supported_destinations": ["fantom", "bsc", "polygon", "avalanche"]
    },
    "0xa0c68c638235ee32657e8f720a23cec1bfc77c77": {
        "protocol": "Polygon PoS Bridge",
        "source_chain": "ethereum",
        "supported_destinations": ["polygon"]
    },
    "0x40ec5b33f54e08337052b7eee041280ed5dcbe63": {
        "protocol": "Polygon ERC20 Deposit Bridge",
        "source_chain": "ethereum",
        "supported_destinations": ["polygon"]
    },
    "0x49048044d57e1c92a77f79988d21fa8faf74e97e": {
        "protocol": "Base Portal Bridge",
        "source_chain": "ethereum",
        "supported_destinations": ["base"]
    }
}

class CrossChainBridgeResolver:
    """
    Forensic resolver for identifying cross-chain bridge hops, chain hopping laundering,
    and correlating origin lock/burn transactions with destination mint/release transactions.
    """
    @staticmethod
    def identify_bridge_contract(address: str) -> Optional[dict]:
        if not address:
            return None
        return KNOWN_BRIDGE_CONTRACTS.get(address.lower())

    @staticmethod
    def is_bridge_transaction(tx_dict: dict) -> bool:
        to_addr = (tx_dict.get("to_address") or "").lower()
        from_addr = (tx_dict.get("from_address") or "").lower()
        return (to_addr in KNOWN_BRIDGE_CONTRACTS) or (from_addr in KNOWN_BRIDGE_CONTRACTS)

    @staticmethod
    def correlate_bridge_hops(
        source_txs: List[dict],
        destination_txs: List[dict],
        time_window_minutes: int = 120,
        value_tolerance_pct: float = 2.0
    ) -> List[dict]:
        """
        Correlates suspected cross-chain exit/entry pairs based on:
        1. Value preservation within value_tolerance_pct
        2. Timestamp ordering (destination tx occurred between 0 and time_window_minutes after source tx)
        """
        correlated = []
        for s_tx in source_txs:
            s_val = float(s_tx.get("value", 0.0))
            s_time = s_tx.get("timestamp")
            if isinstance(s_time, str):
                try:
                    s_dt = datetime.fromisoformat(s_time.replace("Z", "+00:00"))
                except Exception:
                    s_dt = None
            else:
                s_dt = s_time

            if not s_dt or s_val <= 0:
                continue

            for d_tx in destination_txs:
                d_val = float(d_tx.get("value", 0.0))
                d_time = d_tx.get("timestamp")
                if isinstance(d_time, str):
                    try:
                        d_dt = datetime.fromisoformat(d_time.replace("Z", "+00:00"))
                    except Exception:
                        d_dt = None
                else:
                    d_dt = d_time

                if not d_dt:
                    continue

                # Check timestamp ordering
                delta_mins = (d_dt - s_dt).total_seconds() / 60.0
                if 0 <= delta_mins <= time_window_minutes:
                    # Check value preservation
                    val_diff_pct = abs(s_val - d_val) / s_val * 100.0
                    if val_diff_pct <= value_tolerance_pct:
                        correlated.append({
                            "source_tx_hash": s_tx.get("tx_hash"),
                            "source_chain": s_tx.get("chain", "ethereum"),
                            "source_address": s_tx.get("from_address"),
                            "source_amount": s_val,
                            "dest_tx_hash": d_tx.get("tx_hash"),
                            "dest_chain": d_tx.get("chain", "destination"),
                            "dest_address": d_tx.get("to_address"),
                            "dest_amount": d_val,
                            "latency_minutes": round(delta_mins, 1),
                            "value_retained_pct": round(100.0 - val_diff_pct, 2)
                        })
        return correlated

bridge_resolver = CrossChainBridgeResolver()
