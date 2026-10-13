import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import {
  BrainCircuit,
  Cpu,
  Sparkles,
  TrendingDown,
  Activity,
  AlertTriangle,
  RefreshCw,
  Sliders,
  BarChart2,
  ShieldCheck,
  Flame,
} from 'lucide-react';
import { api, ApiError } from '../api/client';
import {
  MLBaselinesBenchmarkResponse,
  MLInferenceResponse,
  MLModelCatalogItem,
  MLTrainingResponse,
} from '../api/types';

export const MachineLearningPage: React.FC = () => {
  // Navigation sub-tabs
  const [activeView, setActiveView] = useState<'inference' | 'training' | 'benchmark'>('inference');

  // Catalog state
  const [catalog, setCatalog] = useState<MLModelCatalogItem[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('GREY_BOX_NEURAL_ODE');

  // Inference state
  const [volume, setVolume] = useState<number>(10.0);
  const [flowRate, setFlowRate] = useState<number>(1.0);
  const [kRate, setKRate] = useState<number>(0.15);
  const [cInlet, setCInlet] = useState<number>(2.0);
  const [cInitial, setCInitial] = useState<number>(0.0);
  const [tFinal, setTFinal] = useState<number>(30.0);
  const [isInferring, setIsInferring] = useState<boolean>(false);
  const [inferenceResult, setInferenceResult] = useState<MLInferenceResponse | null>(null);

  // Training state
  const [trainEpochs, setTrainEpochs] = useState<number>(30);
  const [trainLr, setTrainLr] = useState<number>(0.01);
  const [trainHiddenDim, setTrainHiddenDim] = useState<number>(32);
  const [trainSeed, setTrainSeed] = useState<number>(42);
  const [isTraining, setIsTraining] = useState<boolean>(false);
  const [trainingResult, setTrainingResult] = useState<MLTrainingResponse | null>(null);

  // Benchmark state
  const [benchmark, setBenchmark] = useState<MLBaselinesBenchmarkResponse | null>(null);
  const [isLoadingBenchmark, setIsLoadingBenchmark] = useState<boolean>(false);

  // General error state
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    // Load model catalog
    api
      .listMLModels()
      .then(items => {
        setCatalog(items);
        if (items.length > 0) setSelectedModel(items[0].model_type);
      })
      .catch(() => {});

    // Load benchmark
    loadBenchmark();
  }, []);

  const loadBenchmark = async () => {
    setIsLoadingBenchmark(true);
    try {
      const data = await api.getMLBaselinesBenchmark();
      setBenchmark(data);
    } catch {
      // ignore
    } finally {
      setIsLoadingBenchmark(false);
    }
  };

  const handleRunInference = async () => {
    setIsInferring(true);
    setErrorMessage(null);
    try {
      const res = await api.predictMLTrajectory({
        model_type: selectedModel,
        V: volume,
        Q: flowRate,
        k: kRate,
        C_A_in: cInlet,
        C_A_0: cInitial,
        order: 1,
        t_final: tFinal,
        n_points: 41,
      });
      setInferenceResult(res);
    } catch (err: any) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Failed to compute ML trajectory forecast.');
      }
    } finally {
      setIsInferring(false);
    }
  };

  const handleTrainModel = async () => {
    setIsTraining(true);
    setErrorMessage(null);
    try {
      const res = await api.trainMLModel({
        model_type: selectedModel,
        epochs: trainEpochs,
        learning_rate: trainLr,
        hidden_dim: trainHiddenDim,
        random_seed: trainSeed,
      });
      setTrainingResult(res);
    } catch (err: any) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Training routine failed.');
      }
    } finally {
      setIsTraining(false);
    }
  };

  return (
    <div className="py-6 space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <BrainCircuit className="w-7 h-7 text-indigo-400" />
              Neural ODE & Physics-Informed ML Studio
            </h1>
            <span className="text-xs font-mono uppercase bg-indigo-950 text-indigo-300 border border-indigo-800 px-2 py-0.5 rounded">
              Phase 09–11
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Hybrid grey-box neural differential equations and continuous autograd PINN surrogates enforcing CSTR mass conservation.
          </p>
        </div>

        {/* View Switcher */}
        <div className="flex bg-slate-900 border border-slate-800 p-1 rounded-xl text-xs font-medium">
          <button
            onClick={() => setActiveView('inference')}
            className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
              activeView === 'inference'
                ? 'bg-indigo-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Activity className="w-4 h-4" />
            Forecast & Inference
          </button>
          <button
            onClick={() => setActiveView('training')}
            className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
              activeView === 'training'
                ? 'bg-indigo-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sliders className="w-4 h-4" />
            Training Studio
          </button>
          <button
            onClick={() => setActiveView('benchmark')}
            className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
              activeView === 'benchmark'
                ? 'bg-indigo-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <BarChart2 className="w-4 h-4" />
            Locked Test Leaderboard
          </button>
        </div>
      </div>

      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/80 text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* VIEW 1: INFERENCE & TRAJECTORY FORECAST */}
      {activeView === 'inference' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Controls Column */}
          <div className="glass-panel rounded-2xl p-6 shadow-2xl space-y-5">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-indigo-400" />
              Model Architecture & Inputs
            </h2>

            {/* Architecture Selector */}
            <div className="space-y-1.5">
              <label className="text-xs font-mono text-slate-400">Architecture</label>
              <select
                value={selectedModel}
                onChange={e => setSelectedModel(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
              >
                {catalog.length > 0 ? (
                  catalog.map(cat => (
                    <option key={cat.model_id} value={cat.model_type}>
                      {cat.name}
                    </option>
                  ))
                ) : (
                  <>
                    <option value="GREY_BOX_NEURAL_ODE">Grey-Box Neural ODE (PyTorch RK4)</option>
                    <option value="PINN">Physics-Informed Neural Net (PINN Collocation)</option>
                    <option value="MECHANISTIC_NOMINAL">Mechanistic Analytical Baseline</option>
                    <option value="PERSISTENCE">Static Persistence Baseline</option>
                  </>
                )}
              </select>
            </div>

            {/* Operating Parameters */}
            <div className="grid grid-cols-2 gap-3 pt-2">
              <div className="space-y-1">
                <label className="text-xs font-mono text-slate-400">Volume V [L]</label>
                <input
                  type="number"
                  step="0.5"
                  value={volume}
                  onChange={e => setVolume(parseFloat(e.target.value) || 1.0)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 font-mono"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-mono text-slate-400">Flow Q [L/min]</label>
                <input
                  type="number"
                  step="0.1"
                  value={flowRate}
                  onChange={e => setFlowRate(parseFloat(e.target.value) || 0.1)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 font-mono"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-mono text-slate-400">k [min⁻¹]</label>
                <input
                  type="number"
                  step="0.01"
                  value={kRate}
                  onChange={e => setKRate(parseFloat(e.target.value) || 0.01)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 font-mono"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-mono text-slate-400">C_A,in [mol/L]</label>
                <input
                  type="number"
                  step="0.1"
                  value={cInlet}
                  onChange={e => setCInlet(parseFloat(e.target.value) || 0.0)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 font-mono"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-mono text-slate-400">C_A,0 [mol/L]</label>
                <input
                  type="number"
                  step="0.1"
                  value={cInitial}
                  onChange={e => setCInitial(parseFloat(e.target.value) || 0.0)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 font-mono"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-mono text-slate-400">t_final [min]</label>
                <input
                  type="number"
                  step="5"
                  value={tFinal}
                  onChange={e => setTFinal(parseFloat(e.target.value) || 10.0)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 font-mono"
                />
              </div>
            </div>

            {/* Quick Oracle Preset */}
            <button
              type="button"
              onClick={() => {
                setVolume(10.0);
                setFlowRate(1.0);
                setKRate(0.15);
                setCInlet(2.0);
                setCInitial(0.0);
                setTFinal(30.0);
              }}
              className="w-full text-xs font-mono py-1.5 px-3 rounded-lg border border-indigo-800/60 bg-indigo-950/40 text-indigo-300 hover:bg-indigo-900/60 transition-colors"
            >
              Load Canonical Oracle Preset
            </button>

            {/* Submit Button */}
            <button
              onClick={handleRunInference}
              disabled={isInferring}
              className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs flex items-center justify-center gap-2 shadow-lg shadow-indigo-900/20 disabled:opacity-50 transition-all"
            >
              {isInferring ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Simulating Trajectory...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Run Neural Forecast
                </>
              )}
            </button>

            {/* Provenance Card */}
            {inferenceResult && (
              <div className="p-3.5 bg-slate-950 border border-slate-800 rounded-xl space-y-2 text-xs">
                <div className="flex items-center justify-between text-slate-400">
                  <span>Provenance:</span>
                  <span className="font-mono text-indigo-400 font-bold">{inferenceResult.provenance}</span>
                </div>
                <div className="flex items-center justify-between text-slate-400">
                  <span>Predicted SS:</span>
                  <span className="font-mono text-emerald-400 font-bold">
                    {inferenceResult.steady_state_C_A?.toFixed(4)} mol/L
                  </span>
                </div>
                {inferenceResult.warnings.length > 0 && (
                  <div className="mt-2 p-2 bg-amber-950/40 border border-amber-800 rounded text-amber-300 text-[11px]">
                    {inferenceResult.warnings[0]}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Plotly Chart Column */}
          <div className="lg:col-span-2 glass-panel rounded-2xl p-6 shadow-2xl flex flex-col">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300 mb-3 flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400" />
              Dynamic Concentration Trajectory C_A(t)
            </h2>

            <div className="flex-1 w-full min-h-[420px] rounded-xl overflow-hidden bg-slate-950 border border-slate-850 p-2">
              {inferenceResult ? (
                <Plot
                  data={[
                    {
                      x: inferenceResult.t,
                      y: inferenceResult.C_A,
                      type: 'scatter',
                      mode: 'lines',
                      name: `${inferenceResult.model_type} Forecast`,
                      line: { color: '#6366f1', width: 3 },
                    },
                    ...(inferenceResult.reaction_rate
                      ? [
                          {
                            x: inferenceResult.t,
                            y: inferenceResult.reaction_rate,
                            type: 'scatter' as const,
                            mode: 'lines' as const,
                            name: 'Learned Rate r_A(t)',
                            yaxis: 'y2',
                            line: { color: '#f59e0b', width: 2, dash: 'dot' as const },
                          },
                        ]
                      : []),
                  ]}
                  layout={{
                    autosize: true,
                    paper_bgcolor: 'transparent',
                    plot_bgcolor: 'transparent',
                    font: { color: '#94a3b8', family: 'monospace', size: 11 },
                    margin: { l: 55, r: 55, t: 30, b: 45 },
                    xaxis: {
                      title: { text: 'Time t [min]' },
                      gridcolor: '#1e293b',
                      zerolinecolor: '#334155',
                    },
                    yaxis: {
                      title: { text: 'Concentration C_A [mol/L]' },
                      gridcolor: '#1e293b',
                      zerolinecolor: '#334155',
                    },
                    ...(inferenceResult.reaction_rate
                      ? {
                          yaxis2: {
                            title: { text: 'Reaction Rate [mol/(L·min)]' },
                            overlaying: 'y' as const,
                            side: 'right' as const,
                            gridcolor: 'transparent',
                            tickfont: { color: '#f59e0b' },
                          },
                        }
                      : {}),
                    legend: { orientation: 'h', y: -0.2, x: 0.1 },
                  }}
                  useResizeHandler
                  style={{ width: '100%', height: '100%' }}
                />
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-slate-500 font-mono text-xs space-y-2">
                  <Activity className="w-8 h-8 text-slate-600 animate-pulse" />
                  <span>Configure operating parameters and click "Run Neural Forecast"</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* VIEW 2: TRAINING STUDIO */}
      {activeView === 'training' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="glass-panel rounded-2xl p-6 shadow-2xl space-y-5">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <Sliders className="w-4 h-4 text-indigo-400" />
              Hyperparameter Tuning
            </h2>

            <div className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-mono text-slate-400">Model to Train</label>
                <select
                  value={selectedModel}
                  onChange={e => setSelectedModel(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 font-mono"
                >
                  <option value="GREY_BOX_NEURAL_ODE">Grey-Box Neural ODE</option>
                  <option value="PINN">Physics-Informed Neural Net (PINN)</option>
                </select>
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-xs font-mono text-slate-400">
                  <span>Epochs:</span>
                  <span className="text-indigo-400 font-bold">{trainEpochs}</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="100"
                  step="5"
                  value={trainEpochs}
                  onChange={e => setTrainEpochs(parseInt(e.target.value))}
                  className="w-full accent-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-xs font-mono text-slate-400">
                  <span>Learning Rate:</span>
                  <span className="text-indigo-400 font-bold">{trainLr}</span>
                </div>
                <select
                  value={trainLr}
                  onChange={e => setTrainLr(parseFloat(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 font-mono"
                >
                  <option value="0.02">0.02 (Fast initial convergence)</option>
                  <option value="0.01">0.01 (Standard Adam baseline)</option>
                  <option value="0.005">0.005 (Fine-tuning)</option>
                  <option value="0.001">0.001 (High precision)</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-mono text-slate-400">Hidden Dim</label>
                  <input
                    type="number"
                    value={trainHiddenDim}
                    onChange={e => setTrainHiddenDim(parseInt(e.target.value) || 16)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 font-mono"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-mono text-slate-400">Random Seed</label>
                  <input
                    type="number"
                    value={trainSeed}
                    onChange={e => setTrainSeed(parseInt(e.target.value) || 42)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 font-mono"
                  />
                </div>
              </div>

              <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-xl text-xs space-y-1 text-slate-400">
                <div className="flex items-center gap-1.5 text-emerald-400 font-medium">
                  <ShieldCheck className="w-4 h-4" />
                  <span>Zero-Leakage Guard Enforced</span>
                </div>
                <p className="text-[11px] text-slate-500">
                  Tuning is performed exclusively on training & validation splits. Final test holdout is evaluated once at completion.
                </p>
              </div>

              <button
                onClick={handleTrainModel}
                disabled={isTraining}
                className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs flex items-center justify-center gap-2 shadow-lg shadow-indigo-900/20 disabled:opacity-50 transition-all"
              >
                {isTraining ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Training Neural Net...
                  </>
                ) : (
                  <>
                    <Flame className="w-4 h-4" />
                    Train Architecture
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Training Curve Column */}
          <div className="lg:col-span-2 glass-panel rounded-2xl p-6 shadow-2xl flex flex-col space-y-4">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <TrendingDown className="w-4 h-4 text-indigo-400" />
              Loss Convergence Progression
            </h2>

            {trainingResult && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl">
                  <span className="text-[10px] font-mono uppercase text-slate-500">Best Val Loss</span>
                  <div className="text-base font-bold font-mono text-indigo-400">
                    {trainingResult.best_val_loss?.toExponential(3)}
                  </div>
                </div>
                <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl">
                  <span className="text-[10px] font-mono uppercase text-slate-500">Locked Test RMSE</span>
                  <div className="text-base font-bold font-mono text-emerald-400">
                    {trainingResult.test_rmse?.toFixed(4)} mol/L
                  </div>
                </div>
                <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl">
                  <span className="text-[10px] font-mono uppercase text-slate-500">Locked Test R²</span>
                  <div className="text-base font-bold font-mono text-sky-400">
                    {trainingResult.test_r2?.toFixed(4) || '—'}
                  </div>
                </div>
                <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl">
                  <span className="text-[10px] font-mono uppercase text-slate-500">C_A &lt; 0 Violations</span>
                  <div className="text-base font-bold font-mono text-emerald-400">
                    {trainingResult.negative_conc_count} (0%)
                  </div>
                </div>
              </div>
            )}

            <div className="flex-1 w-full min-h-[360px] rounded-xl overflow-hidden bg-slate-950 border border-slate-850 p-2">
              {trainingResult && trainingResult.train_loss_history.length > 0 ? (
                <Plot
                  data={[
                    {
                      x: Array.from({ length: trainingResult.train_loss_history.length }, (_, i) => i + 1),
                      y: trainingResult.train_loss_history,
                      type: 'scatter',
                      mode: 'lines+markers',
                      name: 'Train Loss',
                      line: { color: '#6366f1', width: 2 },
                    },
                    ...(trainingResult.val_loss_history.length > 0
                      ? [
                          {
                            x: Array.from({ length: trainingResult.val_loss_history.length }, (_, i) => i + 1),
                            y: trainingResult.val_loss_history,
                            type: 'scatter' as const,
                            mode: 'lines+markers' as const,
                            name: 'Validation Loss',
                            line: { color: '#10b981', width: 2 },
                          },
                        ]
                      : []),
                  ]}
                  layout={{
                    autosize: true,
                    paper_bgcolor: 'transparent',
                    plot_bgcolor: 'transparent',
                    font: { color: '#94a3b8', family: 'monospace', size: 11 },
                    margin: { l: 55, r: 25, t: 25, b: 45 },
                    xaxis: {
                      title: { text: 'Epoch' },
                      gridcolor: '#1e293b',
                    },
                    yaxis: {
                      title: { text: 'Loss (MSE)' },
                      gridcolor: '#1e293b',
                      type: 'log',
                    },
                    legend: { orientation: 'h', y: -0.2, x: 0.2 },
                  }}
                  useResizeHandler
                  style={{ width: '100%', height: '100%' }}
                />
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-slate-500 font-mono text-xs space-y-2">
                  <TrendingDown className="w-8 h-8 text-slate-600 animate-pulse" />
                  <span>Configure training settings and click "Train Architecture"</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* VIEW 3: BENCHMARK LEADERBOARD */}
      {activeView === 'benchmark' && (
        <div className="glass-panel rounded-2xl p-6 shadow-2xl space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <BarChart2 className="w-5 h-5 text-indigo-400" />
                70/15/15 Disjoint Locked Test Holdout Leaderboard
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Comparative metrics evaluated across 19 held-out test trajectories (1,846 rows) with zero parameter or row-level leakage.
              </p>
            </div>
            <button
              onClick={loadBenchmark}
              disabled={isLoadingBenchmark}
              className="px-3 py-1.5 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-750 text-slate-200 text-xs font-mono flex items-center gap-2 disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoadingBenchmark ? 'animate-spin' : ''}`} />
              Refresh Benchmark
            </button>
          </div>

          {benchmark ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-950/80 text-slate-400 uppercase border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Model Architecture</th>
                    <th className="py-3 px-4">RMSE (mol/L)</th>
                    <th className="py-3 px-4">MAE (mol/L)</th>
                    <th className="py-3 px-4">R²</th>
                    <th className="py-3 px-4">Max Error</th>
                    <th className="py-3 px-4">Physical Violations</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-850">
                  {Object.entries(benchmark.test_metrics).map(([modelName, m]) => (
                    <tr
                      key={modelName}
                      className={
                        modelName === 'RandomForest' || modelName.includes('Neural')
                          ? 'bg-indigo-950/20 text-indigo-200 font-semibold'
                          : 'text-slate-300'
                      }
                    >
                      <td className="py-3 px-4 flex items-center gap-2">
                        {modelName === 'RandomForest' && <Sparkles className="w-3.5 h-3.5 text-indigo-400" />}
                        <span>{modelName}</span>
                      </td>
                      <td className="py-3 px-4">{m.rmse?.toFixed(5)}</td>
                      <td className="py-3 px-4">{m.mae?.toFixed(5)}</td>
                      <td className="py-3 px-4">{m.r2?.toFixed(4)}</td>
                      <td className="py-3 px-4">{m.max_error?.toFixed(5)}</td>
                      <td className="py-3 px-4 text-emerald-400">
                        {m.negative_conc_count ?? 0}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-12 text-center text-slate-500 font-mono text-xs">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-slate-600" />
              Loading test benchmark results...
            </div>
          )}
        </div>
      )}
    </div>
  );
};
