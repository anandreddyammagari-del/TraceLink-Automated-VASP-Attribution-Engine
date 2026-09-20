import os
import json
import logging
from typing import Dict, List, Set, Any, Optional

logger = logging.getLogger(__name__)

KNOWN_MIXERS: Dict[str, Dict[str, str]] = {
    "0x7f367cc41522ce07553e823bf3be79a889debe1b": {"name": "Tornado.Cash: Router", "category": "MIXER", "risk": "CRITICAL"},
    "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b": {"name": "Tornado.Cash: 0.1 ETH", "category": "MIXER", "risk": "CRITICAL"},
    "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936": {"name": "Tornado.Cash: 1 ETH", "category": "MIXER", "risk": "CRITICAL"},
    "0x910cbd523d972eb0a6f4cae4618ad62622b39dbf": {"name": "Tornado.Cash: 10 ETH", "category": "MIXER", "risk": "CRITICAL"},
    "0xa160cdab225685da1d56aa342ad8841c3b53f291": {"name": "Tornado.Cash: 100 ETH", "category": "MIXER", "risk": "CRITICAL"},
    "0xfa7093cdd9ee6932b4eb2c9e1cde7ce00b1fa4b9": {"name": "Railgun: Privacy Relayer", "category": "MIXER", "risk": "HIGH"}
}

KNOWN_BRIDGES: Dict[str, Dict[str, str]] = {
    "0x98f3c9e6e3face36baad05fe09d375ef14642f88": {"name": "Wormhole: Core Bridge", "category": "BRIDGE"},
    "0x3ee18b2214aff97000d974cf647e7c347e8fa585": {"name": "Wormhole: Token Bridge", "category": "BRIDGE"},
    "0x8731d54e9d02c286767d56ac03e8037c07e01e98": {"name": "Stargate: Bridge Router", "category": "BRIDGE"},
    "0xba8da9dc3aee9d9fb77aea2374174689fe62ff91": {"name": "Multichain: Router v4", "category": "BRIDGE"}
}

class KnownEntityService:
    def __init__(self):
        self._vasp_address_map: Dict[str, Dict[str, Any]] = {}
        self._all_vasp_addresses: Set[str] = set()
        self._load_vasp_directory()

    def _load_vasp_directory(self):
        fixture_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "infra", "fixtures", "vasp_directory.json"
        )
        if os.path.exists(fixture_path):
            try:
                with open(fixture_path, "r", encoding="utf-8") as f:
                    directory = json.load(f)
                    for entry in directory:
                        vasp_info = {
                            "vasp_name": entry.get("vasp_name"),
                            "country": entry.get("country"),
                            "fiu_registered": entry.get("fiu_registered", False),
                            "nodal_officer_email": entry.get("nodal_officer_email"),
                            "compliance_portal": entry.get("compliance_portal")
                        }
                        for addr in entry.get("deposit_clusters", []):
                            clean_addr = addr.strip().lower()
                            self._vasp_address_map[clean_addr] = vasp_info
                            self._all_vasp_addresses.add(clean_addr)
                logger.info(f"Loaded {len(self._all_vasp_addresses)} known VASP deposit addresses into memory.")
            except Exception as e:
                logger.error(f"Failed to load VASP directory fixture: {e}")
        else:
            # Hardcoded fallback
            wazirx = "0x503828976d22510aad0201ac7ec88293211d23dc"
            binance = "0x28c6c06298d514db089934071355e5743bf21d60"
            self._vasp_address_map[wazirx] = {"vasp_name": "WazirX (Zanmai Labs Pvt Ltd)", "country": "India", "fiu_registered": True}
            self._vasp_address_map[binance] = {"vasp_name": "Binance Holdings Ltd", "country": "International", "fiu_registered": True}
            self._all_vasp_addresses.update([wazirx, binance])

    def identify_vasp(self, address: str) -> Optional[Dict[str, Any]]:
        """Identify if an address belongs to a known regulated VASP deposit cluster."""
        return self._vasp_address_map.get(address.strip().lower())

    def is_mixer(self, address: str) -> bool:
        """Check if an address is a sanctioned privacy mixer or relayer."""
        return address.strip().lower() in KNOWN_MIXERS

    def is_bridge(self, address: str) -> bool:
        """Check if an address is a multi-chain bridge contract."""
        return address.strip().lower() in KNOWN_BRIDGES

    def get_known_vasp_addresses(self) -> Set[str]:
        return self._all_vasp_addresses

    def categorize_address(self, address: str, default_category: str = "INTERMEDIARY") -> Dict[str, Any]:
        """Categorize an address and assign risk and entity label."""
        clean = address.strip().lower()
        if clean in self._vasp_address_map:
            v = self._vasp_address_map[clean]
            return {
                "category": "VASP",
                "label": f"{v['vasp_name']} Deposit",
                "risk_score": 10.0,
                "vasp_details": v
            }
        if clean in KNOWN_MIXERS:
            m = KNOWN_MIXERS[clean]
            return {
                "category": "MIXER",
                "label": m["name"],
                "risk_score": 98.0,
                "mixer_details": m
            }
        if clean in KNOWN_BRIDGES:
            b = KNOWN_BRIDGES[clean]
            return {
                "category": "BRIDGE",
                "label": b["name"],
                "risk_score": 40.0,
                "bridge_details": b
            }
        return {
            "category": default_category,
            "label": f"Addr {clean[:6]}...{clean[-4:]}",
            "risk_score": 50.0
        }

known_entity_service = KnownEntityService()
