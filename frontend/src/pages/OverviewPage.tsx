import React from 'react';
import {
  ArrowRight,
  BookOpen,
  FlaskConical,
  Layers,
  ShieldAlert,
  Cpu,
  Sparkles,
} from 'lucide-react';

interface OverviewPageProps {
  onGoToSimulator: () => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({ onGoToSimulator }) => {
  return (
    <div className="max-w-5xl mx-auto space-y-8 py-6">
      {/* Hero Section */}
      <div className="glass-panel rounded-3xl p-8 sm:p-10 shadow-2xl relative overflow-hidden border border-white/10">
        <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-500/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center space-x-2 px-3.5 py-1 bg-emerald-950/80 border border-emerald-500/30 rounded-full text-emerald-400 text-xs font-mono mb-4 shadow-[0_0_12px_rgba(16,185,129,0.2)]">
            <FlaskConical className="w-3.5 h-3.5" />
            <span>Chemical Reaction Engineering • Digital Twin</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white mb-4 leading-tight">
            Continuous Stirred-Tank Reactor <span className="text-emerald-400">(CSTR)</span>
          </h1>

          <p className="text-slate-300 text-sm sm:text-base leading-relaxed mb-6 font-normal">
            High-fidelity computational twin for isothermal and coupled non-isothermal chemical reactors. Bridges deterministic ordinary differential equations, parameter estimation, and scientific machine learning (Grey-Box Neural ODEs & Physics-Informed Neural Networks).
          </p>

          <div className="flex flex-wrap gap-3">
            <button
              onClick={onGoToSimulator}
              className="inline-flex items-center space-x-2 px-6 py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-sm font-semibold shadow-lg shadow-emerald-950/50 hover:shadow-emerald-500/25 transition-all duration-200 transform hover:-translate-y-0.5"
            >
              <span>Launch Interactive Simulator</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <div className="inline-flex items-center space-x-2 px-4 py-2 bg-slate-900/60 border border-slate-800 rounded-xl text-xs text-slate-300 font-mono">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" />
              <span>Offline SciPy & PyTorch Solvers</span>
            </div>
          </div>
        </div>
      </div>

      {/* Governing Equations Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-panel rounded-2xl p-6 border border-white/10 hover:border-emerald-500/30 transition-colors duration-200 shadow-xl">
          <div className="flex items-center space-x-2 text-emerald-400 text-sm font-semibold mb-3">
            <BookOpen className="w-4 h-4" />
            <span>Transient Mole Balance Equation</span>
          </div>
          <p className="text-xs text-slate-400 mb-3">
            Species A balance inside a perfectly mixed control volume with constant volume $V$:
          </p>
          <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 font-mono text-xs text-emerald-300 overflow-x-auto shadow-inner">
            dC_A / dt = (Q / V) · (C_A,in - C_A) + r_A(C_A)
          </div>
          <div className="mt-4 text-xs text-slate-400 space-y-1.5 font-sans">
            <p>• <strong className="text-slate-200">Space Time (τ):</strong> τ = V / Q [min]</p>
            <p>• <strong className="text-slate-200">Effluent Concentration:</strong> C_A,out(t) = C_A(t) (perfect mixing)</p>
          </div>
        </div>

        <div className="glass-panel rounded-2xl p-6 border border-white/10 hover:border-cyan-500/30 transition-colors duration-200 shadow-xl">
          <div className="flex items-center space-x-2 text-cyan-400 text-sm font-semibold mb-3">
            <Layers className="w-4 h-4" />
            <span>First-Order Analytical Solutions</span>
          </div>
          <p className="text-xs text-slate-400 mb-3">
            For irreversible first-order kinetics $r_A = -k C_A$:
          </p>
          <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 font-mono text-xs text-cyan-300 overflow-x-auto shadow-inner">
            C_A,ss = C_A,in / (1 + k · τ)
            <br />
            X_A = (k · τ) / (1 + k · τ) = Da / (1 + Da)
          </div>
          <div className="mt-4 text-xs text-slate-400 space-y-1.5 font-sans">
            <p>• <strong className="text-slate-200">Damköhler Number (Da):</strong> Da = k · τ (reaction vs convection rate)</p>
            <p>• <strong className="text-slate-200">Transient Solution:</strong> Exponential relaxation to steady-state</p>
          </div>
        </div>
      </div>

      {/* Canonical Validation Oracle Banner */}
      <div className="glass-panel rounded-2xl p-6 border border-emerald-500/30 shadow-xl">
        <div className="flex items-start space-x-4">
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 flex-shrink-0">
            <Sparkles className="w-6 h-6" />
          </div>
          <div className="space-y-2">
            <h3 className="text-base font-bold text-white tracking-tight">
              Canonical Validation Oracle Invariant
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Every numerical solver, REST API route, surrogate regressor, and ML model in CSTR Lab is validated against the exact analytical benchmark:
            </p>
            <div className="bg-slate-950/90 border border-slate-800/80 rounded-xl p-3 font-mono text-xs text-emerald-300 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2 text-center">
              <div>V = 10.0 L</div>
              <div>Q = 1.0 L/min</div>
              <div>k = 0.15 min⁻¹</div>
              <div className="text-white font-bold">Da = 1.50</div>
              <div>C_A,in = 1.0 M → C_ss = 0.40 M</div>
              <div>X_A = 60.0%</div>
              <div>C_A,in = 2.0 M → C_ss = 0.80 M</div>
              <div>X_A = 60.0%</div>
            </div>
          </div>
        </div>
      </div>

      {/* Assumptions and Safety Callout */}
      <div className="glass-panel rounded-2xl p-6 border border-amber-500/20 shadow-xl">
        <div className="flex items-start space-x-3 text-amber-300">
          <ShieldAlert className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div className="text-xs leading-relaxed">
            <strong className="block text-amber-200 text-sm mb-1">Modeling Invariants & Scientific Governance</strong>
            <p className="text-slate-300 mb-1">
              • Constant fluid density (incompressible liquid phase).
              • Perfect micromixing: fluid element compositions are uniform throughout the vessel.
              • Isothermal operation assumes instantaneous heat removal; thermal runaway dynamics are audited under Phase 13.
              • Undocumented raw arrays (<code className="text-amber-300 bg-amber-950/60 px-1 py-0.5 rounded font-mono">cstr_rawdata.npy</code>) are permanently quarantined to prevent unverified hallucinations.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
