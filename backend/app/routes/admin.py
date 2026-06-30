"""Admin endpoints – model card, deployment info, feature importance feed."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.config import get_settings
from app.db.session import session_scope
from app.db.models import AuditEntry
from app.security.audit_logger import verify_chain
from app.security.auth_middleware import Principal, verify_request

router = APIRouter()
MODEL_CARD_PATH = Path("ml/models/MODEL_CARD.md")
EVAL_PATH = Path("ml/metrics/evaluation.json")
TRAINING_PATH = Path("ml/metrics/training.json")


@router.get("/model/info")
async def model_info(_principal: Principal = Depends(verify_request)):
    settings = get_settings()
    card = MODEL_CARD_PATH.read_text() if MODEL_CARD_PATH.exists() else ""
    info = {
        "model_version": "xgboost_v1",
        "deploy_env": settings.deploy_env,
        "model_card_excerpt": card[:400] + ("…" if len(card) > 400 else ""),
    }
    if EVAL_PATH.exists():
        info["evaluation"] = json.loads(EVAL_PATH.read_text())
    if TRAINING_PATH.exists():
        info["training"] = json.loads(TRAINING_PATH.read_text())
    return info


@router.get("/audit")
async def audit_chain_status(_principal: Principal = Depends(verify_request)):
    chain_intact = bool(verify_chain())
    with session_scope() as session:
        last = session.query(AuditEntry).order_by(AuditEntry.id.desc()).first()
    return {
        "chain_intact": chain_intact,
        "last_hash": last.chain_hash if last else None,
        "count": last.id if last else 0,
    }


@router.get("/admin/stats")
async def admin_stats(principal: Principal = Depends(verify_request)):
    if not principal.is_admin():
        raise HTTPException(status_code=403, detail="admin only")
    return {
        "principal": principal.subject,
        "stack": "fastapi / onnx / gcp / nvidia-free",
    }
