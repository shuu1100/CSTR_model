import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { HistoryRunItem, CompareRunsResponse } from '../api/types';

export const HistoryPage: React.FC = () => {
  const [runs, setRuns] = useState<HistoryRunItem[]>([]);
  const [filterType, setFilterType] = useState<string>('');
  const [selectedRunIds, setSelectedRunIds] = useState<string[]>([]);
  const [comparison, setComparison] = useState<CompareRunsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [retentionMessage, setRetentionMessage] = useState<string | null>(null);
  const [maxRunsToKeep, setMaxRunsToKeep] = useState<number>(200);

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const data = await api.listHistoryRuns(filterType || undefined);
      setRuns(data);
    } catch {
      // Ignore or empty
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, [filterType]);

  const toggleSelectRun = (id: string) => {
    if (selectedRunIds.includes(id)) {
      setSelectedRunIds(selectedRunIds.filter(r => r !== id));
    } else {
      setSelectedRunIds([...selectedRunIds, id]);
    }
  };

  const handleCompare = async () => {
    if (selectedRunIds.length < 2) return;
    try {
      const res = await api.compareHistoryRuns(selectedRunIds);
      setComparison(res);
    } catch (err: any) {
      alert(err.message || 'Comparison failed');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm(`Delete historical run ${id}?`)) return;
    try {
      await api.deleteHistoryRun(id);
      setRuns(runs.filter(r => r.id !== id));
      setSelectedRunIds(selectedRunIds.filter(r => r !== id));
      if (comparison) {
        setComparison({
          ...comparison,
          runs: comparison.runs.filter(r => r.id !== id),
          compared_runs_count: comparison.runs.length - 1,
        });
      }
    } catch (err: any) {
      alert(err.message || 'Failed to delete run');
    }
  };

  const handleApplyRetention = async () => {
    try {
      const res = await api.applyRetentionPolicy(maxRunsToKeep);
      setRetentionMessage(res.message);
      fetchRuns();
      setTimeout(() => setRetentionMessage(null), 5000);
    } catch (err: any) {
      alert(err.message || 'Failed to apply retention policy');
    }
  };

  return (
    <div className="flex flex-col w-full gap-4">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 bg-white p-4 rounded border border-[#D5E1EE] shadow-2xs">
        <div className="flex flex-col gap-0.5">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-[20px]">history</span>
            <h1 className="font-semibold text-lg text-[#0F1E2E] tracking-tight">Run History, Comparison & Exports</h1>
            <span className="px-1.5 py-0.5 rounded font-mono text-[10px] bg-[#EEF4FF] text-primary border border-[#CBD9E8] font-bold">
              SQLITE-AUDIT
            </span>
          </div>
          <p className="text-xs text-[#4E657E]">
            Immutable execution logs, provenance audit, side-by-side comparison, and canonical exports
          </p>
        </div>

        {/* Global Export Download Buttons */}
        <div className="flex items-center gap-2 flex-wrap">
          <a
            href={api.getExportHistoryUrl('xlsx', filterType || undefined)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-emerald-700 hover:bg-emerald-800 text-white font-semibold text-xs shadow-2xs transition-colors"
          >
            <span className="material-symbols-outlined text-[16px]">table_chart</span>
            <span>Export Multi-Sheet XLSX</span>
          </a>
          <a
            href={api.getExportHistoryUrl('csv', filterType || undefined)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-white hover:bg-[#EEF4FF] border border-[#CBD9E8] text-[#0F1E2E] font-medium text-xs shadow-2xs transition-colors"
          >
            <span className="material-symbols-outlined text-[16px]">file_download</span>
            <span>Export CSV</span>
          </a>
          <a
            href={api.getExportHistoryUrl('json', filterType || undefined)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-white hover:bg-[#EEF4FF] border border-[#CBD9E8] text-[#0F1E2E] font-medium text-xs shadow-2xs transition-colors"
          >
            <span className="material-symbols-outlined text-[16px]">data_object</span>
            <span>Export JSON</span>
          </a>
        </div>
      </div>

      {retentionMessage && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-status-success text-xs rounded flex items-center gap-2">
          <span className="material-symbols-outlined text-[18px]">check_circle</span>
          <span>{retentionMessage}</span>
        </div>
      )}

      {/* Filter and Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-3 rounded border border-[#D5E1EE] shadow-2xs">
        <div className="flex items-center gap-2">
          <span className="text-xs text-[#4E657E] font-medium">Category Filter:</span>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="scientific-input text-xs"
          >
            <option value="">All Categories</option>
            <option value="dynamic">Dynamic Simulations</option>
            <option value="steady_state">Steady State</option>
            <option value="sweep">Parameter Sweeps</option>
            <option value="thermal">Thermal Non-Isothermal</option>
            <option value="ml_forecast">Machine Learning</option>
            <option value="estimation">Parameter Estimation</option>
          </select>

          <button
            onClick={handleCompare}
            disabled={selectedRunIds.length < 2}
            className="flex items-center gap-1 px-3 py-1.5 rounded bg-secondary text-white text-xs font-semibold hover:bg-secondary-container transition-colors disabled:opacity-40 shadow-2xs"
          >
            <span className="material-symbols-outlined text-[16px]">compare_arrows</span>
            <span>Compare Selected ({selectedRunIds.length})</span>
          </button>
        </div>

        {/* Retention Policy Control */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-[#4E657E]">Retain Max:</span>
          <input
            type="number"
            min="10"
            max="2000"
            value={maxRunsToKeep}
            onChange={(e) => setMaxRunsToKeep(parseInt(e.target.value) || 200)}
            className="scientific-input w-20 text-xs"
          />
          <button
            onClick={handleApplyRetention}
            className="px-2.5 py-1.5 bg-[#EEF4FF] hover:bg-[#E4EFFF] border border-[#CBD9E8] text-[#0F1E2E] text-xs font-medium rounded transition-colors"
          >
            Purge Older
          </button>
        </div>
      </div>

      {/* Side-by-Side Comparison Overlay Modal or Inline Panel */}
      {comparison && (
        <div className="flex flex-col p-4 rounded bg-white border-2 border-secondary shadow-md space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-[#CBD9E8]">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-secondary text-[20px]">compare</span>
              <h2 className="font-bold text-sm text-[#0F1E2E]">Side-by-Side Run Comparison ({comparison.compared_runs_count} Runs)</h2>
            </div>
            <button
              onClick={() => setComparison(null)}
              className="text-[#4E657E] hover:text-[#0F1E2E] text-xs font-semibold"
            >
              ✕ Close Comparison
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs font-mono border-collapse">
              <thead>
                <tr className="bg-[#E4EDF6] text-[#4E657E] border-b border-[#CBD9E8]">
                  <th className="p-2 text-left">Property</th>
                  {comparison.runs.map(r => (
                    <th key={r.id} className="p-2 text-left font-bold text-primary">{r.name}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EEF4FF]">
                <tr>
                  <td className="p-2 text-[#4E657E]">Run ID</td>
                  {comparison.runs.map(r => <td key={r.id} className="p-2">{r.id}</td>)}
                </tr>
                <tr>
                  <td className="p-2 text-[#4E657E]">Type</td>
                  {comparison.runs.map(r => <td key={r.id} className="p-2 font-semibold">{r.run_type}</td>)}
                </tr>
                <tr>
                  <td className="p-2 text-[#4E657E]">Provenance</td>
                  {comparison.runs.map(r => (
                    <td key={r.id} className="p-2">
                      <span className="px-1.5 py-0.5 rounded bg-[#EEF4FF] text-primary border border-[#CBD9E8]">
                        {r.provenance}
                      </span>
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="p-2 text-[#4E657E]">Parameters</td>
                  {comparison.runs.map(r => (
                    <td key={r.id} className="p-2">
                      <pre className="text-[10px] bg-[#F4F8FC] p-1.5 rounded border border-[#CBD9E8]">
                        {JSON.stringify(r.parameters, null, 1)}
                      </pre>
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="p-2 text-[#4E657E]">Results Summary</td>
                  {comparison.runs.map(r => (
                    <td key={r.id} className="p-2">
                      <pre className="text-[10px] bg-[#F4F8FC] p-1.5 rounded border border-[#CBD9E8]">
                        {JSON.stringify(r.results_summary, null, 1)}
                      </pre>
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Runs Table */}
      <div className="flex flex-col bg-white rounded border border-[#D5E1EE] shadow-2xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs font-mono border-collapse">
            <thead>
              <tr className="bg-[#E4EDF6] text-[#4E657E] border-b border-[#CBD9E8] font-semibold text-[11px]">
                <th className="p-2.5 text-center w-10">Select</th>
                <th className="p-2.5 text-left">Run ID</th>
                <th className="p-2.5 text-left">Name</th>
                <th className="p-2.5 text-left">Type</th>
                <th className="p-2.5 text-left">Provenance</th>
                <th className="p-2.5 text-left">Created At (UTC)</th>
                <th className="p-2.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#EEF4FF] text-xs">
              {runs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-[#4E657E] font-sans">
                    {loading ? 'Loading historical simulation records...' : 'No historical simulation runs found.'}
                  </td>
                </tr>
              ) : (
                runs.map(r => {
                  const isChecked = selectedRunIds.includes(r.id);
                  return (
                    <tr key={r.id} className={`hover:bg-[#F4F8FC] transition-colors ${isChecked ? 'bg-[#EEF4FF]/50' : ''}`}>
                      <td className="p-2.5 text-center">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => toggleSelectRun(r.id)}
                          className="rounded border-[#CBD9E8] text-primary"
                        />
                      </td>
                      <td className="p-2.5 font-bold text-primary">{r.id}</td>
                      <td className="p-2.5 text-[#0F1E2E] font-medium font-sans">{r.name}</td>
                      <td className="p-2.5 font-semibold text-secondary">{r.run_type}</td>
                      <td className="p-2.5">
                        <span className="px-1.5 py-0.5 rounded bg-[#F4F8FC] border border-[#CBD9E8] text-[10px]">
                          {r.provenance}
                        </span>
                      </td>
                      <td className="p-2.5 text-[#4E657E]">{new Date(r.created_at).toLocaleString()}</td>
                      <td className="p-2.5 text-right">
                        <button
                          onClick={() => handleDelete(r.id)}
                          className="text-status-critical hover:underline text-[11px] font-sans font-medium"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
