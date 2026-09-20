import os
import csv
import logging
from typing import Dict, Optional, List
from backend.core.config import settings

logger = logging.getLogger("tracelink.sanctions")

class SanctionsService:
    """
    Offline-first Sanctions & Blacklist Cross-Checking Engine.
    Loads OFAC SDN, Chainabuse, and national intelligence snapshots into memory for zero-latency lookup.
    """
    def __init__(self, snapshot_path: Optional[str] = None):
        self.snapshot_path = snapshot_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "infra", "fixtures", "ofac_sdn_snapshot.csv"
        )
        # address_lower -> dict of metadata
        self._sanctions_index: Dict[str, dict] = {}
        self._load_snapshot()

    def _load_snapshot(self):
        if not os.path.exists(self.snapshot_path):
            logger.warning(f"Sanctions snapshot file not found at {self.snapshot_path}. Initializing empty.")
            return

        try:
            with open(self.snapshot_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    addr = row.get("wallet_address", "").strip().lower()
                    if addr:
                        self._sanctions_index[addr] = {
                            "wallet_address": addr,
                            "list_source": row.get("list_source", "OFAC_SDN"),
                            "entity_name": row.get("entity_name", "Sanctioned Entity"),
                            "program": row.get("program", "CYBER"),
                            "remarks": row.get("remarks", "")
                        }
            logger.info(f"Loaded {len(self._sanctions_index)} sanctioned addresses into forensic cache.")
        except Exception as e:
            logger.error(f"Failed to load sanctions snapshot: {e}")

    def check_address(self, address: str) -> Optional[dict]:
        """Check if a wallet address matches OFAC SDN or blacklist registries."""
        if not address:
            return None
        return self._sanctions_index.get(address.strip().lower())

    def check_addresses_batch(self, addresses: List[str]) -> List[dict]:
        """Check a batch of addresses and return all matches."""
        matches = []
        for addr in addresses:
            match = self.check_address(addr)
            if match:
                matches.append(match)
        return matches

    def add_manual_designation(self, address: str, entity_name: str, list_source: str = "LEA_INTERNAL", program: str = "CYBER_CRIME", remarks: str = ""):
        """Add an ad-hoc local intelligence designation."""
        addr = address.strip().lower()
        self._sanctions_index[addr] = {
            "wallet_address": addr,
            "list_source": list_source,
            "entity_name": entity_name,
            "program": program,
            "remarks": remarks
        }

    def total_indexed(self) -> int:
        return len(self._sanctions_index)

sanctions_service = SanctionsService()
