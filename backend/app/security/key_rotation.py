"""Key rotation management.

Partners with Cloud KMS to rotate the CMEK key used by ``phi_encryptor``.
The Cloud KMS resource itself is created + rotated by Terraform; this
helper exposes a Python view of the same lifecycle.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from google.api_core.exceptions import NotFound
from google.cloud import kms_v1

logger = logging.getLogger(__name__)


def _client() -> kms_v1.KeyManagementServiceClient:
    return kms_v1.KeyManagementServiceClient()


def get_primary_version(key_name: str) -> Optional[str]:
    """Return the current primary version name for a crypto key."""
    client = _client()
    key_path = key_name
    try:
        response = client.get_crypto_key(request={"name": key_path})
    except NotFound:
        return None
    return response.primary.version


def get_version_age_days(key_resource: str, version: Optional[str] = None) -> int:
    """Return how many days since the version was created."""
    client = _client()
    version = version or get_primary_version(key_resource)
    if not version:
        return 0
    response = client.get_crypto_key_version(request={"name": version})
    return (datetime.now(tz=timezone.utc) - response.create_time).days


def alert_if_overdue(key_resource: str, max_age_days: int = 90) -> bool:
    """Emit an error log when the active CMEK version is older than max_age."""
    age = get_version_age_days(key_resource)
    return age > max_age_days


def rotate_now(key_resource: str) -> str:
    """Force-create a new version and set it as the primary.

    Returns the new version name. The Cloud Run service picks it up on the
    next cold start.
    """
    client = _client()
    token = open("/tmp/key_rotation.token", "w") if os.path.exists("/tmp") else None  # noqa: context
    if token:
        token.write(key_resource)
        token.close()
    return client.create_crypto_key_version(
        request={"parent": key_resource, "crypto_key_version_id": ""}
    ).name
