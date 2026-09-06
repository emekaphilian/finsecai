"""Database boundaries for benchmark and diagnostic execution."""

from __future__ import annotations

import os
from urllib.parse import urlsplit

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


class DatabaseBoundaryError(RuntimeError):
    """Raised when a benchmark or diagnostic lacks an isolated database."""


def isolated_database_url() -> str:
    """Return the explicitly configured non-application benchmark database URL."""
    benchmark_url = os.getenv("FINSECAI_BENCHMARK_DATABASE_URL", "").strip()
    if not benchmark_url:
        raise DatabaseBoundaryError(
            "FINSECAI_BENCHMARK_DATABASE_URL must be set; refusing application database"
        )
    if benchmark_url == settings.database_url or urlsplit(benchmark_url).path.rsplit("/", 1)[-1] == "finsecai":
        raise DatabaseBoundaryError(
            "Benchmark database URL matches the application database; refusing to run"
        )
    return benchmark_url


def benchmark_session_factory():
    """Build a session factory only for an explicitly separate database."""
    url = isolated_database_url()
    parsed = urlsplit(url)
    if not parsed.scheme or not parsed.netloc:
        raise DatabaseBoundaryError("FINSECAI_BENCHMARK_DATABASE_URL is invalid")
    engine = create_engine(url, pool_pre_ping=True)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)
