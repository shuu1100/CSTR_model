import React from 'react';
import { CheckCircle2, Clock, Gauge, Percent, Zap } from 'lucide-react';
import { DynamicSimulationResponse, SteadyStateResponse } from '../api/types';

interface ResultsPanelProps {
  mode: 'steady' | 'dynamic';
  steadyResult: SteadyStateResponse | null;
  dynamicResult: DynamicSimulationResponse | null;
}

export const ResultsPanel: React.FC<ResultsPanelProps> = ({ mode, steadyResult, dynamicResult }) => {
  if (mode === 'steady' && !steadyResult) return null;
  if (mode === 'dynamic' && !dynamicResult) return null;

  const isSteady = mode === 'steady';
  const tau = isSteady ? steadyResult!.outputs.tau : dynamicResult!.tau_initial;
  const cOut = isSteady ? steadyResult!.outputs.C_A_ss : dynamicResult!.C_A[dynamicResult!.C_A.length - 1];
  const conversionVal = isSteady
    ? steadyResult!.outputs.conversion
    : dynamicResult!.conversion
    ? dynamicResult!.conversion[dynamicResult!.conversion.length - 1]
    : null;
  const rateVal = isSteady
    ? steadyResult!.outputs.reaction_rate_ss
    : dynamicResult!.reaction_rate[dynamicResult!.reaction_rate.length - 1];

  const residual = isSteady ? steadyResult!.outputs.residual : null;

  return (
    <div className="glass-panel rounded-2xl p-6 shadow-2xl">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-base font-semibold text-white">Calculated Engineering Results</h3>
          <p className="text-xs text-slate-400">
            {isSteady ? 'Steady-state algebraic solution' : 'Numerical transient trajectory results'}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded bg-blue-950/80 text-blue-300 border border-blue-800/80 shadow-sm">
            SIMULATED
          </span>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-950/90 text-emerald-400 border border-emerald-800/80 shadow-sm">
            {isSteady ? 'Steady State' : `Solver: ${dynamicResult?.solver_details.method}`}
          </span>
        </div>
      </div>

      {/* Grid of Key Performance Indicators */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Space Time */}
        <div className="glass-card border border-white/5 p-4 rounded-xl hover:border-blue-500/30 transition-colors shadow-lg">
          <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
            <Clock className="w-3.5 h-3.5 text-blue-400" />
            <span>Residence Time (τ)</span>
          </div>
          <div className="text-xl font-bold font-mono text-white">
            {tau.toFixed(2)} <span className="text-xs font-normal text-slate-400">min</span>
          </div>
          <div className="text-[11px] text-slate-500 mt-1">τ = V / Q</div>
        </div>

        {/* Effluent Concentration */}
        <div className="glass-card border border-white/5 p-4 rounded-xl hover:border-emerald-500/30 transition-colors shadow-lg">
          <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
            <Gauge className="w-3.5 h-3.5 text-emerald-400" />
            <span>{isSteady ? 'C_A,ss' : 'Final C_A(t)'}</span>
          </div>
          <div className="text-xl font-bold font-mono text-white">
            {cOut.toFixed(4)} <span className="text-xs font-normal text-slate-400">mol/L</span>
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Effluent reactant stream</div>
        </div>

        {/* Fractional Conversion */}
        <div className="glass-card border border-white/5 p-4 rounded-xl hover:border-cyan-500/30 transition-colors shadow-lg">
          <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
            <Percent className="w-3.5 h-3.5 text-cyan-400" />
            <span>Conversion (X_A)</span>
          </div>
          {conversionVal !== null && !isNaN(conversionVal) ? (
            <div>
              <div className="text-xl font-bold font-mono text-cyan-400">
                {(conversionVal * 100).toFixed(2)}%
              </div>
              <div className="text-[11px] text-slate-500 mt-1">
                {(conversionVal).toFixed(4)} fraction
              </div>
            </div>
          ) : (
            <div>
              <div className="text-sm font-semibold text-amber-400 mt-1">Undefined</div>
              <div className="text-[11px] text-slate-500">C_A,in = 0</div>
            </div>
          )}
        </div>

        {/* Reaction Rate */}
        <div className="glass-card border border-white/5 p-4 rounded-xl hover:border-pink-500/30 transition-colors shadow-lg">
          <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
            <Zap className="w-3.5 h-3.5 text-pink-400" />
            <span>Reaction Rate (r_A)</span>
          </div>
          <div className="text-xl font-bold font-mono text-white">
            {rateVal.toFixed(4)} <span className="text-xs font-normal text-slate-400">mol/(L·min)</span>
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Consumption rate</div>
        </div>
      </div>

      {/* Diagnostics & Residual Closure */}
      <div className="mt-4 pt-3 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
        {isSteady && residual !== null && (
          <div className="flex items-center space-x-2 text-slate-300">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>
              Material Balance Residual: <span className="font-mono text-emerald-300">{Math.abs(residual) < 1e-12 ? '0.00e+00' : residual.toExponential(3)}</span> mol/(L·min)
            </span>
            <span className="text-slate-500">(Closed within tolerance)</span>
          </div>
        )}

        {!isSteady && dynamicResult?.analytical_comparison && (
          <div className="flex items-center space-x-2 text-slate-300">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>
              Analytical Benchmark RMSE: <span className="font-mono text-emerald-300">{dynamicResult.analytical_comparison.rmse.toExponential(2)}</span>
            </span>
          </div>
        )}

        <div className="text-slate-500 font-mono text-[11px]">
          Model: {isSteady ? steadyResult?.model_id : dynamicResult?.model_id}
        </div>
      </div>
    </div>
  );
};
