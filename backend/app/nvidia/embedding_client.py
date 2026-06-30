"""High-level feature: build patient-similarity embeddings via Nemotron."""

from __future__ import annotations

import logging
import os

from . import nvidia_client

logger = logging.getLogger(__name__)


def similarity_embeddings(texts: list[str], model: str | None = None) -> list[list[float]]:
    """Get an embedding vector for each de-identified text block."""
    model = model or os.environ.get(
        "NVIDIA_EMBEDDING_MODEL", "nvidia/llama-nemotron-embed-vl-1b-v2"
    )
    response = nvidia_client.embeddings(model=model, input_=texts)
    return [item["embedding"] for item in response["data"]]
