import React, { useState } from 'react';
import Plot from 'react-plotly.js';
import {
  Calculator,
  Sparkles,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  TrendingDown,
  Layers,
  ShieldAlert,
  Target,
  BarChart3,
} from 'lucide-react';
import { api, ApiError } from '../api/client';
import { FitKineticsResponse } from '../api/types';

export const EstimationPage: React.FC = () => {
  // Model & Fitting Configuration
  const [modelType, setModelType] = useState<'dynamic' | 'steady_state'>('dynamic');
  const [reactionOrder, setReactionOrder] = useState<0 | 1 | 2>(1);

  // Operating parameters
  const [volume, setVolume] = useState<number>(10.0);
  const [flowRate, setFlowRate] = useState<number>(1.0);
  const [cInlet, setCInlet] = useState<number>(1.0);
  const [cInitial, setCInitial] = useState<number>(0.1);
  const [fitInitialConc, setFitInitialConc] = useState<boolean>(false);

  // Optimizer settings
  const [kInit, setKInit] = useState<number>(0.05);
  const [kMin, setKMin] = useState<number>(0.0001);
  const [kMax, setKMax] = useState<number>(20.0);
  const [confidenceLevel, setConfidenceLevel] = useState<number>(0.95);

  // Dataset State
  const [dataSource, setDataSource] = useState<'oracle_first_order' | 'noisy_second_order' | 'steady_state_runs' | 'custom'>('oracle_first_order');
  const [timeSeries, setTimeSeries] = useState<number[]>([]);
  const [observedCA, setObservedCA] = useState<number[]>([]);
  const [activeBenchmarkName, setActiveBenchmarkName] = useState<string>('');

  // Execution & Output State
  const [isFitting, setIsFitting] = useState<boolean>(false);
  const [fitResult, setFitResult] = useState<FitKineticsResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Synthetic benchmark generator presets
  const loadOracleFirstOrder = () => {
    // V=10 L, Q=1 L/min, k_true=0.15 min^-1 -> tau=10 min, C_ss=0.40 mol/L
    // C_A(t) = 0.40 + (0.10 - 0.40)*exp(-0.25*t)
    const times: number[] = [];
    const obs: number[] = [];
    for (let t = 0; t <= 40; t += 1.0) {
      times.push(t);
      const clean = 0.40 + (0.10 - 0.40) * Math.exp(-0.25 * t);
      // add realistic small noise
      const noise = (Math.sin(t * 1.5) * 0.008) + ((Math.random() - 0.5) * 0.01);
      obs.push(Math.max(0.0, Number((clean + noise).toFixed(4))));
    }
    setModelType('dynamic');
    setReactionOrder(1);
    setVolume(10.0);
    setFlowRate(1.0);
    setCInlet(1.0);
    setCInitial(0.1);
    setKInit(0.05);
    setTimeSeries(times);
    setObservedCA(obs);
    setDataSource('oracle_first_order');
    setActiveBenchmarkName('First-Order Dynamic Oracle (k_true = 0.15 min⁻¹)');
    setFitResult(null);
    setErrorMessage(null);
  };

  const loadSecondOrderBenchmark = () => {
    // V=10, Q=1, C_in=2.0, k_true=0.25 L/(mol*min)
    const times: number[] = [];
    const obs: number[] = [];
    // approximated numerical trajectory for n=2
    let c = 0.5;
    const dt = 1.0;
    for (let t = 0; t <= 30; t += dt) {
      times.push(t);
      obs.push(Number(c.toFixed(4)));
      // Euler forward step for quick demonstration data
      const dc = (1.0 / 10.0) * (2.0 - c) - 0.25 * c * c;
      const noise = (Math.random() - 0.5) * 0.008;
      c = Math.max(0.0, c + dc * dt + noise);
    }
    setModelType('dynamic');
    setReactionOrder(2);
    setVolume(10.0);
    setFlowRate(1.0);
    setCInlet(2.0);
    setCInitial(0.5);
    setKInit(0.1);
    setTimeSeries(times);
    setObservedCA(obs);
    setDataSource('noisy_second_order');
    setActiveBenchmarkName('Second-Order Dynamic Run (k_true = 0.25 L/(mol·min))');
    setFitResult(null);
    setErrorMessage(null);
  };

  const loadSteadyStateBenchmark = () => {
    // 5 distinct residence times tau = 2, 5, 10, 15, 20 min
    // k_true = 0.15 min^-1 -> C_ss = C_in / (1 + k*tau)
    const taus = [2.0, 5.0, 10.0, 15.0, 20.0];
    const obs = taus.map(tau => {
      const clean = 1.0 / (1.0 + 0.15 * tau);
      const noise = (Math.random() - 0.5) * 0.01;
      return Number((clean + noise).toFixed(4));
    });
    setModelType('steady_state');
    setReactionOrder(1);
    setVolume(10.0);
    setFlowRate(1.0);
    setCInlet(1.0);
    setKInit(0.05);
    setTimeSeries(taus);
    setObservedCA(obs);
    setDataSource('steady_state_runs');
    setActiveBenchmarkName('Multi-Flow Steady-State Points (k_true = 0.15 min⁻¹)');
    setFitResult(null);
    setErrorMessage(null);
  };

  // Default init
  React.useEffect(() => {
    loadOracleFirstOrder();
  }, []);

  const handleRunEstimation = async () => {
    if (timeSeries.length < 3) {
      setErrorMessage('At least 3 data points are required for parameter estimation.');
      return;
    }
    setErrorMessage(null);
    setIsFitting(true);

    try {
      const resp = await api.fitKinetics({
        model_type: modelType,
        order: reactionOrder,
        time_series: timeSeries,
        observed_C_A: observedCA,
        V: volume,
        Q: flowRate,
        C_A_in: cInlet,
        C_A_0: fitInitialConc ? null : cInitial,
        fit_initial_conc: fitInitialConc,
        k_init: kInit,
        k_min: kMin,
        k_max: kMax,
        confidence_level: confidenceLevel,
      });
      setFitResult(resp);
    } catch (err: any) {
      setErrorMessage(err instanceof ApiError ? err.message : 'Parameter estimation failed.');
    } finally {
      setIsFitting(false);
    }
  };

  return (
    <div className="py-6 space-y-6">
      {/* Title & Presets */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-2.5">
            <Calculator className="w-7 h-7 text-emerald-400" />
            <span>Kinetic Parameter Estimation</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Rigorous nonlinear least-squares estimation of reaction rate constants with analytical ODE solvers and confidence intervals.
          </p>
        </div>

        {/* Benchmark dataset selector buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={loadOracleFirstOrder}
            className={`px-2.5 py-1.5 rounded-lg text-xs font-medium border transition flex items-center space-x-1.5 ${
              dataSource === 'oracle_first_order'
                ? 'bg-emerald-950/80 border-emerald-600 text-emerald-300'
                : 'bg-slate-900 border-slate-800 text-slate-300 hover:bg-slate-800'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
            <span>1st Order Dynamic</span>
          </button>

          <button
            onClick={loadSecondOrderBenchmark}
            className={`px-2.5 py-1.5 rounded-lg text-xs font-medium border transition flex items-center space-x-1.5 ${
              dataSource === 'noisy_second_order'
                ? 'bg-emerald-950/80 border-emerald-600 text-emerald-300'
                : 'bg-slate-900 border-slate-800 text-slate-300 hover:bg-slate-800'
            }`}
          >
            <Layers className="w-3.5 h-3.5 text-sky-400" />
            <span>2nd Order Dynamic</span>
          </button>

          <button
            onClick={loadSteadyStateBenchmark}
            className={`px-2.5 py-1.5 rounded-lg text-xs font-medium border transition flex items-center space-x-1.5 ${
              dataSource === 'steady_state_runs'
                ? 'bg-emerald-950/80 border-emerald-600 text-emerald-300'
                : 'bg-slate-900 border-slate-800 text-slate-300 hover:bg-slate-800'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5 text-amber-400" />
            <span>Steady-State Runs</span>
          </button>
        </div>
      </div>

      {errorMessage && (
        <div className="bg-rose-950/60 border border-rose-800 text-rose-300 px-4 py-3 rounded-xl text-xs flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Form (4 cols) */}
        <div className="lg:col-span-4 space-y-6">
          <div className="glass-panel rounded-2xl p-6 shadow-2xl space-y-4">
            <h2 className="text-sm font-semibold text-white flex items-center space-x-2">
              <Sliders className="w-4 h-4 text-emerald-400" />
              <span>Fitting Setup</span>
            </h2>

            {/* Benchmark info badge */}
            <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800/80 text-xs">
              <span className="text-slate-400 block text-[11px]">Selected Benchmark:</span>
              <span className="text-emerald-400 font-mono font-medium block truncate">
                {activeBenchmarkName}
              </span>
              <span className="text-[10px] text-slate-500 font-mono">
                {timeSeries.length} points loaded
              </span>
            </div>

            {/* Model Type */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300 block">Analysis Mode</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setModelType('dynamic')}
                  className={`py-1.5 text-xs rounded-lg font-medium border transition ${
                    modelType === 'dynamic'
                      ? 'bg-emerald-950 text-emerald-400 border-emerald-700'
                      : 'bg-slate-950 text-slate-400 border-slate-800 hover:bg-slate-900'
                  }`}
                >
                  Dynamic ODE
                </button>
                <button
                  type="button"
                  onClick={() => setModelType('steady_state')}
                  className={`py-1.5 text-xs rounded-lg font-medium border transition ${
                    modelType === 'steady_state'
                      ? 'bg-emerald-950 text-emerald-400 border-emerald-700'
                      : 'bg-slate-950 text-slate-400 border-slate-800 hover:bg-slate-900'
                  }`}
                >
                  Steady-State
                </button>
              </div>
            </div>

            {/* Reaction Order */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300 block">
                Reaction Order (n)
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[0, 1, 2].map(order => (
                  <button
                    key={order}
                    type="button"
                    onClick={() => setReactionOrder(order as 0 | 1 | 2)}
                    className={`py-1 text-xs rounded-lg font-mono font-medium border transition ${
                      reactionOrder === order
                        ? 'bg-emerald-950 text-emerald-400 border-emerald-700'
                        : 'bg-slate-950 text-slate-400 border-slate-800 hover:bg-slate-900'
                    }`}
                  >
                    n = {order}
                  </button>
                ))}
              </div>
            </div>

            {/* Reactor Parameters */}
            <div className="grid grid-cols-2 gap-3 pt-2 border-t border-slate-800">
              <div className="space-y-1">
                <label className="text-[11px] text-slate-400 block">Volume (V) [L]</label>
                <input
                  type="number"
                  step="0.5"
                  min="0.1"
                  value={volume}
                  onChange={e => setVolume(parseFloat(e.target.value) || 10)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 font-mono"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[11px] text-slate-400 block">Flow (Q) [L/min]</label>
                <input
                  type="number"
                  step="0.1"
                  min="0.01"
                  value={flowRate}
                  onChange={e => setFlowRate(parseFloat(e.target.value) || 1)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 font-mono"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[11px] text-slate-400 block">Inlet C_A,in [mol/L]</label>
                <input
                  type="number"
                  step="0.1"
                  min="0.0"
                  value={cInlet}
                  onChange={e => setCInlet(parseFloat(e.target.value) || 1)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 font-mono"
                />
              </div>

              {modelType === 'dynamic' && (
                <div className="space-y-1">
                  <label className="text-[11px] text-slate-400 block">Initial C_A(0) [mol/L]</label>
                  <input
                    type="number"
                    step="0.05"
                    min="0.0"
                    disabled={fitInitialConc}
                    value={cInitial}
                    onChange={e => setCInitial(parseFloat(e.target.value) || 0)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 font-mono disabled:opacity-50"
                  />
                </div>
              )}
            </div>

            {/* Optimizer Initial Guess & Bounds */}
            <div className="space-y-3 pt-2 border-t border-slate-800">
              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-300 block">
                  Initial Guess k_init
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0.0001"
                  value={kInit}
                  onChange={e => setKInit(parseFloat(e.target.value) || 0.1)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-[11px] text-slate-400 block mb-0.5">k_min Bound</span>
                  <input
                    type="number"
                    step="0.001"
                    min="0"
                    value={kMin}
                    onChange={e => setKMin(parseFloat(e.target.value) || 1e-5)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 font-mono text-slate-200"
                  />
                </div>
                <div>
                  <span className="text-[11px] text-slate-400 block mb-0.5">k_max Bound</span>
                  <input
                    type="number"
                    step="1"
                    min="1"
                    value={kMax}
                    onChange={e => setKMax(parseFloat(e.target.value) || 50)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 font-mono text-slate-200"
                  />
                </div>
              </div>

              <div className="space-y-1 pt-1">
                <div className="flex justify-between text-xs text-slate-300">
                  <span>Confidence Level:</span>
                  <span className="font-mono text-emerald-400">{(confidenceLevel * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min="0.80"
                  max="0.99"
                  step="0.01"
                  value={confidenceLevel}
                  onChange={e => setConfidenceLevel(parseFloat(e.target.value))}
                  className="w-full accent-emerald-500"
                />
              </div>

              {modelType === 'dynamic' && (
                <label className="flex items-center space-x-2 pt-1 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={fitInitialConc}
                    onChange={e => setFitInitialConc(e.target.checked)}
                    className="rounded border-slate-700 bg-slate-950 text-emerald-500 focus:ring-0"
                  />
                  <span className="text-xs text-slate-300">Co-estimate Initial C_A(0)</span>
                </label>
              )}
            </div>

            {/* Run Button */}
            <button
              onClick={handleRunEstimation}
              disabled={isFitting}
              className="w-full py-2.5 px-4 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs flex items-center justify-center space-x-2 transition shadow-lg shadow-emerald-950"
            >
              {isFitting ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Optimizing Parameters...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Fit Kinetic Parameters</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Dashboard (8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          {fitResult ? (
            <>
              {/* Primary Fitted Parameters Card */}
              <div className="glass-panel rounded-2xl p-6 shadow-2xl space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
                  <div>
                    <span className="text-xs text-slate-400 block">Fitted Rate Constant (k̂)</span>
                    <div className="flex items-baseline space-x-2">
                      <span className="text-3xl font-extrabold text-emerald-400 font-mono">
                        {fitResult.fitted_k.toFixed(5)}
                      </span>
                      <span className="text-xs text-slate-400 font-mono">
                        {fitResult.k_unit}
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-col items-start sm:items-end">
                    <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                      Fitted Estimate
                    </span>
                    <span className="text-[11px] text-slate-500 mt-0.5">
                      {fitResult.optimizer_message}
                    </span>
                  </div>
                </div>

                {/* Confidence Interval & Statistical Metrics Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-slate-500 block">Coefficient R²</span>
                    <span className="text-slate-100 font-mono font-semibold text-sm">
                      {fitResult.r_squared.toFixed(5)}
                    </span>
                  </div>

                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-slate-500 block">RMSE (mol/L)</span>
                    <span className="text-slate-100 font-mono font-semibold text-sm">
                      {fitResult.rmse.toExponential(3)}
                    </span>
                  </div>

                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-slate-500 block">Standard Error SE(k)</span>
                    <span className="text-slate-100 font-mono font-semibold text-sm">
                      {fitResult.confidence_interval_k
                        ? fitResult.confidence_interval_k.std_error.toExponential(3)
                        : 'N/A'}
                    </span>
                  </div>

                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-slate-500 block">95% Confidence Interval</span>
                    <span className="text-emerald-400 font-mono font-semibold text-[11px] block truncate">
                      {fitResult.confidence_interval_k
                        ? `[${fitResult.confidence_interval_k.ci_lower.toFixed(4)}, ${fitResult.confidence_interval_k.ci_upper.toFixed(4)}]`
                        : (fitResult.uncertainty_note || 'Indefensible')}
                    </span>
                  </div>
                </div>

                {/* Identifiability & Collinearity Diagnostics */}
                {(fitResult.condition_number != null || fitResult.parameter_correlation != null) && (
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    {fitResult.condition_number != null && (
                      <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                        <span className="text-slate-500 block">Condition Number κ(JᵀJ)</span>
                        <span className="text-cyan-400 font-mono font-semibold">
                          {fitResult.condition_number.toExponential(2)}
                        </span>
                      </div>
                    )}
                    {fitResult.parameter_correlation?.k_C_A_0 != null && (
                      <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                        <span className="text-slate-500 block">Correlation ρ(k, C_A,0)</span>
                        <span className={`font-mono font-semibold ${Math.abs(fitResult.parameter_correlation.k_C_A_0) > 0.9 ? 'text-amber-400' : 'text-emerald-400'}`}>
                          {fitResult.parameter_correlation.k_C_A_0.toFixed(4)}
                        </span>
                      </div>
                    )}
                  </div>
                )}

                {/* Provenance Notice */}
                <div className="flex items-start space-x-2 text-amber-300 bg-amber-950/30 border border-amber-800/50 p-2.5 rounded-lg text-[11px]">
                  <ShieldAlert className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <span>{fitResult.provenance_label}</span>
                </div>

                {/* Warnings */}
                {fitResult.warnings.length > 0 && (
                  <div className="space-y-1 p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-[11px]">
                    <span className="text-amber-400 font-semibold block">Optimizer Findings:</span>
                    {fitResult.warnings.map((w, i) => (
                      <div key={i} className="flex items-center space-x-1.5 text-amber-300">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                        <span>{w}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Observed vs Fitted Plot */}
              <div className="glass-panel rounded-2xl p-6 shadow-2xl">
                <h3 className="text-sm font-semibold text-white mb-2 flex items-center space-x-2">
                  <Target className="w-4 h-4 text-emerald-400" />
                  <span>Observed vs Model Trajectory</span>
                </h3>
                <Plot
                  data={[
                    {
                      x: fitResult.time_series,
                      y: fitResult.observed_C_A,
                      type: 'scatter',
                      mode: 'markers',
                      name: 'Observed Data Points',
                      marker: { color: '#38bdf8', size: 6 },
                    },
                    {
                      x: fitResult.time_series,
                      y: fitResult.predicted_C_A,
                      type: 'scatter',
                      mode: 'lines',
                      name: `Fitted Model (k̂ = ${fitResult.fitted_k.toFixed(4)})`,
                      line: { color: '#10b981', width: 2.5 },
                    },
                  ]}
                  layout={{
                    autosize: true,
                    paper_bgcolor: '#020617',
                    plot_bgcolor: '#090d16',
                    font: { color: '#94a3b8', family: 'Inter, sans-serif', size: 11 },
                    margin: { l: 50, r: 20, t: 20, b: 50 },
                    xaxis: {
                      title: { text: modelType === 'dynamic' ? 'Time (min)' : 'Residence Time tau (min)' },
                      gridcolor: '#1e293b',
                      zerolinecolor: '#334155',
                    },
                    yaxis: {
                      title: { text: 'Concentration (mol/L)' },
                      gridcolor: '#1e293b',
                      zerolinecolor: '#334155',
                    },
                    legend: { orientation: 'h', y: -0.25 },
                  }}
                  useResizeHandler={true}
                  className="w-full h-80"
                />
              </div>

              {/* Residuals Plot */}
              <div className="glass-panel rounded-2xl p-6 shadow-2xl">
                <h3 className="text-sm font-semibold text-white mb-2 flex items-center space-x-2">
                  <TrendingDown className="w-4 h-4 text-emerald-400" />
                  <span>Residuals Plot (e_i = C_A,obs - C_A,pred)</span>
                </h3>
                <Plot
                  data={[
                    {
                      x: fitResult.time_series,
                      y: fitResult.residuals,
                      type: 'scatter',
                      mode: 'markers',
                      name: 'Residuals',
                      marker: { color: '#f59e0b', size: 6 },
                    },
                  ]}
                  layout={{
                    autosize: true,
                    paper_bgcolor: '#020617',
                    plot_bgcolor: '#090d16',
                    font: { color: '#94a3b8', family: 'Inter, sans-serif', size: 11 },
                    margin: { l: 50, r: 20, t: 20, b: 50 },
                    xaxis: {
                      title: { text: modelType === 'dynamic' ? 'Time (min)' : 'Residence Time tau (min)' },
                      gridcolor: '#1e293b',
                      zerolinecolor: '#334155',
                    },
                    yaxis: {
                      title: { text: 'Residual Error (mol/L)' },
                      gridcolor: '#1e293b',
                      zerolinecolor: '#e2e8f0',
                    },
                  }}
                  useResizeHandler={true}
                  className="w-full h-64"
                />
              </div>
            </>
          ) : (
            <div className="glass-panel rounded-2xl p-12 text-center space-y-3 shadow-2xl">
              <Calculator className="w-12 h-12 text-slate-600 mx-auto" />
              <h3 className="text-base font-semibold text-slate-300">Ready for Kinetic Parameter Estimation</h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Select a benchmark dataset above or configure custom parameters, then click "Fit Kinetic Parameters" to solve nonlinear least-squares and view statistical confidence intervals.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
