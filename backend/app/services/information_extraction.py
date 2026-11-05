"""
LegalEase AI - Legal Information & Entity Extraction Engine (Phase 5)
Extracts names, dates, locations, monetary figures, legal identifiers,
and procedural events with exact source document and page number traceability.
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime, date

# Indian Bank names recognition
INDIAN_BANKS = [
    "State Bank of India", "SBI", "HDFC Bank", "HDFC", "ICICI Bank", "ICICI",
    "Punjab National Bank", "PNB", "Bank of Baroda", "Axis Bank", "Kotak Mahindra Bank",
    "Canara Bank", "Union Bank of India", "IndusInd Bank", "Yes Bank", "Federal Bank",
    "IDFC FIRST Bank", "Central Bank of India", "Indian Bank", "Bank of India"
]

MONTH_NAMES = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
    "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
    "august": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9, "october": 10,
    "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12
}


class LegalInformationExtractor:
    """
    Parses extracted document text to identify structured legal entities,
    monetary consideration, statutory identifiers, and contextual legal events.
    """

    @classmethod
    def extract_entities_from_pages(
        cls,
        pages: List[Dict[str, Any]],
        document_filename: str,
    ) -> Dict[str, Any]:
        """
        Extracts all legal entities across all pages of a document,
        maintaining strict page-number traceability.
        """
        all_dates: List[Dict[str, Any]] = []
        all_amounts: List[Dict[str, Any]] = []
        all_identifiers: List[Dict[str, Any]] = []
        all_parties: List[Dict[str, Any]] = []
        all_events: List[Dict[str, Any]] = []

        for p in pages:
            page_num = p.get("page_number", 1)
            text = p.get("text", "")
            if not text:
                continue

            # 1. Dates
            p_dates = cls._extract_dates(text, page_num, document_filename)
            all_dates.extend(p_dates)

            # 2. Monetary amounts
            p_amounts = cls._extract_monetary_amounts(text, page_num, document_filename)
            all_amounts.extend(p_amounts)

            # 3. Identifiers & reference numbers
            p_ids = cls._extract_identifiers(text, page_num, document_filename)
            all_identifiers.extend(p_ids)

            # 4. Parties & Banks
            p_parties = cls._extract_parties_and_banks(text, page_num, document_filename)
            all_parties.extend(p_parties)

            # 5. Legal Events
            p_events = cls._extract_legal_events(text, page_num, document_filename, p_dates)
            all_events.extend(p_events)

        return {
            "document_filename": document_filename,
            "dates": cls._deduplicate_by_value(all_dates),
            "monetary_amounts": cls._deduplicate_by_value(all_amounts),
            "identifiers": cls._deduplicate_by_value(all_identifiers),
            "parties": cls._deduplicate_by_value(all_parties),
            "events": all_events,
            "total_entities_found": (
                len(all_dates) + len(all_amounts) + len(all_identifiers) + len(all_parties)
            ),
        }

    @classmethod
    def _extract_dates(cls, text: str, page_num: int, doc_name: str) -> List[Dict[str, Any]]:
        """Extracts and normalizes dates from text."""
        dates = []

        # Pattern 1: DD/MM/YYYY or DD-MM-YYYY
        p1 = r"\b([0-3]?[0-9])[/-]([0-1]?[0-9])[/-](20[0-9]{2}|19[0-9]{2})\b"
        for m in re.finditer(p1, text):
            day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
            try:
                dt = date(year, month, day)
                dates.append({
                    "iso_date": dt.isoformat(),
                    "raw_text": m.group(0),
                    "page_number": page_num,
                    "source_document": doc_name,
                    "confidence": 0.95,
                })
            except ValueError:
                pass

        # Pattern 2: DD Month YYYY (e.g. 15th August 2024 or 15 August 2024)
        p2 = r"\b([0-3]?[0-9])(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(20[0-9]{2}|19[0-9]{2})\b"
        for m in re.finditer(p2, text, re.IGNORECASE):
            day = int(m.group(1))
            month_str = m.group(2).lower()
            year = int(m.group(3))
            month = MONTH_NAMES.get(month_str)
            if month:
                try:
                    dt = date(year, month, day)
                    dates.append({
                        "iso_date": dt.isoformat(),
                        "raw_text": m.group(0),
                        "page_number": page_num,
                        "source_document": doc_name,
                        "confidence": 0.95,
                    })
                except ValueError:
                    pass

        # Pattern 3: Month DD, YYYY (e.g. August 15, 2024)
        p3 = r"\b([A-Za-z]+)\s+([0-3]?[0-9])(?:st|nd|rd|th)?,\s*(20[0-9]{2}|19[0-9]{2})\b"
        for m in re.finditer(p3, text, re.IGNORECASE):
            month_str = m.group(1).lower()
            day = int(m.group(2))
            year = int(m.group(3))
            month = MONTH_NAMES.get(month_str)
            if month:
                try:
                    dt = date(year, month, day)
                    dates.append({
                        "iso_date": dt.isoformat(),
                        "raw_text": m.group(0),
                        "page_number": page_num,
                        "source_document": doc_name,
                        "confidence": 0.95,
                    })
                except ValueError:
                    pass

        return dates

    @classmethod
    def _extract_monetary_amounts(
        cls, text: str, page_num: int, doc_name: str
    ) -> List[Dict[str, Any]]:
        """Extracts currency figures in Indian Rupees."""
        amounts = []

        # Patterns for Rs / INR / ₹ with numbers
        p1 = r"(?:Rs\.?|INR|₹|Rupees)\s*([0-9,]+(?:\.[0-9]{2})?)\b"
        for m in re.finditer(p1, text, re.IGNORECASE):
            raw_val = m.group(1).replace(",", "")
            try:
                num = float(raw_val)
                if num > 0:
                    amounts.append({
                        "amount": num,
                        "currency": "INR",
                        "formatted": f"₹ {num:,.2f}",
                        "raw_text": m.group(0),
                        "page_number": page_num,
                        "source_document": doc_name,
                        "confidence": 0.95,
                    })
            except ValueError:
                pass

        # Pattern for Lakh / Crore figures (e.g. 2.5 Lakhs)
        p2 = r"\b([0-9]+(?:\.[0-9]+)?)\s*(Lakhs?|Lacs?|Crores?)\b"
        for m in re.finditer(p2, text, re.IGNORECASE):
            val = float(m.group(1))
            unit = m.group(2).lower()
            multiplier = 100000 if "l" in unit else 10000000
            num = val * multiplier
            amounts.append({
                "amount": num,
                "currency": "INR",
                "formatted": f"₹ {num:,.2f}",
                "raw_text": m.group(0),
                "page_number": page_num,
                "source_document": doc_name,
                "confidence": 0.90,
            })

        return amounts

    @classmethod
    def _extract_identifiers(
        cls, text: str, page_num: int, doc_name: str
    ) -> List[Dict[str, Any]]:
        """Extracts transactional references, cheque numbers, invoices, speed post IDs."""
        ids = []

        # Cheque Number (typically 6 digits)
        m_chq = re.finditer(r"\b(?:Cheque|Chq\.?)\s*(?:No\.?|Number|#)?\s*([0-9]{6})\b", text, re.IGNORECASE)
        for m in m_chq:
            ids.append({
                "type": "CHEQUE_NUMBER",
                "value": m.group(1),
                "raw_text": m.group(0),
                "page_number": page_num,
                "source_document": doc_name,
                "confidence": 0.92,
            })

        # Speed Post / Postal Consignment Tracking ID (e.g. ED123456789IN)
        m_post = re.finditer(r"\b([A-Z]{2}[0-9]{9}IN)\b", text)
        for m in m_post:
            ids.append({
                "type": "SPEED_POST_TRACKING_ID",
                "value": m.group(1),
                "raw_text": m.group(0),
                "page_number": page_num,
                "source_document": doc_name,
                "confidence": 0.98,
            })

        # Invoice Number
        m_inv = re.finditer(r"\b(?:Invoice|Bill)\s*(?:No\.?|Number|#)?\s*([A-Za-z0-9\/-]{4,20})\b", text, re.IGNORECASE)
        for m in m_inv:
            ids.append({
                "type": "INVOICE_NUMBER",
                "value": m.group(1),
                "raw_text": m.group(0),
                "page_number": page_num,
                "source_document": doc_name,
                "confidence": 0.88,
            })

        # Bank Account Number
        m_ac = re.finditer(r"\b(?:A/C|Account)\s*(?:No\.?|Number)?\s*([0-9]{9,18})\b", text, re.IGNORECASE)
        for m in m_ac:
            ac_num = m.group(1)
            masked = "X" * (len(ac_num) - 4) + ac_num[-4:]
            ids.append({
                "type": "BANK_ACCOUNT_NUMBER",
                "value": masked,
                "raw_text": m.group(0),
                "page_number": page_num,
                "source_document": doc_name,
                "confidence": 0.90,
            })

        # Return Memo Reason (NI Act 138)
        reasons = [
            "Funds Insufficient", "Insufficient Funds", "Account Closed",
            "Exceeds Arrangement", "Signature Differs", "Stop Payment"
        ]
        for r in reasons:
            if re.search(r"\b" + re.escape(r) + r"\b", text, re.IGNORECASE):
                ids.append({
                    "type": "BANK_RETURN_REASON",
                    "value": r,
                    "raw_text": r,
                    "page_number": page_num,
                    "source_document": doc_name,
                    "confidence": 0.95,
                })

        return ids

    @classmethod
    def _extract_parties_and_banks(
        cls, text: str, page_num: int, doc_name: str
    ) -> List[Dict[str, Any]]:
        """Identifies banking institutions and legal roles."""
        parties = []

        # Indian Banks
        for bank in INDIAN_BANKS:
            if re.search(r"\b" + re.escape(bank) + r"\b", text, re.IGNORECASE):
                parties.append({
                    "type": "BANK_INSTITUTION",
                    "value": bank,
                    "raw_text": bank,
                    "page_number": page_num,
                    "source_document": doc_name,
                    "confidence": 0.95,
                })

        # Statutory Roles
        roles = [
            ("DRAWER", r"\b(?:drawer|issuer|accused|opposite party)\b"),
            ("PAYEE", r"\b(?:payee|holder in due course|complainant|claimant)\b"),
            ("LANDLORD", r"\b(?:landlord|lessor|owner)\b"),
            ("TENANT", r"\b(?:tenant|lessee|occupant)\b"),
        ]
        for role_name, pat in roles:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                parties.append({
                    "type": "LEGAL_ROLE",
                    "value": role_name,
                    "raw_text": match.group(0),
                    "page_number": page_num,
                    "source_document": doc_name,
                    "confidence": 0.85,
                })

        return parties

    @classmethod
    def _extract_legal_events(
        cls,
        text: str,
        page_num: int,
        doc_name: str,
        page_dates: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Identifies specific procedural milestones and pairs them with dates."""
        events = []
        default_date = page_dates[0]["iso_date"] if page_dates else None

        # Canonical event patterns
        event_patterns = [
            ("CHEQUE_DISHONOUR", r"\b(?:returned unpaid|dishonoured|memo received|funds insufficient)\b", "Cheque Dishonoured by Bank"),
            ("DEMAND_NOTICE_SERVED", r"\b(?:legal notice sent|statutory demand notice|dispatched via speed post|notice served)\b", "Statutory Demand Notice Dispatched"),
            ("AGREEMENT_EXECUTED", r"\b(?:agreement entered|agreement executed|lease signed|contract signed)\b", "Agreement / Contract Executed"),
            ("PURCHASE_TRANSACTION", r"\b(?:purchased|delivered|invoice generated|bill of supply)\b", "Goods Purchased / Invoice Generated"),
            ("POLICE_COMPLAINT_FILED", r"\b(?:complaint lodged|fir registered|submitted to sho|police report)\b", "Police Complaint / FIR Lodged"),
            ("PAYMENT_DEFAULT", r"\b(?:failed to pay|defaulted in payment|non-payment|cure period expired)\b", "Default in Payment After Notice"),
        ]

        for ev_type, pat, title in event_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                # Find the nearest date on this page if available
                ev_date = default_date or "UNDATED_OR_PENDING"
                events.append({
                    "event_type": ev_type,
                    "title": title,
                    "date": ev_date,
                    "evidence_snippet": m.group(0),
                    "page_number": page_num,
                    "source_document": doc_name,
                    "confidence": "HIGH" if ev_date != "UNDATED_OR_PENDING" else "MEDIUM",
                })

        return events

    @staticmethod
    def _deduplicate_by_value(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicates extracted items by their primary key while preserving list order."""
        seen = set()
        deduped = []
        for it in items:
            val = it.get("value") or it.get("iso_date") or it.get("amount")
            key = (it.get("type", ""), str(val))
            if key not in seen:
                seen.add(key)
                deduped.append(it)
        return deduped
