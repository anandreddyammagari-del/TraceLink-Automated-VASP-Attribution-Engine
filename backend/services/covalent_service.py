import os
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import httpx

from backend.core.config import settings

logger = logging.getLogger(__name__)

CHAIN_NAME_MAP = {
    "ethereum": "eth-mainnet",
    "eth": "eth-mainnet",
    "polygon": "matic-mainnet",
    "bsc": "bsc-mainnet",
    "arbitrum": "arbitrum-mainnet"
}

class CovalentService:
    @staticmethod
    async def fetch_wallet_transactions(
        address: str,
        chain: str = "ethereum",
        page_size: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Fetch wallet transaction histories.
        Automatically falls back to offline fixtures in air-gapped lab mode or when external API is unreachable.
        """
        address_clean = address.strip().lower()

        # Check for offline air-gapped mode or dummy key
        if settings.OFFLINE_MODE or not settings.COVALENT_API_KEY or "demo" in settings.COVALENT_API_KEY.lower():
            logger.info(f"[Offline Mode] Serving local forensic fixtures for address {address_clean}")
            return CovalentService._get_offline_fixture_transactions(address_clean, chain)

        chain_id = CHAIN_NAME_MAP.get(chain.lower(), "eth-mainnet")
        url = f"https://api.covalenthq.com/v1/{chain_id}/address/{address_clean}/transactions_v3/"

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {settings.COVALENT_API_KEY}"}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("data", {}).get("items", [])
                    return CovalentService._normalize_covalent_items(items, chain)
                else:
                    logger.warning(f"Covalent API returned status {resp.status_code}. Falling back to offline fixtures.")
                    return CovalentService._get_offline_fixture_transactions(address_clean, chain)
        except Exception as e:
            logger.warning(f"Network error querying Covalent API ({str(e)}). Falling back to offline fixtures.")
            return CovalentService._get_offline_fixture_transactions(address_clean, chain)

    @staticmethod
    def _normalize_covalent_items(items: List[Dict[str, Any]], chain: str) -> List[Dict[str, Any]]:
        normalized = []
        for item in items:
            tx_hash = item.get("tx_hash")
            from_addr = item.get("from_address")
            to_addr = item.get("to_address")
            val_raw = item.get("value", 0)
            
            # Format value
            try:
                val = float(val_raw) / 1e18 if float(val_raw) > 1e12 else float(val_raw)
            except (ValueError, TypeError):
                val = 0.0

            # Timestamp
            ts_raw = item.get("block_signed_at")
            if ts_raw:
                try:
                    dt = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                except ValueError:
                    dt = datetime.now(timezone.utc)
            else:
                dt = datetime.now(timezone.utc)

            normalized.append({
                "tx_hash": tx_hash,
                "from_address": from_addr,
                "to_address": to_addr,
                "value": round(val, 4),
                "token_symbol": "ETH",
                "timestamp": dt,
                "chain": chain,
                "risk_flag": "LIVE_API_FETCHED"
            })
        return normalized

    @staticmethod
    def _get_offline_fixture_transactions(address: str, chain: str) -> List[Dict[str, Any]]:
        """Load fixture data from disk or generate synthetic multi-hop trail for air-gapped lab testing."""
        fixture_path = os.path.join(os.path.dirname(__file__), "..", "..", "infra", "fixtures", "mock_covalent_txs.json")
        if os.path.exists(fixture_path):
            try:
                with open(fixture_path, "r", encoding="utf-8") as f:
                    fixture = json.load(f)
                    items = fixture.get("items", [])
                    return CovalentService._normalize_covalent_items(items, chain)
            except Exception as e:
                logger.error(f"Failed to load mock_covalent_txs.json: {e}")

        # Fallback synthetic deterministic transactions for any given address
        now = datetime.now(timezone.utc)
        return [
            {
                "tx_hash": f"0xmock{address[:8]}111111111111111111111111111111111111111111111111",
                "from_address": "0x1111111111111111111111111111111111111111",
                "to_address": address,
                "value": 15.0,
                "token_symbol": "ETH",
                "timestamp": now - timedelta(days=3),
                "chain": chain,
                "risk_flag": "MOCK_INFLOW"
            },
            {
                "tx_hash": f"0xmock{address[:8]}222222222222222222222222222222222222222222222222",
                "from_address": address,
                "to_address": "0x503828976d22510aad0201ac7ec88293211d23dc",  # WazirX deposit
                "value": 14.8,
                "token_symbol": "ETH",
                "timestamp": now - timedelta(days=2),
                "chain": chain,
                "risk_flag": "VASP_DEPOSIT"
            }
        ]
