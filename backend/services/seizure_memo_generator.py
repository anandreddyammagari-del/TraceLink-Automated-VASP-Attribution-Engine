import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

class SeizureMemoGenerator:
    """
    Generates formal statutory Seizure Memos / Panchnama documents
    under Section 105 Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023.
    """
    @staticmethod
    def generate_seizure_memo(
        fir_number: str,
        police_station: str,
        crime_sections: str,
        seized_assets_description: str,
        custody_officer: dict,
        panch_witnesses: Optional[List[dict]] = None,
        suspect_name: Optional[str] = None
    ) -> dict:
        memo_ref = f"SEIZURE-MEMO/BNSS105/{datetime.now(timezone.utc).year}/{str(uuid.uuid4())[:8].upper()}"
        now_str = datetime.now(timezone.utc).strftime("%d %B %Y at %H:%M UTC")

        witnesses_text = ""
        witness_list = panch_witnesses or [
            {"name": "Independent Witness 1", "address": "New Delhi", "id_ref": "Aadhaar / Voter ID Verified"},
            {"name": "Independent Witness 2", "address": "New Delhi", "id_ref": "Aadhaar / Voter ID Verified"}
        ]
        for idx, w in enumerate(witness_list, 1):
            witnesses_text += f"  {idx}. {w.get('name')} (Address: {w.get('address')}, ID Ref: {w.get('id_ref')})\n"

        memo_body = f"""================================================================================
FORMAL SEIZURE MEMO / PANCHNAMA UNDER SECTION 105 BNSS, 2023
GOVERNMENT OF INDIA // STATE POLICE CYBER CRIME WING
================================================================================

MEMO REFERENCE NUMBER : {memo_ref}
CRIME / FIR REFERENCE : {fir_number}
POLICE STATION        : {police_station}
STATUTORY CLAUSES     : Section 105 Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023
                        r/w {crime_sections}
DATE AND TIME         : {now_str}

WHEREAS, in connection with the investigation of the above-referenced case, the
Investigating Officer has reason to believe that certain digital assets, cryptographic
hardware, credentials, or electronic evidence are proceeds of crime or used in commission
of cyber offenses:

1. PARTICULARS OF THE PERSON IN POSSESSION / SUSPECT:
   Name    : {suspect_name or "Unknown / Custody Entity"}
   Location: Forensic Inspection & Extraction Chamber

2. INVENTORY OF DIGITAL ASSETS / CRYPTOGRAPHIC PROPERTY SEIZED:
{seized_assets_description}

3. PANCH / INDEPENDENT WITNESS AFFIRMATION:
The seizure of the above-listed digital assets and electronic credentials was executed in
our presence. We affirm that all cryptographic material, private keys, or hardware tokens
were sealed in anti-static tamper-evident evidence envelopes bearing unique forensic seals.
Witnesses:
{witnesses_text}

4. INVESTIGATING OFFICER UNDERTAKING:
I, {custody_officer.get('rank', 'Inspector')} {custody_officer.get('badge_number', '')}, Investigating Officer,
hereby take formal physical and digital custody of the aforementioned items under Section 105
BNSS, 2023. The electronic integrity hash has been preserved in the workstation evidence locker.

Signature of Investigating Officer: __________________________
Badge Number                      : {custody_officer.get('badge_number', 'OFFICER-LE')}
Police Station                    : {police_station}
Official Seal                     : [ STATE CYBER CRIME SEAL ]

================================================================================
CONFIDENTIAL POLICE WORKSTATION RECORD // PRESERVED FOR MAGISTRATE SUBMISSION
================================================================================
"""
        return {
            "memo_reference": memo_ref,
            "fir_number": fir_number,
            "statutory_clause": "Section 105 Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023",
            "memo_body": memo_body,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

seizure_memo_generator = SeizureMemoGenerator()
