from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.conftest import Account


def make_post(client: TestClient, account: Account, **overrides: object) -> dict:
    payload = {"title": "Sun safety tips", "body": "Reapply every two hours!", "topic": "prevention", **overrides}
    r = client.post("/api/v1/community/posts", headers=account.headers, json=payload)
    assert r.status_code == 201, r.text
    return r.json()


def test_create_and_list_posts(client: TestClient, alice: Account, bob: Account) -> None:
    post = make_post(client, alice)
    assert post["author"] == {"id": alice.id, "display_name": "Alice W."}
    assert post["is_mine"] is True and post["status"] == "visible"
    assert post["reactions"] == {"support": 0, "hug": 0, "strength": 0, "relate": 0}
    assert post["my_reactions"] == [] and post["comment_count"] == 0
    make_post(client, bob, topic="stories", title="My story")

    listing = client.get("/api/v1/community/posts", headers=bob.headers).json()
    assert listing["total"] == 2
    assert listing["items"][0]["title"] == "My story"
    assert listing["items"][1]["is_mine"] is False
    stories = client.get("/api/v1/community/posts?topic=stories", headers=bob.headers).json()
    assert stories["total"] == 1


def test_anonymous_post_hides_identity(client: TestClient, alice: Account, bob: Account) -> None:
    post = make_post(client, alice, anonymous=True)
    seen = client.get(f"/api/v1/community/posts/{post['id']}", headers=bob.headers).json()
    assert seen["author"] == {"id": None, "display_name": "Anonymous member"}
    assert "Alice" not in str(seen)
    mine = client.get(f"/api/v1/community/posts/{post['id']}", headers=alice.headers).json()
    assert mine["is_mine"] is True


@pytest.mark.parametrize(
    "body",
    [
        "Email me at jane.doe@example.com",
        "contact: jane (at) example (dot) com",
        "Call me on +44 7700 900123",
        "my number is 555-010-1234",
        "ring 07700900123",
    ],
)
def test_privacy_filter_rejects_contact_details(client: TestClient, alice: Account, body: str) -> None:
    r = client.post(
        "/api/v1/community/posts", headers=alice.headers, json={"title": "Hello", "body": body, "topic": "support"}
    )
    assert r.status_code == 422
    assert "email addresses or phone numbers" in r.json()["detail"]


def test_privacy_filter_allows_normal_numbers(client: TestClient, alice: Account) -> None:
    make_post(client, alice, body="I use SPF 50 and reapply every 2 hours since 2019-06-01.")


def test_profanity_is_masked(client: TestClient, alice: Account) -> None:
    post = make_post(client, alice, title="This shit is hard", body="Feeling like crap, but the bullshit fear passed.")
    assert post["title"] == "This s*** is hard"
    assert "b*******" in post["body"] and "crap" in post["body"]


def test_post_validation(client: TestClient, alice: Account) -> None:
    for payload in (
        {"title": "Hi", "body": "x", "topic": "support"},
        {"title": "Valid title", "body": "", "topic": "support"},
        {"title": "Valid title", "body": "x", "topic": "politics"},
        {"title": "Valid title", "body": "x" * 5001, "topic": "support"},
    ):
        assert client.post("/api/v1/community/posts", headers=alice.headers, json=payload).status_code == 422


def test_comments(client: TestClient, alice: Account, bob: Account) -> None:
    post = make_post(client, alice)
    r = client.post(f"/api/v1/community/posts/{post['id']}/comments", headers=bob.headers, json={"body": "Thanks!"})
    assert r.status_code == 201
    comment = r.json()
    assert comment["post_id"] == post["id"] and comment["author"]["display_name"] == "Bob S."
    anon = client.post(
        f"/api/v1/community/posts/{post['id']}/comments", headers=bob.headers, json={"body": "Me too", "anonymous": True}
    ).json()
    assert anon["author"]["id"] is None

    bad = client.post(
        f"/api/v1/community/posts/{post['id']}/comments", headers=bob.headers, json={"body": "mail bob@example.org"}
    )
    assert bad.status_code == 422

    detail = client.get(f"/api/v1/community/posts/{post['id']}", headers=alice.headers).json()
    assert detail["comment_count"] == 2 and [c["body"] for c in detail["comments"]] == ["Thanks!", "Me too"]

    assert client.delete(f"/api/v1/community/comments/{comment['id']}", headers=alice.headers).status_code == 403
    assert client.delete(f"/api/v1/community/comments/{comment['id']}", headers=bob.headers).status_code == 204
    detail = client.get(f"/api/v1/community/posts/{post['id']}", headers=alice.headers).json()
    assert detail["comment_count"] == 1


def test_reactions_toggle(client: TestClient, alice: Account, bob: Account) -> None:
    post = make_post(client, alice)
    url = f"/api/v1/community/posts/{post['id']}/reactions"
    first = client.post(url, headers=bob.headers, json={"kind": "hug"}).json()
    assert first == {"reactions": {"support": 0, "hug": 1, "strength": 0, "relate": 0}, "my_reactions": ["hug"]}
    client.post(url, headers=bob.headers, json={"kind": "support"})
    client.post(url, headers=alice.headers, json={"kind": "hug"})
    state = client.post(url, headers=bob.headers, json={"kind": "hug"}).json()  # toggle off
    assert state["reactions"]["hug"] == 1 and state["reactions"]["support"] == 1
    assert state["my_reactions"] == ["support"]
    assert client.post(url, headers=bob.headers, json={"kind": "like"}).status_code == 422
    listed = client.get("/api/v1/community/posts", headers=bob.headers).json()["items"][0]
    assert listed["my_reactions"] == ["support"]


def test_delete_post_permissions(client: TestClient, alice: Account, bob: Account, moderator: Account) -> None:
    post = make_post(client, alice)
    assert client.delete(f"/api/v1/community/posts/{post['id']}", headers=bob.headers).status_code == 403
    assert client.delete(f"/api/v1/community/posts/{post['id']}", headers=alice.headers).status_code == 204
    assert client.get(f"/api/v1/community/posts/{post['id']}", headers=alice.headers).status_code == 404

    other = make_post(client, bob)
    assert client.delete(f"/api/v1/community/posts/{other['id']}", headers=moderator.headers).status_code == 204
    assert client.get(f"/api/v1/community/posts/{other['id']}", headers=bob.headers).status_code == 404
    as_mod = client.get(f"/api/v1/community/posts/{other['id']}", headers=moderator.headers).json()
    assert as_mod["status"] == "removed"
    assert client.get("/api/v1/community/posts", headers=bob.headers).json()["total"] == 0


def test_reports_auto_hide_and_moderation(client: TestClient, alice: Account, moderator: Account, make_account) -> None:  # noqa: ANN001
    post = make_post(client, alice)
    reporters = [make_account() for _ in range(3)]
    assert client.post(f"/api/v1/community/posts/{post['id']}/report", headers=alice.headers, json={"reason": "x"}).status_code == 422

    first = client.post(f"/api/v1/community/posts/{post['id']}/report", headers=reporters[0].headers, json={"reason": "spam"})
    assert first.status_code == 201 and first.json()["status"] == "open"
    dup = client.post(f"/api/v1/community/posts/{post['id']}/report", headers=reporters[0].headers, json={"reason": "spam"})
    assert dup.json()["id"] == first.json()["id"]
    for account in reporters[1:]:
        client.post(f"/api/v1/community/posts/{post['id']}/report", headers=account.headers, json={"reason": "spam"})

    # Hidden from others pending review, still visible to its author (flagged under review).
    assert client.get(f"/api/v1/community/posts/{post['id']}", headers=reporters[0].headers).status_code == 404
    assert client.get("/api/v1/community/posts", headers=reporters[0].headers).json()["total"] == 0
    own = client.get(f"/api/v1/community/posts/{post['id']}", headers=alice.headers).json()
    assert own["under_review"] is True

    assert client.get("/api/v1/moderation/reports", headers=alice.headers).status_code == 403
    queue = client.get("/api/v1/moderation/reports?status=open", headers=moderator.headers).json()
    assert queue["total"] == 3
    item = queue["items"][0]
    assert item["target_type"] == "post" and item["post_id"] == post["id"] and item["open_report_count"] == 3

    resolved = client.post(
        f"/api/v1/moderation/reports/{item['id']}/resolve", headers=moderator.headers, json={"action": "dismiss"}
    )
    assert resolved.status_code == 200 and resolved.json()["status"] == "dismissed"
    assert client.get("/api/v1/moderation/reports", headers=moderator.headers).json()["total"] == 0
    assert client.get(f"/api/v1/community/posts/{post['id']}", headers=reporters[0].headers).status_code == 200


def test_comment_report_and_remove_content(client: TestClient, alice: Account, bob: Account, moderator: Account) -> None:
    post = make_post(client, alice)
    comment = client.post(f"/api/v1/community/posts/{post['id']}/comments", headers=bob.headers, json={"body": "rude"}).json()
    report = client.post(f"/api/v1/community/comments/{comment['id']}/report", headers=alice.headers, json={"reason": "rude"})
    assert report.status_code == 201
    queue = client.get("/api/v1/moderation/reports", headers=moderator.headers).json()["items"]
    assert queue[0]["target_type"] == "comment" and queue[0]["comment_id"] == comment["id"]
    r = client.post(
        f"/api/v1/moderation/reports/{report.json()['id']}/resolve",
        headers=moderator.headers,
        json={"action": "remove_content"},
    )
    assert r.json()["status"] == "actioned"
    detail = client.get(f"/api/v1/community/posts/{post['id']}", headers=alice.headers).json()
    assert detail["comments"] == [] and detail["comment_count"] == 0
    assert client.post(
        "/api/v1/moderation/reports/999999/resolve", headers=moderator.headers, json={"action": "dismiss"}
    ).status_code == 404
    assert client.post(
        f"/api/v1/moderation/reports/{report.json()['id']}/resolve", headers=moderator.headers, json={"action": "ban"}
    ).status_code == 422
