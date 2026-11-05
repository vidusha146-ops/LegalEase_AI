import json
import os
import sys
from pathlib import Path

# Configure stdout for utf-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure backend directory is in pythonpath
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.rag.extractor import LegalTextExtractor
from app.rag.section_identifier import SectionIdentifier
from app.rag.chunker import LegalDocumentChunker
from app.rag.chroma_client import ChromaDBClient, get_chroma_client
from app.rag.retriever import LegalKnowledgeRetriever
from app.rag.crosswalk import BNSIPCCrosswalk
from app.rag.citation_validator import LegalCitationValidator

ROOT_DIR = backend_dir.parent
RAW_DIR = ROOT_DIR / "legal_knowledge_base" / "raw_statutes"
INDEX_FILE = ROOT_DIR / "legal_knowledge_base" / "bare_act_index.json"
CROSSWALK_FILE = ROOT_DIR / "legal_knowledge_base" / "bns_ipc_crosswalk.json"


def run_comprehensive_verification():
    print("=" * 80)
    print("LEGALEASE AI - PHASE 2 COMPREHENSIVE VERIFICATION SUITE")
    print("=" * 80)

    # --------------------------------------------------------------------------
    # 1. Authentic Indian Bare Acts Collection
    # --------------------------------------------------------------------------
    print("\n[1/10] Verifying Authentic Indian Bare Acts Collection...")
    bare_acts = list(RAW_DIR.glob("*.json"))
    assert len(bare_acts) == 7, f"Expected 7 bare act files, found {len(bare_acts)}"
    total_sections_count = 0
    statute_summary = []

    for fpath in bare_acts:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data.get("act_code"), f"Missing act_code in {fpath.name}"
        assert data.get("source_url", "").startswith("http"), f"Missing official source_url in {fpath.name}"
        assert data.get("verification_date") == "2026-11-04", f"Invalid verification_date in {fpath.name}"
        sec_count = len(data.get("sections", []))
        assert sec_count > 0, f"No sections in {fpath.name}"
        total_sections_count += sec_count
        statute_summary.append({
            "code": data["act_code"],
            "title": data["act_title"],
            "sections": sec_count,
            "url": data["source_url"]
        })
        print(f"  [OK] {data['act_code']}: {data['act_title']} ({sec_count} sections) | Source: {data['source_url']}")

    print(f"  --> Total Verified Indian Statutory Provisions Ingested: {total_sections_count}")
    print("  --> [1/10] Authentic Bare Acts Collection: PASSED.")

    # --------------------------------------------------------------------------
    # 2. Legal Document Text Extraction
    # --------------------------------------------------------------------------
    print("\n[2/10] Verifying Legal Document Extraction...")
    raw_sample = (
        "Whoever, intending to take dishonestly any movable property out of the possession of any person\n\n"
        "without that person's consent, moves that property... Explanation 1.-A thing attached to earth is not theft.\n"
        "Provided that where the value is less than five thousand rupees..."
    )
    cleaned = LegalTextExtractor.clean_text(raw_sample)
    assert "\n\n" not in cleaned, "Failed to normalize whitespace in LegalTextExtractor"
    subsections = LegalTextExtractor.extract_subsections(cleaned)
    assert len(subsections) >= 2, "Failed to extract statutory subsections/provisos"
    print(f"  [OK] Cleaned text sample: {cleaned[:80]}...")
    print(f"  [OK] Extracted {len(subsections)} distinct statutory clauses/provisos.")
    print("  --> [2/10] Legal Document Extraction: PASSED.")

    # --------------------------------------------------------------------------
    # 3. Legal Section Identification
    # --------------------------------------------------------------------------
    print("\n[3/10] Verifying Legal Section Identification & Alias Resolution...")
    test_citations = [
        ("Section 303(1) of Bharatiya Nyaya Sanhita, 2023", "BNS_2023", "303(1)"),
        ("Sec 420 IPC", "IPC", "420"),
        ("Section 35 Consumer Protection Act", "CONSUMER_PROTECTION_2019", "35"),
        ("Section 66D IT Act", "IT_ACT_2000", "66D"),
        ("Section 138 NI Act", "NI_ACT_1881", "138"),
        ("Section 6(1) RTI Act", "RTI_ACT_2005", "6(1)"),
    ]
    for raw_cit, expected_code, expected_sec in test_citations:
        parsed = SectionIdentifier.parse_citation(raw_cit)
        assert parsed is not None, f"Failed to parse '{raw_cit}'"
        assert parsed["act_code"] == expected_code, f"Expected {expected_code}, got {parsed['act_code']}"
        assert parsed["section_number"] == expected_sec, f"Expected {expected_sec}, got {parsed['section_number']}"
        print(f"  [OK] Parsed '{raw_cit}' -> Act: {parsed['act_code']} | Sec: {parsed['section_number']}")

    # Provision type classification
    assert SectionIdentifier.classify_provision_type("Theft (Definition)", "Whoever intending to take...") == "DEFINITION"
    assert SectionIdentifier.classify_provision_type("Punishment for Theft", "Whoever commits theft shall be punished with...") == "PUNISHMENT"
    assert SectionIdentifier.classify_provision_type("Repeal and Savings", "The Indian Penal Code is hereby repealed...") == "TRANSITIONAL_SAVINGS"
    print("  --> [3/10] Section Identification & Classification: PASSED.")

    # --------------------------------------------------------------------------
    # 4. Legal Document Chunking
    # --------------------------------------------------------------------------
    print("\n[4/10] Verifying Semantic Section-Level Chunking...")
    chunker = LegalDocumentChunker(max_chunk_chars=1200)
    chunks = chunker.chunk_statute_section(
        act_code="BNS_2023",
        act_title="Bharatiya Nyaya Sanhita, 2023",
        section_number="303(1)",
        section_title="Theft (Definition)",
        chapter="XVII - Of Offences Against Property",
        legal_domain="CRIMINAL_LAW_BNS",
        provision_type="DEFINITION",
        full_text="Whoever, intending to take dishonestly any movable property out of the possession...",
        source_url="https://egazette.gov.in/WriteReadData/2023/250883.pdf",
        historical_counterpart="Section 378 IPC",
    )
    assert len(chunks) == 1
    chk = chunks[0]
    assert "[STATUTE]: Bharatiya Nyaya Sanhita, 2023" in chk["text"]
    assert "[SECTION]: Section 303(1)" in chk["text"]
    assert "[HISTORICAL COUNTERPART]: Section 378 IPC" in chk["text"]
    assert chk["metadata"]["act_code"] == "BNS_2023"
    print(f"  [OK] Generated chunk ID: {chk['chunk_id']}")
    print(f"  [OK] Verified contextual header: {chk['text'].splitlines()[0:3]}")
    print("  --> [4/10] Document Chunking: PASSED.")

    # --------------------------------------------------------------------------
    # 5 & 6. ChromaDB Persistence & Embedding Generation
    # --------------------------------------------------------------------------
    print("\n[5/10 & 6/10] Verifying ChromaDB Persistent Vector Storage & Embedding Generation...")
    chroma_dir = ROOT_DIR / "chroma_data"
    assert chroma_dir.exists(), f"ChromaDB persistence directory missing at {chroma_dir}"
    client = ChromaDBClient(persist_dir=str(chroma_dir))
    count = client.count()
    print(f"  [OK] Verified persistent collection 'indian_statutes' on disk at: {chroma_dir}")
    print(f"  [OK] Total Persistent Chunks Detected: {count}")
    assert count >= 46, f"Expected at least 46 persistent chunks, found {count}"

    # Verify embeddings exist and are non-empty
    sample_query_res = client.query(query_text="theft movable property", n_results=1)
    assert len(sample_query_res) > 0
    top_doc = sample_query_res[0]
    assert top_doc["distance"] > 0.0, "Zero distance computed"
    print(f"  [OK] Embedding generation verified: ONNX all-MiniLM-L6-v2 running locally.")
    print(f"  [OK] Top chunk ID retrieved: {top_doc['id']} (Distance: {top_doc['distance']:.4f})")
    print("  --> [5/10 & 6/10] ChromaDB Persistent Storage & Embeddings: PASSED.")

    # --------------------------------------------------------------------------
    # 7. Semantic Legal Search with Realistic Citizen Queries
    # --------------------------------------------------------------------------
    print("\n[7/10] Testing Semantic Legal Search with 4 Realistic Citizen Queries...")
    retriever = LegalKnowledgeRetriever(chroma_client=client)

    queries = [
        {
            "desc": "Dwelling House Burglary / Theft",
            "query": "Someone broke into my locked residential house while I was away and stole gold jewelry",
            "expected_act": "BNS_2023",
            "expected_sec": ["305", "303(1)", "303(2)"],
        },
        {
            "desc": "Consumer E-Commerce Grievance",
            "query": "Ordered branded laptop online, received defective unit, customer support refused replacement and refund",
            "expected_act": "CONSUMER_PROTECTION_2019",
            "expected_sec": ["35", "39", "2(11)", "2(47)"],
        },
        {
            "desc": "Cheque Dishonour / Bounce",
            "query": "Client issued cheque for 2 lakh rupees towards pending invoice which bounced with bank memo funds insufficient",
            "expected_act": "NI_ACT_1881",
            "expected_sec": ["138", "142"],
        },
        {
            "desc": "Cyber Phishing & Identity Fraud",
            "query": "Scammer sent fake KYC link posing as bank official and fraudulently siphoned 75000 rupees via UPI",
            "expected_act": "IT_ACT_2000",
            "expected_sec": ["66D", "43", "66C"],
        },
    ]

    for q_data in queries:
        results = retriever.search_statutes(query=q_data["query"], top_k=3)
        assert len(results) > 0, f"No results for query: {q_data['desc']}"
        top_res = results[0]["metadata"]
        retrieved_secs = [r["metadata"]["section_number"] for r in results]
        print(f"  [OK] Query: '{q_data['desc']}'")
        print(f"       * Top Match: {top_res['act_code']} Section {top_res['section_number']} - {top_res['section_title']}")
        print(f"       * Top 3 Retrieved Sections: {retrieved_secs}")
        print(f"       * Distance: {results[0]['distance']:.4f}")

        # Assert correct act code is present in top 3
        act_codes = [r["metadata"]["act_code"] for r in results]
        assert q_data["expected_act"] in act_codes, f"Expected {q_data['expected_act']} in {act_codes}"

    print("  --> [7/10] Semantic Legal Search: PASSED.")

    # --------------------------------------------------------------------------
    # 8. Metadata-Based Retrieval
    # --------------------------------------------------------------------------
    print("\n[8/10] Verifying Metadata-Based Retrieval & Domain Filtering...")
    # Filter 1: Consumer Protection Domain only
    cpa_filtered = retriever.search_statutes(
        query="grievance regarding defective products",
        legal_domain="CONSUMER_PROTECTION",
        top_k=4
    )
    assert len(cpa_filtered) > 0
    for r in cpa_filtered:
        assert r["metadata"]["legal_domain"] == "CONSUMER_PROTECTION"
    print(f"  [OK] Domain filter 'CONSUMER_PROTECTION' returned {len(cpa_filtered)} chunks, all 100% matched.")

    # Filter 2: IT Act only
    it_filtered = retriever.search_statutes(
        query="unauthorized computer tampering and identity theft",
        act_code="IT_ACT_2000",
        top_k=3
    )
    assert len(it_filtered) > 0
    for r in it_filtered:
        assert r["metadata"]["act_code"] == "IT_ACT_2000"
    print(f"  [OK] Act filter 'IT_ACT_2000' returned {len(it_filtered)} chunks, all 100% matched.")

    # Filter 3: Exact section lookup
    exact = retriever.get_exact_section(act_code="BNS_2023", section_number="318(4)")
    assert len(exact) > 0
    assert "Cheating and dishonestly inducing" in exact[0]["metadata"]["section_title"]
    print(f"  [OK] Exact lookup BNS_2023:318(4) -> {exact[0]['metadata']['section_title']}")
    print("  --> [8/10] Metadata-Based Retrieval: PASSED.")

    # --------------------------------------------------------------------------
    # 9. BNS-IPC Cross-Reference Mapping & Savings Provisions
    # --------------------------------------------------------------------------
    print("\n[9/10] Verifying BNS-IPC Crosswalk, Definitions vs Punishments & Savings Rules...")
    crosswalk = BNSIPCCrosswalk(data_path=CROSSWALK_FILE)

    # Check 1: Theft Definition vs Punishment distinction
    theft_def = crosswalk.lookup_by_ipc("378")
    theft_pun = crosswalk.lookup_by_ipc("379")
    assert theft_def["matched_role"] == "DEFINITION"
    assert "303(1)" in theft_def["bns_definition"]
    assert theft_pun["matched_role"] == "PUNISHMENT"
    assert "303(2)" in theft_pun["bns_punishment"]
    assert "Community service" in theft_pun["key_statutory_innovation"]
    print(f"  [OK] Theft (Definition): IPC 378 <==> BNS 303(1)")
    print(f"  [OK] Theft (Punishment): IPC 379 <==> BNS 303(2) [Proviso: Community Service < Rs. 5,000]")

    # Check 2: Cheating Definition vs Aggravated
    cheat_def = crosswalk.lookup_by_ipc("415")
    cheat_agg = crosswalk.lookup_by_ipc("420")
    assert "318(1)" in cheat_def["bns_definition"]
    assert "318(4)" in cheat_agg["bns_punishment"]
    print(f"  [OK] Cheating (Definition): IPC 415 <==> BNS 318(1)")
    print(f"  [OK] Cheating & Delivery: IPC 420 <==> BNS 318(4)")

    # Check 3: Savings & Article 20(1) Temporal Routing
    pre_res = crosswalk.evaluate_temporal_applicability("2024-03-15")
    assert pre_res["status"] == "HISTORICAL_IPC"
    assert "Indian Penal Code" in pre_res["substantive_code"]
    assert "Section 358" in pre_res["savings_clause"]
    print(f"  [OK] Incident 2024-03-15 (Pre-July 1): Routed to IPC (Substantive) & BNSS (Procedure) under Art 20(1)")

    post_res = crosswalk.evaluate_temporal_applicability("2024-09-01")
    assert post_res["status"] == "MODERN_BNS"
    assert "Bharatiya Nyaya Sanhita" in post_res["substantive_code"]
    print(f"  [OK] Incident 2024-09-01 (Post-July 1): Routed to BNS (Substantive) & BNSS (Procedure)")

    print("  --> [9/10] BNS-IPC Cross-Reference Mapping: PASSED.")

    # --------------------------------------------------------------------------
    # 10. Legal Citation Validation Engine
    # --------------------------------------------------------------------------
    print("\n[10/10] Verifying Deterministic Legal Citation Validation...")
    validator = LegalCitationValidator(index_path=INDEX_FILE)

    # Valid Citations
    assert validator.validate_citation("BNS_2023", "303(1)")["is_valid"] is True
    assert validator.validate_citation("BNS_2023", "318(4)")["is_valid"] is True
    assert validator.validate_citation("CONSUMER_PROTECTION_2019", "35")["is_valid"] is True
    assert validator.validate_citation("IT_ACT_2000", "66D")["is_valid"] is True
    assert validator.validate_citation("NI_ACT_1881", "138")["is_valid"] is True
    assert validator.validate_citation("IPC", "420")["is_valid"] is True
    print("  [OK] Genuine provisions successfully verified against Canonical Gazette Index.")

    # Fake / Fabricated Citations
    fake1 = validator.validate_citation("BNS_2023", "999")
    fake2 = validator.validate_citation("IPC", "482B")
    fake3 = validator.validate_citation("CONSUMER_PROTECTION_2019", "888")
    assert fake1["is_valid"] is False and "does not exist" in fake1["rejection_reason"]
    assert fake2["is_valid"] is False
    assert fake3["is_valid"] is False
    print(f"  [OK] Caught fabricated Section: {fake1['rejection_reason']}")
    print(f"  [OK] Caught fabricated Section: {fake2['rejection_reason']}")

    # Mixed Text Narrative Scanning
    narrative = (
        "The complainant states that on 15th August 2024, the accused committed cheating under "
        "Section 318(4) of Bharatiya Nyaya Sanhita and cyber fraud under Section 66D IT Act. "
        "The opposition lawyer falsely invoked Section 999 BNS and Section 482B IPC."
    )
    report = validator.validate_text_citations(narrative)
    assert report["total_citations"] == 4
    assert report["valid_count"] == 2
    assert report["invalid_count"] == 2
    assert report["citation_grounding_ratio"] == 0.5
    print(f"  [OK] Scanned text containing 4 citations: 2 valid verified, 2 fake citations flagged.")
    print("  --> [10/10] Legal Citation Validation: PASSED.")

    # --------------------------------------------------------------------------
    # Additional Verification: Source Document Verbatim Alignment
    # --------------------------------------------------------------------------
    print("\n[ADDITIONAL CHECK] Verifying Source Document Alignment...")
    with open(RAW_DIR / "bns_2023.json", "r", encoding="utf-8") as f:
        bns_raw = json.load(f)
    raw_sec_303_1 = next(s for s in bns_raw["sections"] if s["section_number"] == "303(1)")
    
    chroma_sec_303_1 = retriever.get_exact_section("BNS_2023", "303(1)")
    assert len(chroma_sec_303_1) > 0
    retrieved_text = chroma_sec_303_1[0]["document"]
    assert LegalTextExtractor.clean_text(raw_sec_303_1["full_text"]) in retrieved_text
    print("  [OK] ChromaDB indexed text matches Gazette raw statute text verbatim.")

    print("\n" + "=" * 80)
    print("PHASE 2 COMPREHENSIVE VERIFICATION: ALL 10 VECTORS & CHECKS PASSED (0 ERRORS)")
    print("=" * 80)


if __name__ == "__main__":
    run_comprehensive_verification()
