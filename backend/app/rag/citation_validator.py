import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.rag.section_identifier import SectionIdentifier

logger = logging.getLogger(__name__)

INDEX_PATH = Path(__file__).resolve().parent.parent.parent.parent / "legal_knowledge_base" / "bare_act_index.json"


class LegalCitationValidator:
    """
    Deterministic multi-stage legal citation validation engine.
    Cross-checks all legal citations against the Canonical Gazette Bare Act Index,
    eliminating hallucinated and fabricated statutory sections.
    """

    def __init__(self, index_path: Optional[Path] = None):
        self.path = index_path or INDEX_PATH
        self.canonical_sections: Dict[str, Any] = {}
        self._load_index()

    def _load_index(self) -> None:
        try:
            if self.path.exists():
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.canonical_sections = data.get("sections", {})
            else:
                logger.warning(f"Canonical index not found at {self.path}")
                self.canonical_sections = {}
        except Exception as e:
            logger.error(f"Error loading canonical index: {e}")
            self.canonical_sections = {}

    def validate_citation(self, act_code: str, section_number: str) -> Dict[str, Any]:
        """
        Validates whether a specific section exists in the canonical index for an Act.
        """
        clean_act = act_code.upper().strip()
        clean_sec = section_number.strip()
        key = f"{clean_act}:{clean_sec}".upper()

        # Check exact key
        if key in self.canonical_sections:
            record = self.canonical_sections[key]
            return {
                "is_valid": True,
                "status": "VERIFIED_STATUTORY_PROVISION",
                "act_code": record["act_code"],
                "act_title": record["act_title"],
                "section_number": record["section_number"],
                "section_title": record["section_title"],
                "provision_type": record["provision_type"],
                "source_url": record["source_url"],
                "historical_counterpart": record.get("historical_counterpart"),
                "verification_date": record.get("verification_date", "2026-11-04"),
            }

        # Check base section if sub-clause was requested (e.g. 303 in 303(1))
        if "(" in clean_sec:
            base_sec = clean_sec.split("(")[0]
            base_key = f"{clean_act}:{base_sec}".upper()
            if base_key in self.canonical_sections:
                record = self.canonical_sections[base_key]
                return {
                    "is_valid": True,
                    "status": "VERIFIED_PARENT_STATUTORY_PROVISION",
                    "act_code": record["act_code"],
                    "act_title": record["act_title"],
                    "section_number": record["section_number"],
                    "section_title": record["section_title"],
                    "provision_type": record["provision_type"],
                    "source_url": record["source_url"],
                    "historical_counterpart": record.get("historical_counterpart"),
                    "verification_date": record.get("verification_date", "2026-11-04"),
                }

        return {
            "is_valid": False,
            "status": "UNVERIFIED_OR_FABRICATED_PROVISION",
            "act_code": clean_act,
            "section_number": clean_sec,
            "rejection_reason": (
                f"Statutory provision 'Section {clean_sec}' does not exist in the official "
                f"Gazette Bare Act for {clean_act}."
            ),
        }

    def validate_text_citations(self, text: str) -> Dict[str, Any]:
        """
        Scans a text block for statutory citations, extracts each citation,
        and returns a complete audit validation report.
        """
        if not text:
            return {"total_citations": 0, "valid_count": 0, "invalid_count": 0, "results": []}

        # Robust Statutory citation regex pattern
        pattern = r"(?:Section|Sec\.?|धारा)\s+([0-9]+(?:\([0-9A-Za-z]+\))?[A-Za-z]?)\s*(?:of\s+(?:the\s+)?)?\s*([A-Za-z0-9\s,–-]*?(?:Act|Sanhita|Adhiniyam|Code|IPC|CrPC|BNS|BNSS|BSA))\b"
        matches = re.finditer(pattern, text, re.IGNORECASE)

        results = []
        valid_count = 0
        invalid_count = 0

        for match in matches:
            sec_num = match.group(1).strip()
            raw_act = match.group(2).strip()
            act_code = SectionIdentifier.resolve_act_code(raw_act)

            if not act_code:
                results.append(
                    {
                        "raw_match": match.group(0),
                        "is_valid": False,
                        "status": "UNRECOGNIZED_ACT_NAME",
                        "section_number": sec_num,
                        "raw_act": raw_act,
                        "rejection_reason": f"Could not map '{raw_act}' to an official Indian Central Bare Act.",
                    }
                )
                invalid_count += 1
                continue

            val_res = self.validate_citation(act_code=act_code, section_number=sec_num)
            val_res["raw_match"] = match.group(0)
            if val_res["is_valid"]:
                valid_count += 1
            else:
                invalid_count += 1
            results.append(val_res)

        return {
            "total_citations": len(results),
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "citation_grounding_ratio": (valid_count / len(results)) if results else 1.0,
            "results": results,
        }
