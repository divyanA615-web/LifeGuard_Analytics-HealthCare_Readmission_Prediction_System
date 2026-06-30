"""NVIDIA build.nvidia.com helper.

Stores the API key in Secret Manager. Free-tier endpoint is
``https://integrate.api.nvidia.com/v1/chat/completions`` (Nemotron family).

All requests pass through the ``DeIdentificationGate`` upstream to ensure
PHI never leaves the trust boundary.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)

NVIDIA_API_BASE = os.environ.get("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1")
REQUEST_TIMEOUT_SECONDS = 30


class NIMRateLimitExceeded(Exception):
    """Raised when the per-day free-tier limit is close."""


@dataclass(slots=True)
class RateLimiter:
    max_per_day: int = 1000
    calls: list[float] = field(default_factory=list)

    def can_call(self) -> bool:
        now = time.time()
        cutoff = now - 24 * 3600
        recent = [t for t in self.calls if t > cutoff]
        return len(recent) < self.max_per_day

    def record(self) -> None:
        self.calls.append(time.time())

    def remaining(self) -> int:
        now = time.time()
        cutoff = now - 24 * 3600
        return self.max_per_day - len([t for t in self.calls if t > cutoff])


DATASET_DAILY_USAGE = RateLimiter(max_per_day=int(os.environ.get("NVIDIA_DAILY_LIMIT", "950")))


def _common_headers() -> dict[str, str]:
    key = os.environ.get("NVIDIA_API_KEY")
    if not key:
        raise RuntimeError("NVIDIA_API_KEY is not configured")
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def chat_complete(
    model: str,
    messages: list[dict[str, str]],
    max_tokens: int = 16000,
    temperature: float = 0.2,
    top_p: float = 0.95,
    thinking: bool = True,
    extra_body: Optional[dict] = None,
    timeout: int = REQUEST_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Send a chat-completion request to a Nemotron model."""
    if not DATASET_DAILY_USAGE.can_call():
        raise NIMRateLimitExceeded(
            "NVIDIA daily call budget exhausted; switch to local explanation fallback."
        )
    body = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "stream": False,
    }
    body.setdefault("chat_template_kwargs", {"enable_thinking": thinking})
    if extra_body:
        body.update(extra_body)
    response = requests.post(
        f"{NVIDIA_API_BASE}/chat/completions",
        headers=_common_headers(),
        data=json.dumps(body),
        timeout=timeout,
    )
    response.raise_for_status()
    DATASET_DAILY_USAGE.record()
    return response.json()


def embeddings(
    model: str,
    input_: list[str],
    encoding_format: str = "float",
    timeout: int = REQUEST_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    if not DATASET_DAILY_USAGE.can_call():
        raise NIMRateLimitExceeded("NVIDIA daily call budget exhausted.")
    response = requests.post(
        f"{NVIDIA_API_BASE}/embeddings",
        headers=_common_headers(),
        data=json.dumps(
            {"model": model, "input": input_, "encoding_format": encoding_format}
        ),
        timeout=timeout,
    )
    response.raise_for_status()
    DATASET_DAILY_USAGE.record()
    return response.json()


def parse_documents(model: str, document: str, mode: str = "markdown") -> dict[str, Any]:
    """Nemoretriever Parse endpoint – PDF/document -> structured markdown."""
    if not DATASET_DAILY_USAGE.can_call():
        raise NIMRateLimitExceeded("NVIDIA daily call budget exhausted.")
    response = requests.post(
        f"{NVIDIA_API_BASE}/parse_documents",
        headers=_common_headers(),
        data=json.dumps({"model": model, "document": document, "mode": mode}),
        timeout=timeout,
    )
    response.raise_for_status()
    DATASET_DAILY_USAGE.record()
    return response.json()
