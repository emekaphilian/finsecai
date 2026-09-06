"""Safe utility to remove diagnostic TEST-001 evidence rows.

Deletes EvidenceChunk rows where framework_id == 'TEST-001' and source == 'test'.
This script is intentionally conservative: it lists candidates, requires
confirmation (use --yes to skip prompt), and accepts an optional
--tenant argument to scope deletion to a specific tenant.

Usage (dry-run/list):
  python backend/scripts/delete_test_evidence.py --tenant <TENANT_ID>

To delete without prompt:
  python backend/scripts/delete_test_evidence.py --tenant <TENANT_ID> --yes
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from app.db.session import SessionLocal
from app.db.models import EvidenceChunk


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Delete diagnostic TEST-001 evidence rows (safe)")
    p.add_argument("--tenant", dest="tenant_id", default=None, help="Tenant ID to scope deletion (optional)")
    p.add_argument("--yes", dest="yes", action="store_true", help="Confirm deletion without prompting")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    session = SessionLocal()
    try:
        q = session.query(EvidenceChunk).filter(
            EvidenceChunk.framework_id == "TEST-001",
            EvidenceChunk.source == "test",
        )
        if args.tenant_id:
            q = q.filter(EvidenceChunk.tenant_id == args.tenant_id)

        rows = q.order_by(EvidenceChunk.id).all()

        if not rows:
            print("No matching TEST-001/test evidence rows found.")
            return 0

        print(f"Found {len(rows)} candidate rows to delete:")
        for r in rows:
            md = dict(r.metadata_json or {})
            print(
                f"- id={r.id} tenant={r.tenant_id} framework={r.framework_id} source={r.source} "
                f"embedding_status={md.get('embedding_status')} embedded_at={r.embedded_at} embedding_model={r.embedding_model}"
            )

        if not args.yes:
            resp = input("Proceed to delete these rows? Type 'delete' to confirm: ")
            if resp.strip() != "delete":
                print("Aborting — no rows were deleted.")
                return 1

        # Perform deletion in a transaction
        try:
            deleted = 0
            for r in rows:
                session.delete(r)
                deleted += 1
            session.commit()
            print(f"Deleted {deleted} rows.")
            return 0
        except Exception as exc:
            session.rollback()
            print(f"Error during deletion: {exc}", file=sys.stderr)
            return 2
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
