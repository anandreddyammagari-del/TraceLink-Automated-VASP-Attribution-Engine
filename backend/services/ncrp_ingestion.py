import os
import csv
import io
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone

logger = logging.getLogger("tracelink.ncrp")

class NCRPIngestionService:
    """
    Ingestion engine for National Cyber Crime Reporting Portal (NCRP) complaint datasets.
    Correlates victim complaints with forensic suspect destination wallets.
    """
    @staticmethod
    def parse_complaints(file_content: str) -> List[dict]:
        """
        Parses CSV export from NCRP portal.
        """
        reader = csv.DictReader(io.StringIO(file_content))
        complaints = []

        for row in reader:
            ref = row.get("complaint_ref") or row.get("complaint_id") or row.get("ack_no") or "NCRP/UNKNOWN"
            name = row.get("complainant_name") or row.get("victim_name") or "Anonymous Complainant"
            dest_wallet = (row.get("destination_wallet_reported") or row.get("wallet") or "").strip().lower()
            try:
                loss_inr = float(row.get("loss_amount_inr") or row.get("disputed_amount") or 0.0)
            except ValueError:
                loss_inr = 0.0

            complaints.append({
                "complaint_ref": ref,
                "complainant_name": name,
                "contact_phone": row.get("contact_phone", "CONFIDENTIAL"),
                "destination_wallet": dest_wallet,
                "loss_amount_inr": loss_inr,
                "fraud_modality": row.get("fraud_modality", "Cryptocurrency Investment Fraud"),
                "incident_date": row.get("incident_date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
            })

        return complaints

    @classmethod
    def load_fixture_complaints(cls, fixture_path: Optional[str] = None) -> List[dict]:
        path = fixture_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "infra", "fixtures", "sample_complaints.csv"
        )
        if not os.path.exists(path):
            return []
        with open(path, mode="r", encoding="utf-8") as f:
            return cls.parse_complaints(f.read())

ncrp_service = NCRPIngestionService()
