import React, { useState } from 'react';
import { Play, Sliders, Sparkles } from 'lucide-react';
import {
  ConcentrationUnit,
  DynamicSimulationRequest,
  FlowRateUnit,
  SolverMethod,
  SteadyStateRequest,
  VolumeUnit,
} from '../api/types';

interface SimulationFormProps {
  mode: 'steady' | 'dynamic';
  onModeChange: (mode: 'steady' | 'dynamic') => void;
  onRunSteadyState: (req: SteadyStateRequest) => void;
  onRunDynamicSimulation: (req: DynamicSimulationRequest) => void;
  isLoading: boolean;
}

export const SimulationForm: React.FC<SimulationFormProps> = ({
  mode,
  onModeChange,
  onRunSteadyState,
  onRunDynamicSimulation,
  isLoading,
}) => {
  // Primary Parameters
  const [V, setV] = useState<number>(10.0);
  const [volumeUnit, setVolumeUnit] = useState<VolumeUnit>('L');

  const [Q, setQ] = useState<number>(1.0);
  const [flowRateUnit, setFlowRateUnit] = useState<FlowRateUnit>('L/min');

  const [C_A_in, setC_A_in] = useState<number>(2.0);
  const [concentrationUnit, setConcentrationUnit] = useState<ConcentrationUnit>('mol/L');

  const [order, setOrder] = useState<0 | 1 | 2>(1);
  const [k, setK] = useState<number>(0.15);

  // Dynamic-Only Parameters
  const [C_A_0, setC_A_0] = useState<number>(0.5);
  const [t_final, setT_final] = useState<number>(50.0);
  const [n_points, setN_points] = useState<number>(101);
  const [solverMethod, setSolverMethod] = useState<SolverMethod>('RK45');

  // Step Change Disturbance
  const [enableStepChange, setEnableStepChange] = useState<boolean>(false);
  const [stepTime, setStepTime] = useState<number>(25.0);
  const [stepC_in, setStepC_in] = useState<number>(4.0);
  const [stepQ, setStepQ] = useState<number | undefined>(undefined);

  // Rate constant canonical unit string
  const kUnitLabel =
    order === 0
      ? 'mol/(L·min)'
      : order === 1
      ? 'min⁻¹'
      : 'L/(mol·min)';

  // Presets
  const applyPreset = (presetName: string) => {
    if (presetName === 'oracle_1mol' || presetName === 'reset') {
      setV(10.0);
      setVolumeUnit('L');
      setQ(1.0);
      setFlowRateUnit('L/min');
      setC_A_in(1.0);
      setConcentrationUnit('mol/L');
      setOrder(1);
      setK(0.15);
      setC_A_0(0.5);
      setT_final(50.0);
      setEnableStepChange(false);
    } else if (presetName === 'canonical') {
      setV(10.0);
      setVolumeUnit('L');
      setQ(1.0);
      setFlowRateUnit('L/min');
      setC_A_in(2.0);
      setConcentrationUnit('mol/L');
      setOrder(1);
      setK(0.15);
      setC_A_0(0.0);
      setT_final(50.0);
      setEnableStepChange(false);
    } else if (presetName === 'fast') {
      setV(10.0);
      setQ(1.0);
      setC_A_in(2.0);
      setOrder(1);
      setK(1.5);
      setC_A_0(0.0);
      setT_final(20.0);
      setEnableStepChange(false);
    } else if (presetName === 'step') {
      setV(10.0);
      setQ(1.0);
      setC_A_in(2.0);
      setOrder(1);
      setK(0.15);
      setC_A_0(0.80);
      setT_final(60.0);
      setEnableStepChange(true);
      setStepTime(25.0);
      setStepC_in(4.0);
    } else if (presetName === 'second_order') {
      setV(10.0);
      setQ(1.0);
      setC_A_in(2.0);
      setOrder(2);
      setK(0.1);
      setC_A_0(0.0);
      setT_final(50.0);
      setEnableStepChange(false);
    } else if (presetName === 'zero_order') {
      setV(10.0);
      setQ(1.0);
      setC_A_in(5.0);
      setOrder(0);
      setK(0.3);
      setC_A_0(0.0);
      setT_final(40.0);
      setEnableStepChange(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (mode === 'steady') {
      onRunSteadyState({
        V,
        volume_unit: volumeUnit,
        Q,
        flow_rate_unit: flowRateUnit,
        C_A_in,
        concentration_unit: concentrationUnit,
        order,
        k,
      });
    } else {
      const stepChangeObj = enableStepChange
        ? {
            time: stepTime,
            C_A_in_new: stepC_in,
            Q_new: stepQ,
          }
        : null;

      onRunDynamicSimulation({
        C_A_0,
        C_A_in,
        concentration_unit: concentrationUnit,
        V,
        volume_unit: volumeUnit,
        Q,
        flow_rate_unit: flowRateUnit,
        order,
        k,
        t_final,
        n_points,
        solver_method: solverMethod,
        step_change: stepChangeObj,
      });
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-6 shadow-2xl">
      {/* Mode Selector */}
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2">
          <Sliders className="w-4 h-4 text-emerald-400" />
          <h3 className="text-base font-semibold text-white">Reactor Configuration</h3>
        </div>
        <div className="flex bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
          <button
            type="button"
            onClick={() => onModeChange('steady')}
            className={`px-3 py-1 rounded-md font-medium transition ${
              mode === 'steady'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Steady State
          </button>
          <button
            type="button"
            onClick={() => onModeChange('dynamic')}
            className={`px-3 py-1 rounded-md font-medium transition ${
              mode === 'dynamic'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Dynamic ODE
          </button>
        </div>
      </div>

      {/* Presets Bar */}
      <div className="mb-5">
        <div className="text-[11px] text-slate-400 mb-1.5 font-medium flex items-center space-x-1">
          <Sparkles className="w-3 h-3 text-amber-400" />
          <span>Scientific Presets:</span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          <button
            type="button"
            onClick={() => applyPreset('oracle_1mol')}
            className="px-2 py-1 text-[11px] bg-emerald-950/80 hover:bg-emerald-900 text-emerald-300 rounded border border-emerald-700/80 font-medium transition"
          >
            Oracle (Cin=1 mol/L → Css=0.4, X=60%)
          </button>
          <button
            type="button"
            onClick={() => applyPreset('canonical')}
            className="px-2 py-1 text-[11px] bg-slate-800 hover:bg-slate-700 text-emerald-300 rounded border border-slate-700 transition"
          >
            Oracle (Cin=2 mol/L)
          </button>
          <button
            type="button"
            onClick={() => applyPreset('fast')}
            className="px-2 py-1 text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 transition"
          >
            Fast Kinetics (k=1.5)
          </button>
          <button
            type="button"
            onClick={() => applyPreset('step')}
            className="px-2 py-1 text-[11px] bg-slate-800 hover:bg-slate-700 text-amber-300 rounded border border-slate-700 transition"
          >
            Feed Step Disturbance
          </button>
          <button
            type="button"
            onClick={() => applyPreset('second_order')}
            className="px-2 py-1 text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 transition"
          >
            2nd Order (n=2)
          </button>
          <button
            type="button"
            onClick={() => applyPreset('zero_order')}
            className="px-2 py-1 text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 transition"
          >
            0th Order (n=0)
          </button>
          <button
            type="button"
            onClick={() => applyPreset('reset')}
            className="px-2 py-1 text-[11px] bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded border border-slate-800 transition"
          >
            Reset Defaults
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Row 1: Volume & Flow Rate */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Reactor Volume (V)
            </label>
            <div className="flex space-x-2">
              <input
                type="number"
                step="any"
                min="0.001"
                required
                value={V}
                onChange={e => setV(parseFloat(e.target.value) || 0)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-emerald-500 font-mono"
              />
              <select
                value={volumeUnit}
                onChange={e => setVolumeUnit(e.target.value as VolumeUnit)}
                className="bg-slate-950 border border-slate-800 rounded-lg px-2 text-xs text-slate-300 focus:outline-none focus:border-emerald-500"
              >
                <option value="L">L</option>
                <option value="mL">mL</option>
                <option value="m3">m³</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Volumetric Flow Rate (Q)
            </label>
            <div className="flex space-x-2">
              <input
                type="number"
                step="any"
                min="0.001"
                required
                value={Q}
                onChange={e => setQ(parseFloat(e.target.value) || 0)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-emerald-500 font-mono"
              />
              <select
                value={flowRateUnit}
                onChange={e => setFlowRateUnit(e.target.value as FlowRateUnit)}
                className="bg-slate-950 border border-slate-800 rounded-lg px-2 text-xs text-slate-300 focus:outline-none focus:border-emerald-500"
              >
                <option value="L/min">L/min</option>
                <option value="L/s">L/s</option>
                <option value="L/h">L/h</option>
                <option value="m3/h">m³/h</option>
              </select>
            </div>
          </div>
        </div>

        {/* Row 2: Feed Concentration & Kinetics Order */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Inlet Reactant Conc. (C_A,in)
            </label>
            <div className="flex space-x-2">
              <input
                type="number"
                step="any"
                min="0"
                required
                value={C_A_in}
                onChange={e => setC_A_in(parseFloat(e.target.value) || 0)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-emerald-500 font-mono"
              />
              <select
                value={concentrationUnit}
                onChange={e => setConcentrationUnit(e.target.value as ConcentrationUnit)}
                className="bg-slate-950 border border-slate-800 rounded-lg px-2 text-xs text-slate-300 focus:outline-none focus:border-emerald-500"
              >
                <option value="mol/L">mol/L</option>
                <option value="mol/m3">mol/m³</option>
                <option value="mmol/L">mmol/L</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Reaction Order (n)
            </label>
            <select
              value={order}
              onChange={e => setOrder(parseInt(e.target.value) as 0 | 1 | 2)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-emerald-500"
            >
              <option value={0}>0 — Zero Order (r_A = -k)</option>
              <option value={1}>1 — First Order (r_A = -k·C_A)</option>
              <option value={2}>2 — Second Order (r_A = -k·C_A²)</option>
            </select>
          </div>
        </div>

        {/* Row 3: Rate Constant k */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Rate Constant (k) <span className="text-slate-400 font-mono text-[11px]">[{kUnitLabel}]</span>
          </label>
          <input
            type="number"
            step="any"
            min="0"
            required
            value={k}
            onChange={e => setK(parseFloat(e.target.value) || 0)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-emerald-500 font-mono"
          />
        </div>

        {/* Dynamic-Only Section */}
        {mode === 'dynamic' && (
          <div className="pt-3 border-t border-slate-800 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Initial C_A(0) [mol/L]
                </label>
                <input
                  type="number"
                  step="any"
                  min="0"
                  required
                  value={C_A_0}
                  onChange={e => setC_A_0(parseFloat(e.target.value) || 0)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-white font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Time Horizon [min]
                </label>
                <input
                  type="number"
                  step="any"
                  min="1"
                  max="10000"
                  required
                  value={t_final}
                  onChange={e => setT_final(parseFloat(e.target.value) || 1)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-white font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Points Count
                </label>
                <input
                  type="number"
                  step="1"
                  min="10"
                  max="5000"
                  required
                  value={n_points}
                  onChange={e => setN_points(parseInt(e.target.value) || 101)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-white font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Solver Method
                </label>
                <select
                  value={solverMethod}
                  onChange={e => setSolverMethod(e.target.value as SolverMethod)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white"
                >
                  <option value="RK45">RK45 (Explicit 5(4))</option>
                  <option value="Radau">Radau (Stiff)</option>
                  <option value="BDF">BDF (Stiff)</option>
                </select>
              </div>
            </div>

            {/* Step Change Disturbance Toggle */}
            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
              <label className="flex items-center space-x-2 cursor-pointer text-xs font-medium text-slate-300">
                <input
                  type="checkbox"
                  checked={enableStepChange}
                  onChange={e => setEnableStepChange(e.target.checked)}
                  className="rounded border-slate-800 text-emerald-600 focus:ring-emerald-500"
                />
                <span>Apply Step Disturbance During Operation</span>
              </label>

              {enableStepChange && (
                <div className="mt-2.5 grid grid-cols-3 gap-3 pt-2 border-t border-slate-800/80">
                  <div>
                    <label className="block text-[11px] text-slate-400 mb-1">
                      Disturbance Time [min]
                    </label>
                    <input
                      type="number"
                      step="any"
                      min="0.1"
                      max={t_final}
                      value={stepTime}
                      onChange={e => setStepTime(parseFloat(e.target.value) || 0)}
                      className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1 text-xs text-white font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] text-slate-400 mb-1">
                      New C_A,in [mol/L]
                    </label>
                    <input
                      type="number"
                      step="any"
                      min="0"
                      value={stepC_in}
                      onChange={e => setStepC_in(parseFloat(e.target.value) || 0)}
                      className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1 text-xs text-white font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] text-slate-400 mb-1">
                      New Flow Q [L/min] (opt)
                    </label>
                    <input
                      type="number"
                      step="any"
                      min="0.001"
                      placeholder="Same as Q"
                      value={stepQ !== undefined ? stepQ : ''}
                      onChange={e => {
                        const val = parseFloat(e.target.value);
                        setStepQ(isNaN(val) ? undefined : val);
                      }}
                      className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1 text-xs text-white font-mono"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading}
          className="w-full mt-2 py-2.5 px-4 bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-800/60 disabled:cursor-not-allowed text-white font-medium rounded-lg text-sm shadow-lg shadow-emerald-950 flex items-center justify-center space-x-2 transition"
        >
          {isLoading ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <Play className="w-4 h-4 fill-white" />
          )}
          <span>{isLoading ? 'Computing Simulation...' : 'Run Simulation'}</span>
        </button>
      </form>
    </div>
  );
};
