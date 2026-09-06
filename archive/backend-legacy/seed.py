import random

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models import EvidenceChunk, Incident, Tenant, User

_EVIDENCE_TEXT = {
    "high": "Prior confirmed fraud case involving account takeover and rapid fund transfer.",
    "medium": "Historical case with anomalous login geography, resolved as suspicious but unconfirmed.",
    "low": "Baseline reconnaissance activity, low correlation with confirmed fraud outcomes.",
}


def seed_if_empty(db: Session) -> None:
    if db.query(Tenant).count() > 0:
        return

    tenant = Tenant(name="Acme Corp", description="Financial services demo tenant")
    db.add(tenant)
    db.flush()

    db.add(
        User(
            email="analyst@acme.test",
            hashed_password=hash_password("demo"),
            role="analyst",
            tenant_id=tenant.id,
        )
    )
    db.add(
        User(
            email="admin@acme.test",
            hashed_password=hash_password("demo"),
            role="admin",
            tenant_id=tenant.id,
        )
    )

    for tier, text in _EVIDENCE_TEXT.items():
        for i in range(3):
            db.add(
                EvidenceChunk(
                    tenant_id=tenant.id,
                    source=tier,
                    framework_id=f"CASE-{tier.upper()}-{i}",
                    text=text,
                )
            )

    random.seed(42)
    for i in range(50):
        db.add(
            Incident(
                tenant_id=tenant.id,
                user_id=f"USER-{random.randint(1, 10):04d}",
                amount=round(random.expovariate(1 / 5000), 2),
                risk_score=round(random.uniform(0.05, 0.97), 3),
                anomaly_score=round(random.uniform(0, 1), 3),
                transaction_type=random.choice(["TRANSFER", "WITHDRAWAL", "DEPOSIT"]),
                device_id=f"DEV-{random.randint(1, 20):05d}",
            )
        )

    db.commit()
