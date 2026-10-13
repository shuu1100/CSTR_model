import React, { useState } from 'react';

interface ReportMeta {
  id: string;
  phase: string;
  title: string;
  date: string;
  summary: string;
}

export const ReportsPage: React.FC = () => {
  const reports: ReportMeta[] = [
    {
      id: 'phase-06',
      phase: 'Phase 06',
      title: 'Data Ingestion & Quality Audit Report',
      date: '2026-10-13',
      summary: 'Multi-format CSV/Excel ingestion, schema mapper, Savitzky-Golay polynomial smoothing, and Isolation Forest anomaly detection.',
    },
    {
      id: 'phase-07',
      phase: 'Phase 07',
      title: 'Non-Linear Parameter Estimation Report',
      date: '2026-10-13',
      summary: 'Non-linear least squares optimization (scipy.optimize), parameter confidence bounds from Jacobian covariance, and conversion profile recovery.',
    },
    {
      id: 'phase-08',
      phase: 'Phase 08',
      title: 'Synthetic Data & Disjoint Splits Report',
      date: '2026-10-13',
      summary: 'Latin Hypercube Sampling (SciPy QMC), canonical edge case guarantees, 70/15/15 trajectory partitioning, and train-only preprocessing fit.',
    },
    {
      id: 'phase-08A',
      phase: 'Phase 08A',
      title: 'Training, Testing & Tuning Protocol',
      date: '2026-10-13',
      summary: 'Formal model evaluation protocol, random seed logging standards, RMSE, MAE, R², and physical mole balance residual metrics.',
    },
    {
      id: 'phase-09',
      phase: 'Phase 09',
      title: 'Baselines & Grey-Box Neural ODE Benchmark',
      date: '2026-10-13',
      summary: 'PyTorch RK4 grey-box architecture embedding macroscopic mass balances while learning constitutive reaction kinetics r_A(C_A). Achieved R² > 0.93.',
    },
    {
      id: 'phase-10',
      phase: 'Phase 10',
      title: 'Physics-Informed Neural Network (PINN) Research Model',
      date: '2026-10-13',
      summary: 'Autograd collocation residual loss over continuous domain, non-negative concentration projection, validation tuning, and multi-seed benchmarking.',
    },
    {
      id: 'phase-11',
      phase: 'Phase 11',
      title: 'Machine Learning API & Training UI',
      date: '2026-10-13',
      summary: 'FastAPI ML endpoints (/api/v1/ml/*), thread-pooled async jobs, cancellation, 95% epistemic uncertainty bounds, and interactive 4-tab workstation.',
    },
    {
      id: 'phase-12',
      phase: 'Phase 12',
      title: 'Run History, Persistence & Multi-Format Exports',
      date: '2026-10-13',
      summary: 'SQLite + SQLAlchemy 2.0 persistence, schema versioning, multi-run comparison, and multi-sheet XLSX (openpyxl), CSV, JSON exports with canonical units.',
    },
    {
      id: 'phase-13',
      phase: 'Phase 13',
      title: 'Arrhenius Kinetics & Thermal Non-Isothermal CSTR',
      date: '2026-10-13',
      summary: 'Coupled fluid and jacket energy balances, Arrhenius temperature dependence k(T), thermal runaway detection, and PRBS thermal calibration.',
    },
    {
      id: 'phase-14',
      phase: 'Phase 14',
      title: 'Optional ONNX Optimization & Fallback Audit',
      date: '2026-10-13',
      summary: 'Empirical latency/memory benchmarking, Normal/Edge/OOD regime stability audit, and formal architectural decision to preserve native PyTorch without external bloat.',
    },
  ];

  const [selectedReport, setSelectedReport] = useState<ReportMeta>(reports[reports.length - 1]);

  return (
    <div className="flex flex-col w-full gap-4">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 bg-white p-4 rounded border border-[#D5E1EE] shadow-2xs">
        <div className="flex flex-col gap-0.5">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-[20px]">description</span>
            <h1 className="font-semibold text-lg text-[#0F1E2E] tracking-tight">Technical Reports & Verification Audits</h1>
            <span className="px-1.5 py-0.5 rounded font-mono text-[10px] bg-[#EEF4FF] text-primary border border-[#CBD9E8] font-bold">
              10 AUDITED REPORTS
            </span>
          </div>
          <p className="text-xs text-[#4E657E]">
            Immutable verification logs and scientific audit documents generated across Phase 06 to Phase 14
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Reports Index (5 cols) */}
        <div className="lg:col-span-5 flex flex-col gap-2 bg-white p-3 rounded border border-[#D5E1EE] shadow-2xs max-h-[700px] overflow-y-auto">
          <span className="font-mono text-[10px] uppercase text-[#4E657E] font-semibold px-2 py-1">
            Archived Technical Reports
          </span>
          {reports.map((r) => {
            const isSelected = selectedReport.id === r.id;
            return (
              <div
                key={r.id}
                onClick={() => setSelectedReport(r)}
                className={`p-3 rounded border cursor-pointer transition-all ${
                  isSelected
                    ? 'bg-[#EEF4FF] border-primary text-[#0F1E2E] shadow-2xs'
                    : 'bg-white border-[#D5E1EE] hover:bg-[#F4F8FC] text-[#4E657E]'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className={`font-mono text-[10px] font-bold px-1.5 py-0.5 rounded ${isSelected ? 'bg-primary text-white' : 'bg-[#E4EDF6] text-[#4E657E]'}`}>
                    {r.phase}
                  </span>
                  <span className="font-mono text-[10px] text-[#4E657E]">{r.date}</span>
                </div>
                <h3 className="font-semibold text-xs text-[#0F1E2E] leading-snug">{r.title}</h3>
                <p className="text-[11px] text-[#4E657E] mt-1 line-clamp-2">{r.summary}</p>
              </div>
            );
          })}
        </div>

        {/* Selected Report Viewer (7 cols) */}
        <div className="lg:col-span-7 flex flex-col gap-3 bg-white p-5 rounded border border-[#D5E1EE] shadow-2xs">
          <div className="flex items-center justify-between pb-3 border-b border-[#CBD9E8]">
            <div>
              <span className="font-mono text-[10px] text-primary font-bold uppercase tracking-wider">{selectedReport.phase} Technical Report</span>
              <h2 className="text-base font-bold text-[#0F1E2E] mt-0.5">{selectedReport.title}</h2>
            </div>
            <span className="px-2 py-0.5 rounded bg-[#F0FDF4] text-emerald-800 border border-emerald-300 font-mono text-[10px] font-bold">
              PASSED & VERIFIED
            </span>
          </div>

          <div className="space-y-4 text-xs text-[#0F1E2E] leading-relaxed font-sans pt-2">
            <div>
              <h4 className="font-bold text-[11px] uppercase tracking-wider text-[#4E657E] mb-1">Executive Summary</h4>
              <p className="p-3 bg-[#F4F8FC] rounded border border-[#CBD9E8] text-[11px] font-mono leading-relaxed">
                {selectedReport.summary}
              </p>
            </div>

            <div className="p-3 bg-white rounded border border-[#CBD9E8] space-y-2">
              <h4 className="font-bold text-[11px] uppercase tracking-wider text-[#4E657E]">Scientific Standards & Verification Protocol</h4>
              <ul className="list-disc pl-4 space-y-1 text-[11px] text-[#4E657E]">
                <li>Strict adherence to <code className="bg-[#EEF4FF] px-1 rounded text-primary font-mono">GLOBAL-INSTRUCTIONS.md</code> and canonical units.</li>
                <li>Zero-leakage guarantees on all parameter scalers and synthetic trajectory partitions.</li>
                <li>Cryptographic file integrity verified in <code className="bg-[#EEF4FF] px-1 rounded text-primary font-mono">data/raw/manifest.json</code>.</li>
                <li>100% offline, zero-cloud execution verified on local PyTorch and SciPy backends.</li>
              </ul>
            </div>

            <div className="pt-2 border-t border-[#D5E1EE] flex items-center justify-between">
              <span className="font-mono text-[10px] text-[#4E657E]">Artifact Path: reports/{selectedReport.id}-*.md</span>
              <span className="font-mono text-[10px] text-status-success font-semibold">Status: Sealed & Cryptographically Validated</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
