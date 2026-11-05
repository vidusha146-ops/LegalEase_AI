# LegalEase AI – Intelligent Legal Decision Support System

> **A Production-Oriented, Grounded Legal AI Platform for Indian Citizens**  
> *Major End-Semester Academic Project*

---

## 1. Project Overview & Objectives

**LegalEase AI** is an intelligent decision support system designed specifically to bridge the complex legal landscape of India for everyday citizens. Moving beyond generic chatbots, LegalEase AI adheres to a **Zero-Fabrication Legal Integrity Policy**: every recommendation and statutory reference is strictly grounded in verified Bare Acts and Gazette texts.

### Primary Objectives:
1. **Explainable Legal Assessment**: Demystify complex legal jargon into plain, actionable language (English & Hindi).
2. **Statutory Grounding (BNS $\leftrightarrow$ IPC Dual Reference)**: Clearly distinguish historical Indian Penal Code (IPC) provisions from the applicable Bharatiya Nyaya Sanhita (BNS 2023), distinguishing definitions from punishments, alongside BNSS, BSA, Consumer Protection Act 2019, IT Act 2000, and RTI Act 2005.
3. **Evidence Intelligence & Chronological Timeline**: Parse uploaded complaints, receipts, and legal notices (via OCR/PyMuPDF), detect temporal gaps, and resolve factual contradictions.
4. **Automated Complaint Drafting**: Generate structured preliminary complaint drafts (Police Complaints/FIR drafts, Consumer Forum Grievances, RTI Form A, Legal Notices) ready for review.
5. **Ethics & Regulatory Compliance**: Provide clear, non-lawyer statutory disclaimers under the Advocates Act, 1961, accompanied by transparent information-quality and uncertainty scores.

---

## 2. Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS v4, Lucide Icons, Axios |
| **Backend** | Python 3.11+, FastAPI (Asynchronous), Pydantic v2, Pydantic-Settings |
| **ORM & Database** | SQLAlchemy 2.0 (Asyncio), Greenlet, aiosqlite (Dev fallback), asyncpg (PostgreSQL) |
| **Vector Database & RAG**| ChromaDB (Persistent local vector storage), ONNX Runtime, All-MiniLM-L6-v2 |
| **Security & Auth** | JWT (`pyjwt`), Bcrypt password hashing (`bcrypt`), OAuth2 password bearer |
| **AI & NLP** | Google Gemini API (Structured JSON output), Scikit-learn (TF-IDF + Logistic Regression) |
| **Document Processing** | PyMuPDF (fitz), Tesseract OCR |
| **Testing** | Pytest, Pytest-Asyncio, HTTPX |

---

## 3. Directory & Folder Structure

```
LegalEase-AI/
├── .env.example                       # Root environment configuration template
├── .gitignore                         # Comprehensive Git ignore rules
├── README.md                          # Project documentation and developer guide
│
├── backend/                           # FastAPI Backend Core
│   ├── .env.example                   # Backend environment template
│   ├── .env                           # Local environment config (SQLite fallback)
│   ├── requirements.txt               # Pinned Python dependencies
│   ├── pytest.ini                     # Pytest configuration
│   │
│   ├── app/
│   │   ├── main.py                    # FastAPI entrypoint, CORS & lifespan manager
│   │   ├── core/                      # Global configurations & security
│   │   │   ├── config.py              # Pydantic Settings
│   │   │   ├── security.py            # Bcrypt hashing & PyJWT token utilities
│   │   │   ├── database.py            # Async engine, sessionmaker, table auto-creation
│   │   │   └── constants.py           # Advocates Act disclaimers & statutory domains
│   │   │
│   │   ├── models/                    # SQLAlchemy ORM Models
│   │   │   ├── base.py                # TimestampMixin (created_at, updated_at)
│   │   │   ├── user.py                # User credentials & language preference
│   │   │   ├── case.py                # Citizen legal inquiries & AI analysis state
│   │   │   ├── evidence.py            # Uploaded documents, OCR text & contradictions
│   │   │   ├── timeline.py            # Chronological events & temporal gap detection
│   │   │   ├── draft.py               # Complaint drafts (FIR, Consumer, RTI, Notices)
│   │   │   └── audit.py               # Security & data privacy audit trail
│   │   │
│   │   ├── schemas/                   # Pydantic DTOs
│   │   │   ├── user.py                # Registration, Login, Token, UserResponse
│   │   │   └── health.py              # System health & helpline verification
│   │   │
│   │   ├── api/
│   │   │   ├── deps.py                # Dependency injection (get_db, get_current_user)
│   │   │   └── v1/
│   │   │       ├── router.py          # API v1 aggregator
│   │   │       ├── health.py          # GET /api/v1/health
│   │   │       ├── auth.py            # Citizen Registration & JWT Authentication
│   │   │       └── statutes.py        # /api/v1/statutes (RAG search, Crosswalk & Verifier)
│   │   │
│   │   ├── rag/                       # RAG & Knowledge Retrieval Engine
│   │   │   ├── extractor.py           # Statutory text extraction and clause cleaner
│   │   │   ├── section_identifier.py  # Section, Act, and classification resolver
│   │   │   ├── chunker.py             # Semantic section-level chunker with context headers
│   │   │   ├── chroma_client.py       # ChromaDB persistent vector storage client
│   │   │   ├── retriever.py           # Hybrid vector search + metadata filters
│   │   │   ├── crosswalk.py           # BNS-IPC crosswalk & Article 20(1) temporal router
│   │   │   └── citation_validator.py  # Multi-stage deterministic citation validator
│   │   │
│   │   ├── ml/                        # Machine learning classification models (Phase 3)
│   │   └── utils/                     # Document parsers & citation checkers
│   │
│   └── tests/                         # Automated test suite (13/13 tests passing)
│       ├── test_health_and_auth.py    # Health check & auth workflow tests
│       ├── test_knowledge_base.py     # Bare Acts, ChromaDB & Crosswalk tests
│       └── test_statutes_api.py       # Statutes, Crosswalk & Verification API tests
│
├── legal_knowledge_base/              # Verified Indian Statutory Corpus
│   ├── raw_statutes/                  # Official Gazette Bare Acts (Unmodified Texts)
│   │   ├── bns_2023.json              # Bharatiya Nyaya Sanhita, 2023 (Act 45 of 2023)
│   │   ├── bnss_2023.json             # Bharatiya Nagarik Suraksha Sanhita (Act 46 of 2023)
│   │   ├── bsa_2023.json              # Bharatiya Sakshya Adhiniyam (Act 47 of 2023)
│   │   ├── consumer_protection_2019.json # Consumer Protection Act (Act 35 of 2019)
│   │   ├── it_act_2000.json           # Information Technology Act, 2000 (Act 21 of 2000)
│   │   ├── rti_act_2005.json          # Right to Information Act, 2005 (Act 22 of 2005)
│   │   └── ni_act_1881.json           # Negotiable Instruments Act, 1881 (Sec 138-143A)
│   ├── bare_act_index.json            # Canonical catalog of 73 verified statutory sections
│   ├── bns_ipc_crosswalk.json         # BNS <-> IPC transition crosswalk & savings rules
│   ├── build_index.py                 # Index generator script
│   └── index_knowledge_base.py        # ChromaDB persistent ingestion script
│
└── frontend/                          # React + TypeScript + Vite Frontend
    ├── package.json
    ├── vite.config.ts                 # Vite setup with Tailwind v4 & API proxy
    ├── src/
    │   ├── App.tsx                    # Root component with AuthProvider
    │   ├── index.css                  # Tailwind CSS v4 Dark Navy & Gold theme
    │   ├── components/
    │   │   ├── common/
    │   │   │   └── DisclaimerBanner.tsx # Statutory disclaimer banner
    │   │   ├── layout/
    │   │   │   ├── Navbar.tsx         # Navigation, health status pill & auth buttons
    │   │   │   └── Footer.tsx         # Helplines (1915, 1930, 15100, 112) & credits
    │   │   └── auth/
    │   │       └── AuthModal.tsx      # Sign In / Citizen Registration modal
    │   ├── pages/
    │   │   └── LandingPage.tsx        # System dashboard & live connection status
    │   ├── services/
    │   │   ├── api.ts                 # Axios instance with JWT interceptors
    │   │   ├── auth.service.ts        # Authentication API service
    │   │   └── health.service.ts      # Health check API service
    │   └── context/
    │       └── AuthContext.tsx        # Global citizen session state
```

---

## 4. Phase 2 Deliverables: Verified Legal Knowledge Base & RAG

### 1. Verified Bare Acts Collection
Ingested authentic, government-gazetted Bare Acts from official sources (eGazette, IndiaCode, MeitY, DoPT):
- **BNS 2023** (Act 45 of 2023): Core offenses (Theft, Dwelling theft, Extortion, Criminal breach of trust, Cheating, Forgery, Intimidation, Sec 358 Savings).
- **BNSS 2023** (Act 46 of 2023): Sections 173 (FIR, e-FIR), 175 (Power to investigate), 176 (Forensics), 531 (CrPC 1973 savings rule).
- **BSA 2023** (Act 47 of 2023): Sections 57 (Primary evidence), 61 & 63 (Admissibility of electronic records and certificates), 170 (Savings).
- **Consumer Protection Act, 2019** (Act 35 of 2019): Sections 2(7) (Consumer), 2(11) (Deficiency), 2(47) (Unfair trade practice), 34, 35, 38, 39 (Reliefs).
- **IT Act, 2000**: Sections 43, 66, 66C (Identity theft), 66D (Cyber fraud / Cheating by personation), 66E, 72A.
- **RTI Act, 2005**: Sections 3, 6(1) (Application), 7(1) (30-day & 48-hr timelines), 19(1) & 19(3) (First and Second Appeals).
- **NI Act, 1881**: Chapter XVII, Sections 138 (Cheque dishonour), 141 (Company liability), 142 (Cognizance timelines), 143A (Interim compensation).

### 2. Canonical Bare Act Index & Verification Engine
- **`bare_act_index.json`**: Canonical dictionary containing 73 verified statutory provisions.
- **`citation_validator.py`**: Scans any citizen narrative or AI draft, extracts statutory citations via AST/regex, and deterministically validates them against `bare_act_index.json`. Rejects fabricated sections (e.g. `Section 999 BNS` or `Section 482B IPC`).

### 3. BNS-IPC Dual Reference Crosswalk & Temporal Router
- Strictly separates **Offence Definitions** from **Punishment Provisions**:
  - *Theft*: IPC 378 (Def) $\leftrightarrow$ BNS 303(1); IPC 379 (Punishment) $\leftrightarrow$ BNS 303(2) *(with community service proviso for < ₹5,000)*.
  - *Cheating*: IPC 415 (Def) $\leftrightarrow$ BNS 318(1); IPC 417 (Simple Pun) $\leftrightarrow$ BNS 318(2); IPC 420 (Aggravated) $\leftrightarrow$ BNS 318(4).
  - *Criminal Breach of Trust*: IPC 405 (Def) $\leftrightarrow$ BNS 316(1); IPC 406 (Pun) $\leftrightarrow$ BNS 316(2).
- **Article 20(1) & Savings Rules**:
  - Offenses prior to July 1, 2024: Substantive charge under IPC 1860; Section 358 BNS & Section 531 BNSS savings provisions applied.
  - Offenses on or after July 1, 2024: Charged under BNS 2023.
  - Continuing offenses: Dual-charging guidance provided.

### 4. ChromaDB Persistent Vector Store & Hybrid Retrieval
- **Persistent storage**: `./chroma_data` using ONNX `all-MiniLM-L6-v2` local embedding model.
- **Semantic search**: Queries statutes by natural language descriptions (e.g. *"theft of movable property taken out of possession"* returns BNS 303(1) as rank 1).
- **Metadata filtering**: Constrains queries by legal domain, Act code, or provision type.

---

## 5. API Documentation for Phase 2 Endpoints

Access Swagger interactive documentation at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs):

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/statutes/search` | Semantic vector search on ChromaDB with domain and act filters |
| `GET` | `/api/v1/statutes/crosswalk/ipc/{sec}` | Translates IPC section to BNS equivalent with definition vs punishment role |
| `GET` | `/api/v1/statutes/crosswalk/bns/{sec}` | Translates BNS section to historical IPC counterpart |
| `POST` | `/api/v1/statutes/crosswalk/temporal-applicability` | Evaluates IPC vs BNS applicability based on incident date and Art 20(1) |
| `POST` | `/api/v1/statutes/verify-citations` | Deterministic verification scanning text for citations and validating against canonical index |
| `POST` | `/api/v1/analyzer/predict-domain` | Rapid ML classification of citizen narrative into 10 legal domains |
| `POST` | `/api/v1/analyzer/detect-gaps` | Statutory ingredient gap detection & interactive follow-up questions |
| `POST` | `/api/v1/analyzer/analyze-situation` | Full situation analysis (ML + ChromaDB + Crosswalk + Gaps + Element Mapping + Uncertainty + IQ Score) |
| `POST` | `/api/v1/analyzer/explain-statute` | Decomposes Indian statutory sections into elemental legal ingredients and maps citizen facts |
| `POST` | `/api/v1/analyzer/resolve-gaps` | Dynamic gap answering: merges citizen answers, recalculates completeness, elevates $S_{\text{IQ}}$ |
| `POST` | `/api/v1/analyzer/generate-ai-explanation` | Grounded plain-language rights and actionable procedural steps via structured Gemini RAG |
| `GET` | `/api/v1/analyzer/model-metrics` | Empirical Stratified 5-Fold Cross-Validation metrics & Confusion Matrix |
| `POST` | `/api/v1/evidence/upload` | Multipart upload for PDF, DOCX, images; PyMuPDF text & OCR extraction; entity & event parsing |
| `GET` | `/api/v1/evidence/case/{case_id}` | Lists all ingested evidence documents, extracted metadata, and classifications for a case |
| `GET` | `/api/v1/evidence/{doc_id}` | Detailed preview of OCR extracted text, SHA-256 digest, and structured entities |
| `PATCH` | `/api/v1/evidence/{doc_id}/reclassify` | Citizen manual override and correction of evidence category |
| `DELETE` | `/api/v1/evidence/{doc_id}` | Permanently and securely deletes evidence document record and storage file |
| `GET` | `/api/v1/timeline/case/{case_id}` | Builds sorted chronological timeline, detects temporal gaps, sequence numbers events |
| `POST` | `/api/v1/timeline/event` | Adds citizen manual incident event to chronological timeline |
| `DELETE` | `/api/v1/timeline/event/{event_id}` | Deletes a manual or document timeline event |
| `POST` | `/api/v1/evidence/consistency-check` | Cross-examines documents and narrative to detect amount variances and sequence anomalies |
| `POST` | `/api/v1/evidence/map-to-statute` | Correlates uploaded documents with statutory elements under Explainable AI |

---

## 6. Phase 4 Deliverables: Explainability, Uncertainty Detection & Interactive Gap Resolution

### 1. Explainable Legal AI Engine (`backend/app/services/explainability.py`)
- Decomposes verified Indian statutory provisions (e.g., Section 303(1) BNS Theft, Section 318(4) BNS Cheating, Section 138 NI Act Cheque Dishonour, Section 2(11) Consumer Protection Act Deficiency in Service, Section 66D IT Act Cyber Cheating) into individual statutory requirements.
- Distinguishes **Substantiated Statutory Elements** (with exact textual evidence excerpts from the citizen narrative) from **Pending Proof Requirements** (with actionable evidentiary explanations).
- Provides traceable statutory Gazette references for transparency and defensibility.

### 2. Uncertainty, Contradiction & Assumption Detection (`backend/app/services/uncertainty.py`)
- **Vague & Ambiguous Phrasing**: Flags imprecise language ("someone took money", "some loss recently") and competing legal domain overlaps.
- **Chronological & Statutory Contradictions**: Detects post-dated incidents and Article 20(1) constitutional violations (e.g. incidents occurring prior to July 1, 2024 attempting to cite BNS instead of IPC 1860).
- **Contradiction Penalty ($P_{\text{contradiction}}$)**: Applies mathematical deductions to the raw groundability score ($0.10$ per contradiction, capped at $0.30$) preventing false evidentiary confidence.
- **Citizen Assumption Identification**: Alerts citizens to legally unsupported assumptions (e.g. expecting police to arrest debtors in Section 138 NI Act summon cases, or filing police FIRs for pure consumer contractual refund disputes).

### 3. Interactive Legal Gap Resolution Workflow (`backend/app/services/situation_analyzer.py`)
- Citizens can directly input factual clarifications to detected missing ingredients.
- Dynamically recalculates the Information Quality Score ($S_{\text{IQ}}$) in real-time.
- Augments the narrative with structured citizen answers and automatically upgrades evidentiary status badges from `LOW_QUALITY_INCOMPLETE` to `MODERATE_QUALITY_GAPS` or `COMPREHENSIVE_QUALITY`.

### 4. Structured Grounded Gemini Situation Analyzer (`backend/app/services/gemini_analyzer.py`)
- Synthesizes plain-language summaries, statutory citizen rights, and immediate actionable steps strictly grounded in retrieved Bare Acts.
- Zero ungrounded hallucination: Falls back to deterministic grounded templates when offline or without external API keys.
- Enforces mandatory statutory disclaimer under the Advocates Act, 1961.

### 5. Interactive Frontend Dashboard (`SituationAnalyzer.tsx`)
- Fully integrated in React 19 + Tailwind CSS with the Dark Navy & Gold design system.
- Visual statutory element breakdown cards with satisfied vs pending status chips.
- Interactive question-and-answer interface with immediate score elevation feedback.
- Uncertainty & ambiguity warning callouts.

---

## 7. Phase 5 Deliverables: Evidence Document Processing & Chronological Timeline Construction

### 1. Document Intelligence Engine (`backend/app/services/document_intelligence.py`)
- **PyMuPDF (`fitz`) Text Extraction**: Multi-page PDF text and metadata extraction with page numbering and character count tracking.
- **DOCX Extraction (`python-docx`)**: Extracts headings, body paragraphs, and structured multi-column tables.
- **OCR Engine (`pytesseract` / PIL)**: Handles scanned document pages and images (PNG, JPG, TIFF) with automatic fallback.
- **Security & Validation**: SHA-256 cryptographic digest calculation, magic byte inspection, 15MB size limit enforcement, path traversal sanitization, and handling of corrupted / password-protected files.

### 2. Legal Entity & Information Extraction (`backend/app/services/information_extraction.py`)
- **Date Normalization**: Extracts multiple Indian date formats (`DD/MM/YYYY`, `DD Month YYYY`, `Month DD, YYYY`) and converts them to ISO-8601 (`YYYY-MM-DD`).
- **Currency & Denominations**: Extracts Indian Rupee amounts (`₹`, `Rs.`, `INR`, `Lakhs`, `Crores`).
- **Transactional Identifiers**: Extracts Cheque numbers, Bank Account numbers, IFSC codes, Speed Post tracking numbers (`ED...IN`), Invoice numbers, and Bank Return Memo reasons (`Funds Insufficient`).
- **Parties & Institutions**: Identifies Indian commercial banks and legal dispute roles (`Drawer`, `Payee`, `Landlord`, `Tenant`).
- **Traceability**: All extracted entities record exact `source_document` and `page_number`.

### 3. Evidence Classification (`backend/app/services/evidence_classifier.py`)
- Automatically classifies evidence into 8 canonical categories: `INVOICE_BILL`, `BANK_RECORD`, `LEGAL_NOTICE`, `AGREEMENT_CONTRACT`, `POLICE_COMPLAINT_FIR`, `EMAIL_CORRESPONDENCE`, `IDENTITY_ADDRESS_PROOF`, `OTHER_EVIDENCE`.
- Generates confidence scores ($0.60$ to $0.98$) and keyword indicator citations.
- Supports citizen manual reclassification with `is_user_corrected` tracking.

### 4. Chronological Timeline Engine (`backend/app/services/timeline_engine.py`)
- Aggregates document-derived and citizen-input events into an ordered chronological timeline.
- Assigns sequence numbers, earliest and latest incident dates.
- Detects extended temporal gaps (> 90 days) alerting citizens to statutory limitation concerns.
- Separates and displays undated / pending milestones cleanly.

### 5. Evidence Consistency Analyzer (`backend/app/services/consistency_analyzer.py`)
- Cross-examines documents against each other and against user narrative claims.
- Flags **Monetary Amount Variances** (e.g. Invoice ₹ 2,50,000 vs Cheque ₹ 2,00,000).
- Flags **Chronological Sequence Anomalies** (e.g. demand notice dated before cheque bounce return memo).
- Highlights **Missing Documentary Proof** based on the predicted legal domain.
- **Strict Non-Defamatory Labeling**: Labels discrepancies objectively as `VARIANCE`, `DISCREPANCY`, or `DOCUMENTARY_GAP`, never asserting fraud or forgery without judicial proof.

### 6. Evidence-to-Legal-Fact Mapping (`backend/app/services/evidence_mapper.py`)
- Correlates uploaded evidence categories with statutory ingredients in the Explainable AI engine.
- Satisfies pending legal proof requirements when authentic documents are provided (e.g. bank return memo satisfies `BANK_DISHONOUR` in Section 138 NI Act).

### 7. Interactive Frontend Evidence Vault (`EvidenceManager.tsx`)
- Drag-and-drop multiple document upload with live validation feedback.
- Document repository cards with category selector, extracted entity chips, preview modal, and delete actions.
- Interactive timeline tree showing incident sequence, source document references, and manual event creator.
- Consistency check alert panel displaying variances and recommended proofs.

### 8. AI Legal Document Generation Studio (`backend/app/services/legal_drafting_studio.py`)
- **4 Canonical Document Templates**:
  1. **Consumer Disputes Complaint**: Formatted for the District Consumer Disputes Redressal Commission (DCDRC) under Section 35 of the Consumer Protection Act, 2019. Includes territorial and pecuniary jurisdiction statements ($\le ₹50\text{ Lakhs}$), deficiency in service grounds (Sec 2(11)), unfair trade practices (Sec 2(47)), refund of consideration with interest, mental agony compensation, and solemn verification affidavit.
  2. **Statutory Demand Notice**: Drafted under Section 138 of the Negotiable Instruments Act, 1881. Enforces mandatory 15-day payment demand period, dishonour memo particulars, postal dispatch coordinates, and criminal proceeding warnings under Section 138 NI Act read with Section 318(4) BNS.
  3. **RTI Application Form A**: Formatted under Section 6(1) of the Right to Information Act, 2005. Features Central/State Public Information Officer designation, Indian citizenship declaration (Sec 3), 30-day statutory timeline mandate (Sec 7(1)), and ₹10 prescribed application fee particulars.
  4. **Police Complaint (FIR Draft)**: Formatted under Section 173 of the Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS) (formerly Sec 154 CrPC). Captures Station House Officer (SHO) address, exact date/time/place of occurrence, accused particulars, substantive BNS/IT Act offence sections, and prayer for FIR registration.
- **Structured Missing-Information Detection**: Detects omitted statutory parameters (complainant/opposite party address, unquantified claims, missing transaction dates) and inserts explicit placeholders (`[REQUIRED: ...]`) rather than hallucinating facts.
- **Canonical Citation Verification**: Validates all statutory sections against `bare_act_index.json` before inclusion in document grounds.
- **Evidence-Linked Exhibits (Annexures)**: Automatically binds uploaded Phase 5 documentary evidence into formal legal annexures (`Exhibit A`, `Exhibit B`).
- **Editable Document Preview**: Split-screen editing with live court preview and dynamic PDF/DOCX regeneration on `PUT /api/v1/drafts/{id}`.
- **PDF & DOCX Export Engine (`backend/app/services/document_export.py`)**: Renders court-ready PDFs (via PyMuPDF) with Navy Blue (`#0B132B`) / Gold (`#D4AF37`) styling, margins, running headers/footers ("Page X of Y"), and DOCX documents (via `python-docx`).
- **Advocates Act, 1961 Compliance**: Mandatory non-advocacy disclaimers and explicit prohibition against automated submission.

---

## 8. Automated Testing Instructions

Run the complete backend test suite (**44 passing tests in 7.77s**):
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pytest -c pytest.ini tests/ -v
```

Run Phase 6 independent verification:
```powershell
python backend/tests/verify_phase6_independent.py
```

**Test Breakdown (44 tests total)**:
- `test_legal_drafting.py`: 8 tests (Missing information detection, canonical citation validation, evidence-linked exhibits, consumer complaint generation, legal demand notice generation, RTI Form A and Police Complaint generation, PDF/DOCX export integrity, FastAPI REST API lifecycle).
- `test_evidence_and_timeline.py`: 9 tests (PDF extraction, DOCX extraction, corrupted/unsupported security checks, entity extraction, evidence classification, chronological timeline sorting, consistency analyzer, evidence fact mapping, Phase 5 API endpoints).
- `test_explainability.py`: 7 tests (Statutory element decomposition for Theft and Cheque Bounce, Gemini offline grounded fallback, Phase 4 API endpoints, vague phrasing detection, Art 20(1) contradiction detection, unsupported assumption detection).
- `test_health_and_auth.py`: 3 tests (Root welcome, health check, citizen JWT auth).
- `test_knowledge_base.py`: 7 tests (Bare acts integrity, canonical index, BNS-IPC crosswalk definition vs punishment, Article 20(1) savings, citation validator, narrative validation, ChromaDB semantic retrieval).
- `test_statutes_api.py`: 3 tests (Statutes semantic search API, crosswalk API, citation verification API).
- `test_ml_classifier.py`: 4 tests (Dataset integrity, preprocessor cleaning, model persistence & metrics, multi-class predictions).
- `test_situation_analyzer.py`: 3 tests (Gap detector & follow-ups, end-to-end situation analysis, analyzer API endpoints).

---

## 9. Upcoming Phases Roadmap

- **Phase 7 & 8**: Case Similarity Search, Multilingual Assistant & User Dashboard (AWAITING USER AUTHORIZATION).
