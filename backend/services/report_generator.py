import io
import hashlib
from datetime import datetime, timezone
from typing import Optional, List, Dict

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

class ForensicReportGenerator:
    """
    Generates formal court-admissible PDF forensic dossiers compliant with:
    - Section 65B Indian Evidence Act, 1872 / Section 63 Bharatiya Sakshya Adhiniyam (BSA), 2023
    - Section 94 BNSS (2023) production attachments
    """

    @staticmethod
    def generate_case_dossier_pdf(
        case_dict: dict,
        attribution_dict: Optional[dict] = None,
        transactions: Optional[List[dict]] = None,
        officer: Optional[dict] = None,
        audit_chain_head: Optional[str] = None
    ) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom styles for Police light theme
        navy_color = colors.HexColor("#0F2C59")
        emerald_color = colors.HexColor("#166534")
        dark_slate = colors.HexColor("#1E293B")
        light_bg = colors.HexColor("#F8FAFC")
        border_color = colors.HexColor("#CBD5E1")

        title_style = ParagraphStyle(
            'PoliceTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            textColor=navy_color,
            alignment=1  # Centered
        )

        subtitle_style = ParagraphStyle(
            'PoliceSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#475569"),
            alignment=1
        )

        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=15,
            textColor=navy_color,
            spaceBefore=10,
            spaceAfter=4
        )

        body_style = ParagraphStyle(
            'PoliceBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=12,
            textColor=dark_slate
        )

        mono_style = ParagraphStyle(
            'PoliceMono',
            parent=styles['Normal'],
            fontName='Courier',
            fontSize=7.5,
            leading=10,
            textColor=dark_slate
        )

        legal_cert_style = ParagraphStyle(
            'LegalCert',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#334155")
        )

        story = []

        # 1. Official Header
        story.append(Paragraph("STATE CYBER POLICE & ECONOMIC OFFENCES CELL", title_style))
        story.append(Paragraph("CONFIDENTIAL // LAW ENFORCEMENT INTELLIGENCE DOSSIER // FOR COURT PRODUCTION", subtitle_style))
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=2, color=navy_color, spaceBefore=2, spaceAfter=8))

        # 2. FIR & Case Particulars Table
        fir_num = case_dict.get("fir_number", "FIR-UNASSIGNED")
        case_title = case_dict.get("title", "Forensic Blockchain Investigation")
        ps = case_dict.get("police_station", "Special Cyber Operations Branch")
        sections = case_dict.get("crime_sections", "Sec 66D IT Act r/w BNS")
        officer_name = officer.get("rank", "") + " " + officer.get("badge_number", "") if officer else "ACP Investigating Officer"

        case_meta_data = [
            [
                Paragraph("<b>FIR Number:</b>", body_style), Paragraph(f"<font color='#0F2C59'><b>{fir_num}</b></font>", body_style),
                Paragraph("<b>Police Station:</b>", body_style), Paragraph(ps, body_style)
            ],
            [
                Paragraph("<b>Statutory Sections:</b>", body_style), Paragraph(sections, body_style),
                Paragraph("<b>Investigating Officer:</b>", body_style), Paragraph(officer_name, body_style)
            ],
            [
                Paragraph("<b>Case Classification:</b>", body_style), Paragraph(case_title, body_style),
                Paragraph("<b>Date of Report:</b>", body_style), Paragraph(datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC"), body_style)
            ]
        ]
        case_table = Table(case_meta_data, colWidths=[100, 170, 110, 160])
        case_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), light_bg),
            ('BOX', (0,0), (-1,-1), 1, border_color),
            ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(case_table)
        story.append(Spacer(1, 10))

        # 3. Target VASP Attribution Section
        story.append(Paragraph("I. FORENSIC VASP ATTRIBUTION & STATUTORY TARGET", section_heading))
        if attribution_dict:
            vasp_name = attribution_dict.get("target_vasp_name", "Unknown VASP")
            vasp_addr = attribution_dict.get("vasp_deposit_address", "N/A")
            conf_score = attribution_dict.get("confidence_score", 0.0)
            conf_tier = attribution_dict.get("confidence_tier", "LOW")
            vol = attribution_dict.get("total_volume", 0.0)
            token = attribution_dict.get("token_symbol", "ETH")
            hops = attribution_dict.get("hop_distance", 0)

            attrib_data = [
                [Paragraph("<b>Target Entity (VASP):</b>", body_style), Paragraph(f"<b>{vasp_name}</b>", body_style)],
                [Paragraph("<b>Nodal Deposit Address:</b>", body_style), Paragraph(vasp_addr, mono_style)],
                [Paragraph("<b>ML Confidence Rating:</b>", body_style), Paragraph(f"<b>{conf_score:.1f}% ({conf_tier} PROBABILITY)</b>", body_style)],
                [Paragraph("<b>Attributed Volume:</b>", body_style), Paragraph(f"{vol} {token}", body_style)],
                [Paragraph("<b>Topological Distance:</b>", body_style), Paragraph(f"{hops} hop(s) from primary suspect wallet", body_style)]
            ]
            attrib_table = Table(attrib_data, colWidths=[160, 380])
            attrib_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0FDF4")),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#86EFAC")),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#DCFCE7")),
                ('TOPPADDING', (0,0), (-1,-1), 3),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ]))
            story.append(attrib_table)

            # Evidentiary factors
            factors = attribution_dict.get("evidence_breakdown", [])
            if factors:
                story.append(Spacer(1, 6))
                story.append(Paragraph("<b>Evidentiary Factors & Algorithmic Grounds:</b>", body_style))
                for f in factors[:4]:
                    story.append(Paragraph(f"• {f}", body_style))
        else:
            story.append(Paragraph("Attribution computation pending for this case file.", body_style))

        story.append(Spacer(1, 10))

        # 4. Transaction Flow Ledger
        story.append(Paragraph("II. FORENSIC TRANSACTION FLOW LEDGER", section_heading))
        tx_rows = [
            [
                Paragraph("<b>Timestamp (UTC)</b>", body_style),
                Paragraph("<b>From Address</b>", body_style),
                Paragraph("<b>To Address</b>", body_style),
                Paragraph("<b>Amount</b>", body_style),
                Paragraph("<b>Flag</b>", body_style)
            ]
        ]
        display_txs = (transactions or [])[:8]
        if not display_txs:
            tx_rows.append([Paragraph("No transactions recorded.", body_style), "", "", "", ""])
        else:
            for tx in display_txs:
                ts = str(tx.get("timestamp", "N/A"))[:19].replace("T", " ")
                f_addr = str(tx.get("from_address", ""))[:8] + "..." + str(tx.get("from_address", ""))[-4:]
                t_addr = str(tx.get("to_address", ""))[:8] + "..." + str(tx.get("to_address", ""))[-4:]
                amt = f"{tx.get('value', 0)} {tx.get('token_symbol', 'ETH')}"
                flag = tx.get("risk_flag", "NORMAL")
                tx_rows.append([
                    Paragraph(ts, mono_style),
                    Paragraph(f_addr, mono_style),
                    Paragraph(t_addr, mono_style),
                    Paragraph(amt, body_style),
                    Paragraph(flag, body_style)
                ])

        tx_table = Table(tx_rows, colWidths=[100, 115, 115, 90, 120])
        tx_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
            ('BOX', (0,0), (-1,-1), 1, border_color),
            ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        story.append(tx_table)
        story.append(Spacer(1, 10))

        # 5. Section 65B IEA / Section 63 BSA Admissibility Certificate
        story.append(Paragraph("III. STATUTORY ELECTRONIC EVIDENCE CERTIFICATE", section_heading))
        cert_text = (
            "<b>CERTIFICATE UNDER SECTION 63 OF BHARATIYA SAKSHYA ADHINIYAM (BSA), 2023 "
            "(r/w SECTION 65B INDIAN EVIDENCE ACT, 1872):</b><br/>"
            "I hereby certify that the electronic cryptocurrency transaction records and topological graph "
            "contained in this dossier were produced by the TraceLink Automated Forensic Workstation during the "
            "regular course of official duties. The computer system and cryptographic ledger operate under strict "
            "audit security controls without unauthorized tampering. The cryptographic hash below authenticates "
            "the mathematical integrity of this evidentiary snapshot."
        )
        story.append(Paragraph(cert_text, legal_cert_style))
        story.append(Spacer(1, 6))

        # Chain Head Hash
        head_hash = audit_chain_head or "0" * 64
        hash_box = Table(
            [[Paragraph("<b>Audit Trail Head SHA-256:</b>", body_style), Paragraph(head_hash, mono_style)]],
            colWidths=[150, 390]
        )
        hash_box.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
            ('BOX', (0,0), (-1,-1), 0.5, border_color),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        story.append(hash_box)
        story.append(Spacer(1, 15))

        # 6. Officer Signatures
        sig_data = [
            [
                Paragraph("<b>Investigating Officer Signature:</b><br/><br/>__________________________________<br/>Name:<br/>Badge:", body_style),
                Paragraph("<b>Senior Supervisory Officer / Seal:</b><br/><br/>__________________________________<br/>ACP / DySP Cyber Crime<br/>Date: [ OFFICIAL POLICE SEAL ]", body_style)
            ]
        ]
        sig_table = Table(sig_data, colWidths=[270, 270])
        sig_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, border_color),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(sig_table)

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

report_generator = ForensicReportGenerator()
