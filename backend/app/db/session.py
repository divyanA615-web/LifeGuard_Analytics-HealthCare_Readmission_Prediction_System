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


def _build_engine() -> Engine:
    db_uri = os.environ.get("DATABASE_URL")
    if db_uri:
        connect_args = {"connect_timeout": 5}
        return create_engine(db_uri, connect_args=connect_args, pool_pre_ping=True)
    raise RuntimeError("DATABASE_URL not configured")


def get_engine() -> Engine:
    if not hasattr(get_engine, "_engine"):
        get_engine._engine = _build_engine()
    return getattr(get_engine, "_engine")


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


@contextmanager
def session_scope() -> Iterator:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
