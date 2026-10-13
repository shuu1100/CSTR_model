import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import {
  ThermalSimulationRequest,
  ThermalSimulationResponse,
  PRBSAuditResponse,
  PRBSCalibrationResponse,
} from '../api/types';
import { PlotlyChart } from '../components/PlotlyChart';

export const ThermalPage: React.FC = () => {
  // Thermal parameters
  const [params, setParams] = useState<ThermalSimulationRequest>({
    V: 10.0,
    Q: 1.0,
    C_A_in: 2.0,
    T_in: 300.0,
    C_A_0: 0.0,
    T_0: 300.0,
    A: 1.5e7,
    Ea: 50000.0,
    order: 1,
    delta_H_rxn: -60.0,
    UA: 15.0,
    V_j: 2.5,
    Q_j: 1.5,
    T_j_in: 290.0,
    isothermal: false,
    t_final: 40.0,
    n_points: 81,
  });

  const [simResult, setSimResult] = useState<ThermalSimulationResponse | null>(null);
  const [prbsAudit, setPrbsAudit] = useState<PRBSAuditResponse | null>(null);
  const [prbsCalibration, setPrbsCalibration] = useState<PRBSCalibrationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [calibrating, setCalibrating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Run thermal simulation
  const runSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.simulateThermal(params);
      setSimResult(res);
    } catch (err: any) {
      setError(err.message || 'Thermal CSTR simulation failed.');
    } finally {
      setLoading(false);
    }
  };

  // Fetch PRBS audit on mount
  useEffect(() => {
    runSimulation();
    api.getThermalPRBSAudit().then(setPrbsAudit).catch(() => {});
  }, []);

  // Run PRBS calibration
  const runCalibration = async () => {
    setCalibrating(true);
    try {
      const res = await api.calibrateThermalPRBS();
      setPrbsCalibration(res);
    } catch (err: any) {
      setError(err.message || 'PRBS calibration failed.');
    } finally {
      setCalibrating(false);
    }
  };

  const currentT = simResult?.steady_state_T ?? params.T_in;
  const currentTj = simResult?.T_jacket ? simResult.T_jacket[simResult.T_jacket.length - 1] : params.T_j_in ?? 290.0;
  const maxT = simResult?.T_reactor ? Math.max(...simResult.T_reactor) : currentT;
  const isRunaway = simResult?.thermal_runaway_detected || (maxT - params.T_in > 50.0);
  const heatGenPeak = simResult?.heat_generated ? Math.max(...simResult.heat_generated) : 0;
  const heatRemPeak = simResult?.heat_removed ? Math.max(...simResult.heat_removed) : 0;

  return (
    <div className="flex flex-col w-full gap-4">
      {/* Workspace Header Banner & Status Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 bg-white p-4 rounded border border-[#D5E1EE] shadow-2xs">
        <div className="flex flex-col gap-0.5">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-primary animate-ping" />
            <h1 className="font-semibold text-lg text-[#0F1E2E] tracking-tight">Thermal Non-Isothermal CSTR</h1>
            <span className="px-1.5 py-0.5 rounded font-mono text-[10px] bg-[#E4EFFF] text-primary border border-[#C5DCFA] font-bold">
              SYS-THERM-ODE
            </span>
          </div>
          <p className="text-xs text-[#4E657E]">
            Coupled non-linear energy balance, Arrhenius kinetics, and cooling jacket dynamics
          </p>
        </div>

        {/* Active Diagnostic Pill */}
        <div className="flex items-center gap-2.5 px-3 py-1.5 rounded bg-[#F0F6FC] border border-[#CBD9E8] text-xs">
          <div className="flex items-center gap-1.5">
            <span className="material-symbols-outlined text-primary text-[16px]">verified_user</span>
            <span className="text-[#0F1E2E] font-medium">Coupled System Active</span>
          </div>
          <span className="text-[#CBD9E8]">|</span>
          <div className="flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${isRunaway ? 'bg-status-critical animate-ping' : 'bg-status-success'}`} />
            <span className={`font-mono text-[11px] font-medium ${isRunaway ? 'text-status-critical font-bold' : 'text-primary'}`}>
              {isRunaway ? 'THERMAL RUNAWAY DETECTED' : 'Stable Thermal Regime'}
            </span>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 text-status-critical text-xs rounded flex items-center gap-2">
          <span className="material-symbols-outlined text-[18px]">error</span>
          <span>{error}</span>
        </div>
      )}

      {/* Top Telemetry KPIs (Grid of 5 Cards) */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3">
        {/* Reactor Temp */}
        <div className="flex flex-col justify-between bg-white p-3.5 rounded border border-[#D5E1EE] shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase text-[#4E657E] font-semibold">Reactor Temp [T]</span>
            <span className="material-symbols-outlined text-[16px] text-primary">thermostat</span>
          </div>
          <div className="my-1.5">
            <span className="font-mono text-xl text-primary font-medium tracking-tight">{currentT.toFixed(1)}</span>
            <span className="font-mono text-[10px] text-[#4E657E] ml-1">K</span>
          </div>
          <div className="flex items-center justify-between font-mono text-[10px] pt-1.5 border-t border-[#EEF4FF] text-[#4E657E]">
            <span>Peak: {maxT.toFixed(1)} K</span>
            <span className={isRunaway ? 'text-status-critical font-bold' : 'text-status-success font-medium'}>
              ΔT: {(maxT - params.T_in).toFixed(1)} K
            </span>
          </div>
        </div>

        {/* Jacket Temp */}
        <div className="flex flex-col justify-between bg-white p-3.5 rounded border border-[#D5E1EE] shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase text-[#4E657E] font-semibold">Jacket Temp [T_j]</span>
            <span className="material-symbols-outlined text-[16px] text-secondary">mode_heat_cool</span>
          </div>
          <div className="my-1.5">
            <span className="font-mono text-xl text-secondary font-medium tracking-tight">{currentTj.toFixed(1)}</span>
            <span className="font-mono text-[10px] text-[#4E657E] ml-1">K</span>
          </div>
          <div className="flex items-center justify-between font-mono text-[10px] pt-1.5 border-t border-[#EEF4FF] text-[#4E657E]">
            <span>Inlet: {(params.T_j_in ?? 290.0).toFixed(1)} K</span>
            <span className="text-secondary font-medium">ΔTj: {(currentTj - (params.T_j_in ?? 290.0)).toFixed(1)} K</span>
          </div>
        </div>

        {/* Heat Generation */}
        <div className="flex flex-col justify-between bg-white p-3.5 rounded border border-[#D5E1EE] shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase text-[#4E657E] font-semibold">Heat Gen [Q_gen]</span>
            <span className="material-symbols-outlined text-[16px] text-amber-600">local_fire_department</span>
          </div>
          <div className="my-1.5">
            <span className="font-mono text-xl text-amber-700 font-medium tracking-tight">{heatGenPeak.toFixed(1)}</span>
            <span className="font-mono text-[10px] text-[#4E657E] ml-1">kJ/min</span>
          </div>
          <div className="flex items-center justify-between font-mono text-[10px] pt-1.5 border-t border-[#EEF4FF] text-[#4E657E]">
            <span>ΔH = {params.delta_H_rxn} kJ/mol</span>
            <span className="text-[#0F1E2E]">Exothermic</span>
          </div>
        </div>

        {/* Heat Removal */}
        <div className="flex flex-col justify-between bg-white p-3.5 rounded border border-[#D5E1EE] shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase text-[#4E657E] font-semibold">Heat Rem [Q_rem]</span>
            <span className="material-symbols-outlined text-[16px] text-cyan-700">ac_unit</span>
          </div>
          <div className="my-1.5">
            <span className="font-mono text-xl text-cyan-800 font-medium tracking-tight">{heatRemPeak.toFixed(1)}</span>
            <span className="font-mono text-[10px] text-[#4E657E] ml-1">kJ/min</span>
          </div>
          <div className="flex items-center justify-between font-mono text-[10px] pt-1.5 border-t border-[#EEF4FF] text-[#4E657E]">
            <span>UA = {params.UA} kJ/(min·K)</span>
            <span className="text-status-success font-medium">Jacket Cooling</span>
          </div>
        </div>

        {/* Runaway Risk Status */}
        <div className="flex flex-col justify-between bg-white p-3.5 rounded border border-[#D5E1EE] shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase text-[#4E657E] font-semibold">Thermal Safety</span>
            <span className={`material-symbols-outlined text-[16px] ${isRunaway ? 'text-status-critical' : 'text-status-success'}`}>
              {isRunaway ? 'warning' : 'security'}
            </span>
          </div>
          <div className="my-1.5">
            <span className={`font-mono text-lg font-bold tracking-tight ${isRunaway ? 'text-status-critical' : 'text-status-success'}`}>
              {isRunaway ? 'HIGH RISK' : 'NORMAL'}
            </span>
          </div>
          <div className="flex items-center justify-between font-mono text-[10px] pt-1.5 border-t border-[#EEF4FF] text-[#4E657E]">
            <span>Runaway Cutoff: 50 K</span>
            <span className={isRunaway ? 'text-status-critical font-bold' : 'text-status-success'}>
              {isRunaway ? 'TRIP' : 'SAFE'}
            </span>
          </div>
        </div>
      </div>

      {/* Main 2-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left Parameter Panel (4 cols) */}
        <div className="lg:col-span-4 flex flex-col gap-4">
          <div className="flex flex-col p-4 rounded bg-white border border-[#D5E1EE] shadow-2xs space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-[#D5E1EE]">
              <div className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-primary text-[18px]">tune</span>
                <span className="font-bold text-xs uppercase tracking-wider text-[#0F1E2E]">Thermal Parameters</span>
              </div>
              <label className="flex items-center gap-1.5 text-xs text-[#0F1E2E] cursor-pointer">
                <input
                  type="checkbox"
                  checked={params.isothermal || false}
                  onChange={(e) => setParams({ ...params, isothermal: e.target.checked })}
                  className="rounded border-[#CBD9E8] text-primary focus:ring-primary"
                />
                <span className="font-mono text-[11px] font-medium">Isothermal Lock</span>
              </label>
            </div>

            {/* Reactor Hydraulics */}
            <div className="space-y-1.5 text-xs">
              <span className="font-mono text-[10px] text-[#4E657E] uppercase font-semibold">Reactor Hydraulics</span>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[11px] text-[#4E657E] block">Volume V [L]</label>
                  <input
                    type="number"
                    step="0.5"
                    value={params.V}
                    onChange={(e) => setParams({ ...params, V: parseFloat(e.target.value) || 10.0 })}
                    className="scientific-input w-full text-xs"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-[#4E657E] block">Flow Q [L/min]</label>
                  <input
                    type="number"
                    step="0.1"
                    value={params.Q}
                    onChange={(e) => setParams({ ...params, Q: parseFloat(e.target.value) || 1.0 })}
                    className="scientific-input w-full text-xs"
                  />
                </div>
              </div>
            </div>

            {/* Feed Conditions */}
            <div className="space-y-1.5 text-xs">
              <span className="font-mono text-[10px] text-[#4E657E] uppercase font-semibold">Feed Inlet Conditions</span>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[11px] text-[#4E657E] block">C_A,in [mol/L]</label>
                  <input
                    type="number"
                    step="0.1"
                    value={params.C_A_in}
                    onChange={(e) => setParams({ ...params, C_A_in: parseFloat(e.target.value) || 2.0 })}
                    className="scientific-input w-full text-xs"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-[#4E657E] block">T_in [K]</label>
                  <input
                    type="number"
                    step="1"
                    value={params.T_in}
                    onChange={(e) => setParams({ ...params, T_in: parseFloat(e.target.value) || 300.0 })}
                    className="scientific-input w-full text-xs"
                  />
                </div>
              </div>
            </div>

            {/* Arrhenius Kinetics */}
            <div className="space-y-1.5 text-xs">
              <span className="font-mono text-[10px] text-[#4E657E] uppercase font-semibold">Arrhenius Kinetics</span>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[11px] text-[#4E657E] block">Pre-exp A [min⁻¹]</label>
                  <input
                    type="number"
                    value={params.A}
                    onChange={(e) => setParams({ ...params, A: parseFloat(e.target.value) || 1.5e7 })}
                    className="scientific-input w-full text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-[#4E657E] block">E_a [J/mol]</label>
                  <input
                    type="number"
                    step="1000"
                    value={params.Ea}
                    onChange={(e) => setParams({ ...params, Ea: parseFloat(e.target.value) || 50000.0 })}
                    className="scientific-input w-full text-xs font-mono"
                  />
                </div>
                <div className="col-span-2">
                  <label className="text-[11px] text-[#4E657E] block">Reaction Enthalpy ΔH [kJ/mol]</label>
                  <input
                    type="number"
                    step="5"
                    value={params.delta_H_rxn}
                    onChange={(e) => setParams({ ...params, delta_H_rxn: parseFloat(e.target.value) || -60.0 })}
                    className="scientific-input w-full text-xs font-mono"
                  />
                </div>
              </div>
            </div>

            {/* Cooling Jacket */}
            <div className="space-y-1.5 text-xs">
              <span className="font-mono text-[10px] text-[#4E657E] uppercase font-semibold">Cooling Jacket System</span>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[11px] text-[#4E657E] block">Heat Trans UA [kJ/min·K]</label>
                  <input
                    type="number"
                    step="1"
                    value={params.UA}
                    onChange={(e) => setParams({ ...params, UA: parseFloat(e.target.value) || 15.0 })}
                    className="scientific-input w-full text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-[#4E657E] block">Coolant T_j,in [K]</label>
                  <input
                    type="number"
                    step="1"
                    value={params.T_j_in}
                    onChange={(e) => setParams({ ...params, T_j_in: parseFloat(e.target.value) || 290.0 })}
                    className="scientific-input w-full text-xs font-mono"
                  />
                </div>
              </div>
            </div>

            <button
              onClick={runSimulation}
              disabled={loading}
              className="w-full py-2 bg-primary hover:bg-primary-container text-white font-semibold text-xs rounded transition-colors shadow-2xs disabled:opacity-50"
            >
              {loading ? 'Integrating Thermal ODEs...' : 'Solve Thermal Simulation'}
            </button>
          </div>

          {/* PRBS Experimental Dataset Compatibility & Calibration Card */}
          <div className="flex flex-col p-4 rounded bg-white border border-[#D5E1EE] shadow-2xs space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-[#D5E1EE]">
              <div className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-secondary text-[18px]">biotech</span>
                <span className="font-bold text-xs uppercase tracking-wider text-[#0F1E2E]">PRBS Experimental Calibration</span>
              </div>
              <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-[#EEF4FF] text-secondary border border-[#CBD9E8] font-bold">
                AUDITED
              </span>
            </div>

            <p className="text-[11px] text-[#4E657E]">
              Workbook: <code className="bg-[#F4F8FC] px-1 rounded text-[#0F1E2E]">CSTR_24aug_PRBS_dataset.xlsx</code> (3,131 samples, dt=0.5 s).
            </p>

            {prbsAudit && (
              <div className="p-2.5 rounded bg-[#FFFBEB] border border-[#FDE68A] text-[10px] text-[#92400E] font-medium leading-relaxed">
                {prbsAudit.scientific_governance_notice}
              </div>
            )}

            <button
              onClick={runCalibration}
              disabled={calibrating}
              className="w-full py-1.5 bg-[#EEF4FF] hover:bg-[#E4EFFF] border border-[#CBD9E8] text-primary font-semibold text-xs rounded transition-colors shadow-2xs disabled:opacity-50"
            >
              {calibrating ? 'Calibrating On 60% Split...' : 'Calibrate Heat Transfer On PRBS'}
            </button>

            {prbsCalibration && (
              <div className="p-2.5 rounded bg-[#F4F8FC] border border-[#CBD9E8] font-mono text-[11px] space-y-1">
                <div className="flex justify-between">
                  <span className="text-[#4E657E]">Fitted k_jacket:</span>
                  <span className="font-bold text-primary">
                    {prbsCalibration.calibrated_parameters.k_jacket_per_s.toExponential(3)} s⁻¹
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#4E657E]">Locked Test Grad RMSE:</span>
                  <span className="font-bold text-[#0F1E2E]">
                    {prbsCalibration.locked_test_metrics.derivative_rmse_k_per_s.toFixed(4)} K/s
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#4E657E]">1-Step Temp RMSE:</span>
                  <span className="font-bold text-status-success">
                    {prbsCalibration.locked_test_metrics.temperature_1step_rmse_k.toFixed(4)} K
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Plots Column (8 cols) */}
        <div className="lg:col-span-8 flex flex-col gap-4">
          {/* Temperature Dynamics Plot */}
          <div className="flex flex-col p-4 rounded bg-white border border-[#D5E1EE] shadow-2xs">
            <div className="flex items-center justify-between pb-2 border-b border-[#D5E1EE]">
              <span className="font-bold text-xs uppercase tracking-wider text-[#0F1E2E]">
                Coupled Reactor & Jacket Temperature Dynamics
              </span>
              <span className="text-[10px] font-mono text-[#4E657E]">Unit: Kelvin [K]</span>
            </div>
            <div className="h-[280px] w-full mt-2">
              {simResult ? (
                <PlotlyChart
                  data={[
                    {
                      x: simResult.t,
                      y: simResult.T_reactor,
                      type: 'scatter',
                      mode: 'lines',
                      name: 'Reactor Temp T(t)',
                      line: { color: isRunaway ? '#DC2626' : '#006194', width: 2.5 },
                    },
                    {
                      x: simResult.t,
                      y: simResult.T_jacket,
                      type: 'scatter',
                      mode: 'lines',
                      name: 'Jacket Temp Tj(t)',
                      line: { color: '#0051d5', width: 2, dash: 'dot' },
                    },
                    {
                      x: simResult.t,
                      y: Array(simResult.t.length).fill(params.T_in + 50.0),
                      type: 'scatter',
                      mode: 'lines',
                      name: 'Runaway Threshold (T_in + 50K)',
                      line: { color: '#DC2626', width: 1.5, dash: 'dash' },
                    },
                  ]}
                  layout={{
                    margin: { t: 20, r: 20, b: 40, l: 50 },
                    xaxis: { title: { text: 'Time t [min]', font: { size: 11, color: '#4E657E' } }, gridcolor: '#D5E1EE' },
                    yaxis: { title: { text: 'Temperature [K]', font: { size: 11, color: '#4E657E' } }, gridcolor: '#D5E1EE' },
                    legend: { orientation: 'h', y: 1.15, font: { size: 10, color: '#0F1E2E' } },
                    paper_bgcolor: 'transparent',
                    plot_bgcolor: '#FFFFFF',
                  }}
                />
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-[#4E657E]">
                  Solving thermal balances...
                </div>
              )}
            </div>
          </div>

          {/* Heat Balance Curves & Reaction Conversion */}
          <div className="flex flex-col p-4 rounded bg-white border border-[#D5E1EE] shadow-2xs">
            <div className="flex items-center justify-between pb-2 border-b border-[#D5E1EE]">
              <span className="font-bold text-xs uppercase tracking-wider text-[#0F1E2E]">
                Thermal Energy Balances (Generation vs Removal)
              </span>
              <span className="text-[10px] font-mono text-[#4E657E]">Unit: kJ/min</span>
            </div>
            <div className="h-[260px] w-full mt-2">
              {simResult ? (
                <PlotlyChart
                  data={[
                    {
                      x: simResult.t,
                      y: simResult.heat_generated,
                      type: 'scatter',
                      mode: 'lines',
                      name: 'Heat Generated Q_gen',
                      line: { color: '#D97706', width: 2 },
                    },
                    {
                      x: simResult.t,
                      y: simResult.heat_removed,
                      type: 'scatter',
                      mode: 'lines',
                      name: 'Heat Removed Q_rem',
                      line: { color: '#0284C7', width: 2 },
                    },
                  ]}
                  layout={{
                    margin: { t: 20, r: 20, b: 40, l: 50 },
                    xaxis: { title: { text: 'Time t [min]', font: { size: 11, color: '#4E657E' } }, gridcolor: '#D5E1EE' },
                    yaxis: { title: { text: 'Heat Flow [kJ/min]', font: { size: 11, color: '#4E657E' } }, gridcolor: '#D5E1EE' },
                    legend: { orientation: 'h', y: 1.15, font: { size: 10, color: '#0F1E2E' } },
                    paper_bgcolor: 'transparent',
                    plot_bgcolor: '#FFFFFF',
                  }}
                />
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
