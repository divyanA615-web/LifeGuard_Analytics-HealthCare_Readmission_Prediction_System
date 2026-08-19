"""Request/response Pydantic schemas for the prediction endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FeatureInput(BaseModel):
    """A single de-identified feature + raw numeric value.

    Bound to the same ordering as feature_columns.json so the backend can
    serialise features in the right order without re-sorting.
    """

    name: str = Field(..., description="Feature name")
    value: float = Field(..., description="Numeric value")
    display: str | None = Field(
        default=None, description="Optional clinician-friendly label."
    )


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_request_id: str | None = Field(
        default=None, description="Idempotency token supplied by the client."
    )
    patient_token: str | None = Field(
        default=None,
        description="Optional existing patient identifier (created if absent).",
    )
    age_band: str = Field(default="[50-60)")
    gender_male: int = Field(default=1, ge=0, le=1)
    admission_type_emergency: int = Field(default=1, ge=0, le=1)
    discharge_to_home: int = Field(default=1, ge=0, le=1)
    payer_code: str = Field(default="MC")
    insulin_use: int = Field(default=1)
    metformin_use: int = Field(default=1)
    diabetesMed_yes: int = Field(default=1)
    change_in_meds: int = Field(default=0)
    age: int = Field(default=55, ge=0, le=120)
    time_in_hospital: int = Field(default=5, ge=0)
    num_lab_procedures: int = Field(default=45, ge=0)
    num_procedures: int = Field(default=1, ge=0)
    num_medications: int = Field(default=14, ge=0)
    number_outpatient: int = Field(default=0)
    number_emergency: int = Field(default=0)
    number_inpatient: int = Field(default=0)
    number_diagnoses: int = Field(default=3, ge=0)
    max_glu_serum_num: int = Field(default=0, ge=0, le=3)
    a1c_result_num: int = Field(default=0, ge=0, le=3)


class ExplanationItem(BaseModel):
    feature: str
    value: float
    contribution: float


class PredictResponse(BaseModel):
    request_id: str
    patient_token: str
    risk_proba: float
    risk_label: str
    explanation: list[ExplanationItem]
    model_version: str
    latency_ms: float
    humane_explanation: str | None = None
    similar_patients: list[dict[str, Any]] = Field(default_factory=list)
