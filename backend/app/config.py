"""Application configuration loaded from environment variables.

Sensitive values (DB password, KMS resource ID, NVIDIA key) come from Secret
Manager in production. Locally they can be sourced from `.env` via a custom
loader. Callers should only read these via the central ``Settings`` object.
"""

from __future__ import annotations

import functools
from dataclasses import dataclass

from decouple import config  # type: ignore


@dataclass(frozen=True)
class Settings:
    environment: str = config("ENVIRONMENT", default="dev")
    project_id: str = config("GCP_PROJECT_ID", default="project-b0677df0-7b67-4302-a4a")
    region: str = config("GCP_REGION", default="asia-south1")
    db_connection_secret: str = config("DB_SECRET_NAME", default="db-uri")
    kms_key_resource: str = config("PHI_ENCRYPTION_KEY", default="")
    nvidia_api_key: str | None = config("NVIDIA_API_KEY", default=None)
    nvidia_embedding_model: str = config(
        "NVIDIA_EMBEDDING_MODEL",
        default="nvidia/llama-nemotron-embed-vl-1b-v2",
    )
    nvidia_llm_model: str = config(
        "NVIDIA_LLM_MODEL",
        default="nvidia/nemotron-3-ultra-550b-a55b",
    )
    nvidia_parse_model: str = config(
        "NVIDIA_PARSE_MODEL",
        default="nvidia/nemoretriever-parse",
    )
    audit_log_topic: str = config("AUDIT_TOPIC", default="projects/PROJECT/audit")
    model_artifact_path: str = config("MODEL_ARTIFACT_PATH", default="ml/models/xgboost_v1")
    model_artifact_bucket: str = config("MODEL_BUCKET", default="lifeguard-models-dev")
    deploy_env: str = config("DEPLOY_ENV", default="dev")


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
