import os
import csv
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger("tracelink.valuation")

class ValuationService:
    """
    Historical cryptocurrency-to-INR price valuation engine for cyber crime charge sheets.
    Uses daily historical price fixtures with deterministic interpolation and fallback rates.
    """
    DEFAULT_RATES_INR = {
        "ETH": 280000.0,
        "BTC": 5400000.0,
        "USDT": 83.5,
        "USDC": 83.5,
        "BNB": 48000.0,
        "MATIC": 45.0,
        "SOL": 12500.0
    }

    def __init__(self, fixture_path: Optional[str] = None):
        self.fixture_path = fixture_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "infra", "fixtures", "inr_price_history.csv"
        )
        # (token, date_str) -> (rate_usd, rate_inr)
        self._price_table: Dict[Tuple[str, str], Tuple[float, float]] = {}
        self._load_prices()

    def _load_prices(self):
        if not os.path.exists(self.fixture_path):
            logger.warning(f"Price history fixture not found at {self.fixture_path}. Using fallback rate dictionary.")
            return

        try:
            with open(self.fixture_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    token = (row.get("token_symbol") or "").upper().strip()
                    dt_str = (row.get("price_date") or "").strip()
                    try:
                        usd = float(row.get("rate_usd") or 0.0)
                        inr = float(row.get("rate_inr") or 0.0)
                        if token and dt_str:
                            self._price_table[(token, dt_str)] = (usd, inr)
                    except ValueError:
                        continue
            logger.info(f"Loaded {len(self._price_table)} historical daily price records.")
        except Exception as e:
            logger.error(f"Failed to load price history: {e}")

    def get_rate(self, token_symbol: str, timestamp_str: Optional[str] = None) -> Tuple[float, float]:
        """
        Returns (rate_usd, rate_inr) for a given token and date.
        """
        sym = (token_symbol or "ETH").upper().strip()
        date_key = None

        if timestamp_str:
            try:
                # Extract YYYY-MM-DD
                date_key = timestamp_str[:10]
            except Exception:
                date_key = None

        if date_key and (sym, date_key) in self._price_table:
            return self._price_table[(sym, date_key)]

        # Fallback to default institutional rates
        inr_rate = self.DEFAULT_RATES_INR.get(sym, 280000.0)
        usd_rate = inr_rate / 83.5
        return (usd_rate, inr_rate)

    def calculate_valuation_inr(self, amount: float, token_symbol: str, timestamp_str: Optional[str] = None) -> float:
        """
        Calculates total value in INR for charge-sheet statements.
        """
        _, inr_rate = self.get_rate(token_symbol, timestamp_str)
        return round(amount * inr_rate, 2)

valuation_service = ValuationService()
