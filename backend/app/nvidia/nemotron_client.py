"""High-level feature: explain a SHAP attributions payload via Nemotron."""

from __future__ import annotations

import logging
import os
from typing import Iterable

from . import nvidia_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a clinical decision support assistant that translates SHAP "
    "attributions into a concise, plain-language explanation for a discharge "
    "planner. Never invent patient identifiers. Keep responses under 200 words."
)


def explain_risk(
    risk_score: float,
    top_features: list[dict],
    patient_context: dict | None = None,
) -> str:
    """Return a clinician-friendly explanation text.

    ``top_features`` is a list of {feature, value, contribution} dicts sorted
    by absolute contribution. ``patient_context`` contains ONLY de-identified
    factors (age band, diagnosis group, comorbidity count, etc.) — never PHI.
    """
    bullets = "\n".join(
        f"- {f['feature']}={f['value']} (contribution={f['contribution']:.3f})"
        for f in top_features
    )
    context_str = ", ".join(f"{k}={v}" for k, v in (patient_context or {}).items())
    if context_str:
        context_str = f"Aggregate context: {context_str}\n"

    user_prompt = (
        f"A patient's readmission risk score is {risk_score:.2%}. "
        "Explain in 4 short bullets why the score is what it is. "
        "Highlight the top drivers, the magnitude, and one suggested next step.\n\n"
        f"{context_str}Top SHAP-attribution features (de-identified):\n{bullets}"
    )
    response = nvidia_client.chat_complete(
        model=os.environ.get("NVIDIA_LLM_MODEL", "nvidia/nemotron-3-ultra-550b-a55b"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=600,
        temperature=0.2,
    )
    return response["choices"][0]["message"]["content"]
