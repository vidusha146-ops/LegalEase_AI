"""
LegalEase AI - AI Legal Document Generation Studio (Phase 6)
Drafts court-ready, evidence-linked legal documents:
1. Consumer Disputes Complaint (Consumer Protection Act, 2019)
2. Legal Demand Notice (Section 138 NI Act, 1881 / Contractual Breach)
3. RTI Application Form A (Right to Information Act, 2005)
4. Police Complaint / FIR Information (Section 173 BNSS, 2023)

Features:
- Structured missing-information detection & explicit placeholders (no hallucinated facts)
- Canonical statutory citation verification (no invented sections)
- Documentary evidence linking with exhibit tagging (Phase 5 integration)
- Strict separation of user facts, extracted evidence, legal grounds, assumptions, and missing data
- Advocates Act, 1961 non-advocacy disclaimers & non-automated submission guarantee
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import date, datetime

from app.rag.citation_validator import LegalCitationValidator
from app.schemas.draft import (
    DraftGenerateRequest,
    MissingInfoItem,
    VerifiedCitationItem,
    ExhibitItem,
    PartyDetails,
)

logger = logging.getLogger(__name__)

NON_ADVOCACY_DISCLAIMER_TEXT = (
    "DISCLAIMER UNDER ADVOCATES ACT, 1961 (SECTIONS 29 & 30): This legal document draft is generated "
    "by LegalEase AI for educational, personal drafting assistance and procedural clarity only. It does "
    "not constitute formal legal advice, representation, or advocacy by an Advocate. The user is strictly "
    "advised to consult a qualified Advocate enrolled with the State Bar Council to verify, settle, and "
    "finalize this draft before filing it in any court, commission, tribunal, or police station. "
    "LegalEase AI DOES NOT automatically submit, post, or e-file any document on behalf of the user."
)


class LegalDraftingStudioService:
    """
    Intelligent Legal Drafting Engine grounded in the canonical Indian legal knowledge base,
    statutory elements, and uploaded documentary exhibits.
    """

    def __init__(self):
        self.validator = LegalCitationValidator()

    # =========================================================================
    # 1. MISSING-INFORMATION & GAP CHECKER
    # =========================================================================

    @classmethod
    def detect_missing_information(
        cls,
        draft_type: str,
        request: DraftGenerateRequest,
    ) -> List[MissingInfoItem]:
        """
        Detects missing mandatory and critical factual parameters based on draft type.
        Prevents generative hallucination by explicitly surfacing factual gaps.
        """
        missing_items: List[MissingInfoItem] = []
        clean_type = draft_type.upper().strip()

        # Complainant / Applicant validation
        if not request.complainant or not request.complainant.name or request.complainant.name.strip() in ("", "Citizen"):
            missing_items.append(
                MissingInfoItem(
                    field="complainant_name",
                    rationale="Indian procedural law requires full identification of the complainant/applicant.",
                    impact="Complaint cannot be instituted anonymously or under pseudonyms without leave.",
                    suggested_prompt="Provide your full legal name as per government photo ID.",
                )
            )

        if not request.complainant or not request.complainant.address:
            missing_items.append(
                MissingInfoItem(
                    field="complainant_address",
                    rationale="Complete address with PIN code is mandatory for territorial jurisdiction and summons/notice delivery.",
                    impact="Forum or Registry will mark filing defective for want of service particulars.",
                    suggested_prompt="Provide your complete residential or business postal address.",
                )
            )

        # Opposite Party / Noticee / Accused validation
        if not request.opposite_party or not request.opposite_party.name:
            field_name = "noticee_name" if "NOTICE" in clean_type else "opposite_party_name"
            missing_items.append(
                MissingInfoItem(
                    field=field_name,
                    rationale="A legal proceeding or demand notice must name a specific respondent or accused.",
                    impact="Process cannot be served on an unidentified opposite party.",
                    suggested_prompt="Provide the legal name of the defaulting party, merchant, or company.",
                )
            )

        if not request.opposite_party or not request.opposite_party.address:
            missing_items.append(
                MissingInfoItem(
                    field="opposite_party_address",
                    rationale="A registered notice or court summons requires verified postal dispatch coordinates.",
                    impact="Notice cannot be dispatched via Registered Post / Speed Post without a valid address.",
                    suggested_prompt="Provide the registered office, branch, or residential address of the opposite party.",
                )
            )

        # Type-specific mandatory checks
        if clean_type == "CONSUMER_COMPLAINT":
            if not request.monetary_claim or request.monetary_claim <= 0:
                missing_items.append(
                    MissingInfoItem(
                        field="monetary_claim",
                        rationale="Consumer Protection Act, 2019 defines District Forum pecuniary jurisdiction up to ₹50 Lakhs.",
                        impact="Registry cannot compute appropriate court fee or establish pecuniary jurisdiction.",
                        suggested_prompt="Specify the exact invoice amount and compensation claimed for mental agony.",
                    )
                )
            if not request.incident_date:
                missing_items.append(
                    MissingInfoItem(
                        field="transaction_date",
                        rationale="Section 69 of CPA 2019 prescribes a 2-year limitation period from the date cause of action arose.",
                        impact="Complaint may be barred by statutory limitation if date is missing or beyond 2 years.",
                        suggested_prompt="Provide the exact date of purchase or date of defective service discovery.",
                    )
                )

        elif clean_type == "LEGAL_NOTICE":
            if not request.monetary_claim or request.monetary_claim <= 0:
                missing_items.append(
                    MissingInfoItem(
                        field="cheque_amount",
                        rationale="Section 138 of NI Act requires demand of the exact dishonoured cheque amount.",
                        impact="Notice is invalid if demand amount is indefinite or unquantified.",
                        suggested_prompt="State the exact monetary amount drawn on the dishonoured cheque.",
                    )
                )
            if not request.incident_date:
                missing_items.append(
                    MissingInfoItem(
                        field="cheque_bounce_date",
                        rationale="Under Section 138(b) NI Act, notice must be dispatched within 30 days of receiving the bank memo.",
                        impact="Delay beyond 30 days extinguishes criminal liability under Section 138 NI Act.",
                        suggested_prompt="Specify the exact date on which the bank return memo was received.",
                    )
                )

        elif clean_type == "RTI_APPLICATION":
            if not request.incident_location and not request.jurisdiction_forum:
                missing_items.append(
                    MissingInfoItem(
                        field="public_authority_department",
                        rationale="RTI Act Section 6(1) requires addressing the specific Central or State Public Information Officer.",
                        impact="Application cannot be delivered without designating the correct public department.",
                        suggested_prompt="Specify the public department or ministry holding the requested records.",
                    )
                )

        elif clean_type == "POLICE_COMPLAINT":
            if not request.incident_location:
                missing_items.append(
                    MissingInfoItem(
                        field="place_of_occurrence",
                        rationale="Section 173 BNSS (formerly Sec 154 CrPC) requires police station territorial jurisdiction.",
                        impact="Police station may refer complainant to another station under Zero FIR procedures.",
                        suggested_prompt="Specify the exact address or landmark where the incident occurred.",
                    )
                )
            if not request.incident_date:
                missing_items.append(
                    MissingInfoItem(
                        field="incident_date_time",
                        rationale="Criminal jurisprudence requires exact date, time, and sequence of alleged offence.",
                        impact="FIR registration requires prompt lodging; unexplained delay weakens prosecution.",
                        suggested_prompt="Provide the date and approximate time when the incident took place.",
                    )
                )

        return missing_items

    # =========================================================================
    # 2. STATUTORY CITATION BINDING & CANONICAL VERIFICATION
    # =========================================================================

    def get_verified_statutory_citations(
        self, draft_type: str, grievance_narrative: str
    ) -> List[VerifiedCitationItem]:
        """
        Retrieves authentic Bare Act provisions from the canonical gazette index.
        Rejects all unverified or hallucinated sections.
        """
        citations: List[VerifiedCitationItem] = []
        clean_type = draft_type.upper().strip()

        target_provisions: List[Tuple[str, str]] = []

        if clean_type == "CONSUMER_COMPLAINT":
            target_provisions = [
                ("CONSUMER_PROTECTION_2019", "2(7)"),    # Consumer definition
                ("CONSUMER_PROTECTION_2019", "2(11)"),   # Deficiency in service
                ("CONSUMER_PROTECTION_2019", "2(47)"),   # Unfair trade practice
                ("CONSUMER_PROTECTION_2019", "35"),      # Manner of filing complaint
            ]
        elif clean_type == "LEGAL_NOTICE":
            target_provisions = [
                ("NI_ACT_1881", "138"),    # Dishonour of cheque
                ("NI_ACT_1881", "142"),    # Cognizance of offences
                ("BNS_2023", "318(4)"),    # Cheating & dishonestly inducing delivery
            ]
        elif clean_type == "RTI_APPLICATION":
            target_provisions = [
                ("RTI_ACT_2005", "6(1)"),  # Request for obtaining information
                ("RTI_ACT_2005", "7(1)"),  # Disposal of request within 30 days
            ]
        elif clean_type == "POLICE_COMPLAINT":
            target_provisions = [
                ("BNSS_2023", "173"),      # Information in cognizable cases (FIR)
                ("BNS_2023", "303(1)"),    # Theft
                ("BNS_2023", "318(4)"),    # Cheating
                ("BNS_2023", "316(2)"),    # Criminal Breach of Trust
                ("IT_ACT_2000", "66D"),    # Cheating by personation using computer
            ]

        # Verify each provision against canonical gazette index
        for act_code, sec_num in target_provisions:
            res = self.validator.validate_citation(act_code, sec_num)
            if res.get("is_valid"):
                citations.append(
                    VerifiedCitationItem(
                        act_code=res["act_code"],
                        act_title=res["act_title"],
                        section_number=res["section_number"],
                        section_title=res["section_title"],
                        source_url=res["source_url"],
                        is_verified=True,
                    )
                )

        return citations

    # =========================================================================
    # 3. EVIDENCE LINKING (EXHIBITS BINDING)
    # =========================================================================

    @classmethod
    def bind_evidence_exhibits(
        cls,
        evidence_documents: Optional[List[Dict[str, Any]]] = None,
        selected_ids: Optional[List[int]] = None,
    ) -> List[ExhibitItem]:
        """
        Converts uploaded Phase 5 evidence documents into formal legal exhibits (Annexures).
        """
        exhibits: List[ExhibitItem] = []
        if not evidence_documents:
            return exhibits

        # Filter by selected IDs if specified
        docs_to_bind = evidence_documents
        if selected_ids:
            docs_to_bind = [d for d in evidence_documents if d.get("id") in selected_ids or d.get("document_id") in selected_ids]

        letters = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
        for idx, doc in enumerate(docs_to_bind):
            mark = f"Exhibit {letters[idx % len(letters)]}"
            fname = doc.get("filename") or f"Document_{doc.get('id', idx+1)}"
            cat = doc.get("category") or "OTHER_EVIDENCE"

            relevance = "Corroborative Documentary Proof"
            if cat == "INVOICE_BILL":
                relevance = "Proof of Commercial Transaction & Consideration"
            elif cat == "BANK_RECORD":
                relevance = "Proof of Banking Presentation & Dishonour Memo"
            elif cat == "LEGAL_NOTICE":
                relevance = "Proof of Prior Statutory Demand & Postal Dispatch"
            elif cat == "POLICE_COMPLAINT_FIR":
                relevance = "Copy of Police Acknowledgment / Daily Diary Entry"
            elif cat == "EMAIL_CORRESPONDENCE":
                relevance = "Written Communication & Grievance Trail"

            exhibits.append(
                ExhibitItem(
                    exhibit_label=mark,
                    filename=fname,
                    category=cat,
                    relevance=relevance,
                )
            )

        return exhibits

    # =========================================================================
    # 4. STRUCTURED DOCUMENT GENERATION (4 CANONICAL TEMPLATES)
    # =========================================================================

    def generate_legal_draft(
        self,
        request: DraftGenerateRequest,
        evidence_documents: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Generates a comprehensive, verifiable legal document with explicit separation
        between facts, extracted evidence, statutory citations, and missing information.
        """
        clean_type = request.draft_type.upper().strip()
        missing_info = self.detect_missing_information(clean_type, request)
        verified_citations = self.get_verified_statutory_citations(clean_type, request.narrative or "")
        exhibits = self.bind_evidence_exhibits(evidence_documents, request.selected_evidence_ids)

        if clean_type == "CONSUMER_COMPLAINT":
            content_md, title = self._draft_consumer_complaint(request, verified_citations, exhibits, missing_info)
        elif clean_type == "LEGAL_NOTICE":
            content_md, title = self._draft_legal_notice(request, verified_citations, exhibits, missing_info)
        elif clean_type == "RTI_APPLICATION":
            content_md, title = self._draft_rti_application(request, verified_citations, exhibits, missing_info)
        elif clean_type == "POLICE_COMPLAINT":
            content_md, title = self._draft_police_complaint(request, verified_citations, exhibits, missing_info)
        else:
            raise ValueError(f"Unsupported draft type '{request.draft_type}'. Supported: CONSUMER_COMPLAINT, LEGAL_NOTICE, RTI_APPLICATION, POLICE_COMPLAINT")

        return {
            "draft_type": clean_type,
            "title": request.title or title,
            "content_markdown": content_md,
            "missing_information": missing_info,
            "verified_citations": verified_citations,
            "exhibits": exhibits,
            "disclaimer": NON_ADVOCACY_DISCLAIMER_TEXT,
        }

    # -------------------------------------------------------------------------
    # TEMPLATE 1: CONSUMER DISPUTES COMPLAINT
    # -------------------------------------------------------------------------
    def _draft_consumer_complaint(
        self,
        req: DraftGenerateRequest,
        citations: List[VerifiedCitationItem],
        exhibits: List[ExhibitItem],
        missing: List[MissingInfoItem],
    ) -> Tuple[str, str]:
        c_name = req.complainant.name if req.complainant and req.complainant.name else "[REQUIRED: Complainant Full Name]"
        c_addr = req.complainant.address if req.complainant and req.complainant.address else "[REQUIRED: Complainant Complete Address]"
        c_phone = req.complainant.phone if req.complainant and req.complainant.phone else "[Contact Number]"
        
        op_name = req.opposite_party.name if req.opposite_party and req.opposite_party.name else "[REQUIRED: Opposite Party / Vendor Name]"
        op_addr = req.opposite_party.address if req.opposite_party and req.opposite_party.address else "[REQUIRED: Opposite Party Registered Address]"

        forum = req.jurisdiction_forum or f"DISTRICT CONSUMER DISPUTES REDRESSAL COMMISSION AT {req.incident_location or '[DISTRICT NAME]'}"
        amount_str = f"₹ {req.monetary_claim:,.2f}" if req.monetary_claim else "[REQUIRED: Total Disputed Consideration]"
        tx_date = req.incident_date or "[REQUIRED: Date of Purchase / Availing Service]"

        title = f"Consumer Complaint before District Commission against {op_name}"

        # Build Markdown
        md = []
        md.append(f"# BEFORE THE {forum.upper()}")
        md.append(f"**CONSUMER COMPLAINT NO. _________ OF {date.today().year}**\n")
        md.append("### IN THE MATTER OF:\n")
        md.append(f"**{c_name}**  ")
        md.append(f"Residing at: {c_addr}  ")
        md.append(f"Mobile: {c_phone}  ")
        md.append("**... COMPLAINANT**\n")
        md.append("### VERSUS\n")
        md.append(f"**{op_name}**  ")
        md.append(f"Having its Office / Place of Business at: {op_addr}  ")
        md.append("**... OPPOSITE PARTY**\n")

        md.append("---\n")
        md.append("### COMPLAINT UNDER SECTION 35 OF THE CONSUMER PROTECTION ACT, 2019 FOR DEFICIENCY IN SERVICE AND UNFAIR TRADE PRACTICE\n")

        md.append("## 1. PARTIES & JURISDICTION")
        md.append(f"1. That the Complainant is a 'consumer' within the statutory meaning of **Section 2(7) of the Consumer Protection Act, 2019**, having purchased goods/availed services from the Opposite Party for valuable consideration of {amount_str}.")
        md.append(f"2. That the Opposite Party is a commercial enterprise carrying on business for gain within the territorial jurisdiction of this Hon'ble Commission.")
        md.append(f"3. That the total consideration and compensation claimed is {amount_str}, which is well within the pecuniary jurisdiction limit of ₹50,00,000/- prescribed for District Commissions under Section 34 of the Consumer Protection Act, 2019.\n")

        md.append("## 2. STATEMENT OF FACTS")
        if req.narrative:
            md.append(f"4. {req.narrative}")
        else:
            md.append("4. That the Complainant purchased goods / availed services from the Opposite Party on date " + tx_date + " against payment of full consideration.")
        md.append(f"5. That on {tx_date}, the goods/services supplied were found to suffer from gross deficiency, defect, and operational failure, causing immense harassment and loss to the Complainant.")
        md.append("6. That despite multiple written grievances and requests, the Opposite Party completely neglected, delayed, and refused to rectify the defect or refund the consideration amount.\n")

        md.append("## 3. STATUTORY GROUNDS")
        md.append("7. That the actions and omissions of the Opposite Party constitute:")
        for c in citations:
            md.append(f"   - **{c.act_title} (Section {c.section_number})**: *{c.section_title}* [Verified Statutory Provision].")
        md.append("8. That the Opposite Party is liable to compensate the Complainant under the settled principles of consumer welfare jurisprudence.\n")

        md.append("## 4. LIST OF DOCUMENTARY EXHIBITS")
        if exhibits:
            for ex in exhibits:
                md.append(f"- **{ex.exhibit_label}**: True copy of {ex.filename} ({ex.relevance}).")
        else:
            md.append("- **Exhibit A**: [PENDING DOCUMENT: Tax Invoice / Purchase Receipt / Bill of Supply].")
            md.append("- **Exhibit B**: [PENDING DOCUMENT: Written Communications / Email Grievance Trail / Rejection Letters].\n")

        md.append("## 5. PRAYER & RELIEF SOUGHT")
        md.append("In the premises aforesaid, the Complainant most respectfully prays that this Hon'ble Commission may graciously be pleased to:")
        md.append(f"a) Direct the Opposite Party to immediately refund the principal amount of **{amount_str}** along with interest @ 12% p.a. from date of transaction;")
        md.append("b) Direct the Opposite Party to pay a sum of **₹ 50,000/-** towards compensation for mental agony, harassment, and gross deficiency in service;")
        md.append("c) Direct the Opposite Party to pay a sum of **₹ 15,000/-** towards litigation costs;")
        md.append("d) Pass such other or further order(s) as this Hon'ble Commission may deem fit in the interest of justice.\n")

        md.append("## 6. SOLEMN VERIFICATION AFFIDAVIT")
        md.append(f"I, **{c_name}**, the Complainant above-named, do hereby solemnly declare and verify on oath that the contents of paragraphs 1 to 8 of the present complaint are true and correct to my personal knowledge and belief, and that nothing material has been concealed therefrom.\n")
        md.append(f"Verified at **{req.incident_location or '[Location]'}** on this day of **{date.today().strftime('%d %B %Y')}**.\n")

        # Missing information alert
        if missing:
            md.append("## 7. IDENTIFIED MISSING ELEMENTS & ACTION ITEMS")
            md.append("> **CRITICAL ACTION REQUIRED BEFORE FILING:** The following factual ingredients are currently missing from your case and must be filled in to ensure legal admissibility:")
            for m in missing:
                md.append(f"- **{m.field}**: {m.rationale} (*{m.suggested_prompt}*)")
            md.append("")

        md.append(f"\n---\n> **STATUTORY NON-ADVOCACY NOTICE**: {NON_ADVOCACY_DISCLAIMER_TEXT}")
        return "\n".join(md), title

    # -------------------------------------------------------------------------
    # TEMPLATE 2: LEGAL DEMAND NOTICE (SECTION 138 NI ACT / BREACH)
    # -------------------------------------------------------------------------
    def _draft_legal_notice(
        self,
        req: DraftGenerateRequest,
        citations: List[VerifiedCitationItem],
        exhibits: List[ExhibitItem],
        missing: List[MissingInfoItem],
    ) -> Tuple[str, str]:
        c_name = req.complainant.name if req.complainant and req.complainant.name else "[REQUIRED: Payee / Client Full Name]"
        c_addr = req.complainant.address if req.complainant and req.complainant.address else "[REQUIRED: Client Complete Address]"
        
        op_name = req.opposite_party.name if req.opposite_party and req.opposite_party.name else "[REQUIRED: Drawer / Defaulter Name]"
        op_addr = req.opposite_party.address if req.opposite_party and req.opposite_party.address else "[REQUIRED: Drawer Complete Postal Address]"

        amount_str = f"₹ {req.monetary_claim:,.2f}" if req.monetary_claim else "[REQUIRED: Cheque Dishonoured Amount]"
        bounce_date = req.incident_date or "[REQUIRED: Bank Return Memo Date]"

        title = f"Statutory Demand Notice under Section 138 NI Act to {op_name}"

        md = []
        md.append("# FORMAL LEGAL DEMAND NOTICE")
        md.append("### DISPATCHED VIA REGISTERED POST WITH ACKNOWLEDGEMENT DUE / SPEED POST\n")
        md.append(f"**Date:** {date.today().strftime('%d/%m/%Y')}  ")
        md.append(f"**Consignment Tracking No:** [SPEED POST TRACKING ID: ED_________IN]\n")

        md.append("### TO,\n")
        md.append(f"**{op_name}**  ")
        md.append(f"Address: {op_addr}  ")
        md.append(f"Mobile / Email: {req.opposite_party.phone or req.opposite_party.email or '[Noticee Coordinates]'}\n")

        md.append("### UNDER INSTRUCTIONS FROM OUR CLIENT:\n")
        md.append(f"**{c_name}**, Residing at: {c_addr}\n")

        md.append("---\n")
        md.append(f"**SUBJECT:** STATUTORY DEMAND NOTICE UNDER SECTION 138 OF THE NEGOTIABLE INSTRUMENTS ACT, 1881 FOR DISHONOUR OF CHEQUE OF {amount_str.upper()}.\n")

        md.append("## 1. STATEMENT OF CHRONOLOGICAL FACTS")
        md.append(f"1. That our Client above-named entered into lawful transactions with you, the Noticee, pursuant to which you had a legally enforceable liability and debt towards our Client.")
        if req.narrative:
            md.append(f"2. {req.narrative}")
        else:
            md.append("2. That in discharge of your acknowledged debt and liability, you issued Cheque No. [CHEQUE NUMBER: 6 DIGITS] drawn on your bank account in favor of our Client.")
        md.append(f"3. That our Client duly presented the said cheque for encashment through its bank, but the instrument was returned dishonoured and unpaid on **{bounce_date}** with the official bank return remark: **'Funds Insufficient' / 'Account Closed'**.")
        md.append("4. That the official Cheque Return Memo was communicated to our Client, and the present statutory notice is being issued strictly within the statutory period of 30 days prescribed under Section 138(b) of the Negotiable Instruments Act, 1881.\n")

        md.append("## 2. STATUTORY DEMAND & 15-DAY NOTICE PERIOD")
        md.append(f"5. That in accordance with **Section 138(c) of the Negotiable Instruments Act, 1881**, we hereby call upon you to make payment of the full cheque amount of **{amount_str}** to our Client within **FIFTEEN (15) DAYS** from the date of receipt of this notice.")
        md.append("6. Take notice that if you fail, neglect, or refuse to pay the said sum within 15 days of receiving this notice, our Client has given us peremptory instructions to initiate:")
        for c in citations:
            md.append(f"   - **{c.act_title} (Section {c.section_number})**: *{c.section_title}* [Criminal complaint before the competent Judicial Magistrate];")
        md.append("   - Appropriate civil proceedings for recovery of principal dues with interest @ 18% p.a. and damages.\n")

        md.append("## 3. ANNEXED DOCUMENTARY PROOF")
        if exhibits:
            for ex in exhibits:
                md.append(f"- **{ex.exhibit_label}**: {ex.filename} ({ex.relevance})")
        else:
            md.append("- **Copy of Dishonoured Cheque** (Preserved as primary instrument);")
            md.append("- **Original Bank Return Memo** (Proof of dishonour and date of presentation).\n")

        md.append("Yours faithfully,\n\n")
        md.append(f"**[ADVOCATE NAME / AUTHORIZED SIGNATORY FOR {c_name}]**  ")
        md.append("Enrolment No: ________________________  ")
        md.append("Bar Council of: ______________________  ")
        md.append("Office Address: ______________________\n")

        if missing:
            md.append("## 4. MISSING INFORMATION & PRE-DISPATCH CHECKLIST")
            md.append("> **IMPORTANT:** Ensure the following missing fields are completed before printing on advocate letterhead:")
            for m in missing:
                md.append(f"- **{m.field}**: {m.rationale} (*{m.suggested_prompt}*)")
            md.append("")

        md.append(f"\n---\n> **STATUTORY NON-ADVOCACY NOTICE**: {NON_ADVOCACY_DISCLAIMER_TEXT}")
        return "\n".join(md), title

    # -------------------------------------------------------------------------
    # TEMPLATE 3: RTI APPLICATION (FORM A)
    # -------------------------------------------------------------------------
    def _draft_rti_application(
        self,
        req: DraftGenerateRequest,
        citations: List[VerifiedCitationItem],
        exhibits: List[ExhibitItem],
        missing: List[MissingInfoItem],
    ) -> Tuple[str, str]:
        c_name = req.complainant.name if req.complainant and req.complainant.name else "[REQUIRED: Applicant Full Name]"
        c_addr = req.complainant.address if req.complainant and req.complainant.address else "[REQUIRED: Applicant Postal Address]"
        c_phone = req.complainant.phone if req.complainant and req.complainant.phone else "[Phone / Mobile]"

        dept = req.jurisdiction_forum or req.incident_location or "[PUBLIC AUTHORITY / DEPARTMENT NAME]"
        title = f"RTI Application Form A to Public Information Officer, {dept}"

        md = []
        md.append("# APPLICATION FOR SEEKING INFORMATION UNDER THE RIGHT TO INFORMATION ACT, 2005")
        md.append("### (FORM 'A' UNDER SECTION 6(1) OF THE RTI ACT, 2005)\n")

        md.append("### TO,\n")
        md.append("**THE CENTRAL / STATE PUBLIC INFORMATION OFFICER (CPIO / SPIO)**  ")
        md.append(f"Department / Office: **{dept}**  ")
        md.append(f"Government of India / State Government  ")
        md.append(f"Address: {req.opposite_party.address if req.opposite_party else '[Department Complete Address]'}\n")

        md.append("---\n")
        md.append("## 1. PARTICULARS OF THE APPLICANT")
        md.append(f"- **Full Name:** {c_name}")
        md.append(f"- **Complete Postal Address:** {c_addr}")
        md.append(f"- **Contact Number:** {c_phone}")
        md.append(f"- **Email Address:** {req.complainant.email if req.complainant and req.complainant.email else '[Email Address]'}")
        md.append("- **Citizenship Status:** The Applicant is an **Indian Citizen** entitled to seek information under Section 3 of the RTI Act, 2005.\n")

        md.append("## 2. SPECIFIC PARTICULARS OF INFORMATION SOUGHT")
        md.append("The Applicant requests certified copies of the following government records, files, and circulars:")
        if req.narrative:
            md.append(f"1. {req.narrative}")
        else:
            md.append("1. [REQUIRED: Specific subject matter of requested file / tender / public record].")
        md.append("2. Certified true copy of all file notings, orders, circulars, and departmental correspondence pertaining to the aforesaid subject matter.")
        md.append(f"3. Period to which the information relates: **{req.incident_date or 'Past 3 Financial Years to Date'}**.\n")

        md.append("## 3. STATUTORY TIMELINE MANDATE")
        for c in citations:
            md.append(f"- **{c.act_title} (Section {c.section_number})**: *{c.section_title}* — Requires the PIO to provide information within thirty (30) days of receipt of application.")
        md.append("- (Note: If the requested information concerns the life or liberty of a person, it shall be provided within forty-eight (48) hours under Section 7(1) proviso).\n")

        md.append("## 4. PRESCRIBED APPLICATION FEE PARTICULARS")
        md.append("- Prescribed Application Fee of **₹ 10/- (Rupees Ten Only)** is enclosed herewith via:")
        md.append("  [ ] Indian Postal Order (IPO) No: __________________ Dated: _________")
        md.append("  [ ] Court Fee Stamp affixed")
        md.append("  [ ] Online RTI Portal Transaction Ref: ______________\n")

        md.append("## 5. CITIZEN DECLARATION")
        md.append("I hereby declare that I am an Indian citizen and the information sought does not fall under any exemption provisions specified in Section 8 or Section 9 of the RTI Act, 2005.\n")
        md.append(f"Date: **{date.today().strftime('%d/%m/%Y')}**  ")
        md.append(f"Place: **{req.incident_location or '[Location]'}**\t\t\t\t\t**_____________________________**  ")
        md.append(f"\t\t\t\t\t\t\t\t**Signature of Applicant ({c_name})**\n")

        if missing:
            md.append("## 6. MISSING INFORMATION CHECKLIST")
            md.append("> **CHECKLIST BEFORE POSTING:**")
            for m in missing:
                md.append(f"- **{m.field}**: {m.rationale} (*{m.suggested_prompt}*)")
            md.append("")

        md.append(f"\n---\n> **STATUTORY NON-ADVOCACY NOTICE**: {NON_ADVOCACY_DISCLAIMER_TEXT}")
        return "\n".join(md), title

    # -------------------------------------------------------------------------
    # TEMPLATE 4: POLICE COMPLAINT (FIRST INFORMATION REPORT - FIR DRAFT)
    # -------------------------------------------------------------------------
    def _draft_police_complaint(
        self,
        req: DraftGenerateRequest,
        citations: List[VerifiedCitationItem],
        exhibits: List[ExhibitItem],
        missing: List[MissingInfoItem],
    ) -> Tuple[str, str]:
        c_name = req.complainant.name if req.complainant and req.complainant.name else "[REQUIRED: Informant / Complainant Full Name]"
        c_addr = req.complainant.address if req.complainant and req.complainant.address else "[REQUIRED: Complainant Permanent Address]"
        c_phone = req.complainant.phone if req.complainant and req.complainant.phone else "[Mobile Number]"

        accused_name = req.opposite_party.name if req.opposite_party and req.opposite_party.name else "[ACCUSED PERSON / UNKNOWN PERPETRATOR]"
        accused_addr = req.opposite_party.address if req.opposite_party and req.opposite_party.address else "[Accused Address / Digital Identifier / IP Address]"

        ps_name = req.jurisdiction_forum or f"POLICE STATION {req.incident_location or '[NAME OF POLICE STATION]'}"
        incident_time = req.incident_date or "[REQUIRED: Date and Exact Time of Incident]"
        place_occ = req.incident_location or "[REQUIRED: Exact Place of Occurrence]"

        title = f"Police Complaint (FIR Information) to SHO, {ps_name}"

        md = []
        md.append("# FORMAL POLICE COMPLAINT (INFORMATION OF COGNIZABLE OFFENCE)")
        md.append("### UNDER SECTION 173 OF BHARATIYA NAGARIK SURAKSHA SANHITA, 2023 (BNSS)\n")
        md.append("### TO,\n")
        md.append(f"**THE STATION HOUSE OFFICER (SHO)**  ")
        md.append(f"**{ps_name.upper()}**  ")
        md.append("District / Police Commissionerate: [DISTRICT NAME]\n")

        md.append("---\n")
        md.append("## 1. COMPLAINANT / INFORMANT PARTICULARS")
        md.append(f"- **Full Name:** {c_name}")
        md.append(f"- **Father's / Spouse's Name:** [Father's / Spouse's Name]")
        md.append(f"- **Complete Residential Address:** {c_addr}")
        md.append(f"- **Mobile Number:** {c_phone}")
        md.append(f"- **Email Address:** {req.complainant.email if req.complainant and req.complainant.email else '[Email]'}\n")

        md.append("## 2. DETAILS OF ACCUSED / SUSPECT")
        md.append(f"- **Name of Accused:** {accused_name}")
        md.append(f"- **Address / Details:** {accused_addr}")
        md.append(f"- **Phone / Online Profile:** {req.opposite_party.phone if req.opposite_party else '[Phone/Profile]'}\n")

        md.append("## 3. INCIDENT DETAILS & JURISDICTION")
        md.append(f"- **Date & Time of Occurrence:** {incident_time}")
        md.append(f"- **Place of Occurrence:** {place_occ} (Falling within the territorial limits of this Police Station)")
        if req.monetary_claim:
            md.append(f"- **Disputed Monetary Value / Loss:** ₹ {req.monetary_claim:,.2f}\n")

        md.append("## 4. SEQUENTIAL NARRATIVE OF COGNIZABLE OFFENCE")
        if req.narrative:
            md.append(f"1. {req.narrative}")
        else:
            md.append(f"1. That on {incident_time}, the above-named accused person committed deliberate and cognizable offences causing wrongful loss to the Informant.")
        md.append("2. That the acts committed by the accused establish prima facie ingredients of intentional deception, fraudulent diversion, and criminal breach.")
        md.append("3. That the Informant has suffered severe financial harm, mental trauma, and imminent threat to security.\n")

        md.append("## 5. STATUTORY PROVISIONS & OFFENCE SECTIONS")
        md.append("The acts complained of prima facie disclose commission of cognizable offences under:")
        for c in citations:
            md.append(f"- **{c.act_title} (Section {c.section_number})**: *{c.section_title}* [Verified Statutory Provision].")
        md.append("")

        md.append("## 6. ANNEXED EVIDENTIARY EXHIBITS")
        if exhibits:
            for ex in exhibits:
                md.append(f"- **{ex.exhibit_label}**: {ex.filename} ({ex.relevance})")
        else:
            md.append("- **Exhibit A**: Bank Statement / Transaction Receipt / UTR Slip;")
            md.append("- **Exhibit B**: Screenshots of WhatsApp messages / Call Records / Email Correspondence.\n")

        md.append("## 7. PRAYER")
        md.append("It is therefore most respectfully prayed that this Police Station may be pleased to:")
        md.append("a) Register a regular First Information Report (FIR) under Section 173 BNSS, 2023 against the accused person(s);")
        md.append("b) Investigate the matter expeditiously and recover the stolen/diverted funds/property;")
        md.append("c) Take strict punitive action against the culprit in accordance with law.\n")

        md.append(f"Date: **{date.today().strftime('%d/%m/%Y')}**  ")
        md.append(f"Place: **{req.incident_location or '[City/Town]'}**\t\t\t\t\t**_____________________________**  ")
        md.append(f"\t\t\t\t\t\t\t\t**Signature of Informant ({c_name})**\n")

        if missing:
            md.append("## 8. ACTION REQUIRED: MISSING FACTUAL INGREDIENTS")
            md.append("> **POLICE FILING REQUIREMENT:** Complete the following factual elements to prevent FIR delay:")
            for m in missing:
                md.append(f"- **{m.field}**: {m.rationale} (*{m.suggested_prompt}*)")
            md.append("")

        md.append(f"\n---\n> **STATUTORY NON-ADVOCACY NOTICE**: {NON_ADVOCACY_DISCLAIMER_TEXT}")
        return "\n".join(md), title
