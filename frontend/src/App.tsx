import { useState, useEffect } from 'react';
import { AuthProvider } from './context/AuthContext';
import { Navbar } from './components/layout/Navbar';
import { DisclaimerBanner } from './components/common/DisclaimerBanner';
import { Footer } from './components/layout/Footer';
import { AuthModal } from './components/auth/AuthModal';
import { LandingPage } from './pages/LandingPage';
import type { HealthStatus } from './types/health';
import { healthService } from './services/health.service';

export function AppContent() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [authModalOpen, setAuthModalOpen] = useState<boolean>(false);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await healthService.getHealth();
        setHealth(data);
      } catch {
        // Handled silently or shown as disconnected
      }
    };
    fetchHealth();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-amber-500 selection:text-slate-950">
      <DisclaimerBanner />
      <Navbar health={health} onOpenAuth={() => setAuthModalOpen(true)} />

      <main className="flex-1">
        <LandingPage onOpenAuth={() => setAuthModalOpen(true)} />
      </main>

      <Footer />

      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
      />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
