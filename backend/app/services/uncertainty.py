"""
LegalEase AI - Legal Uncertainty & Assumption Detection Engine
Identifies ambiguous phrasing, incomplete legal facts, chronological/statutory
contradictions, and unsupported legal assumptions in citizen narratives.
Communicates uncertainty transparently rather than generating ungrounded conclusions.
"""

import re
from typing import Dict, Any, List, Optional
from datetime import date, datetime


# Vague phrases indicating informational ambiguity
AMBIGUOUS_PATTERNS = [
    (r"\b(?:some|someone|somebody)\s+(?:did\s+something|did\s+wrong|took\s+money)\b", "Vague allegation without specific act or identity of suspect."),
    (r"\b(?:money\s+issue|financial\s+matter|some\s+problem)\b", "Ambiguous grievance description; lacks actionable statutory details."),
    (r"\b(?:huge\s+amount|a\s+lot\s+of\s+money)\b", "Unspecified monetary value; exact transaction figure required for jurisdiction."),
    (r"\b(?:few\s+days\s+ago|recently|sometime\s+back)\b", "Imprecise temporal timestamp; exact incident date required for limitation and Art 20(1) BNS/IPC determination."),
]


class UncertaintyDetectionEngine:
    """
    Analyzes citizen grievances for factual gaps, legal ambiguities,
    factual contradictions, and unsupported legal assumptions.
    """

    @classmethod
    def analyze_uncertainty(
        cls,
        narrative: str,
        predicted_domain: str,
        classification_confidence: float,
        top_domains: List[Dict[str, Any]],
        missing_ingredients: List[Dict[str, Any]],
        incident_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Synthesizes ambiguity, contradiction, and assumption analysis.
        Returns an uncertainty profile and plain-language cautionary advisories.
        """
        ambiguities = cls._detect_ambiguities(narrative, top_domains)
        contradictions = cls._detect_contradictions(narrative, incident_date)
        assumptions = cls._detect_unsupported_assumptions(narrative, predicted_domain)

        # Compute uncertainty metric [0.0 (certain) to 1.0 (highly uncertain)]
        uncertainty_factors = 0.0

        # Confidence penalty
        if classification_confidence < 0.25:
            uncertainty_factors += 0.30
        elif classification_confidence < 0.40:
            uncertainty_factors += 0.15

        # Ambiguity penalty
        if len(ambiguities) > 0:
            uncertainty_factors += min(0.30, len(ambiguities) * 0.10)

        # Missing statutory facts penalty
        if len(missing_ingredients) >= 3:
            uncertainty_factors += 0.25
        elif len(missing_ingredients) > 0:
            uncertainty_factors += 0.10

        # Contradictions penalty
        if len(contradictions) > 0:
            uncertainty_factors += 0.25

        uncertainty_score = round(min(1.0, max(0.0, uncertainty_factors)), 4)

        if uncertainty_score >= 0.60:
            uncertainty_level = "HIGH_UNCERTAINTY"
            guidance = (
                "High informational uncertainty detected: Core statutory ingredients or timelines "
                "are missing or ambiguous. Any legal remedy suggested at this stage is strictly preliminary. "
                "Resolving follow-up questions or consulting an Advocate / DLSA is advised."
            )
        elif uncertainty_score >= 0.30:
            uncertainty_level = "MODERATE_UNCERTAINTY"
            guidance = (
                "Moderate uncertainty: General legal domain is identified, but specific factual details "
                "(dates, notices, jurisdiction) remain unclarified. Proceeding with complaint drafting requires "
                "addressing the detected gaps."
            )
        else:
            uncertainty_level = "LOW_UNCERTAINTY"
            guidance = (
                "Low uncertainty: Sufficient factual clarity provided to ascertain applicable statutory provisions "
                "and procedural steps with high legal groundability."
            )

        return {
            "uncertainty_score": uncertainty_score,
            "uncertainty_level": uncertainty_level,
            "communicated_advisory": guidance,
            "detected_ambiguities": ambiguities,
            "detected_contradictions": contradictions,
            "unsupported_assumptions": assumptions,
        }

    @classmethod
    def _detect_ambiguities(
        cls,
        narrative: str,
        top_domains: List[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        """Identifies phrasing ambiguity and competing legal domain overlaps."""
        findings = []

        # Check for textual ambiguity patterns
        for pattern, explanation in AMBIGUOUS_PATTERNS:
            if re.search(pattern, narrative, re.IGNORECASE):
                findings.append({
                    "type": "VAGUE_PHRASING",
                    "issue": explanation,
                })

        # Check for competing domain ambiguity
        if len(top_domains) >= 2:
            top_diff = abs(top_domains[0].get("confidence", 0) - top_domains[1].get("confidence", 0))
            if top_diff < 0.04:
                d1 = top_domains[0].get("domain", "").replace("_", " ")
                d2 = top_domains[1].get("domain", "").replace("_", " ")
                findings.append({
                    "type": "COMPETING_LEGAL_DOMAINS",
                    "issue": f"Facts overlap equally between '{d1}' and '{d2}'. Specific transactional proof will determine the forum.",
                })

        return findings

    @classmethod
    def _detect_contradictions(
        cls,
        narrative: str,
        incident_date: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Identifies chronological or statutory contradictions."""
        contradictions = []

        if incident_date:
            try:
                inc_dt = date.fromisoformat(incident_date.strip()[:10])
                today = date.today()
                if inc_dt > today:
                    contradictions.append({
                        "type": "FUTURE_DATE_INVERSION",
                        "issue": f"Date of incident ({inc_dt}) cannot be in the future relative to current date ({today}).",
                    })

                # Article 20(1) statutory mismatch
                if inc_dt < date(2024, 7, 1):
                    if re.search(r"\b(?:Bharatiya Nyaya Sanhita|BNS|BNSS)\b", narrative, re.IGNORECASE):
                        contradictions.append({
                            "type": "STATUTORY_TEMPORAL_MISMATCH",
                            "issue": (
                                f"Incident occurred on {inc_dt} (prior to July 1, 2024), but BNS is referenced. "
                                "Under Article 20(1) of the Indian Constitution, substantive penal law must be IPC 1860."
                            ),
                        })
            except Exception:
                pass

        return contradictions

    @classmethod
    def _detect_unsupported_assumptions(
        cls,
        narrative: str,
        domain: str,
    ) -> List[Dict[str, str]]:
        """Flags citizen assumptions not substantiated by required statutory prerequisites."""
        assumptions = []

        lower = narrative.lower()

        if domain == "CHEQUE_BOUNCE_NI_ACT":
            if "jail" in lower or "arrest" in lower or "police" in lower:
                if "15 days" not in lower and "notice" not in lower:
                    assumptions.append({
                        "assumption": "Immediate police arrest for bounced cheque.",
                        "correction": "Section 138 of NI Act is a complaint-based summon trial before a Magistrate. Police do not register FIRs for simple cheque bounce without prior 15-day statutory notice default.",
                    })

        elif domain == "CONSUMER_PROTECTION":
            if "police" in lower or "fir" in lower:
                assumptions.append({
                    "assumption": "Filing police FIR for consumer deficiency or refund dispute.",
                    "correction": "Defective goods or delayed refunds are civil consumer disputes redressable before the District Consumer Commission under Section 35, not criminal police offenses unless deliberate cheating is proven.",
                })

        elif domain == "CRIMINAL_LAW_BNS":
            if "fir" in lower and ("refused" in lower or "not registered" in lower):
                assumptions.append({
                    "assumption": "Inability to proceed after local police station refuses FIR.",
                    "correction": "Citizens have statutory remedies under Section 173(4) BNSS (petition to Superintendent of Police) and Section 175(3) BNSS (application to Judicial Magistrate).",
                })

        return assumptions
