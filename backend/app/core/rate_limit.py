"""Redis-backed, fixed-window request rate limiting.

The limiter intentionally fails open if Redis is unavailable: losing Redis
must not turn a transient infrastructure issue into a login or upload outage.
"""

from __future__ import annotations

import hashlib
import logging

import redis
from fastapi import HTTPException, Request, status

from app.core.redis_client import get_redis

logger = logging.getLogger("finsecai.rate_limit")
_PREFIX = "finsecai:ratelimit:"


def _key_part(value: str) -> str:
    """Keep Redis keys bounded and avoid retaining raw account identifiers."""
    return hashlib.sha256(value.strip().lower().encode()).hexdigest()


def _check_and_increment(key: str, limit: int, window_seconds: int) -> None:
    try:
        client = get_redis()
        redis_key = _PREFIX + key
        current = client.incr(redis_key)
        if current == 1:
            client.expire(redis_key, window_seconds)
        if current > limit:
            ttl = client.ttl(redis_key)
            retry_after = ttl if ttl and ttl > 0 else window_seconds
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                f"Rate limit exceeded. Try again in {retry_after}s.",
                headers={"Retry-After": str(retry_after)},
            )
    except redis.RedisError:
        logger.warning("Redis unavailable for rate limit key=%s; allowing request", key)


def client_ip(request: Request) -> str:
    # Do not trust X-Forwarded-For without a configured trusted-proxy policy.
    return request.client.host if request.client else "unknown"


def enforce_login_rate_limit(request: Request, username: str) -> None:
    _check_and_increment(f"login:ip:{_key_part(client_ip(request))}", 20, 300)
    _check_and_increment(f"login:user:{_key_part(username)}", 10, 900)


def enforce_upload_rate_limit(user_id: str) -> None:
    _check_and_increment(f"upload:{_key_part(user_id)}", 20, 3600)


def enforce_refresh_rate_limit(request: Request) -> None:
    _check_and_increment(f"refresh:ip:{_key_part(client_ip(request))}", 30, 300)
