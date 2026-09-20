from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from backend.core.database import get_db
from backend.core.security import get_current_officer
from backend.models.case import Case
from backend.models.attribution import VASPAttribution
from backend.models.transaction import Transaction
from backend.models.audit import AuditLog
from backend.services.report_generator import report_generator
import json

router = APIRouter(prefix="/api/reports", tags=["Court Dossier & Statutory Reports"])

@router.get("/case/{case_id}/pdf")
async def generate_court_dossier_pdf(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    officer: dict = Depends(get_current_officer)
):
    """
    Generate and stream an official, court-admissible PDF forensic dossier
    compliant with Section 63 Bharatiya Sakshya Adhiniyam, 2023 / Section 65B Indian Evidence Act.
    """
    # Find case
    stmt = select(Case).where(or_(Case.id == case_id, Case.fir_number == case_id))
    res = await db.execute(stmt)
    case_rec = res.scalars().first()
    if not case_rec:
        raise HTTPException(status_code=404, detail="Case record not found.")

    # Find attribution
    attrib_stmt = select(VASPAttribution).order_by(VASPAttribution.created_at.desc()).limit(1)
    attrib_res = await db.execute(attrib_stmt)
    attrib_rec = attrib_res.scalars().first()
    attrib_dict = None
    if attrib_rec:
        attrib_dict = {
            "target_vasp_name": attrib_rec.target_vasp_name,
            "vasp_deposit_address": attrib_rec.vasp_deposit_address,
            "confidence_score": attrib_rec.confidence_score,
            "confidence_tier": attrib_rec.confidence_tier,
            "total_volume": attrib_rec.total_volume,
            "token_symbol": attrib_rec.token_symbol,
            "hop_distance": attrib_rec.hop_distance,
            "evidence_breakdown": json.loads(attrib_rec.evidence_breakdown_json) if attrib_rec.evidence_breakdown_json else []
        }

    # Find transactions for this case
    tx_stmt = select(Transaction).where(Transaction.case_id == case_rec.id).order_by(Transaction.timestamp.asc()).limit(50)
    tx_res = await db.execute(tx_stmt)
    txs = tx_res.scalars().all()
    tx_list = [
        {
            "tx_hash": t.tx_hash,
            "from_address": t.from_address,
            "to_address": t.to_address,
            "value": t.value,
            "token_symbol": t.token_symbol,
            "timestamp": t.timestamp.isoformat() if t.timestamp else "",
            "risk_flag": t.risk_flag
        }
        for t in txs
    ]

    # Get latest audit log hash
    audit_stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(1)
    audit_rec = (await db.execute(audit_stmt)).scalars().first()
    chain_head = audit_rec.current_hash if audit_rec else "0" * 64

    case_dict = {
        "fir_number": case_rec.fir_number,
        "title": case_rec.title,
        "police_station": case_rec.police_station,
        "crime_sections": case_rec.crime_sections,
        "total_disputed_inr": case_rec.total_disputed_inr
    }

    pdf_bytes = report_generator.generate_case_dossier_pdf(
        case_dict=case_dict,
        attribution_dict=attrib_dict,
        transactions=tx_list,
        officer=officer,
        audit_chain_head=chain_head
    )

    filename = f"Forensic_Dossier_{case_rec.fir_number.replace('/', '_')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
