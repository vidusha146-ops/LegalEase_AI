"""
LegalEase AI - Evidence-to-Legal-Fact Mapping Engine (Phase 5)
Maps verified documentary evidence to statutory elements (actus reus, mens rea, statutory prerequisites)
and elevates Information Quality and Factual Groundability scores ($S_{IQ}$).
"""

from typing import Dict, Any, List, Optional
from app.services.explainability import (
    ExplainableLegalIntelligenceEngine,
    STATUTORY_ELEMENT_DECOMPOSITIONS,
)


# Statutory element to evidence category correlation
ELEMENT_EVIDENCE_MAP = {
    # NI Act 138
    "DRAWN_ON_ACCOUNT": ["BANK_RECORD"],
    "LEGALLY_ENFORCEABLE_DEBT": ["INVOICE_BILL", "AGREEMENT_CONTRACT", "BANK_RECORD"],
    "BANK_DISHONOUR": ["BANK_RECORD"],
    "DEMAND_NOTICE": ["LEGAL_NOTICE", "EMAIL_CORRESPONDENCE"],
    "FAILURE_TO_PAY_15_DAYS": ["LEGAL_NOTICE", "BANK_RECORD"],

    # Consumer Protection Act 2(11)
    "IMPERFECTION_SHORTCOMING": ["OTHER_EVIDENCE", "EMAIL_CORRESPONDENCE"],
    "CONTRACTUAL_STATUTORY_OBLIGATION": ["INVOICE_BILL", "AGREEMENT_CONTRACT"],
    "REFUSAL_TO_RECTIFY": ["EMAIL_CORRESPONDENCE", "LEGAL_NOTICE"],

    # BNS 303(1) (Theft)
    "MOVABLE_PROPERTY": ["INVOICE_BILL", "OTHER_EVIDENCE"],
    "POSSESSION_OF_ANOTHER": ["AGREEMENT_CONTRACT", "POLICE_COMPLAINT_FIR"],
    "WITHOUT_CONSENT": ["POLICE_COMPLAINT_FIR"],
    "DISHONEST_INTENTION": ["POLICE_COMPLAINT_FIR"],
    "ACT_OF_MOVING": ["POLICE_COMPLAINT_FIR"],

    # BNS 318(4) (Cheating)
    "DECEPTION_INDUCEMENT": ["EMAIL_CORRESPONDENCE", "AGREEMENT_CONTRACT", "POLICE_COMPLAINT_FIR"],
    "DELIVERY_OF_PROPERTY": ["BANK_RECORD", "INVOICE_BILL"],
    "WRONGFUL_LOSS": ["BANK_RECORD", "POLICE_COMPLAINT_FIR"],

    # IT Act 66D
    "COMPUTER_RESOURCE_USED": ["EMAIL_CORRESPONDENCE", "BANK_RECORD", "OTHER_EVIDENCE"],
    "PERSONATION_DECEPTION": ["EMAIL_CORRESPONDENCE", "POLICE_COMPLAINT_FIR"],
    "UNAUTHORIZED_TRANSFER": ["BANK_RECORD"],
}


class EvidenceToLegalFactMapper:
    """
    Connects uploaded and verified documents to elemental statutory requirements,
    updating the Explainable AI breakdown and dynamically upgrading evidence confidence.
    """

    @classmethod
    def map_evidence_to_statute(
        cls,
        narrative: str,
        act_code: str,
        section_number: str,
        uploaded_documents: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Decomposes the statute and correlates elements not only with narrative keywords
        but with authentic uploaded document categories.
        """
        base_explanation = ExplainableLegalIntelligenceEngine.explain_statute_mapping(
            narrative=narrative,
            act_code=act_code,
            section_number=section_number,
        )

        # Index uploaded documents by category
        doc_categories = set(d.get("category", "") for d in uploaded_documents)
        doc_map_by_category = {}
        for d in uploaded_documents:
            cat = d.get("category", "")
            if cat not in doc_map_by_category:
                doc_map_by_category[cat] = d.get("filename", "Evidence Document")

        enhanced_elements = []
        document_substantiated_count = 0

        for elem in base_explanation["elements_breakdown"]:
            elem_id = elem["id"]
            required_doc_types = ELEMENT_EVIDENCE_MAP.get(elem_id, [])

            # Check if any uploaded document satisfies this element
            matching_docs = [cat for cat in required_doc_types if cat in doc_categories]
            if matching_docs:
                document_substantiated_count += 1
                matched_filename = doc_map_by_category.get(matching_docs[0], "Uploaded Document")
                elem["substantiated_by_document"] = True
                elem["supporting_document"] = matched_filename
                elem["evidence_verification_status"] = "VERIFIED_BY_DOCUMENTARY_PROOF"
                # If element was not fulfilled by narrative alone, document fulfills it!
                if not elem["fulfilled"]:
                    elem["fulfilled"] = True
                    elem["evidence_excerpt"] = f"Documentary evidence verified: {matched_filename}"
                    elem["explanation"] = f"Substantiated by verified {matching_docs[0]} upload ({matched_filename})."
            else:
                elem["substantiated_by_document"] = False
                elem["supporting_document"] = None
                elem["evidence_verification_status"] = (
                    "PENDING_DOCUMENTARY_UPLOAD" if not elem["fulfilled"] else "ORAL_CLAIM_UNVERIFIED_BY_DOC"
                )

            enhanced_elements.append(elem)

        total_elements = len(enhanced_elements)
        fulfilled_count = sum(1 for e in enhanced_elements if e["fulfilled"])
        new_ratio = round(fulfilled_count / total_elements, 4) if total_elements > 0 else 0.0

        base_explanation["fulfilled_elements"] = fulfilled_count
        base_explanation["unfulfilled_elements"] = total_elements - fulfilled_count
        base_explanation["fulfillment_ratio"] = new_ratio
        base_explanation["elements_breakdown"] = enhanced_elements
        base_explanation["document_substantiated_count"] = document_substantiated_count

        return base_explanation
