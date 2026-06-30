"""Health-check endpoint used by load balancers and uptime probes."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends

from app.ml.pipeline import MLPipeline
from app.security.auth_middleware import Principal, verify_request

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "timestamp": int(time.time())}


@router.get("/health/readiness")
async def readiness(principal: Principal = Depends(verify_request)):
    pipeline = MLPipeline()
    features = pipeline.feature_columns
    return {
        "model_loaded": bool(features),
        "feature_columns_loaded": len(features),
    }
