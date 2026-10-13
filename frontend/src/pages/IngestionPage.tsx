import React, { useState } from 'react';
import Plot from 'react-plotly.js';
import {
  Upload,
  FileSpreadsheet,
  AlertTriangle,
  CheckCircle2,
  Sparkles,
  Sliders,
  Filter,
  ShieldAlert,
  RefreshCw,
  Eye,
} from 'lucide-react';
import { api, ApiError } from '../api/client';
import {
  ConcentrationUnit,
  DatasetInspectionResponse,
  FlowRateUnit,
  ProcessedDatasetResponse,
  TimeUnit,
  VolumeUnit,
} from '../api/types';

export const IngestionPage: React.FC = () => {
  // Inspection State
  const [inspection, setInspection] = useState<DatasetInspectionResponse | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Column Mapping State
  const [timeCol, setTimeCol] = useState<string>('');
  const [timeUnit, setTimeUnit] = useState<TimeUnit>('min');

  const [cOutCol, setCOutCol] = useState<string>('');
  const [concUnit, setConcUnit] = useState<ConcentrationUnit>('mol/L');

  const [cInMode, setCInMode] = useState<'column' | 'constant'>('column');
  const [cInCol, setCInCol] = useState<string>('');
  const [constantCIn, setConstantCIn] = useState<number>(1.0);

  const [flowMode, setFlowMode] = useState<'none' | 'column' | 'constant'>('constant');
  const [flowCol, setFlowCol] = useState<string>('');
  const [constantFlow, setConstantFlow] = useState<number>(1.0);
  const [flowUnit, setFlowUnit] = useState<FlowRateUnit>('L/min');

  const [volMode, setVolMode] = useState<'none' | 'column' | 'constant'>('constant');
  const [volCol, setVolCol] = useState<string>('');
  const [constantVol, setConstantVol] = useState<number>(10.0);
  const [volUnit, setVolUnit] = useState<VolumeUnit>('L');

  // Smoothing & Anomaly settings
  const [applySmoothing, setApplySmoothing] = useState<boolean>(false);
  const [savgolWindow, setSavgolWindow] = useState<number>(5);
  const [savgolPoly, setSavgolPoly] = useState<number>(2);

  const [applyAnomalyDetection, setApplyAnomalyDetection] = useState<boolean>(false);
  const [contamination, setContamination] = useState<number>(0.05);

  // Processed Output State
  const [processedResult, setProcessedResult] = useState<ProcessedDatasetResponse | null>(null);

  // Auto-detect matching columns on inspection
  const autoDetectColumns = (insp: DatasetInspectionResponse) => {
    const cols = insp.columns;
    const lowerCols = cols.map(c => c.toLowerCase());

    // Time
    const tIdx = lowerCols.findIndex(c => c.includes('time') || c === 't' || c.startsWith('t_'));
    if (tIdx !== -1) setTimeCol(cols[tIdx]);
    else if (cols.length > 0) setTimeCol(cols[0]);

    // C_out
    const outIdx = lowerCols.findIndex(
      c => c.includes('outlet') || c.includes('out') || c.includes('c_a') || c.includes('ca')
    );
    if (outIdx !== -1) setCOutCol(cols[outIdx]);
    else if (cols.length > 1) setCOutCol(cols[1]);

    // C_in
    const inIdx = lowerCols.findIndex(c => c.includes('inlet') || c.includes('in') || c.includes('feed'));
    if (inIdx !== -1) {
      setCInMode('column');
      setCInCol(cols[inIdx]);
    } else {
      setCInMode('constant');
    }

    // Flow
    const qIdx = lowerCols.findIndex(c => c.includes('flow') || c === 'q' || c.startsWith('q_'));
    if (qIdx !== -1) {
      setFlowMode('column');
      setFlowCol(cols[qIdx]);
    }

    // Volume
    const vIdx = lowerCols.findIndex(c => c.includes('vol') || c === 'v');
    if (vIdx !== -1) {
      setVolMode('column');
      setVolCol(cols[vIdx]);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setErrorMsg(null);
    setIsUploading(true);
    setProcessedResult(null);

    try {
      const resp = await api.uploadDataset(file);
      setInspection(resp);
      autoDetectColumns(resp);
    } catch (err: any) {
      setErrorMsg(err instanceof ApiError ? err.message : 'Failed to parse dataset.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleLoadSample = async () => {
    setErrorMsg(null);
    setIsUploading(true);
    setProcessedResult(null);

    try {
      const resp = await api.getSampleDataset();
      setInspection(resp);
      autoDetectColumns(resp);
    } catch (err: any) {
      setErrorMsg(err instanceof ApiError ? err.message : 'Failed to load synthetic benchmark dataset.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleProcess = async () => {
    if (!inspection || !inspection.raw_records) return;
    if (!timeCol) {
      setErrorMsg('Please select a valid Time column.');
      return;
    }
    if (!cOutCol) {
      setErrorMsg('Please select a valid Outlet Concentration column.');
      return;
    }

    setErrorMsg(null);
    setIsProcessing(true);

    try {
      const resp = await api.processDataset({
        records: inspection.raw_records,
        time_col: timeCol,
        c_out_col: cOutCol,
        c_in_col: cInMode === 'column' && cInCol ? cInCol : null,
        constant_c_in: cInMode === 'constant' ? constantCIn : null,
        flow_col: flowMode === 'column' && flowCol ? flowCol : null,
        constant_flow: flowMode === 'constant' ? constantFlow : null,
        volume_col: volMode === 'column' && volCol ? volCol : null,
        constant_volume: volMode === 'constant' ? constantVol : null,
        time_unit: timeUnit,
        conc_unit: concUnit,
        flow_unit: flowUnit,
        vol_unit: volUnit,
        apply_smoothing: applySmoothing,
        savgol_window: savgolWindow,
        savgol_poly: savgolPoly,
        apply_anomaly_detection: applyAnomalyDetection,
        contamination: contamination,
      });
      setProcessedResult(resp);
    } catch (err: any) {
      setErrorMsg(err instanceof ApiError ? err.message : 'Error processing mapped dataset.');
    } finally {
      setIsProcessing(false);
    }
  };

  // Prepare plots
  const renderPlots = () => {
    if (!processedResult) return null;
    const series = processedResult.series;

    // Separate anomalies for overlay
    const anomalyIndices = series.is_anomaly
      ? series.is_anomaly
          .map((flag, idx) => (flag ? idx : -1))
          .filter(idx => idx !== -1)
      : [];
    const anomalyTimes = anomalyIndices.map(i => series.time[i]);
    const anomalyVals = anomalyIndices.map(i => series.C_A_out_raw[i]);

    const concTraces: any[] = [
      {
        x: series.time,
        y: series.C_A_out_raw,
        type: 'scatter',
        mode: 'markers',
        name: 'C_A,out (Raw Experimental)',
        marker: { color: '#38bdf8', size: 6, opacity: 0.8 },
      },
    ];

    if (processedResult.smoothing_applied && series.C_A_out_smoothed) {
      concTraces.push({
        x: series.time,
        y: series.C_A_out_smoothed,
        type: 'scatter',
        mode: 'lines',
        name: `C_A,out (Savitzky–Golay w=${processedResult.smoothing_settings?.window_length})`,
        line: { color: '#10b981', width: 2.5 },
      });
    }

    if (series.C_A_in && series.C_A_in.length > 0 && series.C_A_in.some(v => v > 0)) {
      concTraces.push({
        x: series.time,
        y: series.C_A_in,
        type: 'scatter',
        mode: 'lines',
        name: 'C_A,in (Inlet Feed)',
        line: { color: '#94a3b8', width: 2, dash: 'dot' },
      });
    }

    if (processedResult.anomaly_detection_applied && anomalyTimes.length > 0) {
      concTraces.push({
        x: anomalyTimes,
        y: anomalyVals,
        type: 'scatter',
        mode: 'markers',
        name: `Flagged Outliers (${anomalyTimes.length})`,
        marker: {
          color: '#f43f5e',
          size: 10,
          symbol: 'diamond',
          line: { color: '#ffffff', width: 1.5 },
        },
      });
    }

    const convTraces: any[] = [];
    if (series.conversion && series.conversion.some(x => x !== null)) {
      convTraces.push({
        x: series.time,
        y: series.conversion,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Measured Conversion X_A',
        line: { color: '#f59e0b', width: 2 },
        marker: { size: 5, color: '#f59e0b' },
      });
    }

    return (
      <div className="space-y-6">
        {/* Concentration comparison chart */}
        <div className="glass-panel rounded-2xl p-6 shadow-2xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-semibold text-white">
                Concentration Profiles: Raw vs Processed
              </h3>
              <p className="text-xs text-slate-400">
                Visualizing experimental measurement points alongside optional filter smoothing and anomaly flags.
              </p>
            </div>
            {processedResult.smoothing_applied && (
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                SavGol (w={savgolWindow}, p={savgolPoly})
              </span>
            )}
          </div>
          <Plot
            data={concTraces}
            layout={{
              autosize: true,
              paper_bgcolor: '#020617',
              plot_bgcolor: '#090d16',
              font: { color: '#94a3b8', family: 'Inter, sans-serif', size: 11 },
              margin: { l: 50, r: 20, t: 20, b: 50 },
              xaxis: {
                title: { text: `Time (${series.time_unit})` },
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

        {/* Conversion chart */}
        {convTraces.length > 0 && (
          <div className="glass-panel rounded-2xl p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-semibold text-white">
                  Measured Fractional Conversion (X_A)
                </h3>
                <p className="text-xs text-slate-400">
                  Computed strictly when inlet concentration is positive: X_A = (C_A,in - C_A,out) / C_A,in.
                </p>
              </div>
            </div>
            <Plot
              data={convTraces}
              layout={{
                autosize: true,
                paper_bgcolor: '#020617',
                plot_bgcolor: '#090d16',
                font: { color: '#94a3b8', family: 'Inter, sans-serif', size: 11 },
                margin: { l: 50, r: 20, t: 20, b: 50 },
                xaxis: {
                  title: { text: `Time (${series.time_unit})` },
                  gridcolor: '#1e293b',
                  zerolinecolor: '#334155',
                },
                yaxis: {
                  title: { text: 'Conversion X_A' },
                  range: [-0.05, 1.05],
                  gridcolor: '#1e293b',
                  zerolinecolor: '#334155',
                },
                legend: { orientation: 'h', y: -0.25 },
              }}
              useResizeHandler={true}
              className="w-full h-72"
            />
          </div>
        )}

        {/* Quality alerts and provenance */}
        <div className="glass-panel rounded-2xl p-6 shadow-2xl space-y-4">
          <div className="flex items-start space-x-3 text-amber-400 bg-amber-950/40 border border-amber-800/60 p-3 rounded-lg text-xs">
            <ShieldAlert className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold block mb-0.5">Scientific Data Integrity Notice</span>
              <p className="text-amber-200/90 leading-relaxed">
                {processedResult.provenance_note}
              </p>
            </div>
          </div>

          {processedResult.data_quality_warnings.length > 0 && (
            <div className="border border-slate-800 bg-slate-950/60 rounded-lg p-3 text-xs space-y-1">
              <span className="font-semibold text-slate-300 block mb-1">Data Quality Findings:</span>
              {processedResult.data_quality_warnings.map((warn, i) => (
                <div key={i} className="flex items-center space-x-2 text-amber-300">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                  <span>{warn}</span>
                </div>
              ))}
            </div>
          )}

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
              <span className="text-slate-500 block">Total Data Points</span>
              <span className="text-slate-200 font-mono font-medium text-sm">
                {processedResult.dataset_summary.row_count}
              </span>
            </div>
            <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
              <span className="text-slate-500 block">Time Span</span>
              <span className="text-slate-200 font-mono font-medium text-sm">
                {processedResult.dataset_summary.t_min} - {processedResult.dataset_summary.t_max} min
              </span>
            </div>
            <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
              <span className="text-slate-500 block">C_A,out Range</span>
              <span className="text-slate-200 font-mono font-medium text-sm">
                {processedResult.dataset_summary.c_out_min.toFixed(4)} - {processedResult.dataset_summary.c_out_max.toFixed(4)} mol/L
              </span>
            </div>
            <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
              <span className="text-slate-500 block">Outliers Flagged</span>
              <span className="text-rose-400 font-mono font-medium text-sm">
                {processedResult.anomaly_count} (retained)
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="py-6 space-y-6">
      {/* Page Title & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-2.5">
            <FileSpreadsheet className="w-7 h-7 text-emerald-400" />
            <span>CSV / Excel Experimental Data Ingestion</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Controlled ingestion, data profiling, canonical unit conversions, Savitzky–Golay filtering, and outlier detection.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleLoadSample}
            disabled={isUploading || isProcessing}
            className="flex items-center space-x-2 px-3 py-2 rounded-lg text-xs font-medium bg-slate-900 border border-slate-700 text-slate-200 hover:bg-slate-800 transition"
          >
            <Sparkles className="w-4 h-4 text-emerald-400" />
            <span>Load Benchmark Run</span>
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="bg-rose-950/60 border border-rose-800 text-rose-300 px-4 py-3 rounded-xl text-xs flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Main Grid: Left Upload & Mappings, Right Preview & Plots */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (5 Cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* File Upload Drop Area */}
          <div className="glass-panel rounded-2xl p-6 shadow-2xl">
            <h2 className="text-sm font-semibold text-white mb-2 flex items-center space-x-2">
              <Upload className="w-4 h-4 text-emerald-400" />
              <span>Select File</span>
            </h2>
            <label className="border-2 border-dashed border-slate-700 hover:border-emerald-500/70 rounded-xl p-6 flex flex-col items-center justify-center cursor-pointer transition bg-slate-950/50 hover:bg-slate-900/50 text-center">
              <Upload className="w-8 h-8 text-slate-500 mb-2" />
              <span className="text-xs font-medium text-slate-300">
                {isUploading ? 'Inspecting file...' : 'Upload CSV, TSV, or Excel (.xlsx)'}
              </span>
              <span className="text-[11px] text-slate-500 mt-1">
                Max 10 MB • 50,000 rows • 50 columns
              </span>
              <input
                type="file"
                accept=".csv,.tsv,.xlsx,.xls"
                className="hidden"
                onChange={handleFileUpload}
                disabled={isUploading}
              />
            </label>

            {inspection && (
              <div className="mt-4 p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-slate-400">File:</span>
                  <span className="text-slate-200 font-mono font-medium">{inspection.filename}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Rows × Cols:</span>
                  <span className="text-slate-200 font-mono">
                    {inspection.total_rows} × {inspection.total_columns}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Duplicate Rows:</span>
                  <span className="text-slate-200 font-mono">{inspection.duplicate_rows_count}</span>
                </div>
              </div>
            )}
          </div>

          {/* Column Mapping Section */}
          {inspection && (
            <div className="glass-panel rounded-2xl p-6 shadow-2xl space-y-4">
              <h2 className="text-sm font-semibold text-white flex items-center space-x-2">
                <Sliders className="w-4 h-4 text-emerald-400" />
                <span>Column Mapping & Units</span>
              </h2>

              {/* Time Column */}
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-300 block">
                  Time Variable <span className="text-emerald-400">*</span>
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <select
                    value={timeCol}
                    onChange={e => setTimeCol(e.target.value)}
                    className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
                  >
                    <option value="">Select column...</option>
                    {inspection.columns.map(c => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                  <select
                    value={timeUnit}
                    onChange={e => setTimeUnit(e.target.value as TimeUnit)}
                    className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
                  >
                    <option value="min">Minutes (min)</option>
                    <option value="s">Seconds (s)</option>
                    <option value="h">Hours (h)</option>
                  </select>
                </div>
              </div>

              {/* Outlet Concentration C_A,out */}
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-300 block">
                  Outlet Concentration C_A,out <span className="text-emerald-400">*</span>
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <select
                    value={cOutCol}
                    onChange={e => setCOutCol(e.target.value)}
                    className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
                  >
                    <option value="">Select column...</option>
                    {inspection.columns.map(c => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                  <select
                    value={concUnit}
                    onChange={e => setConcUnit(e.target.value as ConcentrationUnit)}
                    className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
                  >
                    <option value="mol/L">mol/L (M)</option>
                    <option value="kmol/m3">kmol/m³</option>
                    <option value="mol/m3">mol/m³</option>
                    <option value="mmol/L">mmol/L</option>
                  </select>
                </div>
              </div>

              {/* Inlet Concentration C_A,in */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-medium text-slate-300">
                    Inlet Concentration C_A,in
                  </label>
                  <div className="flex space-x-2 text-[11px]">
                    <button
                      type="button"
                      onClick={() => setCInMode('column')}
                      className={`px-2 py-0.5 rounded ${cInMode === 'column' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'text-slate-400'}`}
                    >
                      Column
                    </button>
                    <button
                      type="button"
                      onClick={() => setCInMode('constant')}
                      className={`px-2 py-0.5 rounded ${cInMode === 'constant' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'text-slate-400'}`}
                    >
                      Constant
                    </button>
                  </div>
                </div>
                {cInMode === 'column' ? (
                  <select
                    value={cInCol}
                    onChange={e => setCInCol(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
                  >
                    <option value="">Select column...</option>
                    {inspection.columns.map(c => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={constantCIn}
                    onChange={e => setConstantCIn(parseFloat(e.target.value) || 0)}
                    placeholder="e.g. 1.0 mol/L"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 font-mono"
                  />
                )}
              </div>

              {/* Reactor Volume & Flow Rate */}
              <div className="grid grid-cols-2 gap-3 pt-2 border-t border-slate-800/80">
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <label className="text-[11px] text-slate-400">Reactor Volume (V)</label>
                    <select
                      value={volUnit}
                      onChange={e => setVolUnit(e.target.value as VolumeUnit)}
                      className="bg-slate-900 border border-slate-800 rounded text-[10px] text-slate-300 px-1 py-0.5"
                    >
                      <option value="L">L</option>
                      <option value="m3">m³</option>
                      <option value="mL">mL</option>
                    </select>
                  </div>
                  <input
                    type="number"
                    step="0.1"
                    min="0.01"
                    value={constantVol}
                    onChange={e => setConstantVol(parseFloat(e.target.value) || 10)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2 py-1 text-xs text-slate-200 font-mono"
                  />
                </div>
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <label className="text-[11px] text-slate-400">Flow Rate (Q)</label>
                    <select
                      value={flowUnit}
                      onChange={e => setFlowUnit(e.target.value as FlowRateUnit)}
                      className="bg-slate-900 border border-slate-800 rounded text-[10px] text-slate-300 px-1 py-0.5"
                    >
                      <option value="L/min">L/min</option>
                      <option value="L/s">L/s</option>
                      <option value="L/h">L/h</option>
                      <option value="m3/h">m³/h</option>
                    </select>
                  </div>
                  <input
                    type="number"
                    step="0.1"
                    min="0.01"
                    value={constantFlow}
                    onChange={e => setConstantFlow(parseFloat(e.target.value) || 1)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2 py-1 text-xs text-slate-200 font-mono"
                  />
                </div>
              </div>

              {/* Preprocessing Options: Savitzky-Golay & Isolation Forest */}
              <div className="pt-3 border-t border-slate-800 space-y-3">
                <h3 className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5">
                  <Filter className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Optional Preprocessing & Profiling</span>
                </h3>

                {/* Savitzky-Golay */}
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-2">
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={applySmoothing}
                      onChange={e => setApplySmoothing(e.target.checked)}
                      className="rounded border-slate-700 bg-slate-900 text-emerald-500 focus:ring-0"
                    />
                    <span className="text-xs text-slate-200 font-medium">Savitzky–Golay Filter</span>
                  </label>
                  {applySmoothing && (
                    <div className="grid grid-cols-2 gap-2 pt-1 text-xs">
                      <div>
                        <span className="text-[11px] text-slate-400 block mb-0.5">Window (odd)</span>
                        <input
                          type="number"
                          step="2"
                          min="3"
                          value={savgolWindow}
                          onChange={e => {
                            const val = parseInt(e.target.value) || 5;
                            setSavgolWindow(val % 2 === 0 ? val + 1 : val);
                          }}
                          className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 font-mono text-slate-200"
                        />
                      </div>
                      <div>
                        <span className="text-[11px] text-slate-400 block mb-0.5">Poly Order</span>
                        <input
                          type="number"
                          min="1"
                          max={savgolWindow - 1}
                          value={savgolPoly}
                          onChange={e => setSavgolPoly(parseInt(e.target.value) || 2)}
                          className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 font-mono text-slate-200"
                        />
                      </div>
                    </div>
                  )}
                  <p className="text-[10px] text-slate-500 leading-tight">
                    Smooths high-frequency sensor noise; raw series is retained. Caution: can attenuate sharp step transients.
                  </p>
                </div>

                {/* Isolation Forest */}
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-2">
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={applyAnomalyDetection}
                      onChange={e => setApplyAnomalyDetection(e.target.checked)}
                      className="rounded border-slate-700 bg-slate-900 text-emerald-500 focus:ring-0"
                    />
                    <span className="text-xs text-slate-200 font-medium">Isolation Forest Anomaly Flags</span>
                  </label>
                  {applyAnomalyDetection && (
                    <div className="pt-1 text-xs">
                      <div className="flex justify-between text-[11px] text-slate-400 mb-0.5">
                        <span>Expected Outlier Contamination:</span>
                        <span className="font-mono text-slate-200">{(contamination * 100).toFixed(0)}%</span>
                      </div>
                      <input
                        type="range"
                        min="0.01"
                        max="0.20"
                        step="0.01"
                        value={contamination}
                        onChange={e => setContamination(parseFloat(e.target.value))}
                        className="w-full accent-emerald-500"
                      />
                    </div>
                  )}
                  <p className="text-[10px] text-slate-500 leading-tight">
                    Tags suspicious points with outlier markers. Points are never silently deleted.
                  </p>
                </div>
              </div>

              {/* Process Trigger Button */}
              <button
                onClick={handleProcess}
                disabled={isProcessing}
                className="w-full py-2.5 px-4 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs flex items-center justify-center space-x-2 transition shadow-lg shadow-emerald-950"
              >
                {isProcessing ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Processing Series...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Process & Inspect Series</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        {/* Right Column (7 Cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Data Preview Table */}
          {inspection && !processedResult && (
            <div className="glass-panel rounded-2xl p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
                  <Eye className="w-4 h-4 text-emerald-400" />
                  <span>Preview Top 10 Rows</span>
                </h3>
                <span className="text-xs text-slate-400">
                  Showing first {inspection.preview_data.length} of {inspection.total_rows} rows
                </span>
              </div>

              <div className="overflow-x-auto border border-slate-800 rounded-lg">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-slate-950 border-b border-slate-800 text-slate-400">
                    <tr>
                      {inspection.columns.map(col => (
                        <th key={col} className="p-2.5 whitespace-nowrap">
                          <div>{col}</div>
                          <span className="text-[10px] text-slate-600 font-sans block">
                            {inspection.column_types[col]}
                          </span>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 bg-slate-900/60 text-slate-300">
                    {inspection.preview_data.map((row, rIdx) => (
                      <tr key={rIdx} className="hover:bg-slate-800/40">
                        {inspection.columns.map(col => (
                          <td key={col} className="p-2.5 whitespace-nowrap">
                            {row[col] !== null && row[col] !== undefined ? String(row[col]) : (
                              <span className="text-amber-500 italic">null</span>
                            )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Processed Plots and Visualizations */}
          {renderPlots()}

          {/* Initial State / Explanatory Card */}
          {!inspection && (
            <div className="glass-panel rounded-2xl p-10 text-center space-y-3 shadow-2xl">
              <FileSpreadsheet className="w-12 h-12 text-slate-600 mx-auto" />
              <h3 className="text-base font-semibold text-slate-300">No Experimental Dataset Loaded</h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Upload your lab dataset (CSV, TSV, Excel) or click "Load Benchmark Run" to explore dynamic CSTR concentration profiles, filter smoothing, and anomaly inspection.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
