import re
from typing import Dict, Any, Optional, Tuple

ACT_ALIASES = {
    # Bharatiya Nyaya Sanhita
    "BNS": "BNS_2023",
    "BHARATIYA NYAYA SANHITA": "BNS_2023",
    "BNS 2023": "BNS_2023",
    # Indian Penal Code
    "IPC": "IPC",
    "INDIAN PENAL CODE": "IPC",
    # BNSS
    "BNSS": "BNSS_2023",
    "BHARATIYA NAGARIK SURAKSHA SANHITA": "BNSS_2023",
    "CRPC": "CRPC",
    "CODE OF CRIMINAL PROCEDURE": "CRPC",
    # BSA / Evidence
    "BSA": "BSA_2023",
    "BHARATIYA SAKSHYA ADHINIYAM": "BSA_2023",
    "IEA": "IEA",
    "INDIAN EVIDENCE ACT": "IEA",
    # Consumer Protection
    "CONSUMER PROTECTION ACT": "CONSUMER_PROTECTION_2019",
    "CPA": "CONSUMER_PROTECTION_2019",
    "COPRA": "CONSUMER_PROTECTION_2019",
    # Information Technology
    "IT ACT": "IT_ACT_2000",
    "INFORMATION TECHNOLOGY ACT": "IT_ACT_2000",
    # RTI
    "RTI": "RTI_ACT_2005",
    "RTI ACT": "RTI_ACT_2005",
    "RIGHT TO INFORMATION ACT": "RTI_ACT_2005",
    # NI Act
    "NI ACT": "NI_ACT_1881",
    "NEGOTIABLE INSTRUMENTS ACT": "NI_ACT_1881",
}


class SectionIdentifier:
    """
    Parses and standardizes statutory references, resolving act aliases
    and identifying provision classifications (Definition vs Punishment).
    """

    @classmethod
    def resolve_act_code(cls, act_name: str) -> Optional[str]:
        if not act_name:
            return None
        cleaned = act_name.upper().strip()
        # Direct lookup
        if cleaned in ACT_ALIASES:
            return ACT_ALIASES[cleaned]
        # Partial pattern search
        for alias, code in ACT_ALIASES.items():
            if alias in cleaned:
                return code
        return None

    @classmethod
    def parse_citation(cls, citation_str: str) -> Optional[Dict[str, Any]]:
        """
        Parses a statutory string such as:
        - "Section 303(1) of Bharatiya Nyaya Sanhita, 2023"
        - "Sec 420 IPC"
        - "Section 35 Consumer Protection Act"
        - "Section 66D IT Act"
        - "Section 138 NI Act"
        """
        if not citation_str:
            return None

        # Regex for Section Number + Act
        pattern = r"(?:Section|Sec\.?|धारा)\s+([0-9]+(?:\([0-9A-Za-z]+\))?[A-Za-z]?)\s+(?:of\s+(?:the\s+)?)?([A-Za-z0-9\s,–-]+)"
        match = re.search(pattern, citation_str, re.IGNORECASE)
        if not match:
            return None

        sec_num = match.group(1).strip()
        raw_act = match.group(2).strip()
        act_code = cls.resolve_act_code(raw_act)

        if not act_code:
            return None

        return {
            "raw_citation": citation_str.strip(),
            "act_code": act_code,
            "section_number": sec_num,
            "canonical_key": f"{act_code}:{sec_num}".upper(),
        }

    @classmethod
    def classify_provision_type(cls, section_title: str, full_text: str) -> str:
        """Determines whether a section is a Definition, Punishment, Procedural, or Savings rule."""
        combined = f"{section_title} {full_text}".lower()
        if "repeal and savings" in combined or "repealed" in combined:
            return "TRANSITIONAL_SAVINGS"
        if "shall be punished with" in combined or "punishment for" in combined or "punishable with" in combined:
            if "whoever" in combined and "is said to" in combined and "shall be punished" not in section_title.lower():
                return "AGGRAVATED_OFFENCE"
            return "PUNISHMENT"
        if "is said to" in combined or "means any" in combined or "definition" in section_title.lower() or "defined" in combined:
            return "DEFINITION"
        if "complaint shall be" in combined or "jurisdiction" in combined or "procedure" in combined:
            return "PROCEDURAL"
        if "relief" in combined or "compensation" in combined or "order to the opposite party" in combined:
            return "REMEDIAL"
        return "GENERAL_STATUTORY"
