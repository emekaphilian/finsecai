import json
from pathlib import Path
from datetime import datetime, timezone
import hashlib

prod_meta = Path("backend/artifacts/production_model.json")
meta = json.loads(prod_meta.read_text())

registry_dir = Path("backend/artifacts/registry")
registry_dir.mkdir(parents=True, exist_ok=True)

def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''): h.update(chunk)
    return h.hexdigest()

candidate_record = {
    "version_id": meta["active_version"],
    "status": "CANDIDATE - REQUIRES VALIDATION",
    "previous_status": "PROMOTED_VIA_SCRIPT_NO_GOVERNANCE",
    "promoted_by": meta["promoted_by"],
    "promoted_at": meta["promoted_at"],
    "metrics_reported_at_0.5": meta["metrics"],
    "record_count": 7237967,
    "fraud_count": 29368,
    "fraud_rate": 29368/7237967,
    "datasets": {
        "ieee": {"rows": 590540, "frauds": 20663},
        "paysim": {"rows": 6362620, "frauds": 8213},
        "creditcard": {"rows": 284807, "frauds": 492}
    },
    "model_sha256": sha256("backend/artifacts/production/model.joblib"),
    "encoders_sha256": sha256("backend/artifacts/production/encoders.joblib"),
    "issues": ["precision 2.8% at 0.5, threshold 0.92 unvalidated, encoders fitted on full data leakage"]
}

(registry_dir / f"{meta['active_version']}_CANDIDATE.json").write_text(json.dumps(candidate_record, indent=2))

# Deactivate production
deactivated = {
    "active_version": None,
    "previous_active_version": meta["active_version"],
    "status": "NO_ACTIVE_PRODUCTION_MODEL - CANDIDATE_UNDER_REVIEW",
    "candidate_under_review": meta["active_version"],
    "deactivated_at": datetime.now(timezone.utc).isoformat()
}
prod_meta.write_text(json.dumps(deactivated, indent=2))

print(f"DOWNGRADED {meta['active_version']} TO CANDIDATE")
print(f"Model SHA256: {candidate_record['model_sha256'][:16]}...")
print(f"Encoders SHA256: {candidate_record['encoders_sha256'][:16]}...")
