/**
 * TypeScript API interfaces for CSTR Lab matching backend FastAPI schemas.
 */

export type VolumeUnit = "L" | "m3" | "mL";
export type FlowRateUnit = "L/min" | "L/s" | "L/h" | "m3/h" | "m3/s";
export type ConcentrationUnit = "mol/L" | "kmol/m3" | "mol/m3" | "mmol/L";
export type TimeUnit = "min" | "s" | "h";
export type SolverMethod = "RK45" | "Radau" | "BDF" | "LSODA" | "RK23" | "DOP853";

export interface HealthResponse {
  status: "ok" | "degraded" | "error";
  app_name: string;
  version: string;
  timestamp: string;
}

export interface ModelCatalogItem {
  model_id: string;
  name: string;
  description: string;
  supported_orders: number[];
  canonical_units: Record<string, string>;
  assumptions: string[];
  solvers: string[];
}

export interface ModelCatalogResponse {
  models: ModelCatalogItem[];
}

export interface StepChangeRequest {
  time: number;
  C_A_in_new?: number | null;
  Q_new?: number | null;
}

export interface SteadyStateRequest {
  V: number;
  Q: number;
  C_A_in: number;
  order: 0 | 1 | 2;
  k: number;
  volume_unit?: VolumeUnit;
  flow_rate_unit?: FlowRateUnit;
  concentration_unit?: ConcentrationUnit;
}

export interface SteadyStateOutputs {
  tau: number;
  C_A_ss: number;
  conversion: number | null;
  reaction_rate_ss: number;
  residual: number;
}

export interface SteadyStateResponse {
  model_id: string;
  normalized_inputs: Record<string, any>;
  outputs: SteadyStateOutputs;
  units: Record<string, string>;
  assumptions: string[];
  diagnostics: Record<string, any>;
  warnings: string[];
}

export interface DynamicSimulationRequest {
  C_A_0: number;
  C_A_in: number;
  V: number;
  Q: number;
  order: 0 | 1 | 2;
  k: number;
  t_final: number;
  n_points?: number;
  solver_method?: SolverMethod;
  rtol?: number;
  atol?: number;
  step_change?: StepChangeRequest | null;
  volume_unit?: VolumeUnit;
  flow_rate_unit?: FlowRateUnit;
  concentration_unit?: ConcentrationUnit;
  time_unit?: TimeUnit;
}

export interface SolverDetails {
  method: string;
  success: boolean;
  status: number;
  message: string;
  tolerances: {
    rtol: number;
    atol: number;
  };
}

export interface AnalyticalComparison {
  max_absolute_error: number;
  mean_absolute_error: number;
  max_relative_error: number;
  rmse: number;
}

export interface StepChangeApplied {
  time: number;
  C_A_in_initial: number;
  C_A_in_new: number;
  Q_initial: number;
  Q_new: number;
  C_A_at_step: number;
}

export interface DynamicSimulationResponse {
  model_id: string;
  normalized_inputs: Record<string, any>;
  t: number[];
  C_A: number[];
  conversion: (number | null)[] | null;
  reaction_rate: number[];
  tau_initial: number;
  C_A_ss_initial: number;
  solver_details: SolverDetails;
  analytical_comparison?: AnalyticalComparison | null;
  step_change_applied?: StepChangeApplied | null;
  units: Record<string, string>;
  assumptions: string[];
  warnings: string[];
}

export type SweepVariableType = "V" | "Q" | "k" | "C_A_in";

export interface ParameterSweepRequest {
  is_2d?: boolean;
  variable: SweepVariableType;
  min_val: number;
  max_val: number;
  n_points: number;
  variable_y?: SweepVariableType | null;
  min_val_y?: number | null;
  max_val_y?: number | null;
  n_points_y?: number | null;
  baseline_V: number;
  baseline_Q: number;
  baseline_C_in: number;
  baseline_k: number;
  order: 0 | 1 | 2;
}

export interface SweepPointSchema {
  param_value: number;
  tau: number;
  C_A_ss: number;
  conversion: number | null;
  reaction_rate_ss: number;
  residual: number;
  status: "ok" | "failed";
  warning?: string | null;
}

export interface LocalSensitivitySchema {
  derivative_dX_dp: number;
  normalized_elasticity: number;
}

export interface Sweep1DResponse {
  sweep_type: "1D";
  variable: string;
  variable_label: string;
  variable_unit: string;
  baseline_param_value: number;
  fixed_parameters: Record<string, number>;
  order: number;
  points: SweepPointSchema[];
  baseline_metrics: Record<string, any>;
  local_sensitivity?: LocalSensitivitySchema | null;
  trend_summary: string;
  units: Record<string, string>;
}

export interface Sweep2DResponse {
  sweep_type: "2D";
  var_x: string;
  var_x_label: string;
  var_x_unit: string;
  x_values: number[];
  var_y: string;
  var_y_label: string;
  var_y_unit: string;
  y_values: number[];
  fixed_parameters: Record<string, number>;
  order: number;
  conversion_grid: (number | null)[][];
  concentration_grid: number[][];
  tau_grid: number[][];
  baseline_point: { x: number; y: number };
  trend_summary: string;
  units: Record<string, string>;
}

export interface LHSSweepPointSchema {
  sample_index: number;
  V: number;
  Q: number;
  k: number;
  C_A_in: number;
  tau: number;
  C_A_ss: number;
  conversion: number | null;
  reaction_rate_ss: number;
  residual: number;
  status: "ok" | "failed";
  warning?: string | null;
}

export interface LHSSweepRequest {
  n_samples: number;
  seed: number;
  order: 0 | 1 | 2;
  bounds: Record<string, [number, number]>;
}

export interface LHSSweepResponse {
  sweep_type: "LHS";
  n_samples: number;
  seed: number;
  order: number;
  bounds: Record<string, [number, number]>;
  points: LHSSweepPointSchema[];
  summary_statistics: {
    total_evaluations: number;
    successful_evaluations: number;
    failed_evaluations: number;
    mean_conversion: number | null;
    min_conversion: number | null;
    max_conversion: number | null;
    mean_residence_time: number | null;
  };
  failed_count: number;
  units: Record<string, string>;
}

export interface DatasetInspectionResponse {
  filename: string;
  file_type: string;
  total_rows: number;
  total_columns: number;
  columns: string[];
  column_types: Record<string, string>;
  missing_counts: Record<string, number>;
  duplicate_rows_count: number;
  preview_data: Record<string, any>[];
  raw_records: Record<string, any>[];
  warnings: string[];
}

export interface ProcessDatasetRequest {
  records: Record<string, any>[];
  time_col: string;
  c_out_col: string;
  c_in_col?: string | null;
  constant_c_in?: number | null;
  flow_col?: string | null;
  constant_flow?: number | null;
  volume_col?: string | null;
  constant_volume?: number | null;
  time_unit?: TimeUnit;
  conc_unit?: ConcentrationUnit;
  flow_unit?: FlowRateUnit;
  vol_unit?: VolumeUnit;
  apply_smoothing?: boolean;
  savgol_window?: number;
  savgol_poly?: number;
  apply_anomaly_detection?: boolean;
  contamination?: number;
}

export interface ProcessedSeriesSchema {
  time: number[];
  time_unit: string;
  C_A_out_raw: number[];
  C_A_out_smoothed?: number[] | null;
  C_A_in: number[];
  conversion?: (number | null)[] | null;
  anomaly_scores?: number[] | null;
  is_anomaly?: boolean[] | null;
  tau?: number[] | null;
}

export interface ProcessedDatasetResponse {
  dataset_summary: Record<string, any>;
  series: ProcessedSeriesSchema;
  column_mapping: Record<string, string | null>;
  smoothing_applied: boolean;
  smoothing_settings?: Record<string, any> | null;
  anomaly_detection_applied: boolean;
  anomaly_count: number;
  data_quality_warnings: string[];
  provenance_note: string;
}

export interface ParameterConfidenceIntervalSchema {
  param_name: string;
  estimate: number;
  std_error: number;
  confidence_level: number;
  ci_lower: number;
  ci_upper: number;
  degrees_of_freedom: number;
  t_critical: number;
}

export interface FitKineticsRequest {
  model_type: "dynamic" | "steady_state";
  order: 0 | 1 | 2;
  time_series: number[];
  observed_C_A: number[];
  V: number;
  Q: number;
  C_A_in: number;
  C_A_0?: number | null;
  fit_initial_conc?: boolean;
  k_init?: number;
  k_min?: number;
  k_max?: number;
  confidence_level?: number;
  time_unit?: TimeUnit;
  conc_unit?: ConcentrationUnit;
  flow_unit?: FlowRateUnit;
  vol_unit?: VolumeUnit;
  is_flow_rate_input?: boolean;
  dataset_split?: "train" | "val" | "test" | null;
  has_temperature_only?: boolean;
}

export interface FitKineticsResponse {
  model_type: string;
  reaction_order: number;
  fitted_k: number;
  k_unit: string;
  initial_k_guess: number;
  k_bounds: [number, number];
  fitted_C_A_0?: number | null;
  confidence_interval_k?: ParameterConfidenceIntervalSchema | null;
  uncertainty_note?: string | null;
  condition_number?: number | null;
  parameter_correlation?: Record<string, number> | null;

  n_points: number;
  degrees_of_freedom: number;
  ssr: number;
  rmse: number;
  mae: number;
  r_squared: number;

  optimizer_success: boolean;
  optimizer_status: number;
  optimizer_message: string;
  n_fev: number;

  time_series: number[];
  observed_C_A: number[];
  predicted_C_A: number[];
  residuals: number[];

  warnings: string[];
  provenance_label: string;
}

export interface MLModelCatalogItem {
  model_id: string;
  model_type: string;
  name: string;
  description: string;
  task: string;
  provenance: string;
  status: string;
  is_trainable: boolean;
  input_features: string[];
}

export interface MLTrainingRequest {
  model_type: string;
  epochs?: number;
  learning_rate?: number;
  hidden_dim?: number;
  num_layers?: number;
  random_seed?: number;
  is_async?: boolean;
}

export interface MLTrainingResponse {
  job_id: string;
  model_type: string;
  status: string;
  epochs_completed: number;
  best_val_loss?: number | null;
  train_rmse?: number | null;
  val_rmse?: number | null;
  test_rmse?: number | null;
  test_r2?: number | null;
  negative_conc_count: number;
  training_duration_seconds: number;
  train_loss_history: number[];
  val_loss_history: number[];
  provenance: string;
  warnings: string[];
}

export interface MLJobStatusResponse {
  job_id: string;
  model_type: string;
  status: string;
  progress_percent: number;
  current_epoch: number;
  total_epochs: number;
  created_at: string;
  result?: MLTrainingResponse | null;
  error_message?: string | null;
  cancel_requested: boolean;
}

export interface MLInferenceRequest {
  model_type: string;
  V: number;
  Q: number;
  k: number;
  C_A_in: number;
  C_A_0: number;
  order?: number;
  t_final?: number;
  n_points?: number;
}

export interface MLInferenceResponse {
  model_type: string;
  t: number[];
  C_A: number[];
  reaction_rate?: number[] | null;
  mass_balance_residual?: number[] | null;
  steady_state_C_A?: number | null;
  uncertainty_lower?: number[] | null;
  uncertainty_upper?: number[] | null;
  confidence_interval_level?: number | null;
  provenance: string;
  warnings: string[];
}

export interface MLBaselinesBenchmarkResponse {
  task: string;
  n_train_trajectories: number;
  n_val_trajectories: number;
  n_test_trajectories: number;
  test_metrics: Record<string, Record<string, number>>;
  val_metrics: Record<string, Record<string, number>>;
  provenance: string;
}

export interface MLDatasetPreviewResponse {
  total_samples: number;
  total_trajectories: number;
  columns: string[];
  sample_rows: Record<string, any>[];
  split_summary: {
    train_trajectories: number;
    val_trajectories: number;
    test_trajectories: number;
    zero_leakage_verified: boolean;
    split_ratio: string;
  };
  parameter_ranges: Record<string, { min: number; max: number }>;
  provenance: string;
}

export interface MLDatasetValidationResponse {
  is_valid: boolean;
  total_samples: number;
  total_trajectories: number;
  schema_valid: boolean;
  bounds_valid: boolean;
  zero_leakage_verified: boolean;
  errors: string[];
  warnings: string[];
}

export interface ThermalSimulationRequest {
  V: number;
  Q: number;
  C_A_in: number;
  T_in: number;
  C_A_0?: number;
  T_0?: number | null;
  A?: number;
  Ea?: number;
  order?: number;
  delta_H_rxn?: number;
  UA?: number;
  V_j?: number;
  Q_j?: number;
  T_j_in?: number;
  isothermal?: boolean;
  t_final?: number;
  n_points?: number;
}

export interface ThermalSimulationResponse {
  t: number[];
  C_A: number[];
  T_reactor: number[];
  T_jacket: number[];
  k_T: number[];
  conversion: number[];
  heat_generated: number[];
  heat_removed: number[];
  steady_state_C_A: number;
  steady_state_T: number;
  thermal_runaway_detected: boolean;
  units?: Record<string, string>;
  warnings: string[];
  provenance: string;
}

export interface PRBSAuditResponse {
  status: string;
  filepath: string;
  row_count: number;
  column_count: number;
  dt_seconds: number;
  time_span_seconds: number;
  missing_values_count: number;
  signal_mappings: Record<string, string>;
  excitation_identifiability: {
    reactor_temp_range_k: number;
    jacket_temp_range_k: number;
    prbs_levels: number;
    is_sufficiently_excited: boolean;
  };
  scientific_governance_notice: string;
}

export interface PRBSCalibrationResponse {
  status: string;
  audit: Record<string, any>;
  calibrated_parameters: {
    k_jacket_per_s: number;
    k_inlet_per_s: number;
    thermal_bias_k_per_s: number;
  };
  validation_metrics: {
    validation_derivative_rmse_k_per_s: number;
  };
  locked_test_metrics: {
    derivative_rmse_k_per_s: number;
    derivative_mae_k_per_s: number;
    derivative_mean_residual_k_per_s: number;
    temperature_1step_rmse_k: number;
    temperature_1step_mae_k: number;
    temperature_mean_residual_k: number;
    sample_count: number;
  };
  scientific_data_governance: {
    temperature_validated: boolean;
    concentration_validated: boolean;
    warning: string;
  };
}

export interface HistoryRunItem {
  id: string;
  name: string;
  run_type: string;
  created_at: string;
  provenance: string;
  parameters: Record<string, any>;
  results_summary: Record<string, any>;
}

export interface HistoryRunDetail extends HistoryRunItem {
  schema_version?: string;
  artifact_ref?: string | null;
  seed?: number | null;
  split_id?: string | null;
  time_series?: {
    t: number[];
    C_A: number[];
    [key: string]: any;
  } | null;
  metadata?: Record<string, any>;
}

export interface CompareRunsResponse {
  compared_runs_count: number;
  runs: HistoryRunDetail[];
}

export interface RetentionResponse {
  status: string;
  purged_count: number;
  message: string;
}

export interface OptimizationAuditResponse {
  status: string;
  benchmark: {
    model_name: string;
    n_inferences: number;
    mean_latency_ms: number;
    median_latency_ms: number;
    p95_latency_ms: number;
    p99_latency_ms: number;
    throughput_inferences_per_sec: number;
    parameter_count: number;
    memory_footprint_kb: number;
    onnx_available: boolean;
    onnx_runtime_available: boolean;
    onnx_decision: string;
    justification: string;
  };
  regime_stability: {
    regime_name: string;
    description: string;
    inputs: Record<string, number>;
    steady_state_C_A: number;
    is_finite: boolean;
    is_non_negative: boolean;
    atol_tolerance: number;
    rtol_tolerance: number;
  }[];
  all_regimes_finite: boolean;
  all_regimes_non_negative: boolean;
  fallback_status: {
    fallback_engine: string;
    fallback_operational: boolean;
    external_binaries_required: boolean;
  };
  formal_decision: {
    decision: string;
    ship_onnx_runtime: boolean;
    rationale: string;
  };
}


