"""Patient-side endpoints: history retrieval with PHI unmasking."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.db.models import Prediction
from app.db.session import session_scope
from app.security.auth_middleware import Principal, verify_request

router = APIRouter()


@router.get("/patients/{patient_token}/history")
async def history(
    patient_token: str,
    limit: int = Query(20, ge=1, le=200),
    cursor: int | None = Query(default=None, ge=1),
    principal: Principal = Depends(verify_request),  # noqa: B008
):
    """Return encrypted history. The frontend decides which rows to decrypt."""
    with session_scope() as session:
        q = (
            session.query(Prediction)
            .filter(Prediction.patient_token == patient_token)
            .filter(Prediction.clinician_id == principal.subject)
            .order_by(Prediction.created_at.desc())
            .limit(limit)
        )
        rows = q.all()
    return {
        "patient_token": patient_token,
        "predictions": [
            {
                "id": p.id,
                "risk_proba": p.risk_proba,
                "risk_label": p.risk_label,
                "model_version": p.model_version,
                "created_at": p.created_at.isoformat(),
                "explanation": p.explanation_json,
                "feedback_recorded": p.feedback_at is not None,
            }
            for p in rows
        ],
    }


@router.get("/patients/{patient_token}/pii")
async def pii(
    patient_token: str,
    principal: Principal = Depends(verify_request),  # noqa: B008
):
    """Decrypt patient PHI for an authorized clinician."""
    if not principal.is_admin() and principal.role not in ("clinician",):
        raise HTTPException(status_code=403, detail="forbidden")
    return {
        "patient_token": patient_token,
        "decrypted": "(stub) – real decrypted PHI would be returned here",
    }
