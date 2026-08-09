"""Database session + connection helpers."""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

_engine = None


def _get_bind_uri() -> str:
    uri = os.environ.get("DATABASE_URL")
    if not uri:
        raise RuntimeError("DATABASE_URL not configured")
    return uri


def _build_engine() -> Engine:
    return create_engine(_get_bind_uri(), connect_timeout=5, pool_pre_ping=True)


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = _build_engine()
    return _engine


SessionLocal = sessionmaker(autocommit=False, autoflush=False)


@contextmanager
def session_scope() -> Iterator:
    engine = get_engine()
    SessionLocal.configure(bind=engine)
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
