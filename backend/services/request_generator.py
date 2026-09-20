import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from backend.models.case import Case
from backend.models.attribution import VASPAttribution
from backend.models.user import User

class LawfulRequestGenerator:
    """
    Statutory Notice Generator under:
    - Section 94 Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023 (Order to produce documents/things)
    - Section 79(3)(b) Information Technology Act, 2000 (Notice to intermediary for preservation & assistance)
    """

    @staticmethod
    def generate_notice_reference(fir_number: str) -> str:
        clean_fir = fir_number.replace("/", "-").replace(" ", "-")[-10:]
        unique_suffix = uuid.uuid4().hex[:6].upper()
        return f"LEA/{clean_fir}/SEC94/{unique_suffix}"

    @staticmethod
    def generate_section_94_notice(
        case_record: Case,
        attribution: VASPAttribution,
        officer: Dict[str, Any],
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        ref_no = LawfulRequestGenerator.generate_notice_reference(case_record.fir_number)
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%d-%B-%Y")

        statutory_clause = (
            "Section 94 of Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023 "
            "read with Section 79(3)(b) of the Information Technology Act, 2000"
        )

        inr_val_formatted = f"₹ {case_record.total_disputed_inr:,.2f}" if case_record.total_disputed_inr else "Under Forensic Assessment"

        notice_body = f"""OFFICE OF THE INVESTIGATING OFFICER
SPECIAL CYBER CRIME INVESTIGATION UNIT
STATE POLICE HEADQUARTERS / CRIME BRANCH
{case_record.police_station.upper()}

NOTICE UNDER {statutory_clause.upper()}

Ref. No: {ref_no}
Issuance Date: {date_str}
Jurisdiction: State Cyber Operations Division

TO:
The Nodal Officer / Head of Legal & Regulatory Compliance
Entity: {attribution.target_vasp_name}
VASP Deposit Gateway Cluster: {attribution.vasp_deposit_address}

SUBJECT: STATUTORY DIRECTION UNDER SECTION 94 BNSS (2023) AND SECTION 79(3)(b) IT ACT (2000) TO FURNISH SUBSCRIBER KYC, TRANSACTION HISTORIES, AND FREEZE DISPUTED CRYPTO ASSET BALANCES IN FIR NO: {case_record.fir_number}

1. INVESTIGATION BACKGROUND:
   This cyber unit is investigating FIR No. {case_record.fir_number} registered under:
   {case_record.crime_sections}
   concerning cyber-enabled financial fraud and illicit asset diversion totaling {inr_val_formatted}.

2. FORENSIC ATTRIBUTION FINDINGS:
   Topological blockchain tracing and multi-hop graph analysis conducted by certified cyber forensic examiners established that stolen funds originating from the complainant/victim addresses traversed intermediary layering wallets and entered the following deposit address hosted by your exchange/service:

   • Destination Deposit Address: {attribution.vasp_deposit_address}
   • Asset Transferred: {attribution.total_volume} {attribution.token_symbol}
   • Intermediary Hop Distance: {attribution.hop_distance} hop(s)
   • Attribution Confidence Level: {attribution.confidence_score}% (Tier: {attribution.confidence_tier})
   • Transaction Routing Path: Verified direct or structured peel chain to your exchange cluster.

3. STATUTORY PRODUCTION DIRECTIVE (SECTION 94 BNSS):
   In exercise of the powers conferred under Section 94 of the Bharatiya Nagarik Suraksha Sanhita, 2023, you are hereby summoned and directed to produce the following records and digital evidence within 48 (forty-eight) hours of receipt of this notice:
   (a) Complete KYC / Identity Documentation of the registered account holder (Name, Date of Birth, Government ID / Aadhaar / PAN / Passport, residential address, verified email, and phone number).
   (b) Account Opening & Access Logs: IP address logs with exact timestamps and port numbers for account registration and all login sessions for the past 90 days.
   (c) Full Ledger of Inflows & Outflows: Detailed statement of all cryptocurrency and fiat deposits, withdrawals, internal trades, and bank account settlement details (including bank name, account number, and IFSC).

4. DIRECTION TO PRESERVE & RESTRICT DISPOSAL (SECTION 79(3)(b) IT ACT):
   Pursuant to Section 79(3)(b) of the Information Technology Act, 2000, you are directed to immediately place an administrative freeze on the disputed crypto asset volume ({attribution.total_volume} {attribution.token_symbol}) and any associated fiat balances under this UID to prevent further dissipation pending judicial orders.

5. CONTACT & SUBMISSION PARTICULARS:
   Designated Investigating Officer: {officer.get('rank', 'Inspector')} ({officer.get('badge_number', 'N/A')})
   Assigned Unit: {officer.get('station', case_record.police_station)}
   Official Cyber Cell Email: cyber.investigation@police.gov.in

{f"Additional Officer Instructions:\n{custom_instructions}\n" if custom_instructions else ""}
================================================================================
*** MANDATORY INSTITUTIONAL SAFETY NOTICE ***
Investigative draft generated locally for officer review. Direct electronic submission to external portals is deactivated.
All actions recorded with cryptographic timestamp and SHA-256 evidence chain under Section 63 of Bharatiya Sakshya Adhiniyam, 2023.
================================================================================
"""

        return {
            "notice_reference_number": ref_no,
            "statutory_clause": statutory_clause,
            "target_vasp_name": attribution.target_vasp_name,
            "target_deposit_wallet": attribution.vasp_deposit_address,
            "notice_body": notice_body,
            "status": "DRAFT",
            "is_external_submission_deactivated": True
        }
