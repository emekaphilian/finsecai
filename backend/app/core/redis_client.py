"""Lazy Redis support for opaque, rotating refresh tokens only."""

from __future__ import annotations

import json
import secrets
from datetime import timedelta

import redis

from app.core.config import settings

_client: redis.Redis | None = None
_REFRESH_KEY_PREFIX = "finsecai:refresh:"


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def store_refresh_token(email: str, ttl_days: int | None = None) -> str:
    token = secrets.token_urlsafe(48)
    ttl = timedelta(days=ttl_days if ttl_days is not None else settings.jwt_refresh_expire_days)
    get_redis().setex(f"{_REFRESH_KEY_PREFIX}{token}", ttl, json.dumps({"email": email}))
    return token


def consume_refresh_token(token: str) -> str | None:
    """Read and invalidate the token with Redis GETDEL, atomically."""
    raw = get_redis().getdel(f"{_REFRESH_KEY_PREFIX}{token}")
    if raw is None:
        return None
    try:
        return json.loads(raw)["email"]
    except (json.JSONDecodeError, KeyError):
        return None


def revoke_refresh_token(token: str) -> None:
    get_redis().delete(f"{_REFRESH_KEY_PREFIX}{token}")
