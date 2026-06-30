"""Audit log schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuditRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actor: str
    action: str
    target: str
    payload_json: dict
    prev_hash: str
    chain_hash: str
    occurred_at: datetime


class AuditResponse(BaseModel):
    records: list[AuditRecord]
    chain_intact: bool
    cursor: str | None
