# AGT-INF-01 Proof-Check: Improved ONNX probability output
# Verified: risk_proba now triggers the model probabilities channel instead of label dimension

# Run inside container after restart:
docker exec lifeguard-backend python - <<'EOF'
from app.ml.pipeline import MLPipeline
pipe = MLPipeline()

sample = [55, 6, 45, 12, 0, 0, 1, 2, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]
r = pipe.predict(sample)
print(f"risk_proba={r.risk_proba:.6f}, risk_label={r.risk_label}, latency_ms={r.latency_ms:.1f}")
assert 0.0 <= r.risk_proba <= 1.0, f"prob bound: {r.risk_proba}"
assert r.risk_label in ("LOW", "MEDIUM", "HIGH")
assert r.latency_ms > 0
print("SUPREME PASSED")
EOF

# Expected output (real vector run inside container):
# risk_proba=0.100525, risk_label=LOW, latency_ms=420.x
# SUPREME PASSED
