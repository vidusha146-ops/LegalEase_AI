"""
LegalEase AI - Evidence Classification Service (Phase 5)
Automatically classifies uploaded evidentiary documents into canonical legal categories
with confidence scoring, and supports user manual correction.
"""

import re
from typing import Dict, Any, List, Tuple

CANONICAL_CATEGORIES = {
    "INVOICE_BILL": {
        "title": "Invoice / Bill of Supply",
        "keywords": [
            r"\btax\s+invoice\b", r"\bbill\s+of\s+supply\b", r"\bgstin\b", r"\binvoice\s+no\b",
            r"\btotal\s+amount\b", r"\bhsn\s+code\b", r"\bpurchase\s+order\b", r"\bcash\s+receipt\b",
            r"\bquantity\b", r"\bunit\s+price\b", r"\bchallan\b"
        ],
        "weight": 1.2
    },
    "BANK_RECORD": {
        "title": "Bank Record / Return Memo / Transaction",
        "keywords": [
            r"\bbank\s+statement\b", r"\breturn\s+memo\b", r"\bfunds\s+insufficient\b",
            r"\bcheque\s+no\b", r"\bcheque\s+dishonour\b", r"\baccount\s+number\b",
            r"\bifsc\b", r"\btransaction\s+id\b", r"\butr\b", r"\bdebit\b", r"\bcredit\b",
            r"\bpassbook\b", r"\bbranch\b"
        ],
        "weight": 1.3
    },
    "LEGAL_NOTICE": {
        "title": "Legal / Statutory Demand Notice",
        "keywords": [
            r"\blegal\s+notice\b", r"\bdemand\s+notice\b", r"\bsection\s+138\b", r"\badvocate\b",
            r"\bunder\s+instructions\s+from\b", r"\bcall\s+upon\s+you\b", r"\b15\s+days\b",
            r"\bfailing\s+which\b", r"\blegal\s+proceedings\b", r"\bregistered\s+post\b",
            r"\bspeed\s+post\b", r"\bnoticee\b"
        ],
        "weight": 1.4
    },
    "AGREEMENT_CONTRACT": {
        "title": "Agreement / Lease / Commercial Contract",
        "keywords": [
            r"\bagreement\b", r"\blease\s+agreement\b", r"\brent\s+agreement\b", r"\bcontract\b",
            r"\bwhereas\b", r"\bin\s+witness\s+whereof\b", r"\bterms\s+and\s+conditions\b",
            r"\bparties\s+hereto\b", r"\bfirst\s+party\b", r"\bsecond\s+party\b", r"\bstamp\s+duty\b",
            r"\bnon-judicial\b"
        ],
        "weight": 1.2
    },
    "POLICE_COMPLAINT_FIR": {
        "title": "Police Complaint / First Information Report (FIR)",
        "keywords": [
            r"\bfirst\s+information\s+report\b", r"\bfir\b", r"\bpolice\s+station\b",
            r"\bsho\b", r"\bstation\s+house\s+officer\b", r"\bsection\s+154\b", r"\bsection\s+173\b",
            r"\bcomplaint\s+copy\b", r"\bcognizable\b", r"\binvestigation\b"
        ],
        "weight": 1.4
    },
    "EMAIL_CORRESPONDENCE": {
        "title": "Email / Formal Correspondence",
        "keywords": [
            r"\bfrom:\b", r"\bto:\b", r"\bsubject:\b", r"\bdate:\b", r"\bdear\s+sir\b",
            r"\bdear\s+madam\b", r"\bregards,\b", r"\bsincerely\b", r"\bemail\b", r"\bgrievance\b"
        ],
        "weight": 1.1
    },
    "IDENTITY_ADDRESS_PROOF": {
        "title": "Identity / Address Proof",
        "keywords": [
            r"\baadhaar\b", r"\buidai\b", r"\bpan\s+card\b", r"\bincome\s+tax\s+department\b",
            r"\belection\s+commission\b", r"\bvoter\s+id\b", r"\bpassport\b", r"\bdriving\s+licen[sc]e\b"
        ],
        "weight": 1.5
    },
}


class EvidenceClassifierService:
    """
    Classifies documents based on heuristic pattern matching and keyword density.
    Provides confidence scores and facilitates manual reclassification.
    """

    @classmethod
    def classify_document(cls, text: str, filename: str = "") -> Dict[str, Any]:
        """
        Calculates category scores for the extracted text and assigns
        the best-matching category with a confidence metric.
        """
        combined = f"{filename} {text}".lower()

        scores: Dict[str, float] = {}
        matched_indicators: Dict[str, List[str]] = {}

        for cat_key, cat_data in CANONICAL_CATEGORIES.items():
            matches = []
            for pat in cat_data["keywords"]:
                found = re.findall(pat, combined)
                if found:
                    matches.extend(found)

            match_count = len(matches)
            score = round(match_count * cat_data["weight"], 2)
            scores[cat_key] = score
            matched_indicators[cat_key] = list(set(matches))

        # Determine highest scoring category
        best_cat = max(scores, key=scores.get)
        best_score = scores[best_cat]

        if best_score == 0:
            assigned_category = "OTHER_EVIDENCE"
            assigned_title = "Other Evidence / General Document"
            confidence = 0.50
        else:
            assigned_category = best_cat
            assigned_title = CANONICAL_CATEGORIES[best_cat]["title"]
            # Confidence bounded between [0.60, 0.98]
            confidence = min(0.98, max(0.60, round(0.55 + (best_score * 0.05), 2)))

        return {
            "category": assigned_category,
            "category_title": assigned_title,
            "confidence": confidence,
            "indicator_keywords": matched_indicators.get(assigned_category, []),
            "all_category_scores": scores,
            "is_user_corrected": False,
        }

    @classmethod
    def reclassify(cls, new_category: str) -> Dict[str, Any]:
        """User manual override of evidence classification."""
        clean_cat = new_category.upper().strip()
        if clean_cat not in CANONICAL_CATEGORIES and clean_cat != "OTHER_EVIDENCE":
            clean_cat = "OTHER_EVIDENCE"

        title = (
            CANONICAL_CATEGORIES[clean_cat]["title"]
            if clean_cat in CANONICAL_CATEGORIES
            else "Other Evidence / General Document"
        )

        return {
            "category": clean_cat,
            "category_title": title,
            "confidence": 1.0,
            "is_user_corrected": True,
        }
