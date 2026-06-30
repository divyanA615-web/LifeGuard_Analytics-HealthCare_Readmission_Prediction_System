"""POST /v1/feedback – clinicians can correct predictions."""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.db.session import session_scope
from app.db.models import Feedback, Prediction
from app.security.audit_logger import AuditEvent, AuditLogger
from app.security.auth_middleware import Principal, verify_request

from app.schemas.feedback import FeedbackRequest, FeedbackResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/feedback", response_model=FeedbackResponse)
async def feedback(
    body: FeedbackRequest,
    principal: Principal = Depends(verify_request),
) -> FeedbackResponse:
    with session_scope() as session:
        prediction = session.query(Prediction).filter(Prediction.id == body.prediction_id).first()
        if prediction is None:
            raise HTTPException(status_code=404, detail="prediction not found")
        if prediction.clinician_id != principal.subject and not principal.is_admin():
            raise HTTPException(status_code=403, detail="forbidden")

        row = Feedback(
            prediction_id=body.prediction_id,
            clinician_id=principal.subject,
            actual_readmitted_30d=body.actual_readmitted_30d,
            clinician_notes_enc=body.clinician_notes_enc,
        )
        session.add(row)
        session.flush()
        feedback_id = row.id
        submitted_at = row.submitted_at

        prediction.feedback_at = submitted_at
        session.flush()

    AuditLogger().emit(
        AuditEvent(
            actor=principal.email,
            action="feedback",
            target=str(feedback_id),
            payload={
                "prediction_id": body.prediction_id,
                "actual_readmitted": body.actual_readmitted_30d,
                "notes_present": bool(body.clinician_notes_enc),
            },
        )
    )

    return FeedbackResponse(feedback_id=feedback_id, recorded_at=submitted_at)
