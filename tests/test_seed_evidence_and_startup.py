import logging
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.db.models import EvidenceChunk
from app.db.session import Base
from app.main import on_startup
from app.seed import seed_if_empty


@pytest.fixture()
def sqlite_session_factory():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    return SessionLocal


def test_seed_if_empty_creates_evidence_chunks(sqlite_session_factory):
    session = sqlite_session_factory()
    try:
        seed_if_empty(session)
        assert session.query(EvidenceChunk).count() == 9
        assert {row.source for row in session.query(EvidenceChunk).all()} == {"high", "medium", "low"}
    finally:
        session.close()


def test_startup_warns_when_seeding_disabled_and_db_empty(monkeypatch, caplog):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    import app.main as main_module

    monkeypatch.setattr(main_module, "engine", engine)
    monkeypatch.setattr(main_module, "SessionLocal", session_factory)
    monkeypatch.setattr(main_module.settings, "seed_demo_data", False)

    with caplog.at_level(logging.WARNING, logger="finsecai.startup"):
        on_startup()

    assert "SEED_DEMO_DATA is false" in caplog.text
    assert "Login will fail" in caplog.text
