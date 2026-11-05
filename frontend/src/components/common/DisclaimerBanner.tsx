import React, { useState } from 'react';
import { X, ShieldAlert } from 'lucide-react';

interface DisclaimerBannerProps {
  compact?: boolean;
}

export const DisclaimerBanner: React.FC<DisclaimerBannerProps> = ({ compact = false }) => {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed && compact) return null;

  return (
    <aside 
      aria-label="Statutory Legal Disclaimer"
      className="bg-amber-950/40 border-y border-amber-500/30 text-amber-200 px-4 py-2.5 text-xs tracking-wide">
      <div className="max-w-7xl mx-auto flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            <span className="font-semibold text-amber-300 uppercase tracking-wider mr-1.5">
              Statutory Advisory (Advocates Act, 1961):
            </span>
            LegalEase AI is an informational decision support system and does <strong className="text-white underline decoration-amber-400">not</strong> provide formal legal counsel, judicial representation, or lawyer-client privilege. Always verify provisions with an enrolled Advocate or your local District Legal Services Authority (DLSA).
          </p>
        </div>
        {compact && (
          <button
            onClick={() => setDismissed(true)}
            className="text-amber-400 hover:text-white p-1 rounded transition-colors shrink-0"
            title="Dismiss notice"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </aside>
  );
};
