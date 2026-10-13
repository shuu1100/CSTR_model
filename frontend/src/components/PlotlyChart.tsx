import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';
import { DynamicSimulationResponse } from '../api/types';

export const PlotlyChart = Plot;

interface DynamicChartsProps {
  data: DynamicSimulationResponse;
}

export const DynamicCharts: React.FC<DynamicChartsProps> = ({ data }) => {
  const { t, C_A, conversion, reaction_rate, C_A_ss_initial, analytical_comparison, step_change_applied } = data;

  // Concentration Plot Traces
  const concentrationTraces = useMemo(() => {
    const traces: Plotly.Data[] = [
      {
        x: t,
        y: C_A,
        type: 'scatter',
        mode: 'lines',
        name: 'Numerical C_A(t)',
        line: { color: '#10b981', width: 3 },
      },
      {
        x: [t[0], t[t.length - 1]],
        y: [C_A_ss_initial, C_A_ss_initial],
        type: 'scatter',
        mode: 'lines',
        name: 'Initial C_A,ss',
        line: { color: '#64748b', width: 1.5, dash: 'dash' },
      },
    ];

    if (step_change_applied) {
      traces.push({
        x: [step_change_applied.time, step_change_applied.time],
        y: [0, Math.max(...C_A) * 1.1],
        type: 'scatter',
        mode: 'lines',
        name: `Step Disturbance (t=${step_change_applied.time}m)`,
        line: { color: '#f59e0b', width: 2, dash: 'dot' },
      });
    }

    return traces;
  }, [t, C_A, C_A_ss_initial, step_change_applied]);

  // Conversion Plot Traces (only where conversion is defined)
  const hasConversion = conversion && conversion.some(v => v !== null && !isNaN(v));
  const conversionTraces = useMemo(() => {
    if (!hasConversion || !conversion) return [];
    return [
      {
        x: t,
        y: conversion.map(c => (c !== null ? c * 100 : null)),
        type: 'scatter',
        mode: 'lines',
        name: 'Conversion X_A (%)',
        line: { color: '#38bdf8', width: 3 },
      },
    ] as Plotly.Data[];
  }, [t, conversion, hasConversion]);

  // Reaction Rate Traces
  const rateTraces = useMemo(() => {
    return [
      {
        x: t,
        y: reaction_rate,
        type: 'scatter',
        mode: 'lines',
        name: 'Reaction Rate r_A',
        line: { color: '#ec4899', width: 2.5 },
      },
    ] as Plotly.Data[];
  }, [t, reaction_rate]);

  const baseLayout: Partial<Plotly.Layout> = {
    paper_bgcolor: 'rgba(15, 23, 42, 0.4)',
    plot_bgcolor: 'rgba(15, 23, 42, 0.6)',
    font: { color: '#94a3b8', family: 'Inter, sans-serif' },
    margin: { l: 50, r: 30, t: 30, b: 40 },
    xaxis: {
      gridcolor: '#1e293b',
      title: { text: 'Time [min]' },
      zerolinecolor: '#334155',
    },
    yaxis: {
      gridcolor: '#1e293b',
      zerolinecolor: '#334155',
    },
    legend: {
      orientation: 'h',
      x: 0,
      y: 1.15,
      font: { size: 11 },
    },
    autosize: true,
  };

  return (
    <div className="space-y-6">
      {/* Concentration Chart */}
      <div className="glass-panel rounded-2xl p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h3 className="text-base font-semibold text-slate-100">Reactant Concentration vs Time</h3>
            <p className="text-xs text-slate-400">Dynamic effluent & vessel concentration C_A(t) [mol/L]</p>
          </div>
          {analytical_comparison && (
            <div className="text-right">
              <span className="text-xs font-mono text-emerald-400 bg-emerald-950/80 border border-emerald-500/30 px-2.5 py-1 rounded-lg shadow-sm">
                RMSE vs Analytical: {analytical_comparison.rmse.toExponential(2)}
              </span>
            </div>
          )}
        </div>
        <div className="h-72 w-full">
          <Plot
            data={concentrationTraces}
            layout={{
              ...baseLayout,
              yaxis: { ...baseLayout.yaxis, title: { text: 'C_A [mol/L]' } },
            }}
            useResizeHandler
            className="w-full h-full"
            config={{ responsive: true, displayModeBar: false }}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Conversion Chart */}
        {hasConversion ? (
          <div className="glass-panel rounded-2xl p-6 shadow-2xl">
            <h3 className="text-base font-semibold text-slate-100">Fractional Conversion vs Time</h3>
            <p className="text-xs text-slate-400">Reactant conversion X_A(t) [%]</p>
            <div className="h-64 w-full mt-2">
              <Plot
                data={conversionTraces}
                layout={{
                  ...baseLayout,
                  yaxis: { ...baseLayout.yaxis, title: { text: 'Conversion [%]' }, range: [0, 105] },
                }}
                useResizeHandler
                className="w-full h-full"
                config={{ responsive: true, displayModeBar: false }}
              />
            </div>
          </div>
        ) : (
          <div className="glass-panel rounded-2xl p-6 flex flex-col items-center justify-center text-center shadow-2xl">
            <p className="text-sm text-slate-400">Conversion chart unavailable when inlet concentration C_A,in = 0</p>
            <span className="text-xs text-slate-500 mt-1">X_A is mathematically undefined with no reactant feed</span>
          </div>
        )}

        {/* Reaction Rate Chart */}
        <div className="glass-panel rounded-2xl p-6 shadow-2xl">
          <h3 className="text-base font-semibold text-slate-100">Volumetric Reaction Rate vs Time</h3>
          <p className="text-xs text-slate-400">Consumption rate r_A(t) [mol/(L·min)]</p>
          <div className="h-64 w-full mt-2">
            <Plot
              data={rateTraces}
              layout={{
                ...baseLayout,
                yaxis: { ...baseLayout.yaxis, title: { text: 'r_A [mol/(L·min)]' } },
              }}
              useResizeHandler
              className="w-full h-full"
              config={{ responsive: true, displayModeBar: false }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
