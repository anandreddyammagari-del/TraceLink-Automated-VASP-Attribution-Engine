import logging
from typing import List, Dict, Optional

logger = logging.getLogger("tracelink.peel")

class PeelChainDetector:
    """
    Forensic algorithm for identifying peel chain patterns:
    Repeated shaving of small amounts (peel outputs, typically 5-35%)
    while forwarding the larger portion to a fresh change intermediary.
    """
    @staticmethod
    def detect_peel_sequence(transactions: List[dict], min_peel_hops: int = 2) -> dict:
        """
        Analyzes transaction graph connections to identify sequential peel layers.
        """
        # Build adjacency map: from_addr -> list of outgoing txs
        outgoing: Dict[str, List[dict]] = {}
        for tx in transactions:
            f = (tx.get("from_address") or "").lower()
            if f:
                outgoing.setdefault(f, []).append(tx)

        peel_chains = []

        # Look for sequences where a node transfers to 2 addresses (peel + change)
        # or transfers sequentially where value is shaved progressively
        for start_addr, tx_list in outgoing.items():
            # Check if this could be a peel root
            current_addr = start_addr
            current_chain = []
            visited = set()

            while current_addr and current_addr not in visited:
                visited.add(current_addr)
                outs = outgoing.get(current_addr, [])
                if not outs:
                    break

                # Sort outgoing by value
                sorted_outs = sorted(outs, key=lambda x: float(x.get("value", 0.0)))

                if len(sorted_outs) == 2:
                    # Classic 2-output peel: smaller is peel, larger is change
                    small_peel = sorted_outs[0]
                    large_change = sorted_outs[1]
                    s_val = float(small_peel.get("value", 0.0))
                    l_val = float(large_change.get("value", 0.0))
                    total = s_val + l_val

                    if total > 0 and 0.02 <= (s_val / total) <= 0.45:
                        current_chain.append({
                            "peel_node": current_addr,
                            "peel_destination": small_peel.get("to_address"),
                            "peeled_amount": s_val,
                            "change_destination": large_change.get("to_address"),
                            "forwarded_amount": l_val,
                            "shave_percentage": round((s_val / total) * 100, 1),
                            "tx_hash": small_peel.get("tx_hash")
                        })
                        # Follow the change destination
                        current_addr = (large_change.get("to_address") or "").lower()
                        continue
                elif len(sorted_outs) == 1:
                    # Single forward with value reduction
                    tx = sorted_outs[0]
                    current_addr = (tx.get("to_address") or "").lower()
                else:
                    break

            if len(current_chain) >= min_peel_hops:
                total_peeled = sum(p["peeled_amount"] for p in current_chain)
                peel_chains.append({
                    "root_address": start_addr,
                    "depth": len(current_chain),
                    "total_peeled_amount": round(total_peeled, 4),
                    "layers": current_chain
                })

        return {
            "peel_chains_detected": len(peel_chains),
            "chains": peel_chains
        }

peel_chain_detector = PeelChainDetector()
