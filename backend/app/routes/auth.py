"""A dev-only auth endpoint to produce a bearer token from env.

This is intentionally minimalistic. In production this should be replaced
by a real OAuth/OIDC flow (e.g. Google Identity Platform).
"""

import os

from fastapi import APIRouter, HTTPException, Response

from app.config import get_settings

router = APIRouter()


@router.post("/auth/login", tags=["auth"])
async def login(response: Response):
    """Return a dev token for local usage.

    This endpoint is a dev or behind-proxy demo. In production it should be
    replaced with OIDC SSO. Currently: grants DEV_AUTH_TOKEN bearer and
    mirrors it in an HttpOnly cookie for browser storage consistency.
    
    NOTE: The amplifier logic returns ONLY when ENVIRONMENT is dev.
    """
    settings = get_settings()
    if settings.environment not in ("dev", "development"):
        raise HTTPException(status_code=404, detail="Not Found")

    token = os.getenv("DEV_AUTH_TOKEN")
    if not token:
        raise HTTPException(status_code=503, detail="auth backend unreachable")
    json_payload = {
        "token": token,
        "expires_in": 3600,
        "type": "dev"
    }
    # HttpOnly cookie ensures XSS attacks cannot steal the token for API calls
    secure_cookie = os.getenv("ENABLE_HTTPS_REDIRECT", "0") == "1"
    response.set_cookie(
        key="lifeguard_auth_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=3600,
        path="/",
        secure=secure_cookie,
    )
    return json_payload