import React from 'react';

interface HeaderProps {
  currentTab: string;
  onTabChange: (tab: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ currentTab, onTabChange }) => {
  const tabTitles: Record<string, string> = {
    overview: 'CSTR-Overview-01',
    'steady-state': 'CSTR-Iso-SteadyState',
    dynamic: 'CSTR-Dynamic-ODE',
    thermal: 'CSTR-Thermal-Coupled',
    sweeps: 'CSTR-Parameter-Sweeps',
    experiments: 'CSTR-Data-Ingestion',
    estimation: 'CSTR-Kinetic-Fit',
    ml: 'CSTR-SciML-Surrogate',
    history: 'CSTR-Run-History',
    reports: 'CSTR-Technical-Audit',
    status: 'CSTR-System-Health',
  };

  return (
    <header className="fixed top-0 left-64 right-0 h-14 bg-white/95 backdrop-blur-sm border-b border-[#CBD9E8] z-40 flex items-center justify-between px-4 shadow-2xs">
      {/* Workspace Breadcrumbs & Telemetry Status Chips */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1 font-mono text-xs text-[#4E657E]">
          <span className="text-[#707881]">WS:</span>
          <span className="text-[#0F1E2E] font-medium">Reactor Unit 01</span>
          <span className="text-[#CBD9E8]">/</span>
          <span className="text-primary font-semibold">{tabTitles[currentTab] || 'CSTR-Iso-04'}</span>
        </div>

        <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-[#EEF4FF] border border-[#CBD9E8] font-mono text-[10px] text-[#4E657E]">
          <span>Core: FastODE 4.2</span>
          <span className="text-[#CBD9E8]">|</span>
          <span>Mem: 184MB</span>
        </div>

        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded border border-[#CBD9E8] bg-white font-mono text-[10px] text-[#0F1E2E] shadow-2xs">
          <span className="w-1.5 h-1.5 rounded-full bg-status-success" />
          <span>Solvers Verified</span>
        </div>
      </div>

      {/* Action Buttons & Profile */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => onTabChange('dynamic')}
          className="flex items-center gap-1 px-3 py-1.5 rounded bg-primary text-white text-xs font-semibold hover:bg-primary-container transition-colors shadow-2xs"
          type="button"
        >
          <span className="material-symbols-outlined text-[16px]">add</span>
          <span>New Simulation</span>
        </button>

        <button
          onClick={() => onTabChange('status')}
          className="w-8 h-8 rounded border border-[#CBD9E8] bg-white flex items-center justify-center text-[#4E657E] hover:text-[#0F1E2E] hover:bg-[#F0F5FA] transition-colors shadow-2xs"
          title="System Diagnostics"
          type="button"
        >
          <span className="material-symbols-outlined text-[18px]">settings</span>
        </button>

        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-sky-600 to-indigo-600 text-white font-bold text-xs flex items-center justify-center border border-[#CBD9E8] ml-1 shadow-2xs">
          CL
        </div>
      </div>
    </header>
  );
};
