import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import {
  AlertTriangle,
  Compass,
  Play,
  Shuffle,
  Sparkles,
  TrendingUp,
} from 'lucide-react';
import { api, ApiError } from '../api/client';
import {
  LHSSweepRequest,
  LHSSweepResponse,
  ParameterSweepRequest,
  Sweep1DResponse,
  Sweep2DResponse,
  SweepVariableType,
} from '../api/types';
import { ErrorBanner } from '../components/ErrorBanner';

export const SweepsPage: React.FC = () => {
  const [sweepMode, setSweepMode] = useState<'1D' | '2D' | 'LHS'>('1D');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // 1D / X-axis parameter
  const [variable, setVariable] = useState<SweepVariableType>('k');
  const [minVal, setMinVal] = useState<number>(0.01);
  const [maxVal, setMaxVal] = useState<number>(0.8);
  const [nPoints, setNPoints] = useState<number>(40);

  // 2D / Y-axis parameter
  const [variableY, setVariableY] = useState<SweepVariableType>('V');
  const [minValY, setMinValY] = useState<number>(2.0);
  const [maxValY, setMaxValY] = useState<number>(30.0);
  const [nPointsY, setNPointsY] = useState<number>(20);

  // Baselines & Kinetics
  const [baselineV, setBaselineV] = useState<number>(10.0);
  const [baselineQ, setBaselineQ] = useState<number>(1.0);
  const [baselineCin, setBaselineCin] = useState<number>(2.0);
  const [baselineK, setBaselineK] = useState<number>(0.15);
  const [order, setOrder] = useState<0 | 1 | 2>(1);

  // Latin Hypercube Sampling (QMC) state
  const [lhsSamples, setLhsSamples] = useState<number>(50);
  const [lhsSeed, setLhsSeed] = useState<number>(42);
  const [lhsBounds, setLhsBounds] = useState<Record<string, [number, number]>>({
    V: [2.0, 30.0],
    Q: [0.2, 5.0],
    k: [0.01, 1.0],
    C_A_in: [0.5, 5.0],
  });

  // Results
  const [result1D, setResult1D] = useState<Sweep1DResponse | null>(null);
  const [result2D, setResult2D] = useState<Sweep2DResponse | null>(null);
  const [resultLHS, setResultLHS] = useState<LHSSweepResponse | null>(null);

  // Run default sweep on mount
  useEffect(() => {
    execute1DSweep({
      is_2d: false,
      variable: 'k',
      min_val: 0.01,
      max_val: 0.8,
      n_points: 40,
      baseline_V: 10.0,
      baseline_Q: 1.0,
      baseline_C_in: 2.0,
      baseline_k: 0.15,
      order: 1,
    });
  }, []);

  const execute1DSweep = async (req: ParameterSweepRequest) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const res = await api.runParameterSweep(req);
      if (res.sweep_type === '2D') {
        setResult2D(res as Sweep2DResponse);
        setResult1D(null);
        setResultLHS(null);
      } else {
        setResult1D(res as Sweep1DResponse);
        setResult2D(null);
        setResultLHS(null);
      }
    } catch (err: any) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage(err.message || 'Error executing parameter sweep.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const executeLHSSweep = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const req: LHSSweepRequest = {
        n_samples: lhsSamples,
        seed: lhsSeed,
        order,
        bounds: lhsBounds,
      };
      const res = await api.runLHSSweep(req);
      setResultLHS(res);
      setResult1D(null);
      setResult2D(null);
    } catch (err: any) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage(err.message || 'Error executing Latin Hypercube Sampling sweep.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (sweepMode === 'LHS') {
      executeLHSSweep();
    } else {
      execute1DSweep({
        is_2d: sweepMode === '2D',
        variable,
        min_val: minVal,
        max_val: maxVal,
        n_points: nPoints,
        variable_y: sweepMode === '2D' ? variableY : undefined,
        min_val_y: sweepMode === '2D' ? minValY : undefined,
        max_val_y: sweepMode === '2D' ? maxValY : undefined,
        n_points_y: sweepMode === '2D' ? nPointsY : undefined,
        baseline_V: baselineV,
        baseline_Q: baselineQ,
        baseline_C_in: baselineCin,
        baseline_k: baselineK,
        order,
      });
    }
  };

  const applyPreset = (preset: string) => {
    if (preset === 'k_sweep') {
      setSweepMode('1D');
      setVariable('k');
      setMinVal(0.01);
      setMaxVal(1.0);
      setNPoints(50);
      setBaselineV(10.0);
      setBaselineQ(1.0);
      setBaselineCin(2.0);
      setBaselineK(0.15);
      setOrder(1);
    } else if (preset === 'V_sweep') {
      setSweepMode('1D');
      setVariable('V');
      setMinVal(1.0);
      setMaxVal(50.0);
      setNPoints(50);
      setBaselineV(10.0);
      setBaselineQ(1.0);
      setBaselineCin(2.0);
      setBaselineK(0.15);
      setOrder(1);
    } else if (preset === 'Q_sweep') {
      setSweepMode('1D');
      setVariable('Q');
      setMinVal(0.1);
      setMaxVal(5.0);
      setNPoints(50);
      setBaselineV(10.0);
      setBaselineQ(1.0);
      setBaselineCin(2.0);
      setBaselineK(0.15);
      setOrder(1);
    } else if (preset === '2d_k_V') {
      setSweepMode('2D');
      setVariable('k');
      setMinVal(0.05);
      setMaxVal(0.6);
      setNPoints(20);
      setVariableY('V');
      setMinValY(2.0);
      setMaxValY(30.0);
      setNPointsY(20);
      setBaselineV(10.0);
      setBaselineQ(1.0);
      setBaselineCin(2.0);
      setBaselineK(0.15);
      setOrder(1);
    } else if (preset === '2d_Q_V') {
      setSweepMode('2D');
      setVariable('Q');
      setMinVal(0.2);
      setMaxVal(3.0);
      setNPoints(20);
      setVariableY('V');
      setMinValY(2.0);
      setMaxValY(30.0);
      setNPointsY(20);
      setBaselineV(10.0);
      setBaselineQ(1.0);
      setBaselineCin(2.0);
      setBaselineK(0.15);
      setOrder(1);
    } else if (preset === 'lhs_standard') {
      setSweepMode('LHS');
      setLhsSamples(50);
      setLhsSeed(42);
      setOrder(1);
      setLhsBounds({
        V: [2.0, 30.0],
        Q: [0.2, 5.0],
        k: [0.01, 1.0],
        C_A_in: [0.5, 5.0],
      });
    }
  };

  // Base Plotly layout
  const baseLayout: Partial<Plotly.Layout> = {
    paper_bgcolor: 'rgba(15, 23, 42, 0.4)',
    plot_bgcolor: 'rgba(15, 23, 42, 0.6)',
    font: { color: '#94a3b8', family: 'Inter, sans-serif' },
    margin: { l: 55, r: 30, t: 30, b: 45 },
    xaxis: { gridcolor: '#1e293b', zerolinecolor: '#334155' },
    yaxis: { gridcolor: '#1e293b', zerolinecolor: '#334155' },
    autosize: true,
  };

  return (
    <div className="space-y-6 py-6">
      {errorMessage && (
        <ErrorBanner message={errorMessage} onDismiss={() => setErrorMessage(null)} />
      )}

      {/* Header Banner */}
      <div className="glass-panel rounded-2xl p-6 shadow-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-emerald-400 text-xs font-mono mb-1">
            <Compass className="w-3.5 h-3.5" />
            <span>Deterministic Sensitivity Engine</span>
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight">
            Parameter Sweeps & Engineering Sensitivity
          </h2>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Explore how key design variables (reactor volume, flow rate, rate constant, inlet feed) affect steady-state reactant conversion and effluent concentration with 1D lines, 2D surfaces, and Quasi-Monte Carlo Latin Hypercube Sampling.
          </p>
        </div>

        {/* 1D vs 2D vs LHS Switcher */}
        <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 self-start md:self-auto text-xs">
          <button
            type="button"
            onClick={() => setSweepMode('1D')}
            className={`px-3 py-1.5 rounded-lg font-medium transition ${
              sweepMode === '1D' ? 'bg-emerald-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            1D Parameter Sweep
          </button>
          <button
            type="button"
            onClick={() => setSweepMode('2D')}
            className={`px-3 py-1.5 rounded-lg font-medium transition ${
              sweepMode === '2D' ? 'bg-emerald-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            2D Surface Grid Map
          </button>
          <button
            type="button"
            onClick={() => setSweepMode('LHS')}
            className={`px-3 py-1.5 rounded-lg font-medium transition ${
              sweepMode === 'LHS' ? 'bg-emerald-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Latin Hypercube (QMC)
          </button>
        </div>
      </div>

      {/* Grid: Form on Left, Plots on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Form */}
        <div className="lg:col-span-5 space-y-6">
          <div className="glass-panel rounded-2xl p-6 shadow-2xl">
            <h3 className="text-sm font-semibold text-white mb-3">
              {sweepMode === '1D' && '1D Sweep Configuration'}
              {sweepMode === '2D' && '2D Surface Configuration'}
              {sweepMode === 'LHS' && 'Latin Hypercube Sampling Configuration'}
            </h3>

            {/* Presets */}
            <div className="mb-4">
              <span className="text-[11px] text-slate-400 mb-1 flex items-center space-x-1">
                <Sparkles className="w-3 h-3 text-amber-400" />
                <span>Quick Exploration Presets:</span>
              </span>
              <div className="flex flex-wrap gap-1.5 text-xs">
                <button
                  type="button"
                  onClick={() => applyPreset('k_sweep')}
                  className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 text-[11px]"
                >
                  k Sweep
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset('V_sweep')}
                  className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 text-[11px]"
                >
                  Volume V Sweep
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset('Q_sweep')}
                  className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 text-[11px]"
                >
                  Flow Q Sweep
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset('2d_k_V')}
                  className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-emerald-300 rounded border border-slate-700 text-[11px]"
                >
                  2D (k vs V)
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset('2d_Q_V')}
                  className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-cyan-300 rounded border border-slate-700 text-[11px]"
                >
                  2D (Q vs V)
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset('lhs_standard')}
                  className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-purple-300 rounded border border-slate-700 text-[11px]"
                >
                  LHS (50 pts)
                </button>
              </div>
            </div>

            <form onSubmit={handleFormSubmit} className="space-y-4 text-xs">
              {sweepMode !== 'LHS' ? (
                <>
                  {/* Primary Swept Variable */}
                  <div>
                    <label className="block text-slate-300 font-medium mb-1">
                      {sweepMode === '2D' ? 'Primary X-Axis Variable' : 'Swept Variable'}
                    </label>
                    <select
                      value={variable}
                      onChange={e => setVariable(e.target.value as SweepVariableType)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-white"
                    >
                      <option value="k">Rate Constant (k)</option>
                      <option value="V">Reactor Volume (V)</option>
                      <option value="Q">Volumetric Flow Rate (Q)</option>
                      <option value="C_A_in">Inlet Concentration (C_A,in)</option>
                    </select>
                  </div>

                  {/* X Range */}
                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <label className="block text-slate-400 mb-1 text-[11px]">Min Value</label>
                      <input
                        type="number"
                        step="any"
                        min="0"
                        required
                        value={minVal}
                        onChange={e => setMinVal(parseFloat(e.target.value) || 0)}
                        className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-white font-mono"
                      />
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1 text-[11px]">Max Value</label>
                      <input
                        type="number"
                        step="any"
                        min="0"
                        required
                        value={maxVal}
                        onChange={e => setMaxVal(parseFloat(e.target.value) || 0)}
                        className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-white font-mono"
                      />
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1 text-[11px]">Points</label>
                      <input
                        type="number"
                        step="1"
                        min="2"
                        max={sweepMode === '2D' ? 50 : 500}
                        required
                        value={nPoints}
                        onChange={e => setNPoints(parseInt(e.target.value) || 20)}
                        className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-white font-mono"
                      />
                    </div>
                  </div>

                  {/* Secondary Variable for 2D */}
                  {sweepMode === '2D' && (
                    <div className="pt-3 border-t border-slate-800 space-y-3">
                      <div>
                        <label className="block text-slate-300 font-medium mb-1">
                          Secondary Y-Axis Variable
                        </label>
                        <select
                          value={variableY}
                          onChange={e => setVariableY(e.target.value as SweepVariableType)}
                          className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-white"
                        >
                          <option value="V">Reactor Volume (V)</option>
                          <option value="Q">Volumetric Flow Rate (Q)</option>
                          <option value="k">Rate Constant (k)</option>
                          <option value="C_A_in">Inlet Concentration (C_A,in)</option>
                        </select>
                      </div>

                      <div className="grid grid-cols-3 gap-2">
                        <div>
                          <label className="block text-slate-400 mb-1 text-[11px]">Min Y</label>
                          <input
                            type="number"
                            step="any"
                            min="0"
                            required
                            value={minValY}
                            onChange={e => setMinValY(parseFloat(e.target.value) || 0)}
                            className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-white font-mono"
                          />
                        </div>
                        <div>
                          <label className="block text-slate-400 mb-1 text-[11px]">Max Y</label>
                          <input
                            type="number"
                            step="any"
                            min="0"
                            required
                            value={maxValY}
                            onChange={e => setMaxValY(parseFloat(e.target.value) || 0)}
                            className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-white font-mono"
                          />
                        </div>
                        <div>
                          <label className="block text-slate-400 mb-1 text-[11px]">Points Y</label>
                          <input
                            type="number"
                            step="1"
                            min="2"
                            max="50"
                            required
                            value={nPointsY}
                            onChange={e => setNPointsY(parseInt(e.target.value) || 20)}
                            className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-white font-mono"
                          />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Fixed Baseline Parameters */}
                  <div className="pt-3 border-t border-slate-800 space-y-2">
                    <span className="text-[11px] text-slate-400 font-medium block">
                      Fixed Baseline Values:
                    </span>
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-slate-500 text-[10px]">V [L]</label>
                        <input
                          type="number"
                          step="any"
                          min="0.001"
                          value={baselineV}
                          onChange={e => setBaselineV(parseFloat(e.target.value) || 10)}
                          className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-white font-mono"
                        />
                      </div>
                      <div>
                        <label className="block text-slate-500 text-[10px]">Q [L/min]</label>
                        <input
                          type="number"
                          step="any"
                          min="0.001"
                          value={baselineQ}
                          onChange={e => setBaselineQ(parseFloat(e.target.value) || 1)}
                          className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-white font-mono"
                        />
                      </div>
                      <div>
                        <label className="block text-slate-500 text-[10px]">C_A,in [mol/L]</label>
                        <input
                          type="number"
                          step="any"
                          min="0"
                          value={baselineCin}
                          onChange={e => setBaselineCin(parseFloat(e.target.value) || 2)}
                          className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-white font-mono"
                        />
                      </div>
                      <div>
                        <label className="block text-slate-500 text-[10px]">k [canon]</label>
                        <input
                          type="number"
                          step="any"
                          min="0"
                          value={baselineK}
                          onChange={e => setBaselineK(parseFloat(e.target.value) || 0.15)}
                          className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-white font-mono"
                        />
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                /* LHS Sampling Inputs */
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-slate-400 mb-1 text-[11px]">Number of Samples</label>
                      <input
                        type="number"
                        min="2"
                        max="500"
                        value={lhsSamples}
                        onChange={e => setLhsSamples(parseInt(e.target.value) || 50)}
                        className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-white font-mono"
                      />
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1 text-[11px]">Random Seed</label>
                      <input
                        type="number"
                        value={lhsSeed}
                        onChange={e => setLhsSeed(parseInt(e.target.value) || 42)}
                        className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-white font-mono"
                      />
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-800 space-y-2">
                    <span className="text-[11px] text-slate-300 font-semibold block">
                      Multi-Parameter Sampling Bounds:
                    </span>
                    {(['V', 'Q', 'k', 'C_A_in'] as const).map(pKey => (
                      <div key={pKey} className="grid grid-cols-3 gap-2 items-center">
                        <span className="text-slate-400 font-mono text-[11px]">
                          {pKey === 'V' && 'Volume V [L]'}
                          {pKey === 'Q' && 'Flow Q [L/min]'}
                          {pKey === 'k' && 'Rate k [canon]'}
                          {pKey === 'C_A_in' && 'Feed C_A,in [mol/L]'}
                        </span>
                        <div>
                          <input
                            type="number"
                            step="any"
                            value={lhsBounds[pKey]?.[0] ?? 0.1}
                            onChange={e => {
                              const val = parseFloat(e.target.value) || 0.1;
                              setLhsBounds(prev => ({
                                ...prev,
                                [pKey]: [val, prev[pKey][1]],
                              }));
                            }}
                            className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-white font-mono text-[11px]"
                            placeholder="Min"
                          />
                        </div>
                        <div>
                          <input
                            type="number"
                            step="any"
                            value={lhsBounds[pKey]?.[1] ?? 10.0}
                            onChange={e => {
                              const val = parseFloat(e.target.value) || 10.0;
                              setLhsBounds(prev => ({
                                ...prev,
                                [pKey]: [prev[pKey][0], val],
                              }));
                            }}
                            className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-white font-mono text-[11px]"
                            placeholder="Max"
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Kinetic Order Selection */}
              <div>
                <label className="block text-slate-400 mb-1 text-[11px]">Kinetic Order</label>
                <select
                  value={order}
                  onChange={e => setOrder(parseInt(e.target.value) as 0 | 1 | 2)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-white"
                >
                  <option value={0}>0 — Zero Order</option>
                  <option value={1}>1 — First Order</option>
                  <option value={2}>2 — Second Order</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full mt-2 py-2 px-4 bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-800/60 text-white font-medium rounded-lg text-xs shadow-lg flex items-center justify-center space-x-2 transition"
              >
                {isLoading ? (
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : sweepMode === 'LHS' ? (
                  <Shuffle className="w-3.5 h-3.5 text-white" />
                ) : (
                  <Play className="w-3.5 h-3.5 fill-white" />
                )}
                <span>
                  {isLoading
                    ? 'Executing Sweep...'
                    : sweepMode === 'LHS'
                    ? 'Sample Latin Hypercube (SciPy QMC)'
                    : 'Run Parameter Sweep'}
                </span>
              </button>
            </form>
          </div>
        </div>

        {/* Right Charts & Insights */}
        <div className="lg:col-span-7 space-y-6">
          {/* Trend Summary Card for 1D or 2D */}
          {(result1D || result2D) && (
            <div className="glass-panel rounded-2xl p-5 shadow-xl flex items-start space-x-3">
              <TrendingUp className="w-5 h-5 text-emerald-400 mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wide">
                  Calculated Physical Trend
                </h4>
                <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                  {result1D?.trend_summary || result2D?.trend_summary}
                </p>
                {result1D?.local_sensitivity && (
                  <div className="mt-2 flex flex-wrap gap-3 font-mono text-[11px] text-slate-400 bg-slate-950/70 p-2 rounded border border-slate-800/60">
                    <div>
                      <span className="text-slate-500">Local Tangent (dX/dp): </span>
                      <span className="text-emerald-400">
                        {result1D.local_sensitivity.derivative_dX_dp.toFixed(4)}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500">Normalized Elasticity: </span>
                      <span className="text-cyan-400">
                        {result1D.local_sensitivity.normalized_elasticity.toFixed(4)}
                      </span>
                    </div>
                    <div className="text-[10px] text-slate-500 w-full">
                      * Evaluated via finite difference around baseline point. Distinct from global Sobol sensitivity.
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 1D Plotly Charts */}
          {result1D && (
            <div className="space-y-6">
              {/* Conversion vs Parameter */}
              <div className="glass-panel rounded-2xl p-6 shadow-xl">
                <h3 className="text-sm font-semibold text-white mb-1">
                  Fractional Conversion (X_A) vs {result1D.variable_label}
                </h3>
                <p className="text-xs text-slate-400">
                  {result1D.variable_label} swept from {result1D.points[0]?.param_value.toFixed(2)} to{' '}
                  {result1D.points[result1D.points.length - 1]?.param_value.toFixed(2)} {result1D.variable_unit}
                </p>
                <div className="h-64 w-full mt-2">
                  <Plot
                    data={[
                      {
                        x: result1D.points.map(p => p.param_value),
                        y: result1D.points.map(p => (p.conversion !== null ? p.conversion * 100 : null)),
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: 'Conversion (%)',
                        line: { color: '#38bdf8', width: 2.5 },
                        marker: { size: 4 },
                      },
                      {
                        x: [result1D.baseline_param_value],
                        y: [
                          result1D.baseline_metrics.conversion !== null
                            ? result1D.baseline_metrics.conversion * 100
                            : null,
                        ],
                        type: 'scatter',
                        mode: 'markers',
                        name: 'Baseline Marker',
                        marker: { color: '#f59e0b', size: 10, symbol: 'diamond' },
                      },
                    ]}
                    layout={{
                      ...baseLayout,
                      xaxis: {
                        ...baseLayout.xaxis,
                        title: { text: `${result1D.variable_label} [${result1D.variable_unit}]` },
                      },
                      yaxis: { ...baseLayout.yaxis, title: { text: 'Conversion [%]' }, range: [0, 105] },
                    }}
                    useResizeHandler
                    className="w-full h-full"
                    config={{ responsive: true, displayModeBar: false }}
                  />
                </div>
              </div>

              {/* Steady-State Concentration vs Parameter */}
              <div className="glass-panel rounded-2xl p-6 shadow-xl">
                <h3 className="text-sm font-semibold text-white mb-1">
                  Steady-State Concentration (C_A,ss) vs {result1D.variable_label}
                </h3>
                <p className="text-xs text-slate-400">Effluent reactant concentration [mol/L]</p>
                <div className="h-64 w-full mt-2">
                  <Plot
                    data={[
                      {
                        x: result1D.points.map(p => p.param_value),
                        y: result1D.points.map(p => p.C_A_ss),
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: 'C_A,ss [mol/L]',
                        line: { color: '#10b981', width: 2.5 },
                        marker: { size: 4 },
                      },
                      {
                        x: [result1D.baseline_param_value],
                        y: [result1D.baseline_metrics.C_A_ss],
                        type: 'scatter',
                        mode: 'markers',
                        name: 'Baseline Marker',
                        marker: { color: '#f59e0b', size: 10, symbol: 'diamond' },
                      },
                    ]}
                    layout={{
                      ...baseLayout,
                      xaxis: {
                        ...baseLayout.xaxis,
                        title: { text: `${result1D.variable_label} [${result1D.variable_unit}]` },
                      },
                      yaxis: { ...baseLayout.yaxis, title: { text: 'C_A,ss [mol/L]' } },
                    }}
                    useResizeHandler
                    className="w-full h-full"
                    config={{ responsive: true, displayModeBar: false }}
                  />
                </div>
              </div>
            </div>
          )}

          {/* 2D Surface Contour / Heatmap */}
          {result2D && (
            <div className="glass-panel rounded-2xl p-6 shadow-xl">
              <h3 className="text-sm font-semibold text-white mb-1">
                2D Conversion Map: {result2D.var_x_label} vs {result2D.var_y_label}
              </h3>
              <p className="text-xs text-slate-400">
                Heatmap & contour contours of steady-state conversion X_A [%]
              </p>
              <div className="h-80 w-full mt-3">
                <Plot
                  data={[
                    {
                      z: result2D.conversion_grid.map(row =>
                        row.map(v => (v !== null ? v * 100 : 0))
                      ),
                      x: result2D.x_values,
                      y: result2D.y_values,
                      type: 'contour',
                      colorscale: 'Viridis',
                      contours: { coloring: 'heatmap', showlabels: true },
                      colorbar: { title: { text: 'X_A [%]' }, len: 0.8 },
                    },
                    {
                      x: [result2D.baseline_point.x],
                      y: [result2D.baseline_point.y],
                      type: 'scatter',
                      mode: 'markers',
                      name: 'Baseline Operating Point',
                      marker: { color: '#ef4444', size: 12, symbol: 'cross' },
                    },
                  ]}
                  layout={{
                    ...baseLayout,
                    xaxis: {
                      ...baseLayout.xaxis,
                      title: { text: `${result2D.var_x_label} [${result2D.var_x_unit}]` },
                    },
                    yaxis: {
                      ...baseLayout.yaxis,
                      title: { text: `${result2D.var_y_label} [${result2D.var_y_unit}]` },
                    },
                  }}
                  useResizeHandler
                  className="w-full h-full"
                  config={{ responsive: true, displayModeBar: false }}
                />
              </div>
            </div>
          )}

          {/* Latin Hypercube Sampling (QMC) Results */}
          {resultLHS && (
            <div className="space-y-6">
              {/* Summary Stats Banner */}
              <div className="glass-panel rounded-2xl p-6 shadow-xl">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <Shuffle className="w-4 h-4 text-purple-400" />
                    <h3 className="text-sm font-semibold text-white">
                      Latin Hypercube Quasi-Monte Carlo Results
                    </h3>
                  </div>
                  <span className="text-[11px] font-mono text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                    Seed: {resultLHS.seed} | Samples: {resultLHS.n_samples}
                  </span>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                  <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">Evaluated / Success</span>
                    <span className="text-base font-bold text-emerald-400">
                      {resultLHS.summary_statistics.successful_evaluations} /{' '}
                      {resultLHS.summary_statistics.total_evaluations}
                    </span>
                  </div>
                  <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">Failed Cases</span>
                    <span
                      className={`text-base font-bold ${
                        resultLHS.failed_count > 0 ? 'text-rose-400' : 'text-slate-200'
                      }`}
                    >
                      {resultLHS.failed_count}
                    </span>
                  </div>
                  <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">Mean Conversion</span>
                    <span className="text-base font-bold text-cyan-400">
                      {resultLHS.summary_statistics.mean_conversion !== null
                        ? `${(resultLHS.summary_statistics.mean_conversion * 100).toFixed(1)}%`
                        : 'N/A'}
                    </span>
                  </div>
                  <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">Mean Residence Time</span>
                    <span className="text-base font-bold text-amber-400">
                      {resultLHS.summary_statistics.mean_residence_time !== null
                        ? `${resultLHS.summary_statistics.mean_residence_time.toFixed(2)} min`
                        : 'N/A'}
                    </span>
                  </div>
                </div>

                {/* Explicit Failed Cases Warning */}
                {resultLHS.failed_count > 0 && (
                  <div className="mt-3 p-3 bg-rose-950/40 border border-rose-800/80 rounded-lg flex items-start space-x-2 text-xs text-rose-300">
                    <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold block">Failed Simulations Reported:</span>
                      <span>
                        {resultLHS.failed_count} parameter draws failed physically or mathematically. Failed cases are preserved above rather than dropped silently.
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {/* LHS Scatter Plot: Conversion vs Residence Time colored by Rate Constant */}
              <div className="glass-panel rounded-2xl p-6 shadow-xl">
                <h3 className="text-sm font-semibold text-white mb-1">
                  QMC Parametric Space: Conversion ($X_A$) vs Residence Time ($\tau$)
                </h3>
                <p className="text-xs text-slate-400">
                  Colored by Kinetic Rate Constant $k$ [canonical units]
                </p>
                <div className="h-72 w-full mt-2">
                  <Plot
                    data={[
                      {
                        x: resultLHS.points.filter(p => p.status === 'ok').map(p => p.tau),
                        y: resultLHS.points
                          .filter(p => p.status === 'ok')
                          .map(p => (p.conversion !== null ? p.conversion * 100 : null)),
                        text: resultLHS.points
                          .filter(p => p.status === 'ok')
                          .map(
                            p =>
                              `#${p.sample_index}: V=${p.V.toFixed(2)}L, Q=${p.Q.toFixed(2)}L/min, k=${p.k.toFixed(3)}, C_in=${p.C_A_in.toFixed(2)}M`
                          ),
                        type: 'scatter',
                        mode: 'markers',
                        marker: {
                          size: 7,
                          color: resultLHS.points
                            .filter(p => p.status === 'ok')
                            .map(p => p.k),
                          colorscale: 'Plasma',
                          colorbar: { title: { text: 'k' }, len: 0.8 },
                        },
                      },
                    ]}
                    layout={{
                      ...baseLayout,
                      xaxis: { ...baseLayout.xaxis, title: { text: 'Mean Residence Time τ [min]' } },
                      yaxis: {
                        ...baseLayout.yaxis,
                        title: { text: 'Conversion X_A [%]' },
                        range: [0, 105],
                      },
                    }}
                    useResizeHandler
                    className="w-full h-full"
                    config={{ responsive: true, displayModeBar: false }}
                  />
                </div>
              </div>

              {/* Sample Points Table */}
              <div className="glass-panel rounded-2xl p-6 shadow-xl">
                <h4 className="text-xs font-semibold text-white mb-2 uppercase tracking-wide">
                  Quasi-Monte Carlo Sample Points Table (First 15 Samples)
                </h4>
                <div className="overflow-x-auto max-h-56">
                  <table className="w-full text-left text-[11px] font-mono text-slate-300">
                    <thead className="bg-slate-950 text-slate-400 sticky top-0">
                      <tr>
                        <th className="p-1.5">#</th>
                        <th className="p-1.5">V [L]</th>
                        <th className="p-1.5">Q [L/min]</th>
                        <th className="p-1.5">k</th>
                        <th className="p-1.5">C_in</th>
                        <th className="p-1.5">τ [min]</th>
                        <th className="p-1.5">C_ss [M]</th>
                        <th className="p-1.5">X_A [%]</th>
                        <th className="p-1.5">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {resultLHS.points.slice(0, 15).map(pt => (
                        <tr
                          key={pt.sample_index}
                          className={pt.status === 'failed' ? 'bg-rose-950/20 text-rose-300' : ''}
                        >
                          <td className="p-1.5">{pt.sample_index}</td>
                          <td className="p-1.5">{pt.V.toFixed(2)}</td>
                          <td className="p-1.5">{pt.Q.toFixed(2)}</td>
                          <td className="p-1.5">{pt.k.toFixed(3)}</td>
                          <td className="p-1.5">{pt.C_A_in.toFixed(2)}</td>
                          <td className="p-1.5">{pt.tau.toFixed(2)}</td>
                          <td className="p-1.5">{isNaN(pt.C_A_ss) ? '—' : pt.C_A_ss.toFixed(3)}</td>
                          <td className="p-1.5">
                            {pt.conversion !== null ? `${(pt.conversion * 100).toFixed(1)}%` : '—'}
                          </td>
                          <td className="p-1.5">
                            {pt.status === 'ok' ? (
                              <span className="text-emerald-400">ok</span>
                            ) : (
                              <span className="text-rose-400" title={pt.warning || 'Failed'}>
                                failed
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
