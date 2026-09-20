import json
import hmac
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Tuple
from backend.core.config import settings

class CaseExportService:
    """
    Air-gapped Case Bundle Export and Import Service.
    Packages complete case intelligence with HMAC-SHA256 cryptographic signatures
    for secure transit between State Cyber Police Cells.
    """
    @staticmethod
    def _compute_bundle_signature(payload_str: str, secret_key: str) -> str:
        return hmac.new(
            secret_key.encode("utf-8"),
            payload_str.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    @classmethod
    def export_case_bundle(
        cls,
        case_data: dict,
        suspects: list[dict],
        transactions: list[dict],
        attributions: list[dict],
        audit_trail: list[dict],
        exporting_officer: dict
    ) -> dict:
        now_str = datetime.now(timezone.utc).isoformat()
        bundle_content = {
            "format_version": "TRACELINK-CASE-BUNDLE-V1",
            "exported_at": now_str,
            "exporting_station": settings.WORKSTATION_ID,
            "exporting_officer_badge": exporting_officer.get("badge_number", "OFFICER-LE"),
            "case": case_data,
            "suspects": suspects,
            "transactions": transactions,
            "attributions": attributions,
            "audit_trail": audit_trail
        }

        # Deterministic JSON serialization for canonical hashing
        serialized = json.dumps(bundle_content, sort_keys=True)
        sig = cls._compute_bundle_signature(serialized, settings.SECRET_KEY)
        payload_sha256 = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

        return {
            "archive_metadata": {
                "format": "TRACELINK-ENCRYPTED-ARCHIVE",
                "sha256_checksum": payload_sha256,
                "hmac_sha256_signature": sig,
                "signature_algorithm": "HMAC-SHA256",
                "timestamp": now_str
            },
            "bundle_payload": bundle_content
        }

    @classmethod
    def verify_and_import_bundle(
        cls,
        bundle_dict: dict,
        secret_key: str = None
    ) -> Tuple[bool, str, dict]:
        key = secret_key or settings.SECRET_KEY
        metadata = bundle_dict.get("archive_metadata", {})
        payload = bundle_dict.get("bundle_payload", {})

        claimed_sig = metadata.get("hmac_sha256_signature")
        if not claimed_sig:
            return False, "Missing cryptographic HMAC signature in archive.", {}

        serialized = json.dumps(payload, sort_keys=True)
        expected_sig = cls._compute_bundle_signature(serialized, key)

        if not hmac.compare_digest(claimed_sig, expected_sig):
            return False, "SECURITY ALERT: Bundle signature mismatch! Archive has been tampered with.", {}

        # Verify SHA-256
        claimed_sha = metadata.get("sha256_checksum")
        actual_sha = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        if claimed_sha and claimed_sha != actual_sha:
            return False, "Payload checksum mismatch.", {}

        return True, "Archive verified authentic and untampered.", payload

case_export_service = CaseExportService()
