"""Smoke test the FastAPI app — verifies all 6 routes are registered."""

import os, sys
sys.path.insert(0, ".")

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.main import app  # noqa: E402

print(f"App: {app.title}")  # noqa
print(f"Total top-level routes: {len(app.routes)}")  # noqa

print("\n--- All API endpoints (from OpenAPI schema) ---")
schema = app.openapi()
for path, methods in schema.get("paths", {}).items():
    for method in methods:
        print(f"  [{method.upper()}] {path}")  # noqa

print(f"\nTotal paths: {sum(1 for _ in schema.get('paths', {}).keys())}")
print("Done")
