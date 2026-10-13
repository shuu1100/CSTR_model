import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { OverviewPage } from './pages/OverviewPage';
import { SimulatorPage } from './pages/SimulatorPage';
import { ThermalPage } from './pages/ThermalPage';
import { SweepsPage } from './pages/SweepsPage';
import { IngestionPage } from './pages/IngestionPage';
import { EstimationPage } from './pages/EstimationPage';
import { MachineLearningPage } from './pages/MachineLearningPage';
import { HistoryPage } from './pages/HistoryPage';
import { ReportsPage } from './pages/ReportsPage';
import { StatusPage } from './pages/StatusPage';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('overview');

  return (
    <div className="min-h-screen bg-[#F0F5FA] text-[#0F1E2E] font-sans antialiased">
      {/* Fixed Left Sidebar - Scientific Workstation Navigation */}
      <Sidebar currentTab={currentTab} onTabChange={setCurrentTab} />

      {/* Fixed Top Header Toolbar */}
      <Header currentTab={currentTab} onTabChange={setCurrentTab} />

      {/* Main Content Area */}
      <div className="pl-64 pt-14 min-h-screen flex flex-col justify-between">
        <main className="p-4 sm:p-6 w-full max-w-[1700px] mx-auto flex-1">
          {currentTab === 'overview' && (
            <OverviewPage onGoToSimulator={() => setCurrentTab('dynamic')} />
          )}
          {currentTab === 'steady-state' && <SimulatorPage initialMode="steady" />}
          {currentTab === 'dynamic' && <SimulatorPage initialMode="dynamic" />}
          {currentTab === 'thermal' && <ThermalPage />}
          {currentTab === 'sweeps' && <SweepsPage />}
          {currentTab === 'experiments' && <IngestionPage />}
          {currentTab === 'estimation' && <EstimationPage />}
          {currentTab === 'ml' && <MachineLearningPage />}
          {currentTab === 'history' && <HistoryPage />}
          {currentTab === 'reports' && <ReportsPage />}
          {currentTab === 'status' && <StatusPage />}
        </main>

        {/* Workstation Engineering Footer */}
        <footer className="h-9 px-6 bg-[#E4EDF6] border-t border-[#CBD9E8] flex items-center justify-between text-[11px] font-mono text-[#4E657E]">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-status-success animate-pulse" />
              <span className="font-semibold text-[#0F1E2E]">CSTR Lab Digital Twin</span>
            </span>
            <span>•</span>
            <span>Scientific Workstation v2.4-SciML</span>
            <span>•</span>
            <span>FastODE 4.2 / SciPy ODEINT</span>
          </div>

          <div className="flex items-center gap-4">
            <span>Arrhenius Kinetics</span>
            <span>•</span>
            <span>Neural ODE & PINN Active</span>
            <span>•</span>
            <span className="text-emerald-700 font-semibold">100% Local / Zero-Leakage</span>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default App;
