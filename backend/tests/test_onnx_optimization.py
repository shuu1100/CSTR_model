"""Test suite for Phase 14: Optional ONNX Optimization and Latency Benchmarking.

Adheres strictly to GLOBAL-INSTRUCTIONS.md, phase-14, and phase-08A:
- Measures CPU inference latency, throughput, and memory footprint of native PyTorch models.
- Tests numerical stability on Normal, Edge, and Out-Of-Distribution (OOD) operating regimes.
- Verifies zero-crash execution and transparent native PyTorch fallback when ONNX runtime is absent.
- Integration tests for /api/v1/ml/optimization/audit and /api/v1/ml/optimization/benchmark routes.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.ml.onnx_optimization import (
    benchmark_pytorch_grey_box_latency,
    check_onnx_availability,
    evaluate_regimes_numerical_stability,
    full_optimization_audit,
)

client = TestClient(app)


class TestONNXBenchmarkingAndFallbacks:
    """Tests for latency benchmarking, memory usage, and fallback safety."""

    def test_onnx_availability_check(self) -> None:
        has_onnx, has_ort = check_onnx_availability()
        assert isinstance(has_onnx, bool)
        assert isinstance(has_ort, bool)

    def test_native_pytorch_latency_and_memory_benchmark(self) -> None:
        res = benchmark_pytorch_grey_box_latency(n_runs=20, n_points=31)
        assert res.n_inferences == 20
        # Native PyTorch RK4 inference must meet interactive SLAs (< 250 ms mean, < 500 ms p95)
        assert res.mean_latency_ms < 250.0
        assert res.p95_latency_ms < 500.0
        assert res.throughput_inferences_per_sec > 2.0
        assert res.parameter_count > 0
        assert res.memory_footprint_kb > 0.0
        assert res.onnx_decision == "PRESERVE_NATIVE_PYTORCH_FALLBACK"
        assert "Native PyTorch CPU latency" in res.justification


    def test_regime_stability_normal_edge_ood(self) -> None:
        regime_results = evaluate_regimes_numerical_stability()
        assert len(regime_results) == 5

        for reg in regime_results:
            assert reg.is_finite is True, f"Regime {reg.regime_name} produced non-finite values"
            assert reg.is_non_negative is True, f"Regime {reg.regime_name} produced negative concentration"
            assert reg.steady_state_C_A >= 0.0
            assert reg.atol_tolerance == 1e-6
            assert reg.rtol_tolerance == 1e-5

    def test_full_optimization_audit_structure(self) -> None:
        audit = full_optimization_audit(n_runs=10)
        assert audit["status"] == "success"
        assert audit["all_regimes_finite"] is True
        assert audit["all_regimes_non_negative"] is True
        assert audit["fallback_status"]["fallback_operational"] is True
        assert audit["fallback_status"]["fallback_engine"] == "NATIVE_PYTORCH_RK4"
        assert audit["formal_decision"]["ship_onnx_runtime"] is False
        assert audit["formal_decision"]["decision"] == "PRESERVE_NATIVE_PYTORCH_FALLBACK"


class TestOptimizationAPIEndpoints:
    """Integration tests for FastAPI /api/v1/ml/optimization routes."""

    def test_api_optimization_audit_endpoint(self) -> None:
        res = client.get("/api/v1/ml/optimization/audit")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert "benchmark" in data
        assert "regime_stability" in data
        assert data["all_regimes_finite"] is True
        assert data["fallback_status"]["fallback_operational"] is True
        assert data["formal_decision"]["decision"] == "PRESERVE_NATIVE_PYTORCH_FALLBACK"

    def test_api_optimization_benchmark_endpoint(self) -> None:
        res = client.post("/api/v1/ml/optimization/benchmark?n_runs=10&n_points=21")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        bench = data["benchmark"]
        assert bench["n_inferences"] == 10
        assert bench["mean_latency_ms"] > 0.0
        assert bench["throughput_inferences_per_sec"] > 0.0
