import io
import csv
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.transaction import Transaction
from backend.models.wallet import Wallet
from backend.models.suspect import Suspect
from backend.models.audit import AuditLog, format_audit_timestamp

logger = logging.getLogger(__name__)

COLUMN_ALIASES = {
    "tx_hash": ["tx_hash", "txhash", "hash", "transaction_hash", "txn_hash", "id"],
    "person_id": ["person_id", "suspect_id", "suspect", "person", "accused_id"],
    "from_address": ["from_address", "from", "sender", "src_address", "source_address", "src"],
    "to_address": ["to_address", "to", "receiver", "recipient", "dst_address", "destination_address", "dst"],
    "value": ["value", "amount", "crypto_amount", "volume", "val"],
    "timestamp": ["timestamp", "date", "time", "datetime", "block_time", "block_timestamp", "created_at"],
    "token_symbol": ["token_symbol", "token", "symbol", "currency", "asset"],
    "chain": ["chain", "network", "blockchain"],
    "risk_flag": ["risk_flag", "risk", "flag", "tag", "pattern"],
    "attributed_entity": ["attributed_entity", "entity", "label", "vasp", "counterparty"]
}

def normalize_column_name(raw_name: str) -> Optional[str]:
    clean = raw_name.strip().lower().replace(" ", "_").replace("-", "_")
    for canonical, aliases in COLUMN_ALIASES.items():
        if clean == canonical or clean in aliases:
            return canonical
    return None

def parse_timestamp(raw_val: Any) -> datetime:
    """Parse various datetime representations into UTC datetime."""
    if isinstance(raw_val, datetime):
        return raw_val if raw_val.tzinfo else raw_val.replace(tzinfo=timezone.utc)
    
    if isinstance(raw_val, (int, float)):
        # Epoch timestamp
        if raw_val > 1e11:  # Milliseconds
            return datetime.fromtimestamp(raw_val / 1000.0, tz=timezone.utc)
        return datetime.fromtimestamp(raw_val, tz=timezone.utc)

    val_str = str(raw_val).strip()
    if not val_str:
        return datetime.now(timezone.utc)

    # Try numeric string
    try:
        num = float(val_str)
        if num > 1e11:
            return datetime.fromtimestamp(num / 1000.0, tz=timezone.utc)
        return datetime.fromtimestamp(num, tz=timezone.utc)
    except ValueError:
        pass

    # Standard formats
    formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d-%m-%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%d-%B-%Y"
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(val_str, fmt)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    # Fallback to current time if unparseable
    return datetime.now(timezone.utc)

class DatasetIngestionService:
    @staticmethod
    async def ingest_csv_content(
        content: str,
        case_id: Optional[str] = None,
        officer_badge: str = "SYSTEM_INGEST",
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Parse and ingest CSV transaction data."""
        f = io.StringIO(content.strip())
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            return {"error": "Empty CSV file content."}

        header_map = {}
        for idx, h in enumerate(headers):
            canonical = normalize_column_name(h)
            if canonical:
                header_map[idx] = canonical

        rows = []
        for line_num, row in enumerate(reader, start=2):
            if not row or all(c.strip() == "" for c in row):
                continue
            item = {}
            for idx, col in enumerate(row):
                if idx in header_map:
                    item[header_map[idx]] = col.strip()
            rows.append((line_num, item))

        return await DatasetIngestionService._process_parsed_records(rows, case_id, officer_badge, db)

    @staticmethod
    async def ingest_json_content(
        content: str,
        case_id: Optional[str] = None,
        officer_badge: str = "SYSTEM_INGEST",
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Parse and ingest JSON transaction data (array of objects)."""
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON syntax: {str(e)}"}

        if isinstance(data, dict) and "transactions" in data:
            data = data["transactions"]
        elif isinstance(data, dict) and "items" in data:
            data = data["items"]

        if not isinstance(data, list):
            return {"error": "Expected a JSON list of transaction records."}

        rows = []
        for idx, raw_item in enumerate(data, start=1):
            if not isinstance(raw_item, dict):
                continue
            normalized_item = {}
            for k, v in raw_item.items():
                canonical = normalize_column_name(k)
                if canonical:
                    normalized_item[canonical] = v
                else:
                    normalized_item[k.lower()] = v
            rows.append((idx, normalized_item))

        return await DatasetIngestionService._process_parsed_records(rows, case_id, officer_badge, db)

    @staticmethod
    async def _process_parsed_records(
        records: List[Tuple[int, Dict[str, Any]]],
        case_id: Optional[str],
        officer_badge: str,
        db: Optional[AsyncSession]
    ) -> Dict[str, Any]:
        """Validate, deduplicate, and persist transaction records into database."""
        inserted = 0
        skipped_duplicates = 0
        errors = []
        parsed_models = []

        for line_num, item in records:
            tx_hash = item.get("tx_hash")
            from_addr = item.get("from_address")
            to_addr = item.get("to_address")
            val_raw = item.get("value")

            if not tx_hash or not from_addr or not to_addr:
                errors.append(f"Row {line_num}: Missing required fields (tx_hash, from_address, or to_address).")
                continue

            try:
                val = float(str(val_raw).replace(",", "")) if val_raw is not None else 0.0
            except (ValueError, TypeError):
                errors.append(f"Row {line_num}: Invalid numeric value '{val_raw}'.")
                continue

            dt = parse_timestamp(item.get("timestamp"))

            parsed_models.append({
                "tx_hash": str(tx_hash).strip().lower(),
                "case_id": case_id,
                "person_id": item.get("person_id") or "USER_UPLOADED",
                "from_address": str(from_addr).strip().lower(),
                "to_address": str(to_addr).strip().lower(),
                "value": val,
                "token_symbol": item.get("token_symbol", "ETH").upper(),
                "value_inr": float(item.get("value_inr", 0.0) or 0.0),
                "timestamp": dt,
                "chain": item.get("chain", "ethereum").lower(),
                "risk_flag": item.get("risk_flag", "USER_INGESTED"),
                "attributed_entity": item.get("attributed_entity") or ("VASP Target" if "VASP" in str(item.get("risk_flag", "")) else "Intermediary Counterparty"),
                "hop_level": int(item.get("hop_level", 0))
            })

        if db and parsed_models:
            for m in parsed_models:
                # Check for existing tx_hash
                existing = await db.execute(select(Transaction).where(Transaction.tx_hash == m["tx_hash"]))
                if existing.scalars().first():
                    skipped_duplicates += 1
                    continue

                tx_obj = Transaction(
                    tx_hash=m["tx_hash"],
                    case_id=m["case_id"],
                    person_id=m["person_id"],
                    from_address=m["from_address"],
                    to_address=m["to_address"],
                    value=m["value"],
                    token_symbol=m["token_symbol"],
                    value_inr=m["value_inr"],
                    timestamp=m["timestamp"],
                    chain=m["chain"],
                    risk_flag=m["risk_flag"],
                    attributed_entity=m["attributed_entity"],
                    hop_level=m["hop_level"]
                )
                db.add(tx_obj)
                inserted += 1

            await db.commit()

            # Chained audit log entry for this dataset ingestion
            if inserted > 0:
                now = datetime.now(timezone.utc)
                last_audit = (await db.execute(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(1))).scalars().first()
                prev_hash = last_audit.current_hash if last_audit else "0" * 64
                details = f"Dataset ingestion: {inserted} transactions added, {skipped_duplicates} duplicates skipped for Case: {case_id or 'GLOBAL'}"
                audit_hash = AuditLog.compute_hash(
                    prev_hash=prev_hash,
                    event_type="DATASET_INGESTION",
                    officer_id=officer_badge,
                    case_id=case_id or "GLOBAL",
                    details=details,
                    timestamp_str=format_audit_timestamp(now)
                )
                db.add(AuditLog(
                    event_type="DATASET_INGESTION",
                    officer_id=officer_badge,
                    case_id=case_id or "GLOBAL",
                    details=details,
                    prev_hash=prev_hash,
                    current_hash=audit_hash,
                    timestamp=now
                ))
                await db.commit()

        return {
            "total_rows_received": len(records),
            "inserted": inserted,
            "skipped_duplicates": skipped_duplicates,
            "errors": errors,
            "sample_records": parsed_models[:5]
        }
