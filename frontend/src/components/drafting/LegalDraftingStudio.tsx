/**
 * LegalEase AI - AI Legal Document Generation Studio Component (Phase 6)
 * Interactive drafting studio for Consumer Complaints, Legal Notices, RTI, and Police Complaints.
 * Features missing information alerts, canonical citation verification, split-screen editing,
 * live court preview, and one-click PDF & DOCX export.
 */

import React, { useState, useEffect } from 'react';
import {
  FileText,
  Download,
  AlertTriangle,
  CheckCircle2,
  Scale,
  ShieldAlert,
  Edit3,
  Eye,
  RefreshCw,
  BookOpen,
  Paperclip,
  ExternalLink,
  FileDown,
} from 'lucide-react';
import { DraftService } from '../../services/draft.service';
import type { DraftResponse, DraftGenerateRequest } from '../../services/draft.service';
import { evidenceService } from '../../services/evidence.service';
import type { EvidenceDocument } from '../../services/evidence.service';

const DRAFT_TEMPLATES = [
  {
    id: 'CONSUMER_COMPLAINT',
    label: 'Consumer Complaint',
    sublabel: 'District Commission (CPA 2019)',
    description: 'Formal complaint under Section 35 CPA for deficiency in goods/services or unfair trade practices.',
    badge: 'CPA 2019',
  },
  {
    id: 'LEGAL_NOTICE',
    label: 'Statutory Demand Notice',
    sublabel: 'Sec 138 NI Act / Dues Recovery',
    description: '15-day statutory demand notice for cheque bounce or commercial payment default.',
    badge: 'NI Act 1881',
  },
  {
    id: 'RTI_APPLICATION',
    label: 'RTI Application Form A',
    sublabel: 'Right to Information Act, 2005',
    description: 'Form A application seeking public records, tenders, or file notings within 30 days.',
    badge: 'RTI 2005',
  },
  {
    id: 'POLICE_COMPLAINT',
    label: 'Police Complaint (FIR)',
    sublabel: 'Section 173 BNSS, 2023',
    description: 'Information of cognizable offence (theft, cheating, cyber fraud) to jurisdictional SHO.',
    badge: 'BNSS 2023',
  },
];

export const LegalDraftingStudio: React.FC<{ caseId?: number }> = ({ caseId = 1 }) => {
  const [selectedType, setSelectedType] = useState<string>('CONSUMER_COMPLAINT');
  const [complainantName, setComplainantName] = useState<string>('Ramesh Sharma');
  const [complainantAddress, setComplainantAddress] = useState<string>('Flat 402, Lotus Apartments, Connaught Place, New Delhi - 110001');
  const [complainantPhone, setComplainantPhone] = useState<string>('9876543210');
  
  const [oppositePartyName, setOppositePartyName] = useState<string>('Apex Infotech Solutions Pvt Ltd');
  const [oppositePartyAddress, setOppositePartyAddress] = useState<string>('Tower B, Tech Park, Outer Ring Road, Bengaluru - 560103');
  
  const [incidentDate, setIncidentDate] = useState<string>('2024-03-12');
  const [incidentLocation, setIncidentLocation] = useState<string>('New Delhi');
  const [jurisdictionForum, setJurisdictionForum] = useState<string>('DISTRICT CONSUMER DISPUTES REDRESSAL COMMISSION, NEW DELHI');
  const [monetaryClaim, setMonetaryClaim] = useState<string>('350000');
  const [narrative, setNarrative] = useState<string>(
    'Purchased commercial software license for Rs 3,50,000 on 12/03/2024 against tax invoice. The vendor delivered non-functional license keys and failed to rectify deficiency despite repeated formal communications.'
  );

  const [availableEvidence, setAvailableEvidence] = useState<EvidenceDocument[]>([]);
  const [selectedEvidenceIds, setSelectedEvidenceIds] = useState<number[]>([]);

  const [loading, setLoading] = useState<boolean>(false);
  const [savingEdits, setSavingEdits] = useState<boolean>(false);
  const [activeDraft, setActiveDraft] = useState<DraftResponse | null>(null);
  const [editMode, setEditMode] = useState<boolean>(false);
  const [editedMarkdown, setEditedMarkdown] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Load existing evidence documents for linking
  useEffect(() => {
    const fetchEvidence = async () => {
      try {
        const docs = await evidenceService.listCaseEvidence(caseId);
        setAvailableEvidence(docs);
        setSelectedEvidenceIds(docs.map((d: EvidenceDocument) => d.document_id));
      } catch (err) {
        console.warn('Could not load evidence list for drafting linking:', err);
      }
    };
    fetchEvidence();
  }, [caseId]);

  const handleGenerateDraft = async () => {
    setLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    const payload: DraftGenerateRequest = {
      case_id: caseId,
      draft_type: selectedType,
      narrative,
      complainant: {
        name: complainantName,
        address: complainantAddress,
        phone: complainantPhone,
      },
      opposite_party: {
        name: oppositePartyName,
        address: oppositePartyAddress,
      },
      incident_date: incidentDate || undefined,
      incident_location: incidentLocation || undefined,
      jurisdiction_forum: jurisdictionForum || undefined,
      monetary_claim: monetaryClaim ? parseFloat(monetaryClaim) : undefined,
      selected_evidence_ids: selectedEvidenceIds,
    };

    try {
      const draft = await DraftService.generateDraft(payload);
      setActiveDraft(draft);
      setEditedMarkdown(draft.content_markdown);
      setSuccessMessage('Court-ready legal draft generated and grounded in statutory Gazettes.');
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || 'Failed to generate legal draft.');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveEdits = async () => {
    if (!activeDraft) return;
    setSavingEdits(true);
    setErrorMessage(null);
    try {
      const updated = await DraftService.updateDraft(activeDraft.id, {
        content_markdown: editedMarkdown,
      });
      setActiveDraft(updated);
      setSuccessMessage('Draft edits saved. PDF and DOCX exports updated.');
      setEditMode(false);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || 'Failed to save edits.');
    } finally {
      setSavingEdits(false);
    }
  };

  const toggleEvidenceSelection = (docId: number) => {
    setSelectedEvidenceIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto py-4 px-2 sm:px-4">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-[#0B132B] to-[#1C2541] border border-[#D4AF37]/30 rounded-2xl p-6 text-white shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="bg-[#D4AF37]/20 border border-[#D4AF37] text-[#D4AF37] text-xs px-2.5 py-0.5 rounded-full font-semibold uppercase tracking-wider flex items-center gap-1.5">
                <Scale className="w-3.5 h-3.5" />
                Phase 6 Studio
              </span>
              <span className="text-gray-400 text-xs flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                Canonical Gazette Grounding
              </span>
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">AI Legal Document Generation Studio</h1>
            <p className="text-sm text-gray-300 mt-1 max-w-2xl">
              Draft formal, court-ready legal documents linked to your evidence exhibits and authenticated Indian statutory provisions.
            </p>
          </div>
          <div className="flex items-center gap-2 bg-[#070D1E]/80 border border-gray-700/60 p-3 rounded-xl text-xs text-gray-300 max-w-sm">
            <ShieldAlert className="w-5 h-5 text-[#D4AF37] shrink-0" />
            <span>
              <strong>Advocates Act, 1961:</strong> Educational draft. Review by an enrolled Advocate recommended before filing.
            </span>
          </div>
        </div>
      </div>

      {/* Notifications */}
      {errorMessage && (
        <div className="bg-rose-900/40 border border-rose-500/50 rounded-xl p-4 text-rose-200 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}
      {successMessage && (
        <div className="bg-emerald-900/30 border border-emerald-500/40 rounded-xl p-4 text-emerald-200 text-sm flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Template Selector Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {DRAFT_TEMPLATES.map((tmpl) => {
          const isSelected = selectedType === tmpl.id;
          return (
            <button
              key={tmpl.id}
              onClick={() => setSelectedType(tmpl.id)}
              className={`p-4 rounded-xl border text-left transition-all duration-200 cursor-pointer ${
                isSelected
                  ? 'bg-[#0B132B] border-[#D4AF37] shadow-lg shadow-[#D4AF37]/10 ring-1 ring-[#D4AF37]'
                  : 'bg-[#1C2541]/50 border-gray-700/60 hover:bg-[#1C2541] hover:border-gray-500'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-[#D4AF37]/10 text-[#D4AF37] border border-[#D4AF37]/30">
                  {tmpl.badge}
                </span>
                {isSelected && <CheckCircle2 className="w-4 h-4 text-[#D4AF37]" />}
              </div>
              <h3 className="text-sm font-bold text-white mb-0.5">{tmpl.label}</h3>
              <p className="text-xs font-medium text-gray-400 mb-2">{tmpl.sublabel}</p>
              <p className="text-xs text-gray-400 line-clamp-2 leading-relaxed">{tmpl.description}</p>
            </button>
          );
        })}
      </div>

      {/* Main Drafting Section: Two Columns (Form on Left / Preview & Results on Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Form Column (5 cols) */}
        <div className="lg:col-span-5 bg-[#0B132B]/90 border border-gray-700/60 rounded-2xl p-6 shadow-xl space-y-5">
          <div className="border-b border-gray-700/60 pb-3 flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <FileText className="w-4 h-4 text-[#D4AF37]" />
              Structured Filing Details
            </h2>
            <span className="text-xs text-gray-400">Step 1: Input Facts</span>
          </div>

          {/* Complainant Section */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-400">Complainant / Applicant Particulars</h4>
            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">Full Legal Name</label>
              <input
                type="text"
                value={complainantName}
                onChange={(e) => setComplainantName(e.target.value)}
                className="w-full bg-[#1C2541]/70 border border-gray-600 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[#D4AF37]"
                placeholder="Citizen Full Legal Name"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">Permanent / Residential Postal Address</label>
              <textarea
                rows={2}
                value={complainantAddress}
                onChange={(e) => setComplainantAddress(e.target.value)}
                className="w-full bg-[#1C2541]/70 border border-gray-600 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[#D4AF37]"
                placeholder="Complete Address with PIN Code"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">Mobile / Telephone</label>
              <input
                type="text"
                value={complainantPhone}
                onChange={(e) => setComplainantPhone(e.target.value)}
                className="w-full bg-[#1C2541]/70 border border-gray-600 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[#D4AF37]"
                placeholder="10-digit mobile number"
              />
            </div>
          </div>

          {/* Opposite Party Section */}
          <div className="space-y-3 pt-2 border-t border-gray-700/40">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-400">Opposite Party / Accused / Noticee</h4>
            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">Full Name / Corporate Entity Name</label>
              <input
                type="text"
                value={oppositePartyName}
                onChange={(e) => setOppositePartyName(e.target.value)}
                className="w-full bg-[#1C2541]/70 border border-gray-600 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[#D4AF37]"
                placeholder="Vendor, Defaulting Party, or Accused"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">Registered Office or Residential Address</label>
              <textarea
                rows={2}
                value={oppositePartyAddress}
                onChange={(e) => setOppositePartyAddress(e.target.value)}
                className="w-full bg-[#1C2541]/70 border border-gray-600 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[#D4AF37]"
                placeholder="Noticee postal coordinates for dispatch"
              />
            </div>
          </div>

          {/* Incident & Jurisdiction Coordinates */}
          <div className="grid grid-cols-2 gap-3 pt-2 border-t border-gray-700/40">
            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">Incident / Bounce Date</label>
              <input
                type="date"
                value={incidentDate}
                onChange={(e) => setIncidentDate(e.target.value)}
                className="w-full bg-[#1C2541]/70 border border-gray-600 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[#D4AF37]"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">Disputed Amount (₹)</label>
              <input
                type="number"
                value={monetaryClaim}
                onChange={(e) => setMonetaryClaim(e.target.value)}
                className="w-full bg-[#1C2541]/70 border border-gray-600 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[#D4AF37]"
                placeholder="Amount in INR"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">Incident Location / City</label>
              <input
                type="text"
                value={incidentLocation}
                onChange={(e) => setIncidentLocation(e.target.value)}
                className="w-full bg-[#1C2541]/70 border border-gray-600 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[#D4AF37]"
                placeholder="e.g. New Delhi, Bengaluru"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">Jurisdiction / Forum / Police Station</label>
              <input
                type="text"
                value={jurisdictionForum}
                onChange={(e) => setJurisdictionForum(e.target.value)}
                className="w-full bg-[#1C2541]/70 border border-gray-600 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[#D4AF37]"
                placeholder="e.g. DCDRC New Delhi or PS Rohini"
              />
            </div>
          </div>

          {/* Narrative */}
          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">Chronological Factual Statement</label>
            <textarea
              rows={4}
              value={narrative}
              onChange={(e) => setNarrative(e.target.value)}
              className="w-full bg-[#1C2541]/70 border border-gray-600 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[#D4AF37]"
              placeholder="State key dates, transactions, breach, and damages suffered..."
            />
          </div>

          {/* Evidence Linking */}
          {availableEvidence.length > 0 && (
            <div className="pt-2 border-t border-gray-700/40">
              <label className="block text-xs font-semibold text-gray-300 mb-2 flex items-center gap-1.5">
                <Paperclip className="w-3.5 h-3.5 text-[#D4AF37]" />
                Link Uploaded Evidence Exhibits ({selectedEvidenceIds.length} Selected)
              </label>
              <div className="max-h-36 overflow-y-auto space-y-1.5 pr-1">
                {availableEvidence.map((doc) => {
                  const isChecked = selectedEvidenceIds.includes(doc.document_id);
                  return (
                    <div
                      key={doc.document_id}
                      onClick={() => toggleEvidenceSelection(doc.document_id)}
                      className={`flex items-center justify-between p-2 rounded-lg border text-xs cursor-pointer ${
                        isChecked
                          ? 'bg-[#D4AF37]/10 border-[#D4AF37]/50 text-white'
                          : 'bg-[#1C2541]/30 border-gray-700 text-gray-400 hover:bg-[#1C2541]/60'
                      }`}
                    >
                      <span className="truncate max-w-[200px]">{doc.filename}</span>
                      <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-gray-800 text-gray-300">
                        {doc.category}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          <button
            onClick={handleGenerateDraft}
            disabled={loading}
            className="w-full py-3 px-4 rounded-xl font-bold text-sm bg-gradient-to-r from-[#D4AF37] to-[#F3E5AB] text-[#0B132B] hover:opacity-95 transition-all shadow-md flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Synthesizing Legal Document...
              </>
            ) : (
              <>
                <Scale className="w-4 h-4" />
                Generate Grounded Legal Draft
              </>
            )}
          </button>
        </div>

        {/* Right Output Column (7 cols): Missing Info Alerts, Citations & Document Preview */}
        <div className="lg:col-span-7 space-y-5">
          {activeDraft ? (
            <>
              {/* Missing Information Alerts */}
              {activeDraft.missing_information && activeDraft.missing_information.length > 0 && (
                <div className="bg-amber-950/40 border border-amber-500/50 rounded-2xl p-5 shadow-lg space-y-3">
                  <div className="flex items-center gap-2 text-amber-300 font-bold text-sm">
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                    Missing Statutory Elements ({activeDraft.missing_information.length} Items Require Attention)
                  </div>
                  <p className="text-xs text-amber-200/80">
                    Indian procedural law requires these ingredients for legal validity. Placeholders have been inserted in the draft.
                  </p>
                  <div className="space-y-2 mt-2">
                    {activeDraft.missing_information.map((item, idx) => (
                      <div key={idx} className="bg-amber-900/30 border border-amber-700/40 rounded-xl p-3 text-xs">
                        <div className="font-semibold text-amber-200 capitalize">
                          {item.field.replace(/_/g, ' ')}
                        </div>
                        <p className="text-gray-300 mt-0.5">{item.rationale}</p>
                        <div className="text-amber-400 font-medium mt-1">Prompt: {item.suggested_prompt}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Verified Statutory Citations Bar */}
              {activeDraft.verified_citations && activeDraft.verified_citations.length > 0 && (
                <div className="bg-[#0B132B] border border-gray-700/60 rounded-2xl p-4 shadow-md">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-gray-300 flex items-center gap-1.5">
                      <BookOpen className="w-3.5 h-3.5 text-[#D4AF37]" />
                      Verified Statutory Grounds (Official Gazette Index)
                    </span>
                    <span className="text-[11px] text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      100% Authentic Citations
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {activeDraft.verified_citations.map((c, i) => (
                      <a
                        key={i}
                        href={c.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[#1C2541] hover:bg-[#1C2541]/80 border border-gray-600 text-xs text-gray-200"
                        title={c.section_title}
                      >
                        <span className="font-semibold text-[#D4AF37]">{c.act_code}</span>
                        <span>Sec {c.section_number}</span>
                        <ExternalLink className="w-3 h-3 text-gray-400 ml-0.5" />
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {/* Document Preview Card */}
              <div className="bg-[#0B132B] border border-gray-700/60 rounded-2xl shadow-2xl overflow-hidden flex flex-col">
                {/* Header Action Bar */}
                <div className="bg-[#070D1E] border-b border-gray-700/60 px-5 py-3.5 flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-white truncate max-w-xs">{activeDraft.title}</span>
                    <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                      Draft #{activeDraft.id}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    {/* View/Edit Mode Toggle */}
                    <button
                      onClick={() => setEditMode(!editMode)}
                      className="px-3 py-1.5 rounded-lg border border-gray-600 text-xs text-gray-300 hover:text-white hover:bg-gray-800 flex items-center gap-1.5 cursor-pointer"
                    >
                      {editMode ? (
                        <>
                          <Eye className="w-3.5 h-3.5 text-blue-400" />
                          Court Preview
                        </>
                      ) : (
                        <>
                          <Edit3 className="w-3.5 h-3.5 text-[#D4AF37]" />
                          Edit Text
                        </>
                      )}
                    </button>

                    {/* Export PDF Button */}
                    <a
                      href={DraftService.getPdfDownloadUrl(activeDraft.id)}
                      download
                      className="px-3 py-1.5 rounded-lg bg-[#D4AF37] hover:bg-[#D4AF37]/90 text-[#0B132B] text-xs font-bold flex items-center gap-1.5 shadow transition-all cursor-pointer"
                    >
                      <Download className="w-3.5 h-3.5" />
                      PDF
                    </a>

                    {/* Export DOCX Button */}
                    <a
                      href={DraftService.getDocxDownloadUrl(activeDraft.id)}
                      download
                      className="px-3 py-1.5 rounded-lg bg-[#1C2541] hover:bg-[#1C2541]/80 border border-gray-600 text-xs font-semibold text-white flex items-center gap-1.5 shadow transition-all cursor-pointer"
                    >
                      <FileDown className="w-3.5 h-3.5 text-blue-400" />
                      DOCX
                    </a>
                  </div>
                </div>

                {/* Body: Markdown Editor or Rendered Court Paper */}
                <div className="p-6 overflow-y-auto max-h-[700px]">
                  {editMode ? (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between text-xs text-gray-400">
                        <span>Markdown Editor (Changes will update exported PDF/DOCX)</span>
                        <button
                          onClick={handleSaveEdits}
                          disabled={savingEdits}
                          className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-medium text-xs flex items-center gap-1 cursor-pointer disabled:opacity-50"
                        >
                          {savingEdits ? <RefreshCw className="w-3 h-3 animate-spin" /> : <CheckCircle2 className="w-3 h-3" />}
                          Save & Re-render
                        </button>
                      </div>
                      <textarea
                        rows={22}
                        value={editedMarkdown}
                        onChange={(e) => setEditedMarkdown(e.target.value)}
                        className="w-full bg-[#070D1E] border border-gray-700 rounded-xl p-4 text-xs font-mono text-gray-200 focus:outline-none focus:border-[#D4AF37] leading-relaxed"
                      />
                    </div>
                  ) : (
                    /* Clean Court-Style Paper Preview */
                    <div className="bg-[#FAF9F6] text-[#1F2937] p-8 rounded-xl shadow-inner font-serif text-xs leading-relaxed space-y-4 border border-gray-300">
                      <div className="text-center border-b-2 border-[#0B132B] pb-3 mb-4">
                        <div className="text-sm font-bold text-[#0B132B] tracking-wider uppercase">
                          {activeDraft.title}
                        </div>
                        <div className="text-[10px] text-gray-600 uppercase font-sans mt-0.5">
                          {activeDraft.draft_type.replace(/_/g, ' ')}
                        </div>
                      </div>

                      {/* Formatted Content */}
                      <div className="whitespace-pre-wrap font-sans text-xs space-y-2 text-gray-800 leading-normal">
                        {activeDraft.content_markdown}
                      </div>

                      {/* Footer Stamp */}
                      <div className="border-t border-gray-400 pt-3 text-[10px] text-gray-500 text-center font-sans">
                        Generated via LegalEase AI Decision Support System • Subject to Advocates Act, 1961
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </>
          ) : (
            /* Placeholder State */
            <div className="bg-[#0B132B]/60 border border-dashed border-gray-700 rounded-2xl p-12 text-center text-gray-400 space-y-4">
              <Scale className="w-12 h-12 text-[#D4AF37]/40 mx-auto" />
              <h3 className="text-base font-semibold text-white">No Document Generated Yet</h3>
              <p className="text-xs text-gray-400 max-w-md mx-auto leading-relaxed">
                Select your legal document template, complete the structured particulars, and click "Generate Grounded Legal Draft".
                The engine will substantiate your claim against authentic Bare Acts and uploaded evidence.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
