import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Info, ShieldAlert } from 'lucide-react';

interface AssumptionsPanelProps {
  assumptions?: string[];
  normalizedInputs?: Record<string, any>;
  units?: Record<string, string>;
}

export const AssumptionsPanel: React.FC<AssumptionsPanelProps> = ({
  assumptions = [],
  normalizedInputs,
  units,
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(true);

  const defaultAssumptions = [
    "Perfect mixing (spatially uniform concentration in liquid volume V)",
    "Constant reaction volume (constant liquid level maintained)",
    "Constant fluid density with equal inlet and outlet volumetric flow rates (Q_in = Q_out = Q)",
    "Isothermal operation (heat effects neglected)",
    "Reaction kinetics: Irreversible elementary kinetics (orders 0, 1, 2)",
    "Zero-order physical depletion boundary enforced (r_A = 0 when C_A <= 0)",
  ];

  const activeAssumptions = assumptions.length > 0 ? assumptions : defaultAssumptions;

  return (
    <div className="glass-panel rounded-2xl overflow-hidden shadow-xl border border-white/5">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-5 py-3.5 flex items-center justify-between text-left hover:bg-slate-800/40 transition"
      >
        <div className="flex items-center space-x-2.5 text-slate-200">
          <Info className="w-4 h-4 text-emerald-400" />
          <span className="text-sm font-semibold">Model Assumptions & Scientific Baseline</span>
        </div>
        <div className="flex items-center space-x-2 text-slate-400 text-xs">
          <span>{isOpen ? 'Collapse' : 'Expand'}</span>
          {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {isOpen && (
        <div className="p-5 pt-2 border-t border-slate-800/80 space-y-4 text-xs">
          <div>
            <h4 className="text-slate-300 font-medium mb-2">Governing Physical Assumptions:</h4>
            <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 text-slate-400">
              {activeAssumptions.map((assump, idx) => (
                <li key={idx} className="flex items-start space-x-2">
                  <span className="text-emerald-500 font-bold">•</span>
                  <span>{assump}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Normalized Inputs & Units */}
          {normalizedInputs && units && (
            <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-lg">
              <h4 className="text-slate-300 font-medium mb-1.5">Normalized Canonical Inputs:</h4>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-[11px] text-slate-400">
                {Object.entries(normalizedInputs).map(([k, v]) => {
                  if (typeof v === 'object' && v !== null) return null;
                  return (
                    <div key={k} className="bg-slate-900/70 p-1.5 rounded border border-slate-800/50">
                      <span className="text-slate-500">{k}: </span>
                      <span className="text-emerald-400">{String(v)}</span>{' '}
                      <span className="text-slate-500">{units[k] || ''}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Educational Disclaimer */}
          <div className="flex items-start space-x-2 text-slate-400 text-[11px] bg-slate-950/50 p-3 rounded-lg border border-slate-800/40">
            <ShieldAlert className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <p>
              <strong className="text-slate-300">Engineering Disclaimer:</strong> CSTR Lab is an educational and computational research simulator. It is not designed or certified for industrial plant process control or critical safety automation.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
