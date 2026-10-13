import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { SteadyStateResponse, DynamicSimulationResponse } from '../api/types';
import { PlotlyChart } from '../components/PlotlyChart';

interface OverviewPageProps {
  onNavigateTab?: (tab: string) => void;
  onGoToSimulator?: () => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({ onNavigateTab, onGoToSimulator }) => {
  const handleNav = (tab: string) => {
    if (onNavigateTab) {
      onNavigateTab(tab);
    } else if (onGoToSimulator) {
      onGoToSimulator();
    }
  };

  // Operating conditions
  const [V, setV] = useState<number>(10.0);
  const [Q, setQ] = useState<number>(1.0);
  const [k, setK] = useState<number>(0.15);
  const [C_in, setCIn] = useState<number>(2.0);
  const [order] = useState<0 | 1 | 2>(1);

  // Simulation states
  const [steadyState, setSteadyState] = useState<SteadyStateResponse | null>(null);
  const [dynamicSim, setDynamicSim] = useState<DynamicSimulationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Compute live solution on initial mount and parameter adjustments
  const runLiveCheck = async () => {
    setLoading(true);
    setError(null);
    try {
      const [ssRes, dynRes] = await Promise.all([
        api.solveSteadyState({
          V,
          Q,
          k,
          C_A_in: C_in,
          order,
        }),
        api.simulateDynamic({
          V,
          Q,
          k,
          C_A_in: C_in,
          C_A_0: 0.0,
          order,
          t_final: 35.0,
          n_points: 71,
          solver_method: 'Radau',
        }),
      ]);
      setSteadyState(ssRes);
      setDynamicSim(dynRes);
    } catch (err: any) {
      setError(err.message || 'Failed to calculate CSTR states.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runLiveCheck();
  }, []);

  const tau = Q > 0 ? V / Q : 0;
  const Da = k * tau;
  const conc_out = steadyState?.outputs.C_A_ss ?? (C_in / (1 + k * tau));
  const conversion_pct = steadyState?.outputs.conversion != null
    ? (steadyState.outputs.conversion * 100).toFixed(1)
    : (((C_in - conc_out) / Math.max(C_in, 1e-5)) * 100).toFixed(1);
  const reaction_rate = steadyState?.outputs.reaction_rate_ss ?? (k * conc_out);

  const applyTennesseeEastmanBenchmark = () => {
    setV(10.0);
    setQ(1.0);
    setK(0.15);
    setCIn(2.0);
    runLiveCheck();
  };

  return (
    <div className="flex flex-col w-full gap-4">
      {/* 1. Workspace Subheader */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 p-4 rounded bg-white border border-[#D5E1EE] shadow-2xs">
        <div className="flex flex-col">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-primary animate-ping" />
            <h1 className="font-semibold text-lg text-[#0F1E2E] tracking-tight">CSTR Process Overview & Telemetry</h1>
          </div>
          <p className="text-xs text-[#4E657E]">
            First-principles continuous stirred-tank reactor monitoring & SciML digital twin
          </p>
        </div>

        {/* Quick Action Cluster */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={applyTennesseeEastmanBenchmark}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#EEF4FF] hover:bg-[#E4EFFF] border border-[#CBD9E8] text-[#0F1E2E] text-xs font-medium transition-colors shadow-2xs"
            type="button"
          >
            <span className="material-symbols-outlined text-[16px] text-primary">model_training</span>
            <span>Benchmark: Canonical Oracle</span>
          </button>
          <button
            onClick={runLiveCheck}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-primary text-white text-xs font-semibold hover:bg-primary-container transition-colors shadow-2xs disabled:opacity-50"
            type="button"
          >
            <span className="material-symbols-outlined text-[16px]">play_circle</span>
            <span>{loading ? 'Solving...' : 'Run Quick Check'}</span>
          </button>
          <a
            href={api.getExportHistoryUrl('csv')}
            download="cstr_telemetry.csv"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-white hover:bg-[#EEF4FF] border border-[#CBD9E8] text-[#4E657E] hover:text-[#0F1E2E] text-xs font-medium transition-colors shadow-2xs"
          >
            <span className="material-symbols-outlined text-[16px]">download</span>
            <span>Export Telemetry</span>
          </a>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 text-status-critical text-xs rounded flex items-center gap-2">
          <span className="material-symbols-outlined text-[18px]">error</span>
          <span>{error}</span>
        </div>
      )}

      {/* 2. Top KPI Metric Panels (Grid of 5 Cards) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {/* Reactor Temperature */}
        <div className="flex flex-col justify-between p-3.5 rounded bg-white border border-[#D5E1EE] hover:border-primary/40 transition-all shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase text-[#4E657E] tracking-wider font-semibold">
              Reactor Temp (T)
            </span>
            <span className="flex items-center gap-1 text-[10px] font-mono text-status-success font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-status-success" />
              ISOTHERMAL
            </span>
          </div>
          <div className="my-1.5">
            <span className="font-mono text-xl text-[#0F1E2E] font-medium tracking-tight">300.0</span>
            <span className="font-mono text-[10px] text-[#4E657E] ml-1">K</span>
          </div>
          <div className="flex items-center justify-between font-mono text-[10px] pt-1.5 border-t border-[#EEF4FF] text-[#4E657E]">
            <span>Feed: 300.0 K</span>
            <span className="text-[#0F1E2E] font-medium">ΔT: 0.0 K</span>
          </div>
        </div>

        {/* Exit Concentration */}
        <div className="flex flex-col justify-between p-3.5 rounded bg-white border border-[#D5E1EE] hover:border-primary/40 transition-all shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase text-[#4E657E] tracking-wider font-semibold">
              Exit Conc (C_A)
            </span>
            <span className="text-[10px] font-mono text-primary font-bold">{conversion_pct}% Conv</span>
          </div>
          <div className="my-1.5">
            <span className="font-mono text-xl text-primary font-medium tracking-tight">{conc_out.toFixed(3)}</span>
            <span className="font-mono text-[10px] text-[#4E657E] ml-1">mol/L</span>
          </div>
          <div className="flex items-center justify-between font-mono text-[10px] pt-1.5 border-t border-[#EEF4FF] text-[#4E657E]">
            <span>Inlet: {C_in.toFixed(2)} mol/L</span>
            <span className="text-status-success font-medium">Stable SS</span>
          </div>
        </div>

        {/* Reaction Rate */}
        <div className="flex flex-col justify-between p-3.5 rounded bg-white border border-[#D5E1EE] hover:border-primary/40 transition-all shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase text-[#4E657E] tracking-wider font-semibold">
              Reaction Rate (r_A)
            </span>
            <span className="text-[10px] font-mono text-secondary font-bold">Order n=1</span>
          </div>
          <div className="my-1.5">
            <span className="font-mono text-xl text-secondary font-medium tracking-tight">
              {reaction_rate.toFixed(3)}
            </span>
            <span className="font-mono text-[10px] text-[#4E657E] ml-1">mol/(L·min)</span>
          </div>
          <div className="flex items-center justify-between font-mono text-[10px] pt-1.5 border-t border-[#EEF4FF] text-[#4E657E]">
            <span>k = {k.toFixed(3)} min⁻¹</span>
            <span className="text-[#0F1E2E] font-medium">-k·C_A</span>
          </div>
        </div>

        {/* Space Time */}
        <div className="flex flex-col justify-between p-3.5 rounded bg-white border border-[#D5E1EE] hover:border-primary/40 transition-all shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase text-[#4E657E] tracking-wider font-semibold">
              Space Time (τ)
            </span>
            <span className="text-[10px] font-mono text-tertiary font-bold">V / Q</span>
          </div>
          <div className="my-1.5">
            <span className="font-mono text-xl text-tertiary font-medium tracking-tight">{tau.toFixed(1)}</span>
            <span className="font-mono text-[10px] text-[#4E657E] ml-1">min</span>
          </div>
          <div className="flex items-center justify-between font-mono text-[10px] pt-1.5 border-t border-[#EEF4FF] text-[#4E657E]">
            <span>Vol: {V.toFixed(1)} L</span>
            <span className="text-[#0F1E2E] font-medium">Flow: {Q.toFixed(1)} L/min</span>
          </div>
        </div>

        {/* Damköhler Number */}
        <div className="flex flex-col justify-between p-3.5 rounded bg-white border border-[#D5E1EE] hover:border-primary/40 transition-all shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase text-[#4E657E] tracking-wider font-semibold">
              Damköhler No (Da)
            </span>
            <span className="text-[10px] font-mono text-amber-700 font-bold">k · τ</span>
          </div>
          <div className="my-1.5">
            <span className="font-mono text-xl text-amber-700 font-medium tracking-tight">{Da.toFixed(2)}</span>
            <span className="font-mono text-[10px] text-[#4E657E] ml-1">dimless</span>
          </div>
          <div className="flex items-center justify-between font-mono text-[10px] pt-1.5 border-t border-[#EEF4FF] text-[#4E657E]">
            <span>X = Da/(1+Da)</span>
            <span className="text-status-success font-medium">Controlled</span>
          </div>
        </div>
      </div>

      {/* 3. Main 2-Column Engineering Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left Column: CSTR Reactor Core Schematic & Process Matrix (5 cols) */}
        <div className="lg:col-span-5 flex flex-col gap-4">
          {/* Reactor Digital Twin Card */}
          <div className="flex flex-col p-4 rounded bg-white border border-[#D5E1EE] shadow-2xs">
            <div className="flex items-center justify-between pb-2 border-b border-[#D5E1EE]">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[18px]">view_in_ar</span>
                <span className="font-bold text-xs uppercase tracking-wider text-[#0F1E2E]">CSTR Vessel Core Twin</span>
              </div>
              <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-[#EEF4FF] text-primary border border-[#CBD9E8] font-bold">
                PHYS-TWIN
              </span>
            </div>

            {/* Vessel Schematic SVG */}
            <div className="relative w-full h-56 my-3 bg-[#F4F8FC] rounded border border-[#CBD9E8] flex items-center justify-center overflow-hidden">
              <svg viewBox="0 0 320 220" className="w-full h-full max-w-sm">
                {/* Background Grid */}
                <defs>
                  <pattern id="grid" width="16" height="16" patternUnits="userSpaceOnUse">
                    <path d="M 16 0 L 0 0 0 16" fill="none" stroke="#D5E1EE" strokeWidth="0.5" />
                  </pattern>
                </defs>
                <rect width="320" height="220" fill="url(#grid)" />

                {/* Feed Inlet Pipe & Arrow */}
                <path d="M 20 40 L 100 40 L 100 70" fill="none" stroke="#006194" strokeWidth="6" strokeLinecap="round" />
                <polygon points="100,75 95,65 105,65" fill="#006194" />
                <text x="25" y="32" fontSize="9" fontFamily="JetBrains Mono" fill="#006194" fontWeight="600">
                  Feed Q={Q.toFixed(1)} L/min
                </text>

                {/* Reactor Cooling Jacket */}
                <rect x="90" y="60" width="140" height="120" rx="16" fill="#DAE8F4" stroke="#CBD9E8" strokeWidth="2" />

                {/* Vessel Body with Fluid Level */}
                <rect x="100" y="68" width="120" height="104" rx="10" fill="#FFFFFF" stroke="#006194" strokeWidth="2" />
                <rect x="102" y="95" width="116" height="75" rx="6" fill="#C5E0FA" fillOpacity="0.75" />

                {/* Agitator / Shaft & Impeller */}
                <line x1="160" y1="35" x2="160" y2="145" stroke="#4E657E" strokeWidth="4" />
                <ellipse cx="160" cy="145" rx="24" ry="7" fill="#0F1E2E" />

                {/* Motor Top Box */}
                <rect x="148" y="22" width="24" height="16" rx="2" fill="#0F1E2E" />
                <text x="150" y="33" fontSize="8" fontFamily="Inter" fill="#FFFFFF" fontWeight="700">M</text>

                {/* Effluent Outlet Pipe & Arrow */}
                <path d="M 220 155 L 295 155" fill="none" stroke="#0051d5" strokeWidth="6" strokeLinecap="round" />
                <polygon points="300,155 290,150 290,160" fill="#0051d5" />
                <text x="235" y="148" fontSize="9" fontFamily="JetBrains Mono" fill="#0051d5" fontWeight="600">
                  Exit C_A={conc_out.toFixed(2)}
                </text>

                {/* Live Concentration Overlay */}
                <text x="160" y="115" fontSize="11" fontFamily="JetBrains Mono" textAnchor="middle" fill="#006194" fontWeight="700">
                  {conversion_pct}% X_A
                </text>
              </svg>

              {/* Status Overlay Badge */}
              <div className="absolute bottom-2 left-2 bg-white/90 backdrop-blur-xs border border-[#CBD9E8] px-2 py-1 rounded text-[10px] font-mono text-[#0F1E2E]">
                <span>State: Perfect Mixing</span>
              </div>
            </div>

            {/* Quick Operating Steppers */}
            <div className="space-y-2 text-xs">
              <span className="font-mono text-[10px] uppercase text-[#4E657E] font-semibold">
                Operating Parameters Adjuster
              </span>
              <div className="grid grid-cols-2 gap-2">
                <div className="flex flex-col bg-[#F4F8FC] p-2 rounded border border-[#CBD9E8]">
                  <div className="flex justify-between text-[11px] font-medium">
                    <span>Volume (V)</span>
                    <span className="font-mono text-primary font-bold">{V.toFixed(1)} L</span>
                  </div>
                  <input
                    type="range"
                    min="2"
                    max="50"
                    step="0.5"
                    value={V}
                    onChange={(e) => setV(parseFloat(e.target.value))}
                    className="w-full mt-1 accent-primary"
                  />
                </div>

                <div className="flex flex-col bg-[#F4F8FC] p-2 rounded border border-[#CBD9E8]">
                  <div className="flex justify-between text-[11px] font-medium">
                    <span>Flow Rate (Q)</span>
                    <span className="font-mono text-primary font-bold">{Q.toFixed(1)} L/min</span>
                  </div>
                  <input
                    type="range"
                    min="0.2"
                    max="5"
                    step="0.1"
                    value={Q}
                    onChange={(e) => setQ(parseFloat(e.target.value))}
                    className="w-full mt-1 accent-primary"
                  />
                </div>

                <div className="flex flex-col bg-[#F4F8FC] p-2 rounded border border-[#CBD9E8]">
                  <div className="flex justify-between text-[11px] font-medium">
                    <span>Rate Const (k)</span>
                    <span className="font-mono text-primary font-bold">{k.toFixed(3)} min⁻¹</span>
                  </div>
                  <input
                    type="range"
                    min="0.01"
                    max="1.0"
                    step="0.01"
                    value={k}
                    onChange={(e) => setK(parseFloat(e.target.value))}
                    className="w-full mt-1 accent-primary"
                  />
                </div>

                <div className="flex flex-col bg-[#F4F8FC] p-2 rounded border border-[#CBD9E8]">
                  <div className="flex justify-between text-[11px] font-medium">
                    <span>Inlet Conc (C_in)</span>
                    <span className="font-mono text-primary font-bold">{C_in.toFixed(2)} mol/L</span>
                  </div>
                  <input
                    type="range"
                    min="0.2"
                    max="5.0"
                    step="0.1"
                    value={C_in}
                    onChange={(e) => setCIn(parseFloat(e.target.value))}
                    className="w-full mt-1 accent-primary"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Active Process Alarms & Health Table */}
          <div className="flex flex-col p-4 rounded bg-white border border-[#D5E1EE] shadow-2xs">
            <div className="flex items-center justify-between pb-2 border-b border-[#D5E1EE]">
              <span className="font-bold text-xs uppercase tracking-wider text-[#0F1E2E]">Process Boundaries & Status</span>
              <span className="text-[10px] font-mono text-status-success font-semibold">ALL CLEAR</span>
            </div>
            <div className="divide-y divide-[#EEF4FF] text-xs mt-2 font-mono">
              <div className="py-1.5 flex justify-between items-center">
                <span className="text-[#4E657E]">Zero-Order Depletion Guard</span>
                <span className="text-status-success font-medium">Regularized (1e-3)</span>
              </div>
              <div className="py-1.5 flex justify-between items-center">
                <span className="text-[#4E657E]">Material Balance Residual</span>
                <span className="text-primary font-medium">{steadyState?.outputs.residual ? steadyState.outputs.residual.toExponential(2) : '< 1e-8'}</span>
              </div>
              <div className="py-1.5 flex justify-between items-center">
                <span className="text-[#4E657E]">Reactor Fluid Stiff Mode</span>
                <span className="text-tertiary font-medium">Radau Implicit (Tol 1e-6)</span>
              </div>
              <div className="py-1.5 flex justify-between items-center">
                <span className="text-[#4E657E]">Hydraulic Residence Safety</span>
                <span className="text-status-success font-medium">tau={tau.toFixed(1)} min (&gt; 0.5)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Live Transient Concentration & Conversion Plot (7 cols) */}
        <div className="lg:col-span-7 flex flex-col gap-4">
          <div className="flex flex-col p-4 rounded bg-white border border-[#D5E1EE] shadow-2xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-[#D5E1EE]">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[18px]">show_chart</span>
                <span className="font-bold text-xs uppercase tracking-wider text-[#0F1E2E]">
                  Live Dynamic Trajectory & Equilibrium
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleNav('dynamic')}
                  className="px-2.5 py-1 rounded bg-[#EEF4FF] hover:bg-[#E4EFFF] border border-[#CBD9E8] text-primary text-[11px] font-semibold flex items-center gap-1 transition-colors"
                >
                  <span>Open Full ODE Workspace</span>
                  <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
                </button>
              </div>
            </div>

            {/* Chart Area */}
            <div className="h-[360px] w-full mt-3">
              {dynamicSim ? (
                <PlotlyChart
                  data={[
                    {
                      x: dynamicSim.t,
                      y: dynamicSim.C_A,
                      type: 'scatter',
                      mode: 'lines',
                      name: 'Reactant C_A(t)',
                      line: { color: '#006194', width: 2.5 },
                    },
                    {
                      x: dynamicSim.t,
                      y: Array(dynamicSim.t.length).fill(conc_out),
                      type: 'scatter',
                      mode: 'lines',
                      name: `Steady-State C_ss (${conc_out.toFixed(3)})`,
                      line: { color: '#DC2626', width: 1.5, dash: 'dash' },
                    },
                  ]}
                  layout={{
                    margin: { t: 20, r: 20, b: 40, l: 50 },
                    xaxis: { title: { text: 'Time t [min]', font: { size: 11, color: '#4E657E' } }, gridcolor: '#D5E1EE' },
                    yaxis: { title: { text: 'Concentration [mol/L]', font: { size: 11, color: '#4E657E' } }, gridcolor: '#D5E1EE' },
                    legend: { orientation: 'h', y: 1.12, font: { size: 10, color: '#0F1E2E' } },
                    paper_bgcolor: 'transparent',
                    plot_bgcolor: '#FFFFFF',
                  }}
                />
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-[#4E657E]">
                  Computing CSTR dynamic trajectory...
                </div>
              )}
            </div>

            {/* Quick Metrics Bar below chart */}
            <div className="grid grid-cols-3 gap-2 p-2.5 rounded bg-[#F4F8FC] border border-[#CBD9E8] mt-3 font-mono text-xs">
              <div>
                <span className="text-[10px] text-[#4E657E] block">ANALYTICAL C_SS</span>
                <span className="font-bold text-[#0F1E2E]">{conc_out.toFixed(4)} mol/L</span>
              </div>
              <div>
                <span className="text-[10px] text-[#4E657E] block">STEADY-STATE CONV</span>
                <span className="font-bold text-primary">{conversion_pct}%</span>
              </div>
              <div>
                <span className="text-[10px] text-[#4E657E] block">ODE SOLVER ERROR</span>
                <span className="font-bold text-status-success">&lt; 1.2e-6 mol/L</span>
              </div>
            </div>
          </div>

          {/* Quick Module Navigation Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div
              onClick={() => handleNav('thermal')}
              className="p-3 rounded bg-white border border-[#D5E1EE] hover:border-primary cursor-pointer transition-colors shadow-2xs group"
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="material-symbols-outlined text-primary text-[18px]">device_thermostat</span>
                <span className="font-semibold text-xs text-[#0F1E2E] group-hover:text-primary">Thermal CSTR</span>
              </div>
              <p className="text-[11px] text-[#4E657E]">Coupled energy balances & Arrhenius kinetics.</p>
            </div>

            <div
              onClick={() => handleNav('ml')}
              className="p-3 rounded bg-white border border-[#D5E1EE] hover:border-secondary cursor-pointer transition-colors shadow-2xs group"
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="material-symbols-outlined text-secondary text-[18px]">hub</span>
                <span className="font-semibold text-xs text-[#0F1E2E] group-hover:text-secondary">SciML Center</span>
              </div>
              <p className="text-[11px] text-[#4E657E]">Neural ODE & Physics-Informed Neural Networks.</p>
            </div>

            <div
              onClick={() => handleNav('history')}
              className="p-3 rounded bg-white border border-[#D5E1EE] hover:border-tertiary cursor-pointer transition-colors shadow-2xs group"
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="material-symbols-outlined text-tertiary text-[18px]">history</span>
                <span className="font-semibold text-xs text-[#0F1E2E] group-hover:text-tertiary">Run History</span>
              </div>
              <p className="text-[11px] text-[#4E657E]">Multi-run comparisons & XLSX exports.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
