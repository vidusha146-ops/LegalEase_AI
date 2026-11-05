import React from 'react';
import { Scale, Phone, Shield, BookOpen } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-950 border-t border-slate-900 text-slate-400 text-xs py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10">
          {/* Col 1: System Info */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-white font-serif text-base font-bold">
              <Scale className="w-5 h-5 text-amber-400" />
              <span>LegalEase AI</span>
            </div>
            <p className="text-slate-400 text-xs leading-relaxed">
              An intelligent, explainable decision support platform engineered for Indian citizens navigating legal complexities under Bharatiya Nyaya Sanhita (BNS), BNSS, BSA, and specialized central enactments.
            </p>
            <div className="pt-2 text-[11px] text-amber-400/90 font-medium">
              Academic Major Project • Phase 1 Core Architecture
            </div>
          </div>

          {/* Col 2: Emergency Helplines */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold text-white uppercase tracking-wider flex items-center gap-2">
              <Phone className="w-4 h-4 text-amber-400" />
              <span>Official Indian Helplines</span>
            </h4>
            <ul className="space-y-2 text-slate-300 text-xs">
              <li className="flex justify-between items-center py-1 border-b border-slate-900">
                <span className="text-slate-400">Cyber Crime Helpline:</span>
                <span className="font-mono text-amber-400 font-bold">1930</span>
              </li>
              <li className="flex justify-between items-center py-1 border-b border-slate-900">
                <span className="text-slate-400">National Consumer Helpline:</span>
                <span className="font-mono text-amber-400 font-bold">1915</span>
              </li>
              <li className="flex justify-between items-center py-1 border-b border-slate-900">
                <span className="text-slate-400">NALSA Legal Aid:</span>
                <span className="font-mono text-amber-400 font-bold">15100</span>
              </li>
              <li className="flex justify-between items-center py-1">
                <span className="text-slate-400">National Emergency (Police/Medical):</span>
                <span className="font-mono text-amber-400 font-bold">112</span>
              </li>
            </ul>
          </div>

          {/* Col 3: Statutory Frameworks */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold text-white uppercase tracking-wider flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-amber-400" />
              <span>Statutory Frameworks</span>
            </h4>
            <ul className="space-y-1.5 text-xs text-slate-400">
              <li>• Bharatiya Nyaya Sanhita, 2023 (BNS)</li>
              <li>• Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)</li>
              <li>• Bharatiya Sakshya Adhiniyam, 2023 (BSA)</li>
              <li>• Consumer Protection Act, 2019</li>
              <li>• Information Technology Act, 2000 (Cyber Laws)</li>
              <li>• Right to Information Act, 2005 (RTI)</li>
              <li>• Negotiable Instruments Act, 1881 (Sec 138)</li>
            </ul>
          </div>

          {/* Col 4: Legal Shield & Disclaimers */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold text-white uppercase tracking-wider flex items-center gap-2">
              <Shield className="w-4 h-4 text-amber-400" />
              <span>Legal Shield</span>
            </h4>
            <p className="text-[11px] leading-relaxed text-slate-400">
              Strictly non-solicitation platform under Rule 36 of Bar Council of India Rules. AI outputs are probabilistic summaries for initial grievance organization only.
            </p>
            <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-[11px] text-slate-300">
              🔒 <strong>Data Privacy:</strong> Documents are encrypted and processed locally in compliance with the Digital Personal Data Protection Act (DPDPA), 2023.
            </div>
          </div>
        </div>

        <div className="pt-8 border-t border-slate-900 flex flex-col sm:flex-row items-center justify-between gap-4 text-slate-400 text-[11px]">
          <p>© 2026 LegalEase AI. Engineered for academic research and Indian citizen empowerment.</p>
          <p className="text-slate-400">FastAPI • React 19 • TypeScript • Tailwind CSS • SQLAlchemy</p>
        </div>
      </div>
    </footer>
  );
};
