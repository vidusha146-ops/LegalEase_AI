import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

CROSSWALK_PATH = Path(__file__).resolve().parent.parent.parent.parent / "legal_knowledge_base" / "bns_ipc_crosswalk.json"


class BNSIPCCrosswalk:
    """
    Bidirectional legal crosswalk mapping between the Indian Penal Code, 1860 (IPC)
    and the Bharatiya Nyaya Sanhita, 2023 (BNS).
    Strictly distinguishes Offence Definitions from Punishment clauses
    and implements Article 20(1) and Section 358 BNS / Section 531 BNSS savings rules.
    """

    def __init__(self, data_path: Optional[Path] = None):
        self.path = data_path or CROSSWALK_PATH
        self.data: Dict[str, Any] = {}
        self._load_crosswalk()

    def _load_crosswalk(self) -> None:
        try:
            if self.path.exists():
                with open(self.path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            else:
                logger.warning(f"Crosswalk file not found at {self.path}")
                self.data = {"mappings": [], "savings_provisions": {}}
        except Exception as e:
            logger.error(f"Error loading crosswalk: {e}")
            self.data = {"mappings": [], "savings_provisions": {}}

    def get_all_mappings(self) -> List[Dict[str, Any]]:
        return self.data.get("mappings", [])

    def lookup_by_ipc(self, ipc_query: str) -> Optional[Dict[str, Any]]:
        """
        Finds the BNS equivalent for an IPC section.
        Handles both section numbers (e.g., '378', '379', '420') and full strings ('Section 420 IPC').
        """
        clean = ipc_query.upper().replace("SECTION", "").replace("SEC.", "").replace("IPC", "").strip()
        for item in self.data.get("mappings", []):
            ipc_def = item["ipc"]["definition_section"].upper()
            ipc_pun = item["ipc"]["punishment_section"].upper()
            if clean in ipc_def or clean in ipc_pun:
                matched_role = "DEFINITION" if clean in ipc_def else "PUNISHMENT"
                return {
                    "matched_query": ipc_query,
                    "matched_role": matched_role,
                    "category": item["offence_category"],
                    "ipc_definition": item["ipc"]["definition_section"],
                    "ipc_punishment": item["ipc"]["punishment_section"],
                    "bns_definition": item["bns"]["definition_section"],
                    "bns_punishment": item["bns"]["punishment_section"],
                    "bns_title": item["bns"]["title"],
                    "key_statutory_innovation": item["bns"].get("key_statutory_innovation", ""),
                    "transitional_rule": (
                        "For offenses committed prior to July 1, 2024, substantive charge lies under "
                        f"{item['ipc']['punishment_section']}. For offenses committed on or after July 1, 2024, "
                        f"charge lies under {item['bns']['punishment_section']}."
                    ),
                }
        return None

    def lookup_by_bns(self, bns_query: str) -> Optional[Dict[str, Any]]:
        """
        Finds the historical IPC equivalent for a BNS section.
        Handles both section numbers (e.g., '303(1)', '303(2)', '318(4)') and strings.
        """
        clean = bns_query.upper().replace("SECTION", "").replace("SEC.", "").replace("BNS", "").strip()
        for item in self.data.get("mappings", []):
            bns_def = item["bns"]["definition_section"].upper()
            bns_pun = item["bns"]["punishment_section"].upper()
            if clean in bns_def or clean in bns_pun:
                matched_role = "DEFINITION" if clean in bns_def else "PUNISHMENT"
                return {
                    "matched_query": bns_query,
                    "matched_role": matched_role,
                    "category": item["offence_category"],
                    "bns_definition": item["bns"]["definition_section"],
                    "bns_punishment": item["bns"]["punishment_section"],
                    "ipc_definition": item["ipc"]["definition_section"],
                    "ipc_punishment": item["ipc"]["punishment_section"],
                    "bns_title": item["bns"]["title"],
                    "key_statutory_innovation": item["bns"].get("key_statutory_innovation", ""),
                    "transitional_rule": (
                        f"BNS {item['bns']['punishment_section']} replaces historical {item['ipc']['punishment_section']} "
                        "for all acts committed on or after July 1, 2024."
                    ),
                }
        return None

    def evaluate_temporal_applicability(
        self, date_of_incident: Optional[str], is_continuing: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluates applicable penal and procedural statutes based on date of occurrence,
        constitutional Article 20(1) safeguards, and Section 358 BNS / Section 531 BNSS savings rules.
        """
        if not date_of_incident:
            return {
                "status": "UNDETERMINED",
                "applicable_regime": "DUAL_ADVISORY",
                "reason": "Date of incident is not specified. Clarification required to determine whether IPC or BNS applies.",
                "substantive_code": "IPC or BNS depending on incident date",
                "procedural_code": "BNSS, 2023",
                "constitutional_note": "Article 20(1) strictly applies the penal law in force at the time of the commission of the act.",
            }

        if is_continuing:
            return {
                "status": "CONTINUING_OFFENCE",
                "applicable_regime": "DUAL_CHARGE",
                "reason": "Offence is continuing in nature spanning before and after July 1, 2024.",
                "substantive_code": "Dual charging: IPC for pre-July 1 acts, BNS for post-July 1 acts",
                "procedural_code": "Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)",
                "constitutional_note": "Continuing conspiracy or harassment permits dual references with specific act dates.",
            }

        try:
            # Simple ISO date comparison (YYYY-MM-DD)
            clean_date = date_of_incident.strip()[:10]
            if clean_date < "2024-07-01":
                return {
                    "status": "HISTORICAL_IPC",
                    "applicable_regime": "IPC_SUBSTANTIVE_BNSS_PROCEDURE",
                    "reason": f"Incident occurred on {clean_date} (Prior to July 1, 2024).",
                    "substantive_code": "Indian Penal Code, 1860 (IPC)",
                    "procedural_code": "Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS for fresh complaints post-July 1)",
                    "savings_clause": "Section 358 of BNS, 2023 & Section 531 of BNSS, 2023",
                    "constitutional_note": "Under Article 20(1) of the Indian Constitution, no ex-post facto penal law can be applied.",
                }
            else:
                return {
                    "status": "MODERN_BNS",
                    "applicable_regime": "BNS_SUBSTANTIVE_BNSS_PROCEDURE",
                    "reason": f"Incident occurred on {clean_date} (On or after July 1, 2024).",
                    "substantive_code": "Bharatiya Nyaya Sanhita, 2023 (BNS)",
                    "procedural_code": "Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)",
                    "savings_clause": "Act No. 45 of 2023 & Act No. 46 of 2023",
                    "constitutional_note": "Full applicability of modern Bharatiya criminal justice enactments.",
                }
        except Exception:
            return {
                "status": "DATE_PARSE_ERROR",
                "applicable_regime": "DUAL_ADVISORY",
                "reason": f"Could not parse incident date: '{date_of_incident}'.",
                "substantive_code": "IPC / BNS dual reference",
                "procedural_code": "BNSS, 2023",
                "constitutional_note": "Standardize date to YYYY-MM-DD for accurate legal determination.",
            }
