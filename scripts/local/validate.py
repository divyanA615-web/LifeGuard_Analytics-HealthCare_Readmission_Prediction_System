#!/usr/bin/env python3
"""LifeGuard Local Validation (portable: python).

Usage:
  python scripts/local/validate.ps1    # or validate.py if renamed
  ./validate.py

Outputs a `.lifeguard-validation.json` artifact for downstream audits.
Exit code: 0 == all checks passed, 1 == some failed.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent.absolute()
ROOT = SCRIPT_DIR.parent.parent.absolute()
MODEL_PATH = ROOT / "ml" / "models" / "xgboost_v1"
OUT_PATH = ROOT / ".lifeguard-validation.json"


class Check:
    def __init__(self, name: str):
        self.name = name
        self.passed: bool = False
        self.message: str = ""

    def to_dict(self):
        return {"passed": self.passed, "message": self.message}


def log_header(title: str) -> None:
    print("\n" + "=" * 40)
    print(f" {title}")
    print("=" * 40)


def check(name: str) -> Check:
    c = Check(name)
    return c


def check_connection(host: str, port: int, timeout: float = 5.0) -> bool:
    """Retry TCP connect until ready or timeout."""
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True
    except Exception:
        return False


def http_get(url: str, timeout: float = 5.0) -> tuple[int, str]:
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=timeout) as r:
            body = r.read().decode("utf-8")
            return r.status, body
    except Exception as e:
        return -1, str(e)


def main() -> int:
    log_header("LifeGuard Ready Check")
    qualified_status = {"timestamp": datetime.now().isoformat(), "checks": {}, "failed": 0, "passed": True}
    checks: dict[str, Any] = qualified_status["checks"]

    try:
        # 1. Docker
        c = check("Docker Daemon")
        result = subprocess.run(["docker", "info"], capture_output=True, text=True)
        if result.returncode == 0:
            c.passed = True
            c.message = f"server={result.stdout.splitlines()[0][:60]}"
        else:
            c.message = result.stderr
        checks["docker_daemon"] = c.to_dict()

        # 2. Model artifacts present
        c = check("Model Bundle (ml/models/xgboost_v1)")
        if MODEL_PATH.exists() and any(MODEL_PATH.glob("*.onnx")):
            c.passed = True
            c.message = f"model files found: {[x.name for x in MODEL_PATH.iterdir() if x.is_file() and x.parent.name == 'xgboost_v1']}"
        else:
            c.passed = False
            c.message = "model default path not found; run 'python ml/run_all.py'"
        checks["model_bundle"] = c.to_dict()

        # 3. Ports available
        for svc, host, port in [
            ("db", "localhost", 5432),
            ("backend", "localhost", 8080),
            ("frontend", "localhost", 8081),
        ]:
            c = check(svc)
            if check_connection(host, port):
                c.passed = True
                c.message = f"http://{host}:{port} responding"
            else:
                c.passed = False
                c.message = f"cannot connect to {host}:{port}"
            checks[svc] = c.to_dict()

        # 4. Backend health (requires backend up)
        code, body = http_get("http://localhost:8080/v1/health")
        c = check("API health")
        if code == 200 and '"status":"ok"' in body.lower():
            c.passed = True
            c.message = "health endpoint returned ok"
        else:
            c.passed = False
            c.message = f"unexpected response code={code}"
        checks["api_health"] = c.to_dict()

        # 5. Frontend Nginx probe (expects 200 with healthz marker or index.html)
        code, body = http_get("http://localhost:8081/")
        c = check("Frontend SPA served")
        if code == 200 and ("<title>" in body or "lifeguard" in body.lower()):
            c.passed = True
            c.message = "frontend HTML reached"
        else:
            c.passed = False
            c.message = f"unexpected HTML response code={code}"
        checks["frontend_spa"] = c.to_dict()

    except Exception as exc:  # noqa: BLE001
        checks.setdefault("unhandled", {}).update(getattr(checks["unhandled"], "to_dict", lambda: {})())
        qualified_status["error"] = str(exc)
        qualified_status["failed"] = qualified_status.get("failed", 0) + 1
        qualified_status["passed"] = False

    # Summary
    qualified_status["failed"] = sum(1 for c in checks.values() if not c["passed"])
    qualified_status["passed"] = all(c["passed"] for c in checks.values())

    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(qualified_status, fh, indent=2)
    print(f"Results written to {OUT_PATH}")
    print("RESULT:", "PASS" if qualified_status["passed"] else f"FAIL [{qualified_status['failed']} failed]")

    return 0 if qualified_status["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
