from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Scan
from tests.conftest import Account, upload


def test_compare_two_scans(client: TestClient, alice: Account, regular_jpeg: bytes, irregular_jpeg: bytes) -> None:
    a = upload(client, alice, regular_jpeg)
    b = upload(client, alice, irregular_jpeg, lesion_id=str(a["lesion_id"]))
    r = client.get(f"/api/v1/tracking/compare?a={a['id']}&b={b['id']}", headers=alice.headers)
    assert r.status_code == 200
    body = r.json()
    assert body["a"]["id"] == a["id"] and body["b"]["id"] == b["id"]
    deltas = body["deltas"]
    assert set(deltas) == {"asymmetry", "border_irregularity", "color_variation", "diameter_relative", "concern_score"}
    assert deltas["concern_score"] == round(b["concern_score"] - a["concern_score"], 1)
    assert deltas["asymmetry"] > 0
    summary = body["summary"]
    assert "increased" in summary and "Consider professional dermatologist evaluation" in summary
    assert "not a diagnosis" in summary
    assert body["a"]["disclaimer"] and body["b"]["disclaimer"]


def test_compare_same_image_is_stable(client: TestClient, alice: Account, regular_jpeg: bytes) -> None:
    a = upload(client, alice, regular_jpeg)
    b = upload(client, alice, regular_jpeg, lesion_id=str(a["lesion_id"]))
    body = client.get(f"/api/v1/tracking/compare?a={a['id']}&b={b['id']}", headers=alice.headers).json()
    assert all(abs(v) < 1 for v in body["deltas"].values())
    assert "No large visual change" in body["summary"]


def test_compare_requires_ownership(client: TestClient, alice: Account, bob: Account, regular_jpeg: bytes) -> None:
    a = upload(client, alice, regular_jpeg)
    b = upload(client, bob, regular_jpeg)
    r = client.get(f"/api/v1/tracking/compare?a={a['id']}&b={b['id']}", headers=alice.headers)
    assert r.status_code == 404


def test_dashboard(client: TestClient, alice: Account, bob: Account, db: Session, regular_jpeg: bytes, irregular_jpeg: bytes) -> None:
    first = upload(client, alice, irregular_jpeg)
    upload(client, alice, regular_jpeg, lesion_id=str(first["lesion_id"]))  # latest for lesion 1 is low
    upload(client, alice, irregular_jpeg)  # lesion 2 higher
    upload(client, bob, irregular_jpeg)  # must not be counted
    # Backdate one scan to check daily bucketing.
    scan = db.get(Scan, first["id"])
    assert scan is not None
    scan.created_at = datetime.now(UTC) - timedelta(days=3)
    db.commit()
    client.post(
        "/api/v1/reminders/",
        headers=alice.headers,
        json={"title": "Re-scan", "kind": "rescan", "due_at": (datetime.now(UTC) + timedelta(days=2)).isoformat()},
    )

    body = client.get("/api/v1/tracking/dashboard", headers=alice.headers).json()
    assert body["totals"] == {"lesions": 2, "scans": 3, "upcoming_appointments": 0}
    assert body["concern_breakdown"] == {"low": 1, "moderate": 0, "higher": 1}
    assert len(body["scans_over_time"]) == 90
    assert body["scans_over_time"][-1]["date"] == datetime.now(UTC).date().isoformat()
    assert body["scans_over_time"][-1]["count"] == 2
    assert body["scans_over_time"][-4]["count"] == 1
    assert len(body["score_trend"]) == 3
    assert {"date", "lesion_id", "lesion_label", "concern_score"} <= set(body["score_trend"][0])
    assert len(body["recent_scans"]) == 3
    assert body["next_appointment"] is None
    assert [r["title"] for r in body["reminders"]] == ["Re-scan"]


def test_symptom_logs(client: TestClient, alice: Account, bob: Account) -> None:
    lesion = client.post("/api/v1/lesions/", headers=alice.headers, json={"label": "L", "body_location": "back"}).json()
    r = client.post(
        "/api/v1/tracking/symptoms",
        headers=alice.headers,
        json={"lesion_id": lesion["id"], "itching": True, "notes": "after gardening"},
    )
    assert r.status_code == 201
    log = r.json()
    assert log["itching"] is True and log["bleeding"] is False and log["lesion_id"] == lesion["id"]
    general = client.post("/api/v1/tracking/symptoms", headers=alice.headers, json={"new_spot": True})
    assert general.status_code == 201 and general.json()["lesion_id"] is None

    items = client.get("/api/v1/tracking/symptoms", headers=alice.headers).json()["items"]
    assert len(items) == 2
    assert client.get("/api/v1/tracking/symptoms", headers=bob.headers).json()["items"] == []
    foreign = client.post("/api/v1/tracking/symptoms", headers=bob.headers, json={"lesion_id": lesion["id"]})
    assert foreign.status_code == 404
