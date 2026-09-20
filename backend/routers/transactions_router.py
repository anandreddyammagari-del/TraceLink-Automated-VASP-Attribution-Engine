import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, desc
from sqlalchemy.orm import selectinload

from backend.core.database import get_db
from backend.core.security import get_current_officer
from backend.models.transaction import Transaction
from backend.models.suspect import Suspect
from backend.models.case import Case
from backend.schemas.transaction_schema import TransactionResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/transactions", tags=["Master Transaction Ledger"])

@router.get("", response_model=dict)
async def get_master_transaction_stream(
    person_id: Optional[str] = Query(None, description="Filter by Suspect Person ID"),
    wallet_address: Optional[str] = Query(None, description="Filter by Source or Destination Wallet"),
    tx_hash: Optional[str] = Query(None, description="Filter by Transaction Hash"),
    case_id: Optional[str] = Query(None, description="Filter by Case FIR ID"),
    risk_flag: Optional[str] = Query(None, description="Filter by Risk Flag"),
    search: Optional[str] = Query(None, description="Unified search across Person ID, Wallet, and Tx Hash"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    officer: dict = Depends(get_current_officer)
):
    """
    Retrieve aggregated multi-entity transaction stream across all suspects, cases, and tracked wallets.
    Supports real-time search across Person ID, Wallet Address, and Tx Hash.
    """
    query = select(Transaction).order_by(desc(Transaction.timestamp))

    # Unified search filter
    if search:
        s = f"%{search.strip()}%"
        query = query.where(
            or_(
                Transaction.person_id.ilike(s),
                Transaction.from_address.ilike(s),
                Transaction.to_address.ilike(s),
                Transaction.tx_hash.ilike(s),
                Transaction.attributed_entity.ilike(s)
            )
        )

    # Specific filters
    if person_id:
        query = query.where(Transaction.person_id.ilike(f"%{person_id.strip()}%"))
    if wallet_address:
        w = wallet_address.strip().lower()
        query = query.where(
            or_(
                func.lower(Transaction.from_address) == w,
                func.lower(Transaction.to_address) == w
            )
        )
    if tx_hash:
        query = query.where(func.lower(Transaction.tx_hash) == tx_hash.strip().lower())
    if case_id:
        query = query.where(Transaction.case_id == case_id)
    if risk_flag:
        query = query.where(Transaction.risk_flag == risk_flag)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_count = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.limit(limit).offset(offset)
    res = await db.execute(query)
    txs = res.scalars().all()

    return {
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "transactions": [
            {
                "id": tx.id,
                "tx_hash": tx.tx_hash,
                "case_id": tx.case_id,
                "suspect_id": tx.suspect_id,
                "person_id": tx.person_id or "UNASSIGNED",
                "from_address": tx.from_address,
                "to_address": tx.to_address,
                "value": tx.value,
                "token_symbol": tx.token_symbol,
                "value_inr": tx.value_inr,
                "timestamp": tx.timestamp.isoformat() if tx.timestamp else None,
                "chain": tx.chain,
                "risk_flag": tx.risk_flag,
                "attributed_entity": tx.attributed_entity or "Unidentified Intermediary",
                "hop_level": tx.hop_level
            }
            for tx in txs
        ]
    }

@router.get("/stats", response_model=dict)
async def get_ledger_overview_stats(
    db: AsyncSession = Depends(get_db),
    officer: dict = Depends(get_current_officer)
):
    """Get high-level tactical statistics for the main operations dashboard."""
    tx_count_res = await db.execute(select(func.count(Transaction.id)))
    total_txs = tx_count_res.scalar() or 0

    inr_sum_res = await db.execute(select(func.sum(Transaction.value_inr)))
    total_volume_inr = inr_sum_res.scalar() or 0.0

    cases_count_res = await db.execute(select(func.count(Case.id)))
    total_cases = cases_count_res.scalar() or 0

    suspects_count_res = await db.execute(select(func.count(Suspect.id)))
    total_suspects = suspects_count_res.scalar() or 0

    vasp_tx_count = await db.execute(
        select(func.count(Transaction.id)).where(Transaction.risk_flag == "VASP_DEPOSIT")
    )
    attributed_vasp_deposits = vasp_tx_count.scalar() or 0

@router.post("/upload-dataset", response_model=dict)
async def upload_custom_dataset(
    file: UploadFile = File(...),
    case_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    officer: dict = Depends(get_current_officer)
):
    """
    Ingest user-provided transaction datasets in CSV or JSON formats.
    Parses, validates, deduplicates, and commits records directly into the master ledger.
    """
    from backend.services.dataset_ingestion import DatasetIngestionService
    
    filename = file.filename.lower()
    content_bytes = await file.read()
    content_str = content_bytes.decode("utf-8", errors="replace")

    if filename.endswith(".csv"):
        result = await DatasetIngestionService.ingest_csv_content(
            content=content_str,
            case_id=case_id,
            officer_badge=officer["badge_number"],
            db=db
        )
    elif filename.endswith(".json"):
        result = await DatasetIngestionService.ingest_json_content(
            content=content_str,
            case_id=case_id,
            officer_badge=officer["badge_number"],
            db=db
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please provide a valid CSV or JSON dataset."
        )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return {
        "status": "SUCCESS",
        "filename": file.filename,
        "summary": result,
        "message": f"Successfully ingested {result.get('inserted', 0)} new transactions into the Master Ledger."
    }

