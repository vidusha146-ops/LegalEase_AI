"""
LegalEase AI - Evidence Consistency & Contradiction Analyzer (Phase 5)
Detects sequence discrepancies, monetary variances, and factual mismatches
across documents and user statements. Adheres strictly to non-defamatory labeling.
"""

from typing import Dict, Any, List, Optional
from datetime import date


class EvidenceConsistencyAnalyzer:
    """
    Cross-examines extracted documentary facts against citizen narrative claims
    and cross-document records to identify discrepancies, sequence anomalies,
    and missing documentary proofs.
    """

    @classmethod
    def analyze_consistency(
        cls,
        documents_metadata: List[Dict[str, Any]],
        narrative: str,
        predicted_domain: Optional[str] = None,
        narrative_amount: Optional[float] = None,
        narrative_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Runs comprehensive consistency analysis across uploaded documents
        and compares with narrative claims.
        """
        discrepancies: List[Dict[str, Any]] = []
        documentary_gaps: List[Dict[str, Any]] = []

        # 1. Aggregate all extracted amounts and dates across documents
        all_doc_amounts: List[Dict[str, Any]] = []
        all_doc_dates: List[Dict[str, Any]] = []
        uploaded_categories = set()

        for doc in documents_metadata:
            cat = doc.get("category", "OTHER_EVIDENCE")
            uploaded_categories.add(cat)
            doc_name = doc.get("filename", "Document")

            for amt in doc.get("monetary_amounts", []):
                all_doc_amounts.append({
                    "amount": amt["amount"],
                    "formatted": amt["formatted"],
                    "document": doc_name,
                    "page": amt.get("page_number", 1),
                })

            for dt in doc.get("dates", []):
                all_doc_dates.append({
                    "iso_date": dt["iso_date"],
                    "document": doc_name,
                    "page": dt.get("page_number", 1),
                })

        # 2. Check for Monetary Variances
        if len(all_doc_amounts) >= 2:
            amounts_set = set(a["amount"] for a in all_doc_amounts)
            if len(amounts_set) > 1:
                # Group by amount
                distinct_amounts = sorted(list(amounts_set))
                discrepancies.append({
                    "type": "MONETARY_AMOUNT_VARIANCE",
                    "severity": "MODERATE",
                    "description": (
                        f"Differing financial amounts detected across evidence documents: "
                        f"{', '.join(f'₹ {a:,.2f}' for a in distinct_amounts)}. "
                        "Clarify whether these represent installments, partial payments, or principal vs interest."
                    ),
                    "affected_documents": [a["document"] for a in all_doc_amounts],
                })

        # Compare with narrative amount if user stated an exact figure
        if narrative_amount and all_doc_amounts:
            matching_doc_amt = any(abs(a["amount"] - narrative_amount) < 1.0 for a in all_doc_amounts)
            if not matching_doc_amt:
                discrepancies.append({
                    "type": "NARRATIVE_DOCUMENT_AMOUNT_VARIANCE",
                    "severity": "LOW",
                    "description": (
                        f"Narrative states a claimed amount of ₹ {narrative_amount:,.2f}, which does not match "
                        f"the primary figures in uploaded documents ({', '.join(a['formatted'] for a in all_doc_amounts[:2])})."
                    ),
                    "affected_documents": [a["document"] for a in all_doc_amounts[:2]],
                })

        # 3. Check for Chronological Sequence Anomalies between Documents
        # E.g. Check bounce case: Notice date vs Return memo date
        notice_docs = [d for d in documents_metadata if d.get("category") == "LEGAL_NOTICE"]
        memo_docs = [d for d in documents_metadata if d.get("category") == "BANK_RECORD"]

        if notice_docs and memo_docs:
            notice_dates = [d["iso_date"] for d in notice_docs[0].get("dates", [])]
            memo_dates = [d["iso_date"] for d in memo_docs[0].get("dates", [])]

            if notice_dates and memo_dates:
                earliest_notice = min(notice_dates)
                earliest_memo = min(memo_dates)
                if earliest_notice < earliest_memo:
                    discrepancies.append({
                        "type": "CHRONOLOGICAL_SEQUENCE_DISCREPANCY",
                        "severity": "HIGH",
                        "description": (
                            f"Statutory demand notice appears dated ({earliest_notice}) before the bank return memo "
                            f"({earliest_memo}). Under Section 138(b) of the NI Act, a notice can only be dispatched "
                            "after receiving the return memo from the bank."
                        ),
                        "affected_documents": [notice_docs[0].get("filename"), memo_docs[0].get("filename")],
                    })

        # 4. Highlight Missing Essential Supporting Documents by Legal Domain
        if predicted_domain == "CHEQUE_BOUNCE_NI_ACT":
            if "BANK_RECORD" not in uploaded_categories:
                documentary_gaps.append({
                    "missing_document_type": "BANK_RETURN_MEMO",
                    "title": "Bank Cheque Return Memo",
                    "statutory_rationale": "Required under Section 138(b) & Section 146 NI Act as prima facie proof of dishonour.",
                })
            if "LEGAL_NOTICE" not in uploaded_categories:
                documentary_gaps.append({
                    "missing_document_type": "STATUTORY_DEMAND_NOTICE_WITH_POSTAL_RECEIPT",
                    "title": "15-Day Statutory Demand Notice & Speed Post Receipt",
                    "statutory_rationale": "Mandatory prerequisite under Section 138(b) proviso to establish cause of action.",
                })

        elif predicted_domain == "CONSUMER_PROTECTION":
            if "INVOICE_BILL" not in uploaded_categories:
                documentary_gaps.append({
                    "missing_document_type": "PURCHASE_INVOICE_OR_WARRANTY_CARD",
                    "title": "Tax Invoice or Manufacturer Warranty Card",
                    "statutory_rationale": "Required under Section 35 Consumer Protection Act, 2019 to establish consumer status.",
                })

        elif predicted_domain == "PROPERTY_DISPUTE_TENANCY":
            if "AGREEMENT_CONTRACT" not in uploaded_categories:
                documentary_gaps.append({
                    "missing_document_type": "LEASE_RENT_AGREEMENT",
                    "title": "Rent Agreement or Lease Deed",
                    "statutory_rationale": "Establishes landlord-tenant relationship and agreed tenancy terms.",
                })

        is_consistent = len(discrepancies) == 0

        return {
            "is_consistent": is_consistent,
            "discrepancies_count": len(discrepancies),
            "discrepancies": discrepancies,
            "documentary_gaps_count": len(documentary_gaps),
            "documentary_gaps": documentary_gaps,
            "summary": (
                "Documentary evidence is consistent with no sequence or amount discrepancies detected."
                if is_consistent
                else f"{len(discrepancies)} evidentiary variance(s) and {len(documentary_gaps)} missing document(s) identified."
            ),
        }
