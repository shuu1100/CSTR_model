import React, { useState } from 'react';
import { Header } from './components/Header';
import { OverviewPage } from './pages/OverviewPage';
import { SimulatorPage } from './pages/SimulatorPage';
import { SweepsPage } from './pages/SweepsPage';
import { IngestionPage } from './pages/IngestionPage';
import { EstimationPage } from './pages/EstimationPage';
import { MachineLearningPage } from './pages/MachineLearningPage';
import { Activity, ShieldCheck } from 'lucide-react';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('simulator');

  return (
    <div className="relative min-h-screen text-slate-100 flex flex-col font-sans selection:bg-emerald-500 selection:text-white">
      {/* Industrial blurred backdrop + vignette overlay */}
      <div className="industrial-bg" />
      <div className="industrial-overlay" />

      <Header currentTab={currentTab} onTabChange={setCurrentTab} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 z-10">
        {currentTab === 'overview' && (
          <OverviewPage onGoToSimulator={() => setCurrentTab('simulator')} />
        )}
        {currentTab === 'simulator' && <SimulatorPage />}
        {currentTab === 'sweeps' && <SweepsPage />}
        {currentTab === 'ingestion' && <IngestionPage />}
        {currentTab === 'estimation' && <EstimationPage />}
        {currentTab === 'ml' && <MachineLearningPage />}
      </main>

      <footer className="border-t border-slate-800/80 bg-slate-950/70 backdrop-blur-md py-4 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400 font-mono">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-slate-300 font-medium">CSTR Lab • Industrial Digital Twin & SciML Studio</span>
          </div>
          <div className="flex items-center space-x-4 text-[11px] text-slate-500">
            <span className="flex items-center space-x-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>100% Offline & Zero-Leakage Architecture</span>
            </span>
            <span className="flex items-center space-x-1">
              <Activity className="w-3.5 h-3.5 text-cyan-400" />
              <span>Scientific Core v0.1.0</span>
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
