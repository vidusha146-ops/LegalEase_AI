import json
from pathlib import Path
import pytest

from app.rag.citation_validator import LegalCitationValidator
from app.rag.crosswalk import BNSIPCCrosswalk
from app.rag.chunker import LegalDocumentChunker
from app.rag.section_identifier import SectionIdentifier
from app.rag.retriever import LegalKnowledgeRetriever
from app.rag.chroma_client import get_chroma_client

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DIR = BASE_DIR / "legal_knowledge_base" / "raw_statutes"
INDEX_FILE = BASE_DIR / "legal_knowledge_base" / "bare_act_index.json"
CROSSWALK_FILE = BASE_DIR / "legal_knowledge_base" / "bns_ipc_crosswalk.json"


def test_raw_statutes_integrity():
    """Verifies that all 7 official Bare Act files exist and contain valid gazette citations."""
    expected_acts = [
        "bns_2023.json",
        "bnss_2023.json",
        "bsa_2023.json",
        "consumer_protection_2019.json",
        "it_act_2000.json",
        "rti_act_2005.json",
        "ni_act_1881.json",
    ]
    for act_filename in expected_acts:
        filepath = RAW_DIR / act_filename
        assert filepath.exists(), f"Missing Bare Act file: {act_filename}"
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["act_code"], f"Missing act_code in {act_filename}"
            assert data["act_title"], f"Missing act_title in {act_filename}"
            assert data["source_url"].startswith("http"), f"Invalid source_url in {act_filename}"
            assert len(data["sections"]) > 0, f"No sections in {act_filename}"


def test_canonical_index_existence():
    """Verifies that the canonical bare_act_index.json is populated with verified sections."""
    assert INDEX_FILE.exists(), "bare_act_index.json does not exist"
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        sections = data.get("sections", {})
        assert len(sections) >= 40, f"Expected at least 40 canonical sections, got {len(sections)}"

        # Verify key statutory provisions exist
        assert "BNS_2023:303(1)" in sections
        assert "BNS_2023:303(2)" in sections
        assert "BNS_2023:318(4)" in sections
        assert "CONSUMER_PROTECTION_2019:35" in sections
        assert "IT_ACT_2000:66D" in sections
        assert "NI_ACT_1881:138" in sections
        assert "RTI_ACT_2005:6(1)" in sections
        assert "IPC:420" in sections


def test_bns_ipc_crosswalk_definitions_vs_punishments():
    """
    Verifies that the BNS-IPC crosswalk correctly differentiates
    between substantive offence definitions and punishment clauses.
    """
    crosswalk = BNSIPCCrosswalk(data_path=CROSSWALK_FILE)

    # 1. Theft: Definition vs Punishment
    theft_def = crosswalk.lookup_by_ipc("Section 378 IPC")
    assert theft_def is not None
    assert "303(1)" in theft_def["bns_definition"]
    assert theft_def["matched_role"] == "DEFINITION"

    theft_pun = crosswalk.lookup_by_ipc("Section 379 IPC")
    assert theft_pun is not None
    assert "303(2)" in theft_pun["bns_punishment"]
    assert theft_pun["matched_role"] == "PUNISHMENT"
    assert "Community service" in theft_pun["key_statutory_innovation"]

    # 2. Cheating: Definition (IPC 415 -> BNS 318(1)) vs Aggravated (IPC 420 -> BNS 318(4))
    cheat_def = crosswalk.lookup_by_ipc("415")
    assert cheat_def is not None
    assert "318(1)" in cheat_def["bns_definition"]

    cheat_agg = crosswalk.lookup_by_ipc("420")
    assert cheat_agg is not None
    assert "318(4)" in cheat_agg["bns_punishment"]

    # 3. Criminal Breach of Trust
    cbt_def = crosswalk.lookup_by_bns("316(1)")
    assert cbt_def is not None
    assert "405" in cbt_def["ipc_definition"]

    cbt_pun = crosswalk.lookup_by_bns("316(2)")
    assert cbt_pun is not None
    assert "406" in cbt_pun["ipc_punishment"]


def test_temporal_applicability_savings_rules():
    """
    Verifies constitutional Article 20(1) date-of-offence routing
    and Section 358 BNS / Section 531 BNSS savings rules.
    """
    crosswalk = BNSIPCCrosswalk(data_path=CROSSWALK_FILE)

    # Pre-July 1, 2024 -> IPC Substantive
    pre_res = crosswalk.evaluate_temporal_applicability("2024-05-10")
    assert pre_res["status"] == "HISTORICAL_IPC"
    assert "Indian Penal Code" in pre_res["substantive_code"]
    assert "Article 20(1)" in pre_res["constitutional_note"]
    assert "Section 358 of BNS" in pre_res["savings_clause"]

    # Post-July 1, 2024 -> BNS Substantive
    post_res = crosswalk.evaluate_temporal_applicability("2024-08-15")
    assert post_res["status"] == "MODERN_BNS"
    assert "Bharatiya Nyaya Sanhita" in post_res["substantive_code"]

    # Continuing Offence
    cont_res = crosswalk.evaluate_temporal_applicability("2024-06-25", is_continuing=True)
    assert cont_res["status"] == "CONTINUING_OFFENCE"
    assert cont_res["applicable_regime"] == "DUAL_CHARGE"


def test_deterministic_citation_validator():
    """
    Verifies that real Indian statutory provisions pass validation
    and fabricated/hallucinated provisions are caught and rejected.
    """
    validator = LegalCitationValidator(index_path=INDEX_FILE)

    # 1. Genuine provisions must PASS
    v1 = validator.validate_citation("BNS_2023", "303(1)")
    assert v1["is_valid"] is True
    assert v1["status"] == "VERIFIED_STATUTORY_PROVISION"
    assert "Theft" in v1["section_title"]

    v2 = validator.validate_citation("CONSUMER_PROTECTION_2019", "35")
    assert v2["is_valid"] is True
    assert "District Commission" in v2["section_title"]

    v3 = validator.validate_citation("IT_ACT_2000", "66D")
    assert v3["is_valid"] is True
    assert "cheating by personation" in v3["section_title"].lower()

    v4 = validator.validate_citation("NI_ACT_1881", "138")
    assert v4["is_valid"] is True
    assert "Dishonour of cheque" in v4["section_title"]

    v5 = validator.validate_citation("IPC", "420")
    assert v5["is_valid"] is True

    # 2. Fabricated / Hallucinated provisions must FAIL
    f1 = validator.validate_citation("BNS_2023", "999")
    assert f1["is_valid"] is False
    assert f1["status"] == "UNVERIFIED_OR_FABRICATED_PROVISION"
    assert "does not exist" in f1["rejection_reason"]

    f2 = validator.validate_citation("IPC", "482B")
    assert f2["is_valid"] is False

    f3 = validator.validate_citation("CONSUMER_PROTECTION_2019", "888")
    assert f3["is_valid"] is False


def test_validate_text_citations_narrative():
    """
    Verifies that the citation validator correctly parses a mixed paragraph
    containing both authentic and fabricated sections.
    """
    validator = LegalCitationValidator(index_path=INDEX_FILE)

    mixed_text = (
        "The complainant alleges cheating under Section 318(4) of Bharatiya Nyaya Sanhita, 2023 "
        "and cyber fraud under Section 66D of Information Technology Act. However, the accused also "
        "invented a fake charge under Section 999 of Bharatiya Nyaya Sanhita and Section 888 of Consumer Protection Act."
    )

    report = validator.validate_text_citations(mixed_text)
    assert report["total_citations"] == 4
    assert report["valid_count"] == 2
    assert report["invalid_count"] == 2
    assert report["citation_grounding_ratio"] == 0.5


def test_chromadb_semantic_and_metadata_retrieval():
    """
    Verifies semantic vector search and metadata-based filtering
    using the persistent ChromaDB collection.
    """
    retriever = LegalKnowledgeRetriever()

    # 1. Semantic query for Theft -> Should retrieve BNS 303
    theft_results = retriever.search_statutes(
        query="theft of movable property taken out of possession",
        top_k=3,
    )
    assert len(theft_results) > 0
    top_theft = theft_results[0]
    assert "303" in top_theft["metadata"]["section_number"]
    assert any("303" in r["metadata"]["section_number"] for r in theft_results)

    # 2. Semantic query for Consumer Grievance -> Should retrieve Consumer Protection Act
    consumer_results = retriever.search_statutes(
        query="purchased defective goods and company refused to refund or replace",
        legal_domain="CONSUMER_PROTECTION",
        top_k=3,
    )
    assert len(consumer_results) > 0
    top_cpa = consumer_results[0]
    assert top_cpa["metadata"]["act_code"] == "CONSUMER_PROTECTION_2019"

    # 3. Exact section lookup
    exact_res = retriever.get_exact_section(act_code="NI_ACT_1881", section_number="138")
    assert len(exact_res) > 0
    assert "Dishonour of cheque" in exact_res[0]["metadata"]["section_title"]
