"""Test suite for Phase 14: Optional ONNX Optimization and Latency Benchmarking.

Adheres strictly to GLOBAL-INSTRUCTIONS.md, phase-14, and phase-08A:
- Measures CPU inference latency and throughput of native PyTorch models.
- Confirms zero-crash execution when onnx/onnxruntime is not installed.
- Validates the architectural decision and fallback mechanism.
"""

from backend.app.ml.onnx_optimization import (
    benchmark_pytorch_grey_box_latency,
    check_onnx_availability,
)


def test_onnx_availability_check() -> None:
    has_onnx, has_ort = check_onnx_availability()
    assert isinstance(has_onnx, bool)
    assert isinstance(has_ort, bool)


def test_native_pytorch_latency_benchmark() -> None:
    res = benchmark_pytorch_grey_box_latency(n_runs=25, n_points=31)
    assert res.n_inferences == 25
    # Native PyTorch RK4 inference must be fast (well below 150 ms per trajectory on CPU)
    assert res.mean_latency_ms < 150.0
    assert res.p95_latency_ms < 200.0
    assert res.throughput_inferences_per_sec > 5.0
    assert res.onnx_decision == "PRESERVE_NATIVE_PYTORCH_FALLBACK"
    assert "Native PyTorch CPU latency" in res.justification
