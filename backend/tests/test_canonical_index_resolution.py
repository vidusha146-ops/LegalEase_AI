import pytest
from pathlib import Path

from app.rag.citation_validator import LegalCitationValidator, _resolve_index_path
from app.rag.crosswalk import BNSIPCCrosswalk, _resolve_crosswalk_path


def test_bare_act_index_packaged_and_root_resolution():
    """Verifies that the canonical Bare Act index is successfully resolved and loaded."""
    resolved_path = _resolve_index_path()
    assert resolved_path.exists(), f"Resolved Bare Act index does not exist at {resolved_path}"

    validator = LegalCitationValidator()
    assert validator.is_loaded is True
    assert len(validator.canonical_sections) >= 40
    assert "BNS_2023:303(1)" in validator.canonical_sections
    assert "CONSUMER_PROTECTION_2019:35" in validator.canonical_sections


def test_known_valid_statutory_citations():
    """Verifies that known official statutory citations are recognized and validated."""
    validator = LegalCitationValidator()

    # Theft under BNS
    v1 = validator.validate_citation("BNS_2023", "303(1)")
    assert v1["is_valid"] is True
    assert v1["status"] in ("VERIFIED_STATUTORY_PROVISION", "VERIFIED_PARENT_STATUTORY_PROVISION")

    # Consumer Protection
    v2 = validator.validate_citation("CONSUMER_PROTECTION_2019", "35")
    assert v2["is_valid"] is True

    # IT Act cyber fraud
    v3 = validator.validate_citation("IT_ACT_2000", "66D")
    assert v3["is_valid"] is True

    # Cheque bounce under NI Act
    v4 = validator.validate_citation("NI_ACT_1881", "138")
    assert v4["is_valid"] is True

    # Cheating under historical IPC
    v5 = validator.validate_citation("IPC", "420")
    assert v5["is_valid"] is True


def test_unknown_citations_rejected():
    """Verifies that unknown and fabricated sections are strictly rejected."""
    validator = LegalCitationValidator()

    bad_bns = validator.validate_citation("BNS_2023", "9999")
    assert bad_bns["is_valid"] is False
    assert bad_bns["status"] == "UNVERIFIED_OR_FABRICATED_PROVISION"
    assert "rejection_reason" in bad_bns

    bad_cp = validator.validate_citation("CONSUMER_PROTECTION_2019", "888")
    assert bad_cp["is_valid"] is False
    assert bad_cp["status"] == "UNVERIFIED_OR_FABRICATED_PROVISION"


def test_crosswalk_mappings_load_and_resolve():
    """Verifies that the BNS-IPC crosswalk loads mappings and performs bidirectional translation."""
    resolved_cw_path = _resolve_crosswalk_path()
    assert resolved_cw_path.exists(), f"Resolved Crosswalk path does not exist at {resolved_cw_path}"

    crosswalk = BNSIPCCrosswalk()
    assert crosswalk.is_loaded is True
    assert len(crosswalk.get_all_mappings()) >= 5

    # IPC 378 (Theft definition) -> BNS Section 303(1)
    theft_def = crosswalk.lookup_by_ipc("378")
    assert theft_def is not None
    assert theft_def["matched_role"] == "DEFINITION"
    assert "303(1)" in theft_def["bns_definition"]

    # IPC 379 (Theft punishment) -> BNS Section 303(2)
    theft_pun = crosswalk.lookup_by_ipc("379")
    assert theft_pun is not None
    assert theft_pun["matched_role"] == "PUNISHMENT"
    assert "303(2)" in theft_pun["bns_punishment"]

    # BNS 316(1) (CBT definition) -> IPC Section 405
    cbt_def = crosswalk.lookup_by_bns("316(1)")
    assert cbt_def is not None
    assert "405" in cbt_def["ipc_definition"]

    # Nonexistent section returns None
    assert crosswalk.lookup_by_ipc("9999") is None


def test_missing_knowledge_base_files_diagnosable():
    """
    Verifies that missing knowledge-base files produce explicit, diagnosable states
    rather than silently presenting an empty index as successful verification.
    """
    fake_path = Path("/non_existent_dir_12345/bare_act_index.json")
    unloaded_validator = LegalCitationValidator(index_path=fake_path)

    assert unloaded_validator.is_loaded is False
    assert unloaded_validator.canonical_sections == {}

    # Single citation check must return explicit CANONICAL_INDEX_UNAVAILABLE status
    citation_res = unloaded_validator.validate_citation("BNS_2023", "303(1)")
    assert citation_res["is_valid"] is False
    assert citation_res["status"] == "CANONICAL_INDEX_UNAVAILABLE"
    assert "unavailable" in citation_res["rejection_reason"].lower()

    # Text validation must report explicit error message
    text_res = unloaded_validator.validate_text_citations(
        "Offence committed under Section 303(1) of Bharatiya Nyaya Sanhita."
    )
    assert text_res["total_citations"] == 0
    assert "error" in text_res
    assert "unavailable" in text_res["error"].lower()

    # Crosswalk with missing file must be uninitialized
    fake_cw_path = Path("/non_existent_dir_12345/bns_ipc_crosswalk.json")
    unloaded_crosswalk = BNSIPCCrosswalk(data_path=fake_cw_path)
    assert unloaded_crosswalk.is_loaded is False
    assert unloaded_crosswalk.lookup_by_ipc("378") is None
