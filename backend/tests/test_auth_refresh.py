import json


class MemoryRedis:
    """Small Redis protocol double; GETDEL mirrors atomic token consumption."""

    def __init__(self):
        self.data = {}

    def setex(self, key, _ttl, value):
        self.data[key] = value

    def getdel(self, key):
        return self.data.pop(key, None)

    def delete(self, key):
        self.data.pop(key, None)

    def incr(self, key):
        self.data[key] = int(self.data.get(key, 0)) + 1
        return self.data[key]

    def expire(self, _key, _seconds):
        pass

    def ttl(self, _key):
        return 60


def test_refresh_token_rotation_and_logout(client, db_session, monkeypatch):
    from app.core.redis_client import _REFRESH_KEY_PREFIX
    import app.core.redis_client as redis_client
    from app.core.security import hash_password
    from app.db.models import Tenant, User

    memory_redis = MemoryRedis()
    monkeypatch.setattr(redis_client, "_client", memory_redis)

    tenant = Tenant(name="Refresh Tenant")
    db_session.add(tenant)
    db_session.flush()
    db_session.add(User(
        email="refresh@example.com",
        hashed_password=hash_password("securepass"),
        tenant_id=tenant.id,
        role="analyst",
    ))
    db_session.commit()

    wrong_password = client.post(
        "/auth/login", data={"username": "refresh@example.com", "password": "wrong"})
    assert wrong_password.status_code == 401

    login = client.post(
        "/auth/login", data={"username": "refresh@example.com", "password": "securepass"})
    assert login.status_code == 200
    first_refresh = login.json()["refresh_token"]
    assert first_refresh
    assert json.loads(memory_redis.data[_REFRESH_KEY_PREFIX + first_refresh])["email"] == "refresh@example.com"

    refresh = client.post("/auth/refresh", json={"refresh_token": first_refresh})
    assert refresh.status_code == 200
    second_refresh = refresh.json()["refresh_token"]
    assert second_refresh and second_refresh != first_refresh

    reused = client.post("/auth/refresh", json={"refresh_token": first_refresh})
    assert reused.status_code == 401

    logout = client.post("/auth/logout", json={"refresh_token": second_refresh})
    assert logout.status_code == 200
    revoked = client.post("/auth/refresh", json={"refresh_token": second_refresh})
    assert revoked.status_code == 401
