import React, { useState } from 'react';
import {
  Scale,
  AlertCircle,
  BookOpen,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  PhoneCall,
  Loader2,
  Calendar,
  Languages,
  FileQuestion,
  ExternalLink,
  Sparkles,
  Check,
  X,
  TrendingUp,
  AlertTriangle,
  Send,
} from 'lucide-react';
import {
  analyzerService,
  type SituationAnalysisResponse,
  type StatuteExplanationResponse,
  type GroundedAiGuidanceResponse,
} from '../../services/analyzer.service';

const SAMPLE_PROMPTS = [
  {
    label: 'Cheque Dishonour',
    text: 'A business client gave me a cheque of Rs 2,50,000 towards purchase of building materials which bounced with remarks "Funds Insufficient". I want to recover my money.',
    date: '2024-08-10',
  },
  {
    label: 'Cyber UPI Phishing',
    text: 'I received an SMS to update electricity KYC. After clicking the link, Rs 85,000 was debited via unauthorized UPI transfers without my knowledge.',
    date: '2024-09-05',
  },
  {
    label: 'Consumer E-Commerce Defect',
    text: 'I bought a smart LED TV from an e-commerce website with 2-year warranty. The display went completely black after 2 months and the seller refused repair or replacement.',
    date: '2024-07-20',
  },
  {
    label: 'Illegal Tenant Eviction',
    text: 'The landlord disconnected our electricity and water supply to forcefully evict us from our rented apartment without court orders before our lease expired.',
    date: '2024-06-15',
  },
  {
    label: 'Article 20(1) Date Contradiction',
    text: 'On 12th January 2024, my bike was stolen from outside my office and the police are registering an FIR under Section 303(1) of the BNS.',
    date: '2024-01-12',
  },
];

export const SituationAnalyzer: React.FC = () => {
  const [narrative, setNarrative] = useState('');
  const [incidentDate, setIncidentDate] = useState('');
  const [isContinuing, setIsContinuing] = useState(false);
  const [language, setLanguage] = useState<'en' | 'hi'>('en');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Core Analysis State
  const [analysis, setAnalysis] = useState<SituationAnalysisResponse | null>(null);

  // Interactive Gap Answering State
  const [gapAnswers, setGapAnswers] = useState<Record<string, string>>({});
  const [resolvingGaps, setResolvingGaps] = useState(false);
  const [gapSuccessMsg, setGapSuccessMsg] = useState<string | null>(null);

  // Statute Decomposition State
  const [selectedStatute, setSelectedStatute] = useState<StatuteExplanationResponse | null>(null);
  const [loadingStatute, setLoadingStatute] = useState(false);

  // Grounded AI Guidance State
  const [aiGuidance, setAiGuidance] = useState<GroundedAiGuidanceResponse | null>(null);
  const [loadingAi, setLoadingAi] = useState(false);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!narrative.trim() || narrative.trim().length < 10) {
      setError('Please provide at least 10 characters describing the situation.');
      return;
    }

    setLoading(true);
    setError(null);
    setGapAnswers({});
    setGapSuccessMsg(null);
    setAiGuidance(null);

    try {
      const res = await analyzerService.analyzeSituation({
        narrative,
        incident_date: incidentDate || undefined,
        is_continuing_offense: isContinuing,
        preferred_language: language,
      });
      setAnalysis(res);
      if (res.statute_element_mapping) {
        setSelectedStatute(res.statute_element_mapping);
      } else {
        setSelectedStatute(null);
      }
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          'Failed to complete situation analysis. Please ensure the backend is running.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleFetchStatuteExplanation = async (actCode: string, sectionNumber: string) => {
    setLoadingStatute(true);
    try {
      const res = await analyzerService.explainStatute({
        narrative,
        act_code: actCode,
        section_number: sectionNumber,
      });
      setSelectedStatute(res);
    } catch (err) {
      console.error('Failed to explain statute', err);
    } finally {
      setLoadingStatute(false);
    }
  };

  const handleResolveGaps = async () => {
    if (!analysis) return;
    const answeredKeys = Object.keys(gapAnswers).filter((k) => gapAnswers[k]?.trim());
    if (answeredKeys.length === 0) {
      setError('Please enter at least one answer to resolve legal gaps.');
      return;
    }

    setResolvingGaps(true);
    setError(null);

    try {
      const res = await analyzerService.resolveGaps({
        original_narrative: narrative,
        domain: analysis.predicted_domain,
        incident_date: incidentDate || undefined,
        is_continuing_offense: isContinuing,
        preferred_language: language,
        answers: gapAnswers,
      });

      setNarrative(res.augmented_narrative);
      setAnalysis(res.updated_analysis);
      if (res.statute_explanation) {
        setSelectedStatute(res.statute_explanation);
      }
      setGapSuccessMsg(
        `Score elevated by +${(res.score_delta * 100).toFixed(1)}%! Groundability improved from ${(
          res.previous_score * 100
        ).toFixed(1)}% to ${(res.elevated_score * 100).toFixed(1)}% (${res.resolved_count} gaps resolved).`
      );
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to resolve gaps.');
    } finally {
      setResolvingGaps(false);
    }
  };

  const handleGenerateAiGuidance = async () => {
    if (!narrative) return;
    setLoadingAi(true);
    try {
      const res = await analyzerService.generateAiExplanation({
        narrative,
        incident_date: incidentDate || undefined,
        is_continuing_offense: isContinuing,
        preferred_language: language,
      });
      setAiGuidance(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate AI guidance.');
    } finally {
      setLoadingAi(false);
    }
  };

  const loadSample = (sample: (typeof SAMPLE_PROMPTS)[0]) => {
    setNarrative(sample.text);
    setIncidentDate(sample.date);
    setError(null);
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#D4AF37]/10 border border-[#D4AF37]/30 text-[#D4AF37] text-xs font-semibold tracking-wide uppercase">
          <Scale className="w-3.5 h-3.5" />
          Explainable Legal AI & Situation Analyzer
        </div>
        <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
          Explainable Legal Reasoning & Statutory Grounding
        </h2>
        <p className="text-slate-400 max-w-2xl mx-auto text-sm sm:text-base">
          Describe your legal issue. Our system decomposes Indian Bare Acts into constituent elements,
          detects ambiguities and contradictions, and guides you to resolve evidentiary gaps.
        </p>
      </div>

      {/* Input Form Card */}
      <div className="p-6 sm:p-8 rounded-2xl bg-[#0B132B]/80 border border-slate-800 shadow-xl backdrop-blur-sm">
        <form onSubmit={handleAnalyze} className="space-y-6">
          {/* Quick Sample Prompts */}
          <div>
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
              Try a realistic scenario:
            </label>
            <div className="flex flex-wrap gap-2">
              {SAMPLE_PROMPTS.map((sp) => (
                <button
                  key={sp.label}
                  type="button"
                  onClick={() => loadSample(sp)}
                  className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800/80 hover:bg-[#D4AF37]/20 hover:text-[#D4AF37] text-slate-300 border border-slate-700/60 transition-colors"
                >
                  {sp.label}
                </button>
              ))}
            </div>
          </div>

          {/* Narrative Textarea */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-200 flex items-center justify-between">
              <span>Describe Your Legal Problem / Situation: *</span>
              <span className="text-xs text-slate-400">
                {narrative.length} characters
              </span>
            </label>
            <textarea
              rows={4}
              value={narrative}
              onChange={(e) => setNarrative(e.target.value)}
              placeholder="E.g., On 15th August 2024, I paid Rs 60,000 for a laptop which was delivered with a broken screen. The seller refused refund or replacement..."
              className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-700/70 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-[#D4AF37] focus:border-transparent text-sm leading-relaxed"
              required
            />
          </div>

          {/* Metadata Controls */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Incident Date */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-[#D4AF37]" />
                Date of Incident
              </label>
              <input
                type="date"
                value={incidentDate}
                onChange={(e) => setIncidentDate(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-900/90 border border-slate-700/70 text-slate-200 text-sm focus:outline-none focus:ring-1 focus:ring-[#D4AF37]"
              />
              <span className="text-[11px] text-slate-400 block">
                Crucial for BNS vs IPC applicability
              </span>
            </div>

            {/* Continuing Offense */}
            <div className="flex items-center space-x-3 sm:pt-6">
              <input
                type="checkbox"
                id="isContinuing"
                checked={isContinuing}
                onChange={(e) => setIsContinuing(e.target.checked)}
                className="w-4 h-4 rounded text-[#D4AF37] bg-slate-900 border-slate-700 focus:ring-[#D4AF37]"
              />
              <label htmlFor="isContinuing" className="text-xs font-medium text-slate-300">
                Continuing / Ongoing Offense
              </label>
            </div>

            {/* Preferred Language */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <Languages className="w-3.5 h-3.5 text-[#D4AF37]" />
                Explanation Language
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value as 'en' | 'hi')}
                className="w-full px-3 py-2 rounded-lg bg-slate-900/90 border border-slate-700/70 text-slate-200 text-sm focus:outline-none focus:ring-1 focus:ring-[#D4AF37]"
              >
                <option value="en">English (Official)</option>
                <option value="hi">हिन्दी (Hindi)</option>
              </select>
            </div>
          </div>

          {error && (
            <div className="p-3.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-gradient-to-r from-[#D4AF37] to-[#F3E5AB] text-[#070D1E] font-bold text-sm tracking-wide hover:opacity-95 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2 shadow-lg shadow-[#D4AF37]/20"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Analyzing Statutory Grounding...
              </>
            ) : (
              <>
                Analyze Legal Situation & Grounding
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>
      </div>

      {/* Analysis Results Display */}
      {analysis && (
        <div className="space-y-8 animate-fadeIn">
          {/* Top Level Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Predicted Domain Card */}
            <div className="p-5 rounded-2xl bg-[#0B132B]/80 border border-slate-800 shadow-md">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                Predicted Legal Domain
              </span>
              <div className="text-lg font-bold text-[#D4AF37] mb-1">
                {analysis.predicted_domain.replace(/_/g, ' ')}
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-medium">
                  {(analysis.classification_confidence * 100).toFixed(1)}% Confidence
                </span>
                <span>(ML Multi-class Classifier)</span>
              </div>
            </div>

            {/* Information Quality Gauge */}
            <div className="p-5 rounded-2xl bg-[#0B132B]/80 border border-slate-800 shadow-md md:col-span-2">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Information Quality & Groundability (S_IQ)
                </span>
                <span
                  className="px-2.5 py-0.5 rounded-full text-xs font-bold"
                  style={{
                    backgroundColor: `${analysis.information_quality.badge_color}20`,
                    color: analysis.information_quality.badge_color,
                    border: `1px solid ${analysis.information_quality.badge_color}50`,
                  }}
                >
                  {analysis.information_quality.badge.replace(/_/g, ' ')}
                </span>
              </div>

              {/* Progress bar */}
              <div className="space-y-1.5 mb-3">
                <div className="flex justify-between text-xs font-semibold text-slate-200">
                  <span>Groundability Score</span>
                  <span>{(analysis.information_quality.score * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full h-2.5 rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${analysis.information_quality.score * 100}%`,
                      backgroundColor: analysis.information_quality.badge_color,
                    }}
                  />
                </div>
              </div>

              {/* Component breakdown */}
              <div className="grid grid-cols-4 gap-2 pt-2 border-t border-slate-800/80 text-[11px] text-slate-400">
                <div>
                  <span className="block text-slate-500">Statutory Grounding:</span>
                  <span className="font-semibold text-slate-300">
                    {(analysis.information_quality.component_scores.statutory_grounding * 100).toFixed(0)}%
                  </span>
                </div>
                <div>
                  <span className="block text-slate-500">Facts Provided:</span>
                  <span className="font-semibold text-slate-300">
                    {(analysis.information_quality.component_scores.factual_completeness * 100).toFixed(0)}%
                  </span>
                </div>
                <div>
                  <span className="block text-slate-500">Citations Grounding:</span>
                  <span className="font-semibold text-slate-300">
                    {(analysis.information_quality.component_scores.citation_validity * 100).toFixed(0)}%
                  </span>
                </div>
                <div>
                  <span className="block text-slate-500">Contradiction Penalty:</span>
                  <span className="font-semibold text-rose-400">
                    -{(analysis.information_quality.component_scores.contradiction_penalty * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Uncertainty & Ambiguity Alerts Panel */}
          {analysis.uncertainty_analysis && (
            <div className="p-5 rounded-2xl bg-[#0B132B]/80 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-white">
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                  <h4 className="font-bold text-sm text-slate-100">
                    Uncertainty & Ambiguity Detection
                  </h4>
                </div>
                <span className="text-xs text-slate-400">
                  Uncertainty Score: {(analysis.uncertainty_analysis.uncertainty_score * 100).toFixed(0)}%
                </span>
              </div>

              {(analysis.uncertainty_analysis.detected_ambiguities || analysis.uncertainty_analysis.ambiguities)?.length > 0 && (
                <div className="space-y-1.5">
                  <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider block">
                    Vague / Ambiguous Expressions:
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {(analysis.uncertainty_analysis.detected_ambiguities || analysis.uncertainty_analysis.ambiguities).map((item: any, i: number) => (
                      <div key={i} className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-200">
                        <span className="font-bold block">"{item.expression || item.type.replace(/_/g, ' ')}"</span>
                        <span className="text-[11px] text-slate-300">{item.rationale || item.issue}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {(analysis.uncertainty_analysis.detected_contradictions || analysis.uncertainty_analysis.contradictions)?.length > 0 && (
                <div className="space-y-1.5 pt-2">
                  <span className="text-xs font-semibold text-rose-400 uppercase tracking-wider block">
                    Statutory / Chronological Contradictions:
                  </span>
                  <div className="space-y-2">
                    {(analysis.uncertainty_analysis.detected_contradictions || analysis.uncertainty_analysis.contradictions).map((item: any, i: number) => (
                      <div key={i} className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-xs text-rose-200">
                        <div className="flex items-center gap-2 font-bold mb-1">
                          <X className="w-3.5 h-3.5 text-rose-400" />
                          <span>{item.type.replace(/_/g, ' ')} {item.severity ? `(${item.severity})` : ''}</span>
                        </div>
                        <p className="text-slate-300 leading-relaxed">{item.explanation || item.issue}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {analysis.uncertainty_analysis.unsupported_assumptions?.length > 0 && (
                <div className="space-y-1.5 pt-2">
                  <span className="text-xs font-semibold text-sky-400 uppercase tracking-wider block">
                    Citizen Assumptions Identified:
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {analysis.uncertainty_analysis.unsupported_assumptions.map((item: any, i: number) => (
                      <div key={i} className="p-2.5 rounded-lg bg-sky-500/10 border border-sky-500/20 text-xs text-sky-200">
                        <span className="font-bold block">"{item.phrase || item.assumption}"</span>
                        <span className="text-[11px] text-slate-300">{item.clarification || item.correction}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Temporal Transition Banner (if applicable) */}
          {analysis.temporal_applicability && (
            <div className="p-4 rounded-xl bg-blue-950/40 border border-blue-500/30 text-blue-200 text-xs flex items-start gap-3">
              <ShieldCheck className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <div className="font-semibold text-blue-300">
                  Statutory Temporal Determination ({analysis.temporal_applicability.incident_date}):
                </div>
                <p className="text-slate-300 leading-relaxed">
                  {analysis.temporal_applicability.guidance}
                </p>
                <div className="text-[11px] text-blue-400/80 font-mono">
                  {analysis.temporal_applicability.savings_clause}
                </div>
              </div>
            </div>
          )}

          {/* Interactive Legal Gap Resolution Workflow */}
          {analysis.legal_gaps.follow_up_questions.length > 0 && (
            <div className="p-6 rounded-2xl bg-amber-500/5 border border-amber-500/20 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-amber-400">
                  <FileQuestion className="w-5 h-5" />
                  <h3 className="font-bold text-base text-amber-300">
                    Interactive Legal Gap Resolution ({analysis.legal_gaps.missing_count} Missing Ingredients)
                  </h3>
                </div>
                <span className="text-xs text-amber-400 font-medium">
                  Dynamic Information Score Elevation
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Indian statutory forums (Consumer Commissions, Police, Magistrates, Labour Tribunals) require specific factual ingredients to proceed. Provide the missing information below to strengthen your claim:
              </p>

              {gapSuccessMsg && (
                <div className="p-3.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>{gapSuccessMsg}</span>
                </div>
              )}

              <div className="space-y-3">
                {analysis.legal_gaps.follow_up_questions.map((fq) => (
                  <div
                    key={fq.ingredient_id}
                    className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-200">{fq.name}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                        {fq.severity}
                      </span>
                    </div>
                    <p className="text-slate-300 font-medium">"{fq.question}"</p>
                    <p className="text-[11px] text-slate-500 italic">Why needed: {fq.rationale}</p>
                    <div className="pt-1">
                      <input
                        type="text"
                        value={gapAnswers[fq.ingredient_id] || ''}
                        onChange={(e) =>
                          setGapAnswers({ ...gapAnswers, [fq.ingredient_id]: e.target.value })
                        }
                        placeholder="Provide details or evidence regarding this point..."
                        className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700/80 text-slate-200 text-xs focus:outline-none focus:ring-1 focus:ring-[#D4AF37]"
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="button"
                  onClick={handleResolveGaps}
                  disabled={resolvingGaps}
                  className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-slate-950 font-bold text-xs flex items-center gap-2 transition-all disabled:opacity-50 shadow-md"
                >
                  {resolvingGaps ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      Recalculating Groundability...
                    </>
                  ) : (
                    <>
                      <Send className="w-3.5 h-3.5" />
                      Submit Details & Elevate Score
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Explainable Statutory Element Mapping */}
          {selectedStatute && (
            <div className="p-6 rounded-2xl bg-[#0B132B]/90 border border-[#D4AF37]/30 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-white">
                  <Scale className="w-5 h-5 text-[#D4AF37]" />
                  <h3 className="font-bold text-base text-white">
                    Statutory Element Decomposition: {selectedStatute.act_code} Section {selectedStatute.section_number} ({selectedStatute.offence_title})
                  </h3>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#D4AF37]/10 text-[#D4AF37] border border-[#D4AF37]/30">
                    {selectedStatute.fulfilled_elements} / {selectedStatute.total_elements} Elements Satisfied ({(selectedStatute.fulfillment_ratio * 100).toFixed(0)}%)
                  </span>
                </div>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Under Indian jurisprudence, an offence or cause of action requires every statutory element to be proven. Below is the mapping of your facts to each element:
              </p>

              <div className="space-y-3">
                {selectedStatute.elements_breakdown.map((elem) => (
                  <div
                    key={elem.id}
                    className={`p-4 rounded-xl border text-xs space-y-2 transition-colors ${
                      elem.fulfilled
                        ? 'bg-emerald-950/20 border-emerald-500/30'
                        : 'bg-slate-900/90 border-slate-800'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-2 font-semibold">
                        {elem.fulfilled ? (
                          <span className="p-1 rounded-full bg-emerald-500/20 text-emerald-400">
                            <Check className="w-3.5 h-3.5" />
                          </span>
                        ) : (
                          <span className="p-1 rounded-full bg-rose-500/20 text-rose-400">
                            <X className="w-3.5 h-3.5" />
                          </span>
                        )}
                        <span className={elem.fulfilled ? 'text-emerald-200' : 'text-slate-200'}>
                          {elem.label}
                        </span>
                      </div>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase shrink-0 ${
                          elem.fulfilled
                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                            : 'bg-slate-800 text-slate-400 border border-slate-700'
                        }`}
                      >
                        {elem.fulfilled ? 'Satisfied by Facts' : 'Evidence Pending'}
                      </span>
                    </div>

                    <p className="text-[11px] font-mono text-slate-400 bg-slate-950/60 p-2.5 rounded border border-slate-900">
                      Statutory Definition: {elem.statutory_text}
                    </p>

                    <div className="flex flex-col sm:flex-row gap-2 pt-1 text-[11px]">
                      {elem.evidence_excerpt && (
                        <div className="text-emerald-300">
                          <span className="font-semibold text-slate-400">Evidence from your text: </span>
                          "{elem.evidence_excerpt}"
                        </div>
                      )}
                      <div className="text-slate-300">
                        <span className="font-semibold text-slate-400">Analysis: </span>
                        {elem.explanation}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Applicable Verified Bare Act Sections */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-white">
                <BookOpen className="w-5 h-5 text-[#D4AF37]" />
                <h3 className="font-bold text-lg">Applicable Indian Bare Act Provisions</h3>
              </div>
              <span className="text-xs text-slate-400">
                Grounded in official Gazette texts
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {analysis.applicable_statutes.map((stat, idx) => (
                <div
                  key={idx}
                  className="p-5 rounded-2xl bg-[#0B132B]/90 border border-slate-800 space-y-3 hover:border-[#D4AF37]/50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-[11px] font-bold text-[#D4AF37] uppercase tracking-wider block">
                        {stat.act_title} ({stat.act_code})
                      </span>
                      <h4 className="text-base font-bold text-white mt-0.5">
                        Section {stat.section_number}: {stat.section_title}
                      </h4>
                    </div>
                    {stat.provision_type && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-300 border border-slate-700 shrink-0">
                        {stat.provision_type}
                      </span>
                    )}
                  </div>

                  {stat.historical_crosswalk && (
                    <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs space-y-1">
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">
                        Historical IPC Transition Crosswalk:
                      </span>
                      <div className="text-slate-200">
                        {stat.historical_crosswalk.ipc_equivalent} ({stat.historical_crosswalk.role})
                      </div>
                      <p className="text-[11px] text-slate-400">
                        {stat.historical_crosswalk.notes}
                      </p>
                    </div>
                  )}

                  <p className="text-xs text-slate-300 leading-relaxed font-serif line-clamp-4 bg-slate-950/60 p-3 rounded-lg border border-slate-900">
                    {stat.document}
                  </p>

                  <div className="flex items-center justify-between pt-1">
                    {stat.source_url ? (
                      <a
                        href={stat.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 text-xs text-[#D4AF37] hover:underline"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        Official Gazette Source
                      </a>
                    ) : <div />}

                    <button
                      type="button"
                      onClick={() => handleFetchStatuteExplanation(stat.act_code, stat.section_number)}
                      disabled={loadingStatute}
                      className="px-3 py-1 rounded-lg bg-slate-800 hover:bg-[#D4AF37]/20 hover:text-[#D4AF37] text-slate-300 border border-slate-700 text-xs font-medium transition-colors"
                    >
                      Decompose Elements
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Grounded Situation Guidance via Gemini Analyzer */}
          <div className="p-6 rounded-2xl bg-[#0B132B]/80 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-white">
                <Sparkles className="w-5 h-5 text-[#D4AF37]" />
                <h3 className="font-bold text-lg">Structured Plain-Language Guidance</h3>
              </div>
              {!aiGuidance && (
                <button
                  type="button"
                  onClick={handleGenerateAiGuidance}
                  disabled={loadingAi}
                  className="px-4 py-2 rounded-xl bg-[#D4AF37]/20 hover:bg-[#D4AF37]/30 text-[#D4AF37] border border-[#D4AF37]/40 text-xs font-semibold flex items-center gap-1.5 transition-colors"
                >
                  {loadingAi ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      Synthesizing...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-3.5 h-3.5" />
                      Generate Grounded Guidance
                    </>
                  )}
                </button>
              )}
            </div>

            {aiGuidance ? (
              <div className="space-y-4 text-xs">
                <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-slate-400">
                    <span className="font-semibold text-slate-300">Situation Summary</span>
                    <span className="text-[10px] uppercase font-mono">{aiGuidance.grounded_ai_guidance.source}</span>
                  </div>
                  <p className="text-slate-200 leading-relaxed">
                    {aiGuidance.grounded_ai_guidance.plain_language_summary}
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Citizen Rights */}
                  <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
                    <span className="font-semibold text-emerald-400 uppercase tracking-wider block">
                      Recognized Statutory Rights:
                    </span>
                    <ul className="space-y-1.5 list-disc list-inside text-slate-300">
                      {aiGuidance.grounded_ai_guidance.citizen_rights.map((r, i) => (
                        <li key={i} className="leading-relaxed">{r}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Immediate Steps */}
                  <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
                    <span className="font-semibold text-[#D4AF37] uppercase tracking-wider block">
                      Immediate Actionable Steps:
                    </span>
                    <ul className="space-y-1.5 list-disc list-inside text-slate-300">
                      {aiGuidance.grounded_ai_guidance.immediate_steps.map((s, i) => (
                        <li key={i} className="leading-relaxed">{s}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Advisory Warning */}
                {aiGuidance.grounded_ai_guidance.advisory_warning && (
                  <div className="p-3.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-200 text-xs">
                    <span className="font-bold block mb-1">Procedural Caution:</span>
                    {aiGuidance.grounded_ai_guidance.advisory_warning}
                  </div>
                )}
              </div>
            ) : (
              <p className="text-xs text-slate-400 leading-relaxed">
                Click "Generate Grounded Guidance" to synthesize plain-language legal rights, actionable timelines, and forum procedures strictly grounded in retrieved Bare Acts.
              </p>
            )}
          </div>

          {/* Recommended Citizen Actions & Procedural Steps */}
          <div className="p-6 rounded-2xl bg-[#0B132B]/80 border border-slate-800 space-y-4">
            <div className="flex items-center gap-2 text-white">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <h3 className="font-bold text-lg">Recommended Procedural Roadmap</h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {analysis.recommended_actions.map((act, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1.5 text-xs"
                >
                  <span className="font-bold text-[#D4AF37] block">{act.step}</span>
                  <p className="text-slate-300 leading-relaxed">{act.action}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Emergency Helplines Pill Grid */}
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
              Official Indian Grievance & Emergency Helplines:
            </span>
            <div className="flex flex-wrap gap-3">
              {Object.entries(analysis.emergency_helplines).map(([key, num]) => (
                <a
                  key={key}
                  href={`tel:${num}`}
                  className="px-3.5 py-2 rounded-xl bg-slate-800/80 hover:bg-[#D4AF37]/20 border border-slate-700/80 text-xs font-medium text-slate-200 flex items-center gap-2 transition-colors"
                >
                  <PhoneCall className="w-3.5 h-3.5 text-[#D4AF37]" />
                  <span>{key.replace(/_/g, ' ')}:</span>
                  <span className="font-bold text-white">{num}</span>
                </a>
              ))}
            </div>
          </div>

          {/* Advocates Act Statutory Disclaimer */}
          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 text-[11px] text-slate-400 leading-relaxed text-center">
            {analysis.statutory_disclaimer}
          </div>
        </div>
      )}
    </div>
  );
};
