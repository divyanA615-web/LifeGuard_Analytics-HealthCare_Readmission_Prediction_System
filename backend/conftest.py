"""Shared pytest configuration."""

import os

# Ensure DATABASE_URL is set before any backend imports
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("NVIDIA_API_KEY", "test-key")
os.environ.setdefault("PHI_ENCRYPTION_KEY", "")
os.environ.setdefault("DEV_AUTH_TOKEN", "test-token")
