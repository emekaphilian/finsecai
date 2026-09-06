"""AML record-retention guardrails.

The Nigerian Money Laundering (Prevention and Prohibition) Act 2022 requires
AML records to be retained for at least five years. This module enforces that
minimum; it deliberately does not automatically purge older records.
"""

from datetime import datetime, timedelta, timezone

from app.core.config import settings


class RetentionViolation(Exception):
    """Raised when deletion is attempted during the mandatory retention period."""


def is_within_retention_period(created_at: datetime) -> bool:
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(days=365 * settings.audit_retention_years)
    return created_at >= cutoff


def assert_deletable(created_at: datetime, record_description: str = "record") -> None:
    if is_within_retention_period(created_at):
        raise RetentionViolation(
            f"Cannot delete this {record_description}: it is within the mandatory "
            f"{settings.audit_retention_years}-year AML retention period."
        )
