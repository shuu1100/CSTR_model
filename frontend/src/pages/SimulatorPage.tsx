import React, { useEffect, useState } from 'react';
import { api, ApiError } from '../api/client';
import {
  DynamicSimulationRequest,
  DynamicSimulationResponse,
  SteadyStateRequest,
  SteadyStateResponse,
} from '../api/types';
import { AssumptionsPanel } from '../components/AssumptionsPanel';
import { ErrorBanner } from '../components/ErrorBanner';
import { DynamicCharts } from '../components/PlotlyChart';
import { ResultsPanel } from '../components/ResultsPanel';
import { SimulationForm } from '../components/SimulationForm';

interface SimulatorPageProps {
  initialMode?: 'steady' | 'dynamic';
}

export const SimulatorPage: React.FC<SimulatorPageProps> = ({ initialMode = 'dynamic' }) => {
  const [mode, setMode] = useState<'steady' | 'dynamic'>(initialMode);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [steadyResult, setSteadyResult] = useState<SteadyStateResponse | null>(null);
  const [dynamicResult, setDynamicResult] = useState<DynamicSimulationResponse | null>(null);

  useEffect(() => {
    if (initialMode) {
      setMode(initialMode);
    }
  }, [initialMode]);

  // Initial load: automatically execute canonical oracle simulation
  useEffect(() => {
    handleRunDynamicSimulation({
      C_A_0: 0.5,
      C_A_in: 2.0,
      V: 10.0,
      Q: 1.0,
      order: 1,
      k: 0.15,
      t_final: 50.0,
      n_points: 101,
      solver_method: 'RK45',
    });
  }, []);

  const handleRunSteadyState = async (req: SteadyStateRequest) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const res = await api.runSteadyState(req);
      setSteadyResult(res);
    } catch (err: any) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage(err.message || 'An unexpected error occurred while running the simulation.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunDynamicSimulation = async (req: DynamicSimulationRequest) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const res = await api.runDynamicSimulation(req);
      setDynamicResult(res);
    } catch (err: any) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage(err.message || 'An unexpected error occurred while simulating dynamic ODE.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6 py-6">
      {/* Top Banner / Error Display */}
      {errorMessage && (
        <ErrorBanner
          message={errorMessage}
          onDismiss={() => setErrorMessage(null)}
        />
      )}

      {/* Main Grid: Form on Left, Output on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Form & Controls */}
        <div className="lg:col-span-5 space-y-6">
          <SimulationForm
            mode={mode}
            onModeChange={setMode}
            onRunSteadyState={handleRunSteadyState}
            onRunDynamicSimulation={handleRunDynamicSimulation}
            isLoading={isLoading}
          />

          <AssumptionsPanel
            assumptions={
              mode === 'steady'
                ? steadyResult?.assumptions
                : dynamicResult?.assumptions
            }
            normalizedInputs={
              mode === 'steady'
                ? steadyResult?.normalized_inputs
                : dynamicResult?.normalized_inputs
            }
            units={
              mode === 'steady'
                ? steadyResult?.units
                : dynamicResult?.units
            }
          />
        </div>

        {/* Right Column: Results & Interactive Plots */}
        <div className="lg:col-span-7 space-y-6">
          {/* Engineering Results KPI Cards */}
          <ResultsPanel
            mode={mode}
            steadyResult={steadyResult}
            dynamicResult={dynamicResult}
          />

          {/* Dynamic Plotly Charts (only in dynamic mode) */}
          {mode === 'dynamic' && dynamicResult && (
            <DynamicCharts data={dynamicResult} />
          )}

          {/* Steady State Explanatory Card (in steady mode) */}
          {mode === 'steady' && steadyResult && (
            <div className="workstation-card">
              <h3 className="text-sm font-bold text-[#0F1E2E] mb-1">Steady-State Regime Summary</h3>
              <p className="text-xs text-[#4E657E] leading-relaxed mb-3">
                In steady-state continuous operation (dC_A/dt = 0), fluid convective inflow, outflow, and reaction consumption maintain exact algebraic equilibrium inside the vessel.
              </p>
              <div className="bg-[#F0F5FA] p-3 rounded border border-[#CBD9E8] font-mono text-xs text-[#0F1E2E] space-y-1">
                <div>Residence Time (τ): <span className="font-semibold text-primary">{steadyResult.outputs.tau.toFixed(4)} min</span></div>
                <div>Steady-State Reactant Conc. (C_A,ss): <span className="font-semibold text-[#0F1E2E]">{steadyResult.outputs.C_A_ss.toFixed(4)} mol/L</span></div>
                <div>Fractional Conversion (X_A): <span className="font-semibold text-emerald-700">{steadyResult.outputs.conversion !== null ? `${(steadyResult.outputs.conversion * 100).toFixed(2)}%` : 'Undefined (C_A,in = 0)'}</span></div>
                <div>Material Balance Residual: <span className="font-semibold text-[#4E657E]">{steadyResult.outputs.residual.toExponential(3)} mol/(L·min)</span></div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
