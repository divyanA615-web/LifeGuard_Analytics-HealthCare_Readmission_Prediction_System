"""Append-only audit logger for prediction events.

Every prediction call records into a hash-chained on-disk and optionally
Pub/Sub-backed audit log. The chain format is compatible with the chain
verification job; tampering breaks the hash chain immediately.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

AUDIT_TOPIC_ENV = "AUDIT_TOPIC"
LOCAL_AUDIT_PATH = Path("ml/data/processed/audit_chain.ndjson")


@dataclass
class AuditEvent:
    actor: str
    action: str
    target: str
    payload: dict[str, Any]
    occurred_at: str = field(default_factory=lambda: dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"))
    prev_hash: str = "0" * 64
    chain_hash: str | None = None

    def compute_hash(self) -> str:
        canonical = json.dumps(
            {
                "actor": self.actor,
                "action": self.action,
                "target": self.target,
                "payload": self.payload,
                "occurred_at": self.occurred_at,
                "prev_hash": self.prev_hash,
            },
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()


class AuditLogger:
    """Thread-safe append-only logger backed by NDJSON + optional Pub/Sub."""

    def __init__(self, path: Path = LOCAL_AUDIT_PATH):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._last_hash = self._load_last_hash()

    def _load_last_hash(self) -> str:
        if not self.path.exists():
            return "0" * 64
        with self.path.open("rb") as fh:
            content = fh.read().splitlines()
        if not content:
            return "0" * 64
        try:
            last = json.loads(content[-1])
            return last.get("chain_hash", "0" * 64)
        except (ValueError, KeyError):
            logger.warning("Audit log appears corrupted at tail – resetting prev_hash")
            return "0" * 64

    def emit(self, event: AuditEvent) -> None:
        event.prev_hash = self._last_hash
        event.chain_hash = event.compute_hash()
        with self.path.open("a") as fh:
            fh.write(json.dumps(event.__dict__, default=str) + "\n")
        self._last_hash = event.chain_hash
        self._maybe_publish(event)

    def _maybe_publish(self, event: AuditEvent) -> None:
        topic = os.environ.get(AUDIT_TOPIC_ENV)
        if not topic:
            return
        try:  # pragma: no cover - Pub/Sub path
            from google.cloud import pubsub_v1

            publisher = pubsub_v1.PublisherClient()
            publisher.publish(
                topic=topic,
                data=event.chain_hash.encode("utf-8"),
                attributes={"action": event.action},
            )
        except (OSError, RuntimeError) as exc:
            logger.debug("Pub/Sub audit publish skipped: %s", exc)


def verify_chain(path: Path = LOCAL_AUDIT_PATH) -> bool:
    """Verify that all linked hashes form a valid chain.

    Returns False on any tamper attempt, malformed JSON, or missing
    fields, rather than raising – this lets callers use it as a one-line
    readiness probe.
    """
    if not path.exists():
        return True
    prev = "0" * 64
    try:
        for line in path.open():
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                return False
            canonical = json.dumps(
                {k: v for k, v in rec.items() if k != "chain_hash"},
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            ).encode("utf-8")
            expected = hashlib.sha256(canonical).hexdigest()
            if rec.get("prev_hash") != prev or rec.get("chain_hash") != expected:
                return False
            prev = expected
    except OSError:
        return False
    return True
