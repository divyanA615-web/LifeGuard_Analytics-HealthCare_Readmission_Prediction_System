"""Pydantic schemas for feedback endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prediction_id: int
    actual_readmitted_30d: bool
    clinician_notes_enc: str = Field(
        default="",
        description="Pre-encrypted clinician notes (AES-256-GCM).",
    )


class FeedbackResponse(BaseModel):
    feedback_id: int
    recorded_at: datetime
