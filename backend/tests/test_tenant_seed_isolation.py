from app.db.models import EvidenceChunk, Tenant
from app.seed import ensure_evidence_seeded


def test_startup_evidence_seed_only_targets_demo_tenants(db_session, monkeypatch):
    demo = Tenant(name="Seed Demo", tenant_type="DEMO")
    customer = Tenant(name="Seed Customer", tenant_type="CUSTOMER")
    db_session.add_all([demo, customer])
    db_session.commit()

    monkeypatch.setattr("app.seed.embed_evidence_chunks", lambda db, chunks: 0)

    seeded = ensure_evidence_seeded(db_session)

    assert seeded == 1
    assert db_session.query(EvidenceChunk).filter_by(tenant_id=demo.id).count() > 0
    assert db_session.query(EvidenceChunk).filter_by(tenant_id=customer.id).count() == 0
