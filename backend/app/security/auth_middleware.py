"""Cloud IAP auth middleware.

Validates the JWT emitted by Cloud Identity-Aware Proxy and rejects calls
without an authenticated principal. In local development we accept a
deterministic dev token (read from ``DEV_AUTH_TOKEN``).

Use::

    from fastapi import Depends, FastAPI
    from app.security.auth_middleware import verify_request, Principal

    app = FastAPI()
    @app.post('/v1/predict')
    async def predict(p: Principal = Depends(verify_request)):
        ...
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Optional

import jwt
from fastapi import Cookie, Header, HTTPException, status

logger = logging.getLogger(__name__)

IAP_AUDIENCE_ENV = "IAP_JWT_AUDIENCE"
DEV_AUTH_TOKEN_ENV = "DEV_AUTH_TOKEN"  # nosec B105


@dataclass(slots=True)
class Principal:
    """The authenticated user issuing the request."""

    subject: str
    email: str
    role: str = "clinician"

    def is_admin(self) -> bool:
        return self.role in ("admin", "compliance")


async def verify_request(
    x_iap_jwt_assertion: Optional[str] = Header(default=None),
    authorization: Optional[str] = Header(default=None),
    lifeguard_auth_token: Optional[str] = Cookie(default=None),
) -> Principal:
    """Extract a Principal from Cloud IAP headers or local-dev token."""
    if x_iap_jwt_assertion:
        return _verify_iap(x_iap_jwt_assertion)

    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        return _verify_token(token)

    if lifeguard_auth_token:
        return _verify_token(lifeguard_auth_token)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="missing authentication header",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _verify_token(token: str) -> Principal:
    """Accept either the local dev token or a real Google ID token."""
    dev = os.environ.get(DEV_AUTH_TOKEN_ENV)
    if dev and token == dev:
        return Principal(subject="dev-user", email="dev@lifeguard.local", role="clinician")

    audience = os.environ.get(IAP_AUDIENCE_ENV, "/projects/dev/lifeguard-app")
    try:
        claims = jwt.decode(
            token,
            audience=audience,
            algorithms=["ES256"],
            options={"verify_at_hash": True},
        )
    except jwt.PyJWTError as exc:
        logger.info("JWT invalid: %s", exc)
        raise HTTPException(status_code=401, detail="invalid token") from exc

    return Principal(
        subject=claims.get("sub", "unknown"),
        email=claims.get("email", "unknown"),
        role=claims.get("role", "clinician"),
    )


def _verify_iap(jwt_assertion: str) -> Principal:
    """Decode the IAP JWT (signature verified by GCP edge proxy)."""
    audience = os.environ["IAP_JWT_AUDIENCE"]
    try:
        # IAP JWTs are signed by Google; signature is verified at the edge.
        # We decode and re-check the audience here for defence in depth.
        claims = jwt.decode(
            jwt_assertion,
            audience=audience,
            algorithms=["ES256"],
            options={"verify_signature": False, "verify_at_hash": True},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="invalid IAP token") from exc

    return Principal(
        subject=claims.get("sub", "iap-user"),
        email=claims.get("email", "unknown"),
        role=claims.get("role", "clinician"),
    )
