"""
LegalEase AI - Intelligent Legal Situation Analyzer
Synthesizes ML Problem Classification, ChromaDB Statutory Retrieval,
BNS-IPC Crosswalk, Legal Gap Detection, and Mathematical Information Quality Scoring.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import date

from app.core.constants import (
    LEGAL_DISCLAIMER_EN,
    LEGAL_DISCLAIMER_HI,
    OFFICIAL_INDIAN_HELPLINES,
)
from app.ml.classifier import get_classifier
from app.rag.retriever import LegalKnowledgeRetriever
from app.rag.crosswalk import BNSIPCCrosswalk
from app.rag.citation_validator import LegalCitationValidator
from app.services.gap_detector import LegalGapDetector
from app.services.uncertainty import UncertaintyDetectionEngine
from app.services.explainability import ExplainableLegalIntelligenceEngine

logger = logging.getLogger(__name__)


# Domain-specific procedural remedies & immediate citizen actions
DOMAIN_PROCEDURAL_ACTIONS: Dict[str, List[Dict[str, str]]] = {
    "CRIMINAL_LAW_BNS": [
        {
            "step": "1. Lodge FIR / e-FIR",
            "action": "Approach the local police station or submit an e-FIR under Section 173(1) of BNSS, 2023. Obtain a free copy of the FIR as guaranteed by law."
        },
        {
            "step": "2. Remedy for Refusal to Register FIR",
            "action": "If the Station House Officer (SHO) refuses, send the complaint in writing by registered post to the Superintendent of Police (SP) under Section 173(4) BNSS."
        },
        {
            "step": "3. Preservation of Evidence",
            "action": "Preserve CCTV footage, medical examination reports (MLC), and witness contact details immediately."
        }
    ],

    "CONSUMER_PROTECTION": [
        {
            "step": "1. Serve Pre-Litigation Legal Notice",
            "action": "Dispatch a formal 15-day grievance notice via email and registered post to the manufacturer/seller demanding replacement or refund."
        },
        {
            "step": "2. National Consumer Helpline (NCH)",
            "action": "Dial 1915 or register a grievance on consumerhelpline.gov.in (often resolves 60% of e-commerce and retail disputes without court filing)."
        },
        {
            "step": "3. File Online via e-Daakhil",
            "action": "If unresolved, lodge a formal consumer complaint before the District Consumer Disputes Redressal Commission via edaakhil.nic.in under Section 35."
        }
    ],

    "CYBER_LAW_IT_ACT": [
        {
            "step": "1. Golden Hour Cyber Freeze (Call 1930)",
            "action": "Dial the National Cybercrime Reporting Helpline 1930 immediately to freeze beneficiary bank accounts before funds are withdrawn."
        },
        {
            "step": "2. Register Cybercrime Portal Complaint",
            "action": "File a formal incident report on cybercrime.gov.in and download the official acknowledgment receipt."
        },
        {
            "step": "3. Formal Bank Dispute (Zero Liability)",
            "action": "Submit a written dispute form with UTR details to your home bank branch within 3 days to invoke RBI's Zero Customer Liability protections."
        }
    ],

    "CHEQUE_BOUNCE_NI_ACT": [
        {
            "step": "1. 30-Day Statutory Notice Limitation",
            "action": "Issue a formal Legal Demand Notice through an Advocate or registered speed post within 30 days of receiving the bank memo."
        },
        {
            "step": "2. 15-Day Payment Window",
            "action": "Allow the drawer a mandatory 15-day statutory cure period from the date of notice receipt to tender payment."
        },
        {
            "step": "3. File Section 138 Magistrate Complaint",
            "action": "Upon expiry of 15 days without payment, file a criminal complaint before the Judicial Magistrate within 30 days."
        }
    ],

    "LABOUR_EMPLOYMENT": [
        {
            "step": "1. Formal Demand Representation",
            "action": "Send a formal demand letter to HR and Company Directors demanding unpaid salary/gratuity within 15 days."
        },
        {
            "step": "2. Labour Commissioner Conciliation",
            "action": "File an application for conciliation before the local Labour Officer / Conciliation Officer under the Industrial Disputes Act."
        },
        {
            "step": "3. EPFO / Gratuity Authority",
            "action": "For PF default or gratuity withholding, file a complaint on epfigms.gov.in or before the Controlling Authority under Payment of Gratuity Act."
        }
    ],

    "FAMILY_MATRIMONIAL": [
        {
            "step": "1. Protection & Emergency Relief",
            "action": "For domestic violence, approach the Protection Officer or Service Provider under PWDVA 2005 or call Women Helpline 1091."
        },
        {
            "step": "2. Interim Maintenance Petition",
            "action": "File a maintenance application under Section 144 BNSS (or Sec 125 CrPC) before the Family Court along with the mandatory Affidavit of Assets."
        },
        {
            "step": "3. Pre-Litigation Mediation",
            "action": "Utilize DLSA (District Legal Services Authority) mediation cells to explore settlement regarding child custody and stridhan."
        }
    ],

    "RTI_GOVERNANCE": [
        {
            "step": "1. Track 30-Day Statutory Timeline",
            "action": "Wait for 30 days from RTI receipt. If no response is received, it constitutes a 'deemed refusal' under Section 7(2)."
        },
        {
            "step": "2. File First Appeal (Section 19(1))",
            "action": "File a First Appeal to the designated First Appellate Authority (FAA) within 30 days from expiry of the response period."
        },
        {
            "step": "3. Second Appeal to Information Commission",
            "action": "If First Appeal is rejected or ignored for 45 days, file a Second Appeal before the Central/State Information Commission under Section 19(3)."
        }
    ],

    "PROPERTY_TENANCY": [
        {
            "step": "1. Issue Notice to Landlord / Tenant",
            "action": "Serve a formal written legal notice detailing breach of tenancy terms and giving 15 days to rectify."
        },
        {
            "step": "2. Police Complaint for Disconnected Utilities",
            "action": "Disconnection of essential water/electricity without court order is illegal under Rent Control Acts; file immediate complaint with police and rent authority."
        },
        {
            "step": "3. Rent Tribunal / Civil Court",
            "action": "Approach the Rent Authority / Rent Tribunal under the applicable Tenancy Act or file a civil recovery suit for security deposit."
        }
    ],

    "MOTOR_VEHICLE_ACCIDENT": [
        {
            "step": "1. Ensure Police Accident FIR & DAR",
            "action": "Ensure police register an FIR and prepare the Detailed Accident Report (DAR) within statutory timelines under MV Act."
        },
        {
            "step": "2. Preserve MLC & Medical Records",
            "action": "Obtain certified copies of Medico-Legal Certificate (MLC), hospitalization bills, and permanent disability certificates."
        },
        {
            "step": "3. File Claim before MACT",
            "action": "File compensation claim before the Motor Accident Claims Tribunal (MACT) having jurisdiction over the accident spot or claimant's residence."
        }
    ],

    "CONSTITUTIONAL_CIVIL_RIGHTS": [
        {
            "step": "1. Representation to Higher Authorities",
            "action": "Submit an urgent written representation demanding immediate stoppage of arbitrary state action."
        },
        {
            "step": "2. State / National Human Rights Commission",
            "action": "File an urgent complaint before the SHRC / NHRC for custodial abuse or human rights violation."
        },
        {
            "step": "3. Writ Petition before High Court",
            "action": "Approach the High Court under Article 226 for Writ of Habeas Corpus, Mandamus, or Quashing of arbitrary administrative orders."
        }
    ]
}


class IntelligentSituationAnalyzer:
    """
    Intelligent Legal Situation Analyzer synthesizing:
    1. Scikit-learn ML Legal Problem Classifier
    2. ChromaDB Persistent Bare Acts Vector Retrieval
    3. BNS-IPC Dual Reference Crosswalk & Savings Provisions
    4. Legal Gap Detection & Interactive Follow-up Questions
    5. Mathematical Information Quality & Uncertainty Scoring
    """

    def __init__(
        self,
        classifier: Optional[Any] = None,
        retriever: Optional[LegalKnowledgeRetriever] = None,
        crosswalk: Optional[BNSIPCCrosswalk] = None,
        validator: Optional[LegalCitationValidator] = None,
    ):
        self.classifier = classifier or get_classifier()
        self.retriever = retriever or LegalKnowledgeRetriever()
        self.crosswalk = crosswalk or BNSIPCCrosswalk()
        self.validator = validator or LegalCitationValidator()

    def analyze_situation(
        self,
        narrative: str,
        incident_date: Optional[str] = None,
        is_continuing_offense: bool = False,
        preferred_language: str = "en",
    ) -> Dict[str, Any]:
        """
        Executes end-to-end analysis of a citizen's legal problem narrative.
        """
        if not narrative or not narrative.strip():
            raise ValueError("Narrative description cannot be empty.")

        # ----------------------------------------------------------------------
        # 1. ML Legal Problem Classification
        # ----------------------------------------------------------------------
        ml_prediction = self.classifier.predict(narrative)
        predicted_domain = ml_prediction["predicted_domain"]
        classification_confidence = ml_prediction["confidence"]

        # ----------------------------------------------------------------------
        # 2. ChromaDB Statutory Vector Retrieval
        # ----------------------------------------------------------------------
        # Retrieve statutory provisions matching the narrative with predicted domain filter
        domain_filter = predicted_domain if predicted_domain in [
            "CRIMINAL_LAW_BNS", "CONSUMER_PROTECTION", "CYBER_LAW_IT_ACT", "RTI_GOVERNANCE", "CHEQUE_BOUNCE_NI_ACT"
        ] else None

        statute_results = self.retriever.search_statutes(
            query=narrative,
            legal_domain=domain_filter,
            top_k=4,
        )

        # If domain filter returned fewer than 2 results, run open search
        if len(statute_results) < 2 and domain_filter:
            statute_results = self.retriever.search_statutes(query=narrative, top_k=4)

        # ----------------------------------------------------------------------
        # 3. BNS-IPC Crosswalk & Temporal Applicability
        # ----------------------------------------------------------------------
        temporal_analysis = None
        if incident_date:
            try:
                temporal_analysis = self.crosswalk.evaluate_temporal_applicability(
                    date_of_incident=incident_date,
                    is_continuing=is_continuing_offense,
                )
            except Exception as e:
                logger.warning(f"Error parsing incident_date {incident_date}: {e}")

        # Format retrieved statutes and check for any historical IPC counterparts
        statutes_with_crosswalk = []
        for s in statute_results:
            meta = s.get("metadata", {})
            act_code = meta.get("act_code", "")
            sec_num = meta.get("section_number", "")

            statute_item = {
                "id": s.get("id"),
                "act_code": act_code,
                "act_title": meta.get("act_title"),
                "section_number": sec_num,
                "section_title": meta.get("section_title"),
                "chapter": meta.get("chapter"),
                "provision_type": meta.get("provision_type"),
                "source_url": meta.get("source_url"),
                "document": s.get("document"),
                "distance": s.get("distance", 0.0),
            }

            # If it's BNS, retrieve historical IPC mapping
            if act_code == "BNS_2023":
                bns_map = self.crosswalk.lookup_by_bns(sec_num)
                if bns_map:
                    statute_item["historical_crosswalk"] = bns_map
            statutes_with_crosswalk.append(statute_item)

        # ----------------------------------------------------------------------
        # 4. Legal Gap Detection & Interactive Follow-up Questions
        # ----------------------------------------------------------------------
        gap_report = LegalGapDetector.detect_gaps(
            text=narrative,
            domain=predicted_domain,
        )

        # ----------------------------------------------------------------------
        # 5. Citation Verification on User Narrative & Retrieved Text
        # ----------------------------------------------------------------------
        citation_report = self.validator.validate_text_citations(narrative)

        # ----------------------------------------------------------------------
        # 6. Corrected Mathematical Information Quality Scoring (S_IQ)
        # S_raw = w_grounding * S_grounding + w_facts * S_facts + w_citations * S_citations - P_contradiction
        # w_grounding = 0.40, w_facts = 0.35, w_citations = 0.25
        # ----------------------------------------------------------------------
        # Grounding score: cosine similarity derived from top retrieved chunk distance
        if statute_results:
            best_distance = statute_results[0].get("distance", 1.0)
            # Distance in cosine space typically in [0, 2]; map to [0, 1]
            s_grounding = max(0.0, 1.0 - (best_distance / 1.5))
        else:
            s_grounding = 0.30

        # Facts score: proportion of statutory ingredients provided
        s_facts = gap_report.get("completeness_ratio", 0.5)

        # Citations score: proportion of valid citations
        if citation_report["total_citations"] > 0:
            s_citations = citation_report.get("citation_grounding_ratio", 0.0)
        else:
            # If citizen did not cite any statutory numbers, neutral grounding baseline
            s_citations = 0.80

        # ----------------------------------------------------------------------
        # 6. Uncertainty, Ambiguity & Contradiction Detection
        # ----------------------------------------------------------------------
        uncertainty_profile = UncertaintyDetectionEngine.analyze_uncertainty(
            narrative=narrative,
            predicted_domain=predicted_domain,
            classification_confidence=classification_confidence,
            top_domains=ml_prediction["top_domains"],
            missing_ingredients=gap_report["missing_ingredients"],
            incident_date=incident_date,
        )

        # Evidence Contradiction penalty from detected contradictions
        contradictions_count = len(uncertainty_profile["detected_contradictions"])
        p_contradiction = round(min(0.30, contradictions_count * 0.10), 4)

        # Statutory element breakdown for the primary retrieved statute
        statute_element_mapping = None
        if statutes_with_crosswalk:
            primary_st = statutes_with_crosswalk[0]
            if primary_st.get("act_code") and primary_st.get("section_number"):
                statute_element_mapping = ExplainableLegalIntelligenceEngine.explain_statute_mapping(
                    narrative=narrative,
                    act_code=primary_st["act_code"],
                    section_number=primary_st["section_number"],
                )

        w_grounding = 0.40
        w_facts = 0.35
        w_citations = 0.25

        s_raw = (
            (w_grounding * s_grounding)
            + (w_facts * s_facts)
            + (w_citations * s_citations)
            - p_contradiction
        )

        # Clamping and normalization [0.0, 1.0]
        s_iq = round(min(1.0, max(0.0, s_raw)), 4)

        # Score stratification badge
        if s_iq >= 0.80:
            quality_badge = "COMPREHENSIVE_QUALITY"
            badge_color = "#10B981"  # Emerald
            quality_summary = "Factual details and statutory grounding are comprehensive. Ready for complaint drafting."
        elif s_iq >= 0.50:
            quality_badge = "MODERATE_QUALITY_GAPS"
            badge_color = "#F59E0B"  # Amber
            quality_summary = "Crucial statutory ingredients are missing. Resolving interactive follow-up questions is recommended."
        else:
            quality_badge = "LOW_QUALITY_INCOMPLETE"
            badge_color = "#EF4444"  # Rose
            quality_summary = "Narrative lacks core factual and legal details. In-person consultation with DLSA or an Advocate is advised."

        # ----------------------------------------------------------------------
        # 7. Procedural Steps & Helpline Recommendations
        # ----------------------------------------------------------------------
        procedural_steps = DOMAIN_PROCEDURAL_ACTIONS.get(predicted_domain, [
            {
                "step": "1. Consult an Advocate",
                "action": "Schedule an in-person consultation with an Advocate registered with the Bar Council."
            },
            {
                "step": "2. District Legal Services Authority",
                "action": "Visit your nearest DLSA for free legal assistance if eligible under Section 12 of Legal Services Authorities Act."
            }
        ])

        disclaimer = (
            LEGAL_DISCLAIMER_HI if preferred_language == "hi" else LEGAL_DISCLAIMER_EN
        )

        return {
            "narrative": narrative,
            "predicted_domain": predicted_domain,
            "classification_confidence": classification_confidence,
            "top_candidate_domains": ml_prediction["top_domains"],
            "applicable_statutes": statutes_with_crosswalk,
            "temporal_applicability": temporal_analysis,
            "legal_gaps": gap_report,
            "citation_verification": citation_report,
            "uncertainty_analysis": uncertainty_profile,
            "statute_element_mapping": statute_element_mapping,
            "information_quality": {
                "score": s_iq,
                "badge": quality_badge,
                "badge_color": badge_color,
                "summary": quality_summary,
                "component_scores": {
                    "statutory_grounding": round(s_grounding, 4),
                    "factual_completeness": round(s_facts, 4),
                    "citation_validity": round(s_citations, 4),
                    "contradiction_penalty": p_contradiction,
                },
            },
            "recommended_actions": procedural_steps,
            "emergency_helplines": OFFICIAL_INDIAN_HELPLINES,
            "statutory_disclaimer": disclaimer,
        }


# Singleton instance
_analyzer_instance: Optional[IntelligentSituationAnalyzer] = None


def get_situation_analyzer() -> IntelligentSituationAnalyzer:
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = IntelligentSituationAnalyzer()
    return _analyzer_instance
