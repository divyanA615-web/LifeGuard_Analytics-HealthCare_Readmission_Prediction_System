"""High-level feature: structured extraction of clinical notes."""

from __future__ import annotations

import logging
import os

from . import nvidia_client

logger = logging.getLogger(__name__)


def parse_clinical_note(document_b64: str, mode: str = "markdown") -> dict:
    """Send a base64-encoded clinical note to Nemoretriever Parse."""
    model = os.environ.get("NVIDIA_PARSE_MODEL", "nvidia/nemoretriever-parse")
    return nvidia_client.parse_documents(model=model, document=document_b64, mode=mode)
