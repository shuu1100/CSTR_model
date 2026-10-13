import {
  DynamicSimulationRequest,
  DynamicSimulationResponse,
  HealthResponse,
  ModelCatalogResponse,
  ParameterSweepRequest,
  SteadyStateRequest,
  SteadyStateResponse,
  Sweep1DResponse,
  Sweep2DResponse,
  LHSSweepRequest,
  LHSSweepResponse,
  DatasetInspectionResponse,
  ProcessDatasetRequest,
  ProcessedDatasetResponse,
  FitKineticsRequest,
  FitKineticsResponse,
  MLBaselinesBenchmarkResponse,
  MLDatasetPreviewResponse,
  MLDatasetValidationResponse,
  MLInferenceRequest,
  MLInferenceResponse,
  MLJobStatusResponse,
  MLModelCatalogItem,
  MLTrainingRequest,
  MLTrainingResponse,
  ThermalSimulationRequest,
  ThermalSimulationResponse,
  PRBSAuditResponse,
  PRBSCalibrationResponse,
  HistoryRunItem,
  HistoryRunDetail,
  CompareRunsResponse,
  RetentionResponse,
  OptimizationAuditResponse,
} from "./types";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8001";

export class ApiError extends Error {
  status: number;
  details: any;

  constructor(status: number, message: string, details?: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errMessage = `HTTP error ${res.status}: ${res.statusText}`;
    let errDetails: any = null;
    try {
      const data = await res.json();
      if (data.detail) {
        if (typeof data.detail === "string") {
          errMessage = data.detail;
        } else if (Array.isArray(data.detail)) {
          errMessage = data.detail.map((d: any) => `${d.loc ? d.loc.join('.') + ': ' : ''}${d.msg}`).join("; ");
        } else {
          errMessage = JSON.stringify(data.detail);
        }
      }
      errDetails = data;
    } catch {
      // Body not JSON
    }
    throw new ApiError(res.status, errMessage, errDetails);
  }
  return res.json() as Promise<T>;
}

export const api = {
  async getHealth(): Promise<HealthResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/health`);
    return handleResponse<HealthResponse>(res);
  },

  async getModels(): Promise<ModelCatalogResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/models`);
    return handleResponse<ModelCatalogResponse>(res);
  },

  async runSteadyState(req: SteadyStateRequest): Promise<SteadyStateResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/simulations/steady-state`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    return handleResponse<SteadyStateResponse>(res);
  },

  async solveSteadyState(req: SteadyStateRequest): Promise<SteadyStateResponse> {
    return this.runSteadyState(req);
  },

  async runDynamicSimulation(req: DynamicSimulationRequest): Promise<DynamicSimulationResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/simulations/dynamic`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    return handleResponse<DynamicSimulationResponse>(res);
  },

  async simulateDynamic(req: DynamicSimulationRequest): Promise<DynamicSimulationResponse> {
    return this.runDynamicSimulation(req);
  },

  async runParameterSweep(
    req: ParameterSweepRequest
  ): Promise<Sweep1DResponse | Sweep2DResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/simulations/parameter-sweep`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    return handleResponse<Sweep1DResponse | Sweep2DResponse>(res);
  },

  async runLHSSweep(req: LHSSweepRequest): Promise<LHSSweepResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/simulations/parameter-sweep/lhs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    return handleResponse<LHSSweepResponse>(res);
  },

  async uploadDataset(file: File): Promise<DatasetInspectionResponse> {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE_URL}/api/v1/datasets/upload`, {
      method: "POST",
      body: formData,
    });
    return handleResponse<DatasetInspectionResponse>(res);
  },

  async processDataset(req: ProcessDatasetRequest): Promise<ProcessedDatasetResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/datasets/process`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    return handleResponse<ProcessedDatasetResponse>(res);
  },

  async getSampleDataset(): Promise<DatasetInspectionResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/datasets/sample-dataset`);
    return handleResponse<DatasetInspectionResponse>(res);
  },

  async fitKinetics(req: FitKineticsRequest): Promise<FitKineticsResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/analysis/fit-kinetics`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    return handleResponse<FitKineticsResponse>(res);
  },
 
  async listMLModels(): Promise<MLModelCatalogItem[]> {
    const res = await fetch(`${API_BASE_URL}/api/v1/ml/models`);
    return handleResponse<MLModelCatalogItem[]>(res);
  },

  async getMLBaselinesBenchmark(): Promise<MLBaselinesBenchmarkResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/ml/baselines/benchmark`);
    return handleResponse<MLBaselinesBenchmarkResponse>(res);
  },

  async trainMLModel(req: MLTrainingRequest): Promise<MLTrainingResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/ml/train`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    return handleResponse<MLTrainingResponse>(res);
  },

  async predictMLTrajectory(req: MLInferenceRequest): Promise<MLInferenceResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/ml/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    return handleResponse<MLInferenceResponse>(res);
  },

  async getMLDatasetPreview(): Promise<MLDatasetPreviewResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/ml/dataset/preview`);
    return handleResponse<MLDatasetPreviewResponse>(res);
  },

  async validateMLDataset(): Promise<MLDatasetValidationResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/ml/dataset/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    return handleResponse<MLDatasetValidationResponse>(res);
  },

  async listMLJobs(): Promise<MLJobStatusResponse[]> {
    const res = await fetch(`${API_BASE_URL}/api/v1/ml/jobs`);
    return handleResponse<MLJobStatusResponse[]>(res);
  },

  async getMLJobStatus(jobId: string): Promise<MLJobStatusResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/ml/jobs/${jobId}`);
    return handleResponse<MLJobStatusResponse>(res);
  },

  async cancelMLJob(jobId: string): Promise<{ job_id: string; status: string; message: string }> {
    const res = await fetch(`${API_BASE_URL}/api/v1/ml/jobs/${jobId}/cancel`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    return handleResponse<{ job_id: string; status: string; message: string }>(res);
  },

  // --- Thermal CSTR Simulations & PRBS ---
  async simulateThermal(req: ThermalSimulationRequest): Promise<ThermalSimulationResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/simulations/thermal`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    return handleResponse<ThermalSimulationResponse>(res);
  },

  async getThermalPRBSAudit(): Promise<PRBSAuditResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/simulations/thermal/prbs-audit`);
    return handleResponse<PRBSAuditResponse>(res);
  },

  async calibrateThermalPRBS(): Promise<PRBSCalibrationResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/simulations/thermal/prbs-calibration`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    return handleResponse<PRBSCalibrationResponse>(res);
  },

  // --- Run History, Comparison & Exports ---
  async listHistoryRuns(runType?: string, limit: number = 50, offset: number = 0): Promise<HistoryRunItem[]> {
    let url = `${API_BASE_URL}/api/v1/history/runs?limit=${limit}&offset=${offset}`;
    if (runType) url += `&run_type=${encodeURIComponent(runType)}`;
    const res = await fetch(url);
    return handleResponse<HistoryRunItem[]>(res);
  },

  async getHistoryRun(runId: string): Promise<HistoryRunDetail> {
    const res = await fetch(`${API_BASE_URL}/api/v1/history/runs/${encodeURIComponent(runId)}`);
    return handleResponse<HistoryRunDetail>(res);
  },

  async deleteHistoryRun(runId: string): Promise<void> {
    const res = await fetch(`${API_BASE_URL}/api/v1/history/runs/${encodeURIComponent(runId)}`, {
      method: "DELETE",
    });
    if (!res.ok) {
      throw new ApiError(res.status, `Failed to delete run: ${res.statusText}`);
    }
  },

  async compareHistoryRuns(runIds: string[]): Promise<CompareRunsResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/history/compare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ run_ids: runIds }),
    });
    return handleResponse<CompareRunsResponse>(res);
  },

  async applyRetentionPolicy(maxRuns: number = 500, retentionDays?: number): Promise<RetentionResponse> {
    let url = `${API_BASE_URL}/api/v1/history/retention/apply?max_runs=${maxRuns}`;
    if (retentionDays) url += `&retention_days=${retentionDays}`;
    const res = await fetch(url, { method: "POST" });
    return handleResponse<RetentionResponse>(res);
  },

  getExportHistoryUrl(format: "json" | "csv" | "xlsx", runType?: string): string {
    let url = `${API_BASE_URL}/api/v1/history/export?format=${format}`;
    if (runType) url += `&run_type=${encodeURIComponent(runType)}`;
    return url;
  },

  // --- Optimization & Latency Benchmarks ---
  async getOptimizationAudit(): Promise<OptimizationAuditResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/ml/optimization/audit`);
    return handleResponse<OptimizationAuditResponse>(res);
  },

  async benchmarkOptimization(nRuns: number = 50, nPoints: number = 41): Promise<{ status: string; benchmark: any }> {
    const res = await fetch(`${API_BASE_URL}/api/v1/ml/optimization/benchmark?n_runs=${nRuns}&n_points=${nPoints}`, {
      method: "POST",
    });
    return handleResponse<{ status: string; benchmark: any }>(res);
  },
};


