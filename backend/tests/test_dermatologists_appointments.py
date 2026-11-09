from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Appointment, Dermatologist
from tests.conftest import Account


def next_weekday(days_ahead: int = 7) -> date:
    day = datetime.now(UTC).date() + timedelta(days=days_ahead)
    while day.weekday() >= 5:
        day += timedelta(days=1)
    return day


def next_weekend() -> date:
    day = datetime.now(UTC).date() + timedelta(days=1)
    while day.weekday() != 5:
        day += timedelta(days=1)
    return day


def derm_id(client: TestClient, account: Account, city: str = "London", accepting: bool = True) -> int:
    items = client.get(f"/api/v1/dermatologists?city={city}", headers=account.headers).json()["items"]
    return next(d["id"] for d in items if d["accepts_new_patients"] is accepting)


def book(client: TestClient, account: Account, derm: int, day: date, time: str = "10:00", **extra: object):  # noqa: ANN201
    return client.post(
        "/api/v1/appointments",
        headers=account.headers,
        json={"dermatologist_id": derm, "date": day.isoformat(), "time": time, "reason": "Skin check", **extra},
    )


def test_list_sample_dermatologists(client: TestClient, alice: Account) -> None:
    body = client.get("/api/v1/dermatologists", headers=alice.headers).json()
    assert body["total"] == 12
    assert all(d["is_sample"] for d in body["items"])
    assert all("(sample)" in d["clinic_name"] for d in body["items"])
    assert {d["city"] for d in body["items"]} >= {"London", "Mumbai", "New York"}
    first = body["items"][0]
    assert set(first) >= {
        "id", "name", "title", "specialty", "clinic_name", "city", "address", "phone", "rating",
        "review_count", "languages", "accepts_new_patients", "bio", "is_sample",
    }


@pytest.mark.parametrize(
    ("query", "expected"),
    [("city=london", 2), ("city=MUMBAI", 1), ("specialty=mole", 3), ("q=northside", 1), ("q=chennai", 1), ("q=zzz", 0)],
)
def test_search_dermatologists(client: TestClient, alice: Account, query: str, expected: int) -> None:
    assert client.get(f"/api/v1/dermatologists/?{query}", headers=alice.headers).json()["total"] == expected


def test_search_escapes_wildcards(client: TestClient, alice: Account) -> None:
    assert client.get("/api/v1/dermatologists?q=%25", headers=alice.headers).json()["total"] == 0


def test_dermatologist_pagination_limit(client: TestClient, alice: Account) -> None:
    assert client.get("/api/v1/dermatologists?limit=101", headers=alice.headers).status_code == 422
    page = client.get("/api/v1/dermatologists?limit=5&offset=10", headers=alice.headers).json()
    assert len(page["items"]) == 2 and page["total"] == 12


def test_get_dermatologist(client: TestClient, alice: Account) -> None:
    derm = derm_id(client, alice)
    assert client.get(f"/api/v1/dermatologists/{derm}", headers=alice.headers).json()["id"] == derm
    assert client.get("/api/v1/dermatologists/999999", headers=alice.headers).status_code == 404


def test_availability(client: TestClient, alice: Account) -> None:
    derm = derm_id(client, alice)
    day = next_weekday()
    body = client.get(f"/api/v1/dermatologists/{derm}/availability?date={day}", headers=alice.headers).json()
    assert body["date"] == day.isoformat()
    assert body["slots"][0] == "09:00" and body["slots"][-1] == "16:30" and len(body["slots"]) == 16
    weekend = client.get(f"/api/v1/dermatologists/{derm}/availability?date={next_weekend()}", headers=alice.headers)
    assert weekend.json()["slots"] == []
    past = client.get(f"/api/v1/dermatologists/{derm}/availability?date=2020-01-06", headers=alice.headers)
    assert past.json()["slots"] == []


def test_book_appointment_creates_reminder_and_blocks_slot(client: TestClient, alice: Account, bob: Account) -> None:
    derm = derm_id(client, alice)
    day = next_weekday()
    r = book(client, alice, derm, day, "10:00")
    assert r.status_code == 201, r.text
    appt = r.json()
    assert appt["status"] == "booked" and appt["dermatologist"]["id"] == derm and appt["scan_id"] is None
    scheduled = datetime.fromisoformat(appt["scheduled_at"].replace("Z", "+00:00"))
    assert appt["scheduled_at"].endswith("Z")

    reminders = client.get("/api/v1/reminders/", headers=alice.headers).json()["items"]
    assert len(reminders) == 1
    reminder = reminders[0]
    assert reminder["kind"] == "appointment" and reminder["appointment_id"] == appt["id"]
    due = datetime.fromisoformat(reminder["due_at"].replace("Z", "+00:00"))
    assert due == scheduled - timedelta(hours=24)

    slots = client.get(f"/api/v1/dermatologists/{derm}/availability?date={day}", headers=alice.headers).json()["slots"]
    assert "10:00" not in slots and len(slots) == 15

    conflict = book(client, bob, derm, day, "10:00")
    assert conflict.status_code == 409

    dashboard = client.get("/api/v1/tracking/dashboard", headers=alice.headers).json()
    assert dashboard["totals"]["upcoming_appointments"] == 1
    assert dashboard["next_appointment"]["id"] == appt["id"]


def test_slot_uses_clinic_local_time(client: TestClient, alice: Account) -> None:
    derm = derm_id(client, alice, city="Mumbai")
    appt = book(client, alice, derm, next_weekday(), "09:00").json()
    # 09:00 in Asia/Kolkata (UTC+05:30) is 03:30 UTC.
    assert appt["scheduled_at"].endswith("T03:30:00Z")


@pytest.mark.parametrize("time", ["08:30", "09:15", "17:00", "25:00"])
def test_book_invalid_times(client: TestClient, alice: Account, time: str) -> None:
    r = book(client, alice, derm_id(client, alice), next_weekday(), time)
    assert r.status_code == 422


def test_book_weekend_or_past_rejected(client: TestClient, alice: Account) -> None:
    derm = derm_id(client, alice)
    assert book(client, alice, derm, next_weekend()).status_code == 422
    assert book(client, alice, derm, date(2020, 1, 6)).status_code == 422


def test_book_not_accepting_new_patients(client: TestClient, alice: Account) -> None:
    derm = derm_id(client, alice, city="Edinburgh", accepting=False)
    assert book(client, alice, derm, next_weekday()).status_code == 422


def test_book_with_foreign_scan_404(client: TestClient, alice: Account, bob: Account, regular_jpeg: bytes) -> None:
    from tests.conftest import upload

    scan = upload(client, bob, regular_jpeg)
    assert book(client, alice, derm_id(client, alice), next_weekday(), scan_id=scan["id"]).status_code == 404
    own = upload(client, alice, regular_jpeg)
    ok = book(client, alice, derm_id(client, alice), next_weekday(), scan_id=own["id"])
    assert ok.status_code == 201 and ok.json()["scan_id"] == own["id"]


def test_reschedule(client: TestClient, alice: Account, bob: Account) -> None:
    derm = derm_id(client, alice)
    day = next_weekday()
    appt = book(client, alice, derm, day, "10:00").json()
    book(client, bob, derm, day, "11:00")

    taken = client.patch(f"/api/v1/appointments/{appt['id']}", headers=alice.headers, json={"time": "11:00"})
    assert taken.status_code == 409

    moved = client.patch(
        f"/api/v1/appointments/{appt['id']}", headers=alice.headers, json={"time": "14:30", "reason": "Follow-up"}
    )
    assert moved.status_code == 200
    body = moved.json()
    assert body["reason"] == "Follow-up" and body["scheduled_at"] != appt["scheduled_at"]
    reminder = client.get("/api/v1/reminders/", headers=alice.headers).json()["items"][0]
    expected_due = datetime.fromisoformat(body["scheduled_at"].replace("Z", "+00:00")) - timedelta(hours=24)
    assert datetime.fromisoformat(reminder["due_at"].replace("Z", "+00:00")) == expected_due

    slots = client.get(f"/api/v1/dermatologists/{derm}/availability?date={day}", headers=alice.headers).json()["slots"]
    assert "10:00" in slots and "14:30" not in slots

    # Rescheduling to the same slot it already holds is allowed.
    same = client.patch(f"/api/v1/appointments/{appt['id']}", headers=alice.headers, json={"time": "14:30"})
    assert same.status_code == 200


def test_cancel_frees_slot_and_removes_reminder(client: TestClient, alice: Account, bob: Account) -> None:
    derm = derm_id(client, alice)
    day = next_weekday()
    appt = book(client, alice, derm, day, "15:00").json()
    assert client.post(f"/api/v1/appointments/{appt['id']}/cancel", headers=bob.headers).status_code == 404
    r = client.post(f"/api/v1/appointments/{appt['id']}/cancel", headers=alice.headers)
    assert r.status_code == 200 and r.json()["status"] == "cancelled"
    assert client.get("/api/v1/reminders/", headers=alice.headers).json()["items"] == []
    assert book(client, bob, derm, day, "15:00").status_code == 201
    again = client.patch(f"/api/v1/appointments/{appt['id']}", headers=alice.headers, json={"time": "16:00"})
    assert again.status_code == 409


def test_list_appointments_by_status(client: TestClient, alice: Account, db: Session) -> None:
    derm = derm_id(client, alice)
    upcoming = book(client, alice, derm, next_weekday(), "09:30").json()
    cancelled = book(client, alice, derm, next_weekday(), "12:00").json()
    client.post(f"/api/v1/appointments/{cancelled['id']}/cancel", headers=alice.headers)
    old = db.get(Appointment, book(client, alice, derm, next_weekday(), "13:00").json()["id"])
    assert old is not None
    old.scheduled_at = datetime.now(UTC) - timedelta(days=30)
    old.status = "completed"
    db.commit()

    def ids(status: str) -> set[int]:
        return {a["id"] for a in client.get(f"/api/v1/appointments?status={status}", headers=alice.headers).json()["items"]}

    assert ids("upcoming") == {upcoming["id"]}
    assert ids("past") == {cancelled["id"], old.id}
    assert len(ids("all")) == 3
    assert client.get("/api/v1/appointments?status=soon", headers=alice.headers).status_code == 422


def test_database_enforces_unique_active_slot(db: Session, alice: Account) -> None:
    derm = db.query(Dermatologist).first()
    assert derm is not None
    when = datetime(2030, 1, 7, 10, 0, tzinfo=UTC)
    db.add(Appointment(user_id=alice.id, dermatologist_id=derm.id, scheduled_at=when, reason="a", status="cancelled"))
    db.add(Appointment(user_id=alice.id, dermatologist_id=derm.id, scheduled_at=when, reason="b", status="booked"))
    db.commit()  # a cancelled row does not block
    db.add(Appointment(user_id=alice.id, dermatologist_id=derm.id, scheduled_at=when, reason="c", status="booked"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
