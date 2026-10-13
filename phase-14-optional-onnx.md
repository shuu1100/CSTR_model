# Phase 14 — Optional ONNX Optimization

Only export a stable useful ML model if latency evidence justifies it. Benchmark original model first; measure latency/throughput/memory. Test ONNX numerical agreement on normal, edge and OOD inputs, record tolerances, and preserve fallback. ONNX must remain optional; if there is no measurable benefit, document the decision not to ship it.

## Global compliance
Follow `GLOBAL-INSTRUCTIONS.md` and preserve the existing Phase 0–15 architecture. Inspect prior work before editing, add tests, run checks, and report actual results.
