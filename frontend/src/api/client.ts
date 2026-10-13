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

  async runDynamicSimulation(req: DynamicSimulationRequest): Promise<DynamicSimulationResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/simulations/dynamic`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    return handleResponse<DynamicSimulationResponse>(res);
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
};

