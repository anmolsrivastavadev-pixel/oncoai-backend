from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from tests.conftest import Account


def iso(days: int) -> str:
    return (datetime.now(UTC) + timedelta(days=days)).isoformat()


def test_reminder_crud(client: TestClient, alice: Account, bob: Account) -> None:
    lesion = client.post("/api/v1/lesions/", headers=alice.headers, json={"label": "L", "body_location": "back"}).json()
    r = client.post(
        "/api/v1/reminders/",
        headers=alice.headers,
        json={"title": "Re-scan back spot", "kind": "rescan", "due_at": iso(28), "lesion_id": lesion["id"]},
    )
    assert r.status_code == 201
    reminder = r.json()
    assert set(reminder) == {"id", "title", "kind", "due_at", "done", "lesion_id", "appointment_id", "repeat_days"}
    assert reminder["done"] is False and reminder["lesion_id"] == lesion["id"]

    patched = client.patch(f"/api/v1/reminders/{reminder['id']}", headers=alice.headers, json={"title": "Updated", "done": True})
    assert patched.status_code == 200 and patched.json()["done"] is True and patched.json()["title"] == "Updated"

    assert client.patch(f"/api/v1/reminders/{reminder['id']}", headers=bob.headers, json={"done": False}).status_code == 404
    assert client.delete(f"/api/v1/reminders/{reminder['id']}", headers=bob.headers).status_code == 404
    assert client.delete(f"/api/v1/reminders/{reminder['id']}", headers=alice.headers).status_code == 204
    assert client.get("/api/v1/reminders", headers=alice.headers).json()["items"] == []


def test_recurring_reminder_rolls_forward(client: TestClient, alice: Account) -> None:
    due = datetime(2031, 3, 1, 9, 0, tzinfo=UTC)
    reminder = client.post(
        "/api/v1/reminders/",
        headers=alice.headers,
        json={"title": "Monthly self-check", "kind": "self_check", "due_at": due.isoformat(), "repeat_days": 30},
    ).json()
    client.patch(f"/api/v1/reminders/{reminder['id']}", headers=alice.headers, json={"done": True})
    items = client.get("/api/v1/reminders/", headers=alice.headers).json()["items"]
    pending = [i for i in items if not i["done"]]
    assert len(items) == 2 and len(pending) == 1
    assert pending[0]["due_at"] == (due + timedelta(days=30)).isoformat().replace("+00:00", "Z")


def test_reminder_validation(client: TestClient, alice: Account, bob: Account) -> None:
    base = {"title": "x", "due_at": iso(1)}
    assert client.post("/api/v1/reminders/", headers=alice.headers, json={**base, "kind": "nap"}).status_code == 422
    assert client.post(
        "/api/v1/reminders/", headers=alice.headers, json={**base, "kind": "custom", "repeat_days": 0}
    ).status_code == 422
    lesion = client.post("/api/v1/lesions/", headers=bob.headers, json={"label": "B", "body_location": "back"}).json()
    assert client.post(
        "/api/v1/reminders/", headers=alice.headers, json={**base, "kind": "rescan", "lesion_id": lesion["id"]}
    ).status_code == 404
