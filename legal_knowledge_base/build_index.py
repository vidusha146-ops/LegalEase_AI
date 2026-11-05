import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw_statutes"
INDEX_FILE = BASE_DIR / "bare_act_index.json"
CROSSWALK_FILE = BASE_DIR / "bns_ipc_crosswalk.json"


def build_canonical_index():
    canonical_index = {
        "metadata": {
            "title": "Canonical Index of Verified Indian Central Statutory Provisions",
            "last_updated": "2026-11-04",
            "authority": "Gazette of India, Ministry of Law and Justice",
        },
        "sections": {},
    }

    statute_files = list(RAW_DIR.glob("*.json"))
    print(f"Loading {len(statute_files)} Bare Act files from {RAW_DIR}...")

    total_provisions = 0
    for s_file in statute_files:
        with open(s_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        act_code = data["act_code"]
        act_title = data["act_title"]
        source_url = data["source_url"]
        legal_domain = data["legal_domain"]
        verification_date = data["verification_date"]

        for sec in data["sections"]:
            sec_num = sec["section_number"]
            # Primary key format: "ACT_CODE:SECTION_NUM" (e.g., "BNS_2023:303(1)")
            key = f"{act_code}:{sec_num}".upper()

            entry = {
                "act_code": act_code,
                "act_title": act_title,
                "section_number": sec_num,
                "section_title": sec["section_title"],
                "provision_type": sec["provision_type"],
                "chapter": sec.get("chapter", ""),
                "legal_domain": legal_domain,
                "source_url": source_url,
                "verification_date": verification_date,
                "historical_counterpart": sec.get("historical_counterpart", None),
                "full_text": sec["full_text"],
            }
            canonical_index["sections"][key] = entry
            total_provisions += 1

            # Also index without sub-clause if applicable (e.g. "BNS_2023:303")
            if "(" in sec_num:
                base_num = sec_num.split("(")[0]
                base_key = f"{act_code}:{base_num}".upper()
                if base_key not in canonical_index["sections"]:
                    canonical_index["sections"][base_key] = entry

    # Add historical IPC counterparts from crosswalk so citation verifier can validate them
    if CROSSWALK_FILE.exists():
        with open(CROSSWALK_FILE, "r", encoding="utf-8") as f:
            cw_data = json.load(f)
        for mapping in cw_data["mappings"]:
            ipc_info = mapping["ipc"]
            def_sec = ipc_info["definition_section"].replace("Section ", "").replace(" IPC", "").strip()
            pun_sec = ipc_info["punishment_section"].replace("Section ", "").replace(" IPC", "").strip()

            for sec_str, p_type in [(def_sec, "DEFINITION"), (pun_sec, "PUNISHMENT")]:
                clean_sec = sec_str.split()[0].replace(",", "")
                ipc_key = f"IPC:{clean_sec}".upper()
                if ipc_key not in canonical_index["sections"]:
                    canonical_index["sections"][ipc_key] = {
                        "act_code": "IPC",
                        "act_title": "Indian Penal Code, 1860",
                        "section_number": clean_sec,
                        "section_title": f"{ipc_info['title']} ({p_type.capitalize()})",
                        "provision_type": p_type,
                        "chapter": "Historical Indian Penal Code",
                        "legal_domain": "CRIMINAL_LAW_BNS",
                        "source_url": "https://www.indiacode.nic.in/handle/123456789/2263",
                        "verification_date": "2026-11-04",
                        "bns_counterpart": mapping["bns"]["definition_section" if p_type == "DEFINITION" else "punishment_section"],
                    }

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(canonical_index, f, indent=2, ensure_ascii=False)

    print(f"Successfully compiled canonical index with {len(canonical_index['sections'])} entries to {INDEX_FILE}")
    return len(canonical_index["sections"])


if __name__ == "__main__":
    build_canonical_index()
