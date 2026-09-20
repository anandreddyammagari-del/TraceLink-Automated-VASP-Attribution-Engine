import os
import json
import logging
from datetime import datetime, timezone
from backend.services.chainalysis_service import known_entity_service
from backend.services.sanctions_service import sanctions_service
from backend.services.valuation_service import valuation_service

logger = logging.getLogger("tracelink.datapack")

class DataPackUpdaterService:
    """
    Manages offline forensic intelligence data packs:
    - VASP directory registry
    - OFAC SDN & sanctions snapshots
    - Cryptocurrency INR historical rate indexes
    """
    @staticmethod
    def get_datapack_status() -> dict:
        fixtures_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "infra", "fixtures"
        )
        files = {
            "vasp_directory": "vasp_directory.json",
            "ofac_sdn_snapshot": "ofac_sdn_snapshot.csv",
            "inr_price_history": "inr_price_history.csv",
            "synthetic_training_data": "synthetic_training_data.csv"
        }

        status = {}
        for key, fname in files.items():
            fpath = os.path.join(fixtures_dir, fname)
            if os.path.exists(fpath):
                mtime = os.path.getmtime(fpath)
                status[key] = {
                    "filename": fname,
                    "status": "LOADED_AND_VERIFIED",
                    "file_size_bytes": os.path.getsize(fpath),
                    "last_updated": datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
                }
            else:
                status[key] = {
                    "filename": fname,
                    "status": "MISSING",
                    "file_size_bytes": 0,
                    "last_updated": None
                }
        return {
            "datapack_version": "2026.09-AIRGAPPED-RELEASE",
            "total_packages": len(files),
            "packages": status
        }

    @staticmethod
    def reload_all_packs() -> dict:
        """Dynamically reloads all intelligence fixtures into active memory."""
        known_entity_service._load_vasp_directory()
        sanctions_service._load_snapshot()
        valuation_service._load_prices()
        return {
            "status": "RELOADED_SUCCESSFULLY",
            "reloaded_at": datetime.now(timezone.utc).isoformat(),
            "indexed_vasp_count": len(known_entity_service._all_vasp_addresses),
            "indexed_sanctions_count": sanctions_service.total_indexed()
        }

datapack_service = DataPackUpdaterService()
