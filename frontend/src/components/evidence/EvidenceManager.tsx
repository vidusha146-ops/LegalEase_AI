import React, { useState, useEffect } from 'react';
import {
  Upload,
  FileText,
  Clock,
  AlertTriangle,
  CheckCircle2,
  Trash2,
  Eye,
  Plus,
  Loader2,
  Calendar,
  DollarSign,
  Tag,
  ShieldAlert,
  RefreshCw,
} from 'lucide-react';
import {
  evidenceService,
  type EvidenceDocument,
  type CaseTimeline,
  type ConsistencyCheckResponse,
} from '../../services/evidence.service';

interface EvidenceManagerProps {
  caseId?: number;
  narrative?: string;
  predictedDomain?: string;
}

const CATEGORY_OPTIONS = [
  { value: 'INVOICE_BILL', label: 'Invoice / Bill of Supply' },
  { value: 'BANK_RECORD', label: 'Bank Return Memo / Transaction' },
  { value: 'LEGAL_NOTICE', label: 'Statutory Demand Notice' },
  { value: 'AGREEMENT_CONTRACT', label: 'Agreement / Lease Contract' },
  { value: 'POLICE_COMPLAINT_FIR', label: 'Police Complaint / FIR' },
  { value: 'EMAIL_CORRESPONDENCE', label: 'Email / Written Communication' },
  { value: 'IDENTITY_ADDRESS_PROOF', label: 'Identity / Address Proof' },
  { value: 'OTHER_EVIDENCE', label: 'Other Evidence / Document' },
];

export const EvidenceManager: React.FC<EvidenceManagerProps> = ({
  caseId = 101,
  narrative = '',
  predictedDomain = 'CHEQUE_BOUNCE_NI_ACT',
}) => {
  const [documents, setDocuments] = useState<EvidenceDocument[]>([]);
  const [timeline, setTimeline] = useState<CaseTimeline | null>(null);
  const [consistency, setConsistency] = useState<ConsistencyCheckResponse | null>(null);

  const [uploading, setUploading] = useState(false);
  const [checkingConsistency, setCheckingConsistency] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Preview Modal State
  const [selectedDoc, setSelectedDoc] = useState<EvidenceDocument | null>(null);
  const [showPreviewModal, setShowPreviewModal] = useState(false);

  // Manual Event Form State
  const [showAddEvent, setShowAddEvent] = useState(false);
  const [newEventDate, setNewEventDate] = useState('');
  const [newEventTitle, setNewEventTitle] = useState('');
  const [newEventDesc, setNewEventDesc] = useState('');
  const [addingEvent, setAddingEvent] = useState(false);

  // Initial Data Fetch
  useEffect(() => {
    fetchDocumentsAndTimeline();
  }, [caseId]);

  const fetchDocumentsAndTimeline = async () => {
    try {
      const docs = await evidenceService.listCaseEvidence(caseId);
      setDocuments(docs);
      const tl = await evidenceService.getCaseTimeline(caseId);
      setTimeline(tl);
    } catch {
      // Handled silently for new or uninitialized case
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const fileList = Array.from(files);
      const uploaded = await evidenceService.uploadEvidence(caseId, fileList);
      setSuccessMsg(`Successfully processed ${uploaded.length} evidence document(s).`);
      await fetchDocumentsAndTimeline();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload and extract document text.');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleReclassify = async (docId: number, newCategory: string) => {
    try {
      await evidenceService.reclassifyDocument(docId, newCategory);
      setDocuments((prev) =>
        prev.map((d) => (d.document_id === docId ? { ...d, category: newCategory } : d))
      );
      setSuccessMsg('Evidence category updated successfully.');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update category.');
    }
  };

  const handleDeleteDocument = async (docId: number) => {
    if (!confirm('Are you sure you want to delete this evidence document?')) return;
    try {
      await evidenceService.deleteEvidenceDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.document_id !== docId));
      const tl = await evidenceService.getCaseTimeline(caseId);
      setTimeline(tl);
      setSuccessMsg('Document deleted.');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete document.');
    }
  };

  const handleAddManualEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEventDate || !newEventTitle) return;

    setAddingEvent(true);
    setError(null);
    try {
      await evidenceService.addManualTimelineEvent({
        case_id: caseId,
        event_date: newEventDate,
        event_title: newEventTitle,
        event_description: newEventDesc,
      });
      setNewEventDate('');
      setNewEventTitle('');
      setNewEventDesc('');
      setShowAddEvent(false);
      const tl = await evidenceService.getCaseTimeline(caseId);
      setTimeline(tl);
      setSuccessMsg('Manual timeline event recorded.');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add timeline event.');
    } finally {
      setAddingEvent(false);
    }
  };

  const handleDeleteTimelineEvent = async (eventId: number) => {
    try {
      await evidenceService.deleteTimelineEvent(eventId);
      const tl = await evidenceService.getCaseTimeline(caseId);
      setTimeline(tl);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete event.');
    }
  };

  const handleRunConsistencyCheck = async () => {
    setCheckingConsistency(true);
    setError(null);
    try {
      const res = await evidenceService.checkConsistency({
        case_id: caseId,
        narrative: narrative || 'Legal dispute narrative under analysis',
        predicted_domain: predictedDomain,
      });
      setConsistency(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to perform consistency analysis.');
    } finally {
      setCheckingConsistency(false);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#D4AF37]/10 border border-[#D4AF37]/30 text-[#D4AF37] text-xs font-semibold tracking-wide uppercase">
          <Clock className="w-3.5 h-3.5" />
          Evidence Vault & Chronological Timeline Builder
        </div>
        <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
          Multi-Document Ingestion, OCR & Timeline Construction
        </h2>
        <p className="text-slate-400 max-w-2xl mx-auto text-sm sm:text-base">
          Upload notices, invoices, bank return memos, and contracts. Our document intelligence
          extracts entities, verifies chronological sequences, and identifies evidentiary contradictions.
        </p>
      </div>

      {/* Notifications */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2.5">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}
      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2.5">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Upload Dropzone Card */}
      <div className="p-8 rounded-2xl bg-[#0B132B]/80 border border-dashed border-slate-700/80 hover:border-[#D4AF37]/60 transition-colors text-center shadow-xl backdrop-blur-sm">
        <div className="max-w-md mx-auto space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-[#D4AF37]/10 border border-[#D4AF37]/20 flex items-center justify-center mx-auto text-[#D4AF37]">
            {uploading ? (
              <Loader2 className="w-7 h-7 animate-spin" />
            ) : (
              <Upload className="w-7 h-7" />
            )}
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Upload Supporting Evidence</h3>
            <p className="text-xs text-slate-400 mt-1">
              Supports PDF, DOCX, PNG, JPG, TIFF (Max 15MB per file)
            </p>
          </div>
          <label className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-[#D4AF37] to-[#F3E5AB] text-[#070D1E] font-bold text-xs tracking-wide cursor-pointer hover:opacity-95 transition-opacity shadow-lg shadow-[#D4AF37]/20">
            <span>Select Files for Document Intelligence</span>
            <input
              type="file"
              multiple
              accept=".pdf,.docx,.png,.jpg,.jpeg,.tiff"
              onChange={handleFileUpload}
              disabled={uploading}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {/* Evidence Repository & Document Cards */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-white">
            <FileText className="w-5 h-5 text-[#D4AF37]" />
            <h3 className="font-bold text-lg">
              Uploaded Evidence Documents ({documents.length})
            </h3>
          </div>
          <button
            type="button"
            onClick={handleRunConsistencyCheck}
            disabled={checkingConsistency || documents.length === 0}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-[#D4AF37]/20 hover:text-[#D4AF37] border border-slate-700 text-xs font-semibold text-slate-300 flex items-center gap-2 transition-colors disabled:opacity-40"
          >
            {checkingConsistency ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <RefreshCw className="w-3.5 h-3.5" />
            )}
            Run Consistency Check
          </button>
        </div>

        {documents.length === 0 ? (
          <div className="p-8 rounded-2xl bg-[#0B132B]/50 border border-slate-800 text-center text-slate-500 text-xs">
            No evidence documents uploaded yet. Upload invoices, demand notices, or bank memos above.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {documents.map((doc) => (
              <div
                key={doc.document_id}
                className="p-5 rounded-2xl bg-[#0B132B]/90 border border-slate-800 space-y-3.5 hover:border-slate-700 transition-colors shadow-md"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <div className="w-9 h-9 rounded-xl bg-slate-800 border border-slate-700/80 flex items-center justify-center text-[#D4AF37] shrink-0 mt-0.5">
                      <FileText className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white truncate max-w-[220px]">
                        {doc.filename}
                      </h4>
                      <p className="text-[11px] text-slate-400 font-mono">
                        {doc.file_type} • {(doc.file_size_bytes / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedDoc(doc);
                        setShowPreviewModal(true);
                      }}
                      className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                      title="Preview Text"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDeleteDocument(doc.document_id)}
                      className="p-1.5 rounded-lg bg-slate-800 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 transition-colors"
                      title="Delete Document"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Classification Dropdown */}
                <div className="flex items-center gap-2 pt-1">
                  <span className="text-[11px] text-slate-400 shrink-0 flex items-center gap-1">
                    <Tag className="w-3 h-3 text-[#D4AF37]" />
                    Category:
                  </span>
                  <select
                    value={doc.category}
                    onChange={(e) => handleReclassify(doc.document_id, e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 text-xs focus:outline-none focus:ring-1 focus:ring-[#D4AF37]"
                  >
                    {CATEGORY_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Extracted Entity Highlights */}
                {doc.extracted_entities && (
                  <div className="pt-2 border-t border-slate-800/80 space-y-2 text-[11px]">
                    {doc.extracted_entities.monetary_amounts?.length > 0 && (
                      <div className="flex items-center gap-1.5 text-emerald-400">
                        <DollarSign className="w-3 h-3 shrink-0" />
                        <span className="text-slate-400">Extracted Amount:</span>
                        <span className="font-semibold">
                          {doc.extracted_entities.monetary_amounts[0].formatted}
                        </span>
                      </div>
                    )}
                    {doc.extracted_entities.dates?.length > 0 && (
                      <div className="flex items-center gap-1.5 text-[#D4AF37]">
                        <Calendar className="w-3 h-3 shrink-0" />
                        <span className="text-slate-400">Document Date:</span>
                        <span className="font-semibold">
                          {doc.extracted_entities.dates[0].iso_date}
                        </span>
                      </div>
                    )}
                    {doc.extracted_entities.identifiers?.length > 0 && (
                      <div className="flex items-center gap-1.5 text-sky-400">
                        <Tag className="w-3 h-3 shrink-0" />
                        <span className="text-slate-400">
                          {doc.extracted_entities.identifiers[0].type.replace(/_/g, ' ')}:
                        </span>
                        <span className="font-semibold">
                          {doc.extracted_entities.identifiers[0].value}
                        </span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Consistency & Discrepancies Alerts Card */}
      {consistency && (
        <div className="p-6 rounded-2xl bg-[#0B132B]/90 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-white">
              <ShieldAlert className="w-5 h-5 text-amber-400" />
              <h3 className="font-bold text-base">
                Cross-Document Consistency Analysis ({consistency.discrepancies_count} Discrepancies)
              </h3>
            </div>
            <span
              className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                consistency.is_consistent
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
              }`}
            >
              {consistency.is_consistent ? 'EVIDENTIARY CONSISTENCY VERIFIED' : 'VARIANCE DETECTED'}
            </span>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">{consistency.summary}</p>

          {consistency.discrepancies.length > 0 && (
            <div className="space-y-2">
              <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider block">
                Detected Evidentiary Variances:
              </span>
              <div className="space-y-2">
                {consistency.discrepancies.map((disc, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-200 space-y-1"
                  >
                    <div className="font-bold flex items-center justify-between">
                      <span>{disc.type.replace(/_/g, ' ')}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] bg-amber-500/20 border border-amber-500/30 font-mono">
                        {disc.severity} SEVERITY
                      </span>
                    </div>
                    <p className="text-slate-300 leading-relaxed">{disc.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {consistency.documentary_gaps.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-slate-800">
              <span className="text-xs font-semibold text-sky-400 uppercase tracking-wider block">
                Recommended Supporting Documents to Strengthen Claim:
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {consistency.documentary_gaps.map((gap, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-lg bg-sky-500/10 border border-sky-500/20 text-xs text-sky-200 space-y-1"
                  >
                    <span className="font-bold block">{gap.title}</span>
                    <span className="text-[11px] text-slate-300 block">{gap.statutory_rationale}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Chronological Incident Timeline */}
      <div className="p-6 sm:p-8 rounded-2xl bg-[#0B132B]/80 border border-slate-800 space-y-6 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 text-white">
              <Clock className="w-5 h-5 text-[#D4AF37]" />
              <h3 className="font-bold text-lg">Chronological Incident Timeline</h3>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              {timeline ? `${timeline.dated_events_count} dated events in chronological sequence` : 'Building timeline...'}
            </p>
          </div>

          <button
            type="button"
            onClick={() => setShowAddEvent(!showAddEvent)}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-slate-950 font-bold text-xs flex items-center gap-1.5 transition-all shadow-md self-start sm:self-auto"
          >
            <Plus className="w-4 h-4" />
            Add Manual Event
          </button>
        </div>

        {/* Add Event Form Modal / Accordion */}
        {showAddEvent && (
          <form
            onSubmit={handleAddManualEvent}
            className="p-4 rounded-xl bg-slate-900/90 border border-[#D4AF37]/30 space-y-3 text-xs"
          >
            <div className="font-bold text-white text-sm">Add Incident or Procedural Milestone</div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Date (YYYY-MM-DD): *</label>
                <input
                  type="date"
                  value={newEventDate}
                  onChange={(e) => setNewEventDate(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-slate-200 text-xs focus:ring-1 focus:ring-[#D4AF37]"
                  required
                />
              </div>
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Event Title: *</label>
                <input
                  type="text"
                  placeholder="E.g., Cheque Handed Over to Complainant"
                  value={newEventTitle}
                  onChange={(e) => setNewEventTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-slate-200 text-xs focus:ring-1 focus:ring-[#D4AF37]"
                  required
                />
              </div>
            </div>
            <div>
              <label className="text-[11px] text-slate-400 block mb-1">Event Description & Context:</label>
              <textarea
                rows={2}
                placeholder="Details of what transpired on this date..."
                value={newEventDesc}
                onChange={(e) => setNewEventDesc(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-slate-200 text-xs focus:ring-1 focus:ring-[#D4AF37]"
              />
            </div>
            <div className="flex justify-end gap-2 pt-1">
              <button
                type="button"
                onClick={() => setShowAddEvent(false)}
                className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 text-xs hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={addingEvent}
                className="px-4 py-1.5 rounded-lg bg-[#D4AF37] text-slate-950 font-bold text-xs hover:opacity-90"
              >
                {addingEvent ? 'Adding...' : 'Save Event'}
              </button>
            </div>
          </form>
        )}

        {/* Temporal Gap Warnings */}
        {timeline?.temporal_warnings && timeline.temporal_warnings.length > 0 && (
          <div className="space-y-2">
            {timeline.temporal_warnings.map((w, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200 text-xs flex items-start gap-2.5"
              >
                <Clock className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <p className="leading-relaxed">{w.advisory}</p>
              </div>
            ))}
          </div>
        )}

        {/* Timeline Event Sequence */}
        {timeline?.chronological_events && timeline.chronological_events.length > 0 ? (
          <div className="relative pl-6 sm:pl-8 space-y-6 before:absolute before:left-2.5 sm:before:left-3.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-800">
            {timeline.chronological_events.map((ev, idx) => (
              <div key={idx} className="relative group">
                {/* Timeline Node Dot */}
                <div className="absolute -left-6 sm:-left-8 top-1.5 w-5 h-5 rounded-full bg-[#0B132B] border-2 border-[#D4AF37] flex items-center justify-center text-[10px] font-bold text-[#D4AF37]">
                  {ev.sequence_number || idx + 1}
                </div>

                <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 group-hover:border-slate-700 transition-colors space-y-2">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-[#D4AF37]/10 text-[#D4AF37] border border-[#D4AF37]/20">
                        {ev.event_date}
                      </span>
                      <h4 className="font-bold text-white text-sm">{ev.event_title}</h4>
                    </div>

                    <div className="flex items-center gap-2 text-[11px] text-slate-400">
                      {ev.source_reference && (
                        <span className="truncate max-w-[200px] italic">
                          Ref: {ev.source_reference}
                        </span>
                      )}
                      {ev.is_manual && (
                        <button
                          type="button"
                          onClick={() => handleDeleteTimelineEvent(ev.id)}
                          className="text-slate-500 hover:text-rose-400 p-1"
                          title="Remove Event"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>

                  {ev.event_description && (
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {ev.event_description}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-6 rounded-xl bg-slate-900/40 border border-slate-800/80 text-center text-slate-500 text-xs">
            Timeline is currently empty. Upload evidence documents or add manual milestones above.
          </div>
        )}
      </div>

      {/* Document Text Preview Modal */}
      {showPreviewModal && selectedDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-[#0B132B] border border-slate-800 rounded-2xl max-w-2xl w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h4 className="font-bold text-white text-base">{selectedDoc.filename}</h4>
                <p className="text-xs text-slate-400 font-mono">
                  {selectedDoc.category_title} • {selectedDoc.file_type}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowPreviewModal(false)}
                className="text-slate-400 hover:text-white text-lg font-bold p-1"
              >
                ✕
              </button>
            </div>

            <div className="max-h-96 overflow-y-auto p-4 rounded-xl bg-slate-950 font-mono text-xs text-slate-300 leading-relaxed whitespace-pre-wrap border border-slate-900">
              {selectedDoc.ocr_extracted_text || selectedDoc.extracted_text_preview || 'No text extracted.'}
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={() => setShowPreviewModal(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
