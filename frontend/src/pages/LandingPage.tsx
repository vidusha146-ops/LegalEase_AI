import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Scale,
  Brain,
  FileText,
  Clock,
  CheckCircle,
  AlertTriangle,
  ArrowRight,
  Database,
  Lock,
  Sparkles,
  PhoneCall,
} from 'lucide-react';
import type { HealthStatus } from '../types/health';
import { healthService } from '../services/health.service';
import { useAuth } from '../context/AuthContext';
import { SituationAnalyzer } from '../components/analyzer/SituationAnalyzer';
import { EvidenceManager } from '../components/evidence/EvidenceManager';
import { LegalDraftingStudio } from '../components/drafting/LegalDraftingStudio';

interface LandingPageProps {
  onOpenAuth: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onOpenAuth }) => {
  const { user, isAuthenticated } = useAuth();
  const [activeTab, setActiveTab] = useState<'analyzer' | 'evidence' | 'drafting'>('analyzer');
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [healthLoading, setHealthLoading] = useState<boolean>(true);
  const [healthError, setHealthError] = useState<string | null>(null);

  const fetchHealth = async () => {
    setHealthLoading(true);
    setHealthError(null);
    try {
      const data = await healthService.getHealth();
      setHealth(data);
    } catch {
      setHealthError('Unable to connect to backend at http://127.0.0.1:8000');
    } finally {
      setHealthLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="min-h-screen text-slate-100 pb-16">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-20 border-b border-slate-900 bg-gradient-to-b from-slate-950 via-slate-900/60 to-slate-950">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(212,175,55,0.06),transparent_50%)] pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="max-w-3xl mx-auto text-center space-y-6">
            {/* Pill tag */}
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-medium tracking-wide">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              <span>Intelligent Legal Decision Support for Indian Citizens</span>
            </div>

            {/* Headline */}
            <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight font-serif text-white leading-tight">
              Demystifying Indian Law with{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-300 via-amber-400 to-amber-500">
                Grounding & Explainability
              </span>
            </h1>

            {/* Subtitle */}
            <p className="text-base sm:text-lg text-slate-300 leading-relaxed max-w-2xl mx-auto">
              Navigating legal disputes should not be intimidating. LegalEase AI analyzes your grievance, grounds recommendations in verified Indian Bare Acts (BNS, BNSS, BSA, Consumer Act, IT Act), builds chronological evidence timelines, and drafts formal complaints.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
              <a
                href="#situation-analyzer"
                className="px-6 py-3.5 rounded-xl bg-gradient-to-r from-amber-500 via-amber-400 to-amber-500 hover:from-amber-400 hover:to-amber-300 text-slate-950 font-bold text-sm tracking-wide transition-all shadow-lg shadow-amber-500/20 flex items-center gap-2 transform hover:-translate-y-0.5"
              >
                <span>Analyze Your Legal Situation</span>
                <ArrowRight className="w-4 h-4" />
              </a>
              <button
                onClick={onOpenAuth}
                className="px-5 py-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 font-semibold text-sm transition-all flex items-center gap-2"
              >
                <Lock className="w-4 h-4 text-amber-400" />
                <span>{isAuthenticated ? 'Citizen Account' : 'Sign In / Register'}</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* System Core & Live Connectivity Section */}
      <section id="system-status" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-12">
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md">
          <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800/80 gap-4">
            <div>
              <div className="flex items-center gap-2.5">
                <div className="w-3 h-3 rounded-full bg-emerald-400 animate-ping" />
                <h2 className="text-lg font-bold text-white font-serif flex items-center gap-2">
                  <span>Phase 1 Architecture Status: Core Scaffolding Online</span>
                </h2>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                FastAPI backend + Async SQLAlchemy + SQLite/Postgres dual-mode database engine
              </p>
            </div>

            <button
              onClick={fetchHealth}
              disabled={healthLoading}
              className="self-start md:self-auto px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-amber-300 border border-amber-500/20 font-medium transition-colors"
            >
              {healthLoading ? 'Testing Connectivity...' : 'Re-verify Health Endpoint'}
            </button>
          </div>

          {/* Health Diagnostics Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-6">
            {/* Box 1: API Status */}
            <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 flex items-start gap-3.5">
              <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
                <CheckCircle className="w-5 h-5" />
              </div>
              <div>
                <p className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">FastAPI Gateway</p>
                <p className="text-sm font-bold text-white mt-0.5">
                  {healthLoading ? 'Checking...' : health?.status === 'healthy' ? 'Active / Online' : 'Offline'}
                </p>
                <p className="text-[11px] text-slate-400 mt-1 font-mono">Port 8000 • CORS Configured</p>
              </div>
            </div>

            {/* Box 2: Database Status */}
            <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 flex items-start gap-3.5">
              <div className="w-9 h-9 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 shrink-0">
                <Database className="w-5 h-5" />
              </div>
              <div>
                <p className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Database Engine</p>
                <p className="text-sm font-bold text-white mt-0.5">
                  {healthLoading ? 'Checking...' : health?.database_status === 'connected' ? 'SQLite (Async Fallback)' : 'Disconnected'}
                </p>
                <p className="text-[11px] text-slate-400 mt-1 font-mono">SQLAlchemy 2.0 Async</p>
              </div>
            </div>

            {/* Box 3: Authentication Security */}
            <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 flex items-start gap-3.5">
              <div className="w-9 h-9 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
                <Lock className="w-5 h-5" />
              </div>
              <div>
                <p className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Auth & Encryption</p>
                <p className="text-sm font-bold text-white mt-0.5">JWT + Bcrypt</p>
                <p className="text-[11px] text-slate-400 mt-1 font-mono">HS256 24h Expiry</p>
              </div>
            </div>

            {/* Box 4: Current Citizen Session */}
            <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 flex items-start gap-3.5">
              <div className="w-9 h-9 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-300 shrink-0">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <p className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">User Session</p>
                <p className="text-sm font-bold text-white mt-0.5 truncate max-w-[140px]">
                  {isAuthenticated && user ? user.full_name : 'Guest (Unauthenticated)'}
                </p>
                <p className="text-[11px] text-slate-400 mt-1">
                  {isAuthenticated ? 'Session Active' : 'Click Sign In above'}
                </p>
              </div>
            </div>
          </div>

          {healthError && (
            <div className="mt-4 p-3 rounded-lg bg-rose-950/50 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{healthError}</span>
            </div>
          )}
        </div>
      </section>

      {/* Interactive Workspace Navigation Tabs */}
      <section id="workspace-tabs" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16">
        <div className="flex items-center justify-center gap-2 sm:gap-3 p-1.5 rounded-2xl bg-slate-900/90 border border-slate-800 max-w-xl mx-auto mb-10 shadow-lg">
          <button
            type="button"
            onClick={() => setActiveTab('analyzer')}
            className={`flex-1 py-2.5 px-3 sm:px-4 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 sm:gap-2 ${
              activeTab === 'analyzer'
                ? 'bg-[#D4AF37] text-slate-950 shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Brain className="w-4 h-4" />
            Situation Analyzer
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('evidence')}
            className={`flex-1 py-2.5 px-3 sm:px-4 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 sm:gap-2 ${
              activeTab === 'evidence'
                ? 'bg-[#D4AF37] text-slate-950 shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Clock className="w-4 h-4" />
            Evidence & Timeline
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('drafting')}
            className={`flex-1 py-2.5 px-3 sm:px-4 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 sm:gap-2 ${
              activeTab === 'drafting'
                ? 'bg-[#D4AF37] text-slate-950 shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <FileText className="w-4 h-4" />
            Drafting Studio
          </button>
        </div>

        {activeTab === 'analyzer' ? (
          <SituationAnalyzer />
        ) : activeTab === 'evidence' ? (
          <EvidenceManager caseId={101} />
        ) : (
          <LegalDraftingStudio caseId={101} />
        )}
      </section>

      {/* Architectural Modules Matrix */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <h3 className="text-2xl font-bold font-serif text-white">
            Architectural System Modules
          </h3>
          <p className="text-xs sm:text-sm text-slate-400 mt-2">
            Engineered modularly with strict zero-hallucination legal grounding
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1 */}
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 hover:border-amber-500/40 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 mb-5 group-hover:scale-110 transition-transform">
              <Brain className="w-6 h-6" />
            </div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-mono text-amber-400/80 font-semibold">Module 2 & 3</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">Phase 3</span>
            </div>
            <h4 className="text-base font-bold text-white mb-2 font-serif">Intelligent Situation Analyzer</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Analyzes citizen grievances in plain language, classifies legal domain (Criminal, Consumer, Cyber, Labour), and extracts citizen rights with dual BNS/IPC crosswalks.
            </p>
          </div>

          {/* Card 2 */}
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 hover:border-amber-500/40 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mb-5 group-hover:scale-110 transition-transform">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-mono text-emerald-400/80 font-semibold">Module 4 & 5</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">Phase 4</span>
            </div>
            <h4 className="text-base font-bold text-white mb-2 font-serif">Explainability & Uncertainty</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Calculates confidence metrics, detects missing legal facts (e.g., date of occurrence, territorial jurisdiction), and flags uncertainty before suggesting remedies.
            </p>
          </div>

          {/* Card 3 */}
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 hover:border-amber-500/40 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 mb-5 group-hover:scale-110 transition-transform">
              <Clock className="w-6 h-6" />
            </div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-mono text-amber-400/80 font-semibold">Module 6 & 7</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">Phase 5</span>
            </div>
            <h4 className="text-base font-bold text-white mb-2 font-serif">Evidence & Timeline Builder</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Ingests PDFs, notices, and payment receipts via PyMuPDF/OCR. Detects temporal gaps, resolves claim contradictions, and builds chronological incident timelines.
            </p>
          </div>

          {/* Card 4 */}
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 hover:border-amber-500/40 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400 mb-5 group-hover:scale-110 transition-transform">
              <FileText className="w-6 h-6" />
            </div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-mono text-sky-400/80 font-semibold">Module 8</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">Phase 6</span>
            </div>
            <h4 className="text-base font-bold text-white mb-2 font-serif">Legal Document Drafting</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Synthesizes formatted complaint drafts: Police Complaints (FIR drafts), Consumer Grievances (District Commission), RTI Form A, and Legal Notices with export to PDF.
            </p>
          </div>

          {/* Card 5 */}
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 hover:border-amber-500/40 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 mb-5 group-hover:scale-110 transition-transform">
              <Scale className="w-6 h-6" />
            </div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-mono text-purple-400/80 font-semibold">Module 9 & 10</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">Phase 7</span>
            </div>
            <h4 className="text-base font-bold text-white mb-2 font-serif">Verification & Multilingual AI</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Regex and statutory grounding against indexed Indian Gazette texts. Multilingual support offering Hindi legal explanations alongside English.
            </p>
          </div>

          {/* Card 6 */}
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 hover:border-amber-500/40 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400 mb-5 group-hover:scale-110 transition-transform">
              <PhoneCall className="w-6 h-6" />
            </div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-mono text-rose-400/80 font-semibold">Module 11 & 12</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">Phase 7 & 8</span>
            </div>
            <h4 className="text-base font-bold text-white mb-2 font-serif">Legal Aid Finder & Dashboard</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Direct access to NALSA, State & District Legal Services Authorities (SLSA/DLSA), pro-bono resources, and a consolidated citizen case vault.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};
