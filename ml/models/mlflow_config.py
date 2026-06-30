"""MLflow project configuration for the readmission pipeline.

Set the tracking URI via the ``MLFLOW_TRACKING_URI`` environment variable
in CI or local development. In production, the value should be a Cloud
Storage-backed SQL store (e.g. ``postgresql+psycopg2://...``).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MLflowConfig:
    tracking_uri: str
    experiment: str = "lifeguard-readmission"
    registry_uri: Optional[str] = None

    @classmethod
    def from_env(cls) -> "MLflowConfig":
        tracking_uri = os.environ.get(
            "MLFLOW_TRACKING_URI", "file:./mlruns"
        )
        registry_uri = os.environ.get("MLFLOW_REGISTRY_URI", tracking_uri)
        return cls(tracking_uri=tracking_uri, registry_uri=registry_uri)

    def is_remote(self) -> bool:
        return not urlparse(self.tracking_uri).scheme in ("", "file")


def get_config() -> MLflowConfig:
    cfg = MLflowConfig.from_env()
    logger.info("Using MLflow URI: %s", cfg.tracking_uri)
    return cfg


def pre_train_setup() -> None:
    """Set environment variables for MLflow + dependencies before training."""
    cfg = get_config()
    if cfg.is_remote:
        os.environ["MLFLOW_TRACKING_USERNAME"] = os.environ.get(
            "MLFLOW_TRACKING_USERNAME", ""
        )
        os.environ["MLFLOW_TRACKING_PASSWORD"] = os.environ.get(
            "MLFLOW_TRACKING_PASSWORD", ""
        )
