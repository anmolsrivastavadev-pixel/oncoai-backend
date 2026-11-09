from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import create_token
from tests.conftest import Account, upload


def test_register_returns_token_pair(client: TestClient) -> None:
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "New@Example.com", "password": "abcdefg1", "full_name": "  New Person "},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]
    assert body["user"]["email"] == "new@example.com"
    assert body["user"]["full_name"] == "New Person"
    assert body["user"]["role"] == "user"
    assert body["user"]["created_at"].endswith("Z")
    assert "hashed_password" not in body["user"]


def test_register_duplicate_email_conflict(client: TestClient, alice: Account) -> None:
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "ALICE@example.com", "password": "abcdefg1", "full_name": "Dup"},
    )
    assert r.status_code == 409


@pytest.mark.parametrize("password", ["short1", "allletters", "12345678"])
def test_register_rejects_weak_passwords(client: TestClient, password: str) -> None:
    r = client.post(
        "/api/v1/auth/register", json={"email": "w@example.com", "password": password, "full_name": "W"}
    )
    assert r.status_code == 422


def test_login_success_and_failures(client: TestClient, alice: Account) -> None:
    ok = client.post("/api/v1/auth/login", json={"email": alice.email, "password": alice.password})
    assert ok.status_code == 200 and ok.json()["user"]["id"] == alice.id

    bad = client.post("/api/v1/auth/login", json={"email": alice.email, "password": "wrongpass1"})
    assert bad.status_code == 401
    assert bad.headers["www-authenticate"] == "Bearer"

    unknown = client.post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": "x1234567"})
    assert unknown.status_code == 401


def test_refresh_flow(client: TestClient, alice: Account) -> None:
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": alice.refresh})
    assert r.status_code == 200
    me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {r.json()['access_token']}"})
    assert me.status_code == 200


def test_refresh_rejects_access_token(client: TestClient, alice: Account) -> None:
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": alice.token})
    assert r.status_code == 401


def test_access_requires_access_token_type(client: TestClient, alice: Account) -> None:
    r = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {alice.refresh}"})
    assert r.status_code == 401


@pytest.mark.parametrize("header", [None, "Bearer garbage", "Basic abc"])
def test_protected_route_rejects_missing_or_bad_token(client: TestClient, header: str | None) -> None:
    headers = {"Authorization": header} if header else {}
    r = client.get("/api/v1/users/me", headers=headers)
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == "Bearer"


def test_token_for_deleted_user_rejected(client: TestClient) -> None:
    token = create_token(999999, "access")
    r = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_login_rate_limited(client: TestClient, alice: Account, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    codes = [
        client.post("/api/v1/auth/login", json={"email": alice.email, "password": "wrongpass1"}).status_code
        for _ in range(6)
    ]
    assert codes[:5] == [401] * 5
    assert codes[5] == 429


def test_update_profile(client: TestClient, alice: Account) -> None:
    r = client.patch(
        "/api/v1/users/me",
        headers=alice.headers,
        json={"skin_type": "III", "date_of_birth": "1990-04-02", "location": "Leeds", "bio": "Hi"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["skin_type"] == "III" and body["date_of_birth"] == "1990-04-02"
    assert body["location"] == "Leeds"


@pytest.mark.parametrize(
    "payload", [{"skin_type": "VII"}, {"date_of_birth": "2999-01-01"}, {"full_name": ""}]
)
def test_update_profile_validation(client: TestClient, alice: Account, payload: dict) -> None:
    assert client.patch("/api/v1/users/me", headers=alice.headers, json=payload).status_code == 422


def test_change_password(client: TestClient, alice: Account) -> None:
    wrong = client.post(
        "/api/v1/users/me/password",
        headers=alice.headers,
        json={"current_password": "nope12345", "new_password": "NewPassw0rd"},
    )
    assert wrong.status_code == 400
    ok = client.post(
        "/api/v1/users/me/password",
        headers=alice.headers,
        json={"current_password": alice.password, "new_password": "NewPassw0rd"},
    )
    assert ok.status_code == 204
    assert client.post("/api/v1/auth/login", json={"email": alice.email, "password": "NewPassw0rd"}).status_code == 200


def test_delete_account_removes_data_and_images(client: TestClient, alice: Account, regular_jpeg: bytes) -> None:
    upload(client, alice, regular_jpeg)
    user_dir = settings.UPLOAD_DIR / str(alice.id)
    assert any(user_dir.iterdir())
    assert client.delete("/api/v1/users/me", headers=alice.headers).status_code == 204
    assert not user_dir.exists()
    assert client.post("/api/v1/auth/login", json={"email": alice.email, "password": alice.password}).status_code == 401
