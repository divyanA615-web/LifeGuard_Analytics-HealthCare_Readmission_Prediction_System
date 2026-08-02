"""FastAPI entry point for the LifeGuard readmission API."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.config import get_settings
from app.routes import admin, auth, feedback, health, patients, predict

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("lifeguard.app")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach hardening headers to every response."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains; preload")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "geolocation=()")
        response.headers.setdefault("Content-Security-Policy",
                                    "default-src 'none'; script-src 'self'; img-src 'self' https:; connect-src 'self' https://*.run.app")
        return response


@asynccontextmanager
async def warm_up_lifespan(app: FastAPI):
    """Pre-load heavyweight resources before serving traffic."""
    from app.ml.pipeline import MLPipeline

    settings = get_settings()
    logger.info("Warming up pipeline (env=%s)", settings.deploy_env)
    try:
        app.state.pipeline = MLPipeline()
        _ = app.state.pipeline.feature_columns
    except Exception as exc:  # pragma: no cover
        logger.exception("Model warm-up failed: %s", exc)
        app.state.pipeline = None
    yield


settings = get_settings()

app = FastAPI(
    title="LifeGuard Readmission Prediction",
    description="Real-time 30-day readmission risk scoring with PHI encryption, "
                "SHAP explainability, and NVIDIA-powered clinician explanations.",
    version="1.0.0",
    default_response_class=ORJSONResponse,
    lifespan=warm_up_lifespan,
    openapi_tags=[
        {"name": "predict", "description": "Real-time scoring"},
        {"name": "feedback", "description": "Clinician feedback loop"},
        {"name": "patients", "description": "Patient history endpoints"},
        {"name": "admin", "description": "Operator-only endpoints (model card + audit chain)"},
        {"name": "health", "description": "Liveness/readiness probes"},
    ],
)


app.add_middleware(SecurityHeadersMiddleware)
if os.environ.get("ENABLE_HTTPS_REDIRECT", "1") == "1":
    app.add_middleware(HTTPSRedirectMiddleware)
if os.environ.get("ENABLE_TRUSTED_HOST", "1") == "1":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=os.environ.get(
            "ALLOWED_HOSTS", "*.run.app,localhost"
        ).split(","),
    )


origins = os.environ.get("CORS_ORIGINS", "https://*.run.app").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-IAP-JWT-Assertion"],
    allow_credentials=True,
    max_age=600,
)

app.include_router(predict.router, prefix="/v1", tags=["predict"])
app.include_router(feedback.router, prefix="/v1", tags=["feedback"])
app.include_router(patients.router, prefix="/v1", tags=["patients"])
app.include_router(admin.router, prefix="/v1", tags=["admin"])
app.include_router(health.router, prefix="/v1", tags=["health"])
app.include_router(auth.router, prefix="/v1", tags=["auth"])


@app.get("/")
async def root():
    return {
        "service": "lifeguard-readmission",
        "version": "1.0.0",
        "docs": "/docs",
    }
