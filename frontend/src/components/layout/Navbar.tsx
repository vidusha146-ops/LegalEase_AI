import React from 'react';
import { Scale, User as UserIcon, LogOut, PhoneCall } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import type { HealthStatus } from '../../types/health';

interface NavbarProps {
  health: HealthStatus | null;
  onOpenAuth: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ health, onOpenAuth }) => {
  const { user, logout, isAuthenticated } = useAuth();

  return (
    <header className="sticky top-0 z-40 bg-slate-950/85 backdrop-blur-md border-b border-slate-800/80 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-18 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-400/20 via-amber-500/10 to-transparent border border-amber-500/40 flex items-center justify-center shadow-inner">
            <Scale className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold tracking-tight text-white font-serif">
                LegalEase<span className="text-amber-400">.AI</span>
              </span>
              <span className="px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/30 rounded-full">
                Bharat
              </span>
            </div>
            <p className="text-[11px] text-slate-400 tracking-wide font-sans">
              Intelligent Legal Decision Support System
            </p>
          </div>
        </div>

        {/* Center / Health Pill */}
        <div className="hidden md:flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs">
            <span
              className={`w-2 h-2 rounded-full ${
                health?.status === 'healthy' ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'
              }`}
            />
            <span className="text-slate-300 font-medium">
              Backend:{' '}
              <strong className={health?.status === 'healthy' ? 'text-emerald-400' : 'text-amber-400'}>
                {health?.status === 'healthy' ? 'Active' : 'Connecting...'}
              </strong>
            </span>
            <span className="text-slate-600">|</span>
            <span className="text-slate-400">
              DB:{' '}
              <strong className="text-slate-200">
                {health?.database_status === 'connected' ? 'SQLite (Dev)' : 'Connecting...'}
              </strong>
            </span>
          </div>

          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300">
            <PhoneCall className="w-3.5 h-3.5 text-amber-400" />
            <span>Cybercrime: <strong>1930</strong> | Consumer: <strong>1915</strong></span>
          </div>
        </div>

        {/* User Auth Controls */}
        <div className="flex items-center gap-3">
          {isAuthenticated && user ? (
            <div className="flex items-center gap-3">
              <div className="text-right hidden sm:block">
                <p className="text-xs font-semibold text-white">{user.full_name}</p>
                <p className="text-[10px] text-slate-400">{user.email}</p>
              </div>
              <div className="w-9 h-9 rounded-full bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-300 font-bold text-sm">
                {user.full_name.charAt(0).toUpperCase()}
              </div>
              <button
                onClick={logout}
                className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-rose-400 hover:border-rose-500/30 transition-all text-xs flex items-center gap-1.5"
                title="Logout"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </div>
          ) : (
            <button
              onClick={onOpenAuth}
              className="px-4 py-2 rounded-lg bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-semibold text-xs tracking-wide transition-all shadow-md shadow-amber-500/10 flex items-center gap-2"
            >
              <UserIcon className="w-4 h-4" />
              <span>Citizen Portal Sign In</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
