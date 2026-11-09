from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import DISCLAIMER, settings
from app.services.assistant import claude_provider, guardrails
from tests.conftest import Account, upload


def ask(client: TestClient, account: Account, text: str, **extra: Any) -> dict:
    r = client.post(
        "/api/v1/assistant/chat", headers=account.headers, json={"messages": [{"role": "user", "content": text}], **extra}
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_topics_listed(client: TestClient) -> None:
    items = client.get("/api/v1/assistant/topics").json()["items"]
    ids = {i["id"] for i in items}
    assert {"abcde-rule", "uv-protection", "self-exam", "dermatologist-visit", "understanding-results", "skin-types"} <= ids
    assert all(i["title"] and i["summary"] for i in items)


@pytest.mark.parametrize(
    ("question", "expected_title"),
    [
        ("What is the ABCDE rule?", "ABCDE"),
        ("what spf sunscreen should I use on holiday", "UV index"),
        ("how do I check my skin every month", "self-exam"),
        ("what is the ugly duckling sign", "ugly duckling"),
        ("which fitzpatrick skin type burns easily", "Fitzpatrick"),
        ("what happens at a dermatologist appointment", "dermatologist appointment"),
    ],
)
def test_knowledge_base_answers(client: TestClient, alice: Account, question: str, expected_title: str) -> None:
    body = ask(client, alice, question)
    assert body["provider"] == "knowledge_base"
    assert expected_title.lower() in body["reply"].lower()
    assert body["disclaimer"] == DISCLAIMER
    assert body["sources"] and all(s["url"].startswith("https://") for s in body["sources"])
    assert body["suggestions"]
    assert body["safety"] == {"redirected": False, "reason": None}


def test_unrelated_question_gets_intro(client: TestClient, alice: Account) -> None:
    body = ask(client, alice, "qwerty zxcvb")
    assert "educational assistant" in body["reply"] and body["suggestions"]


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("Do I have skin cancer?", guardrails.DIAGNOSIS),
        ("is this melanoma?", guardrails.DIAGNOSIS),
        ("Could my mole be cancerous", guardrails.DIAGNOSIS),
        ("Can you diagnose my spot", guardrails.DIAGNOSIS),
        ("What cream should I put on my mole? cream for my mole", guardrails.TREATMENT),
        ("What dosage of ibuprofen should I take?", guardrails.TREATMENT),
        ("how do I get rid of this spot", guardrails.TREATMENT),
        ("how can I remove my mole at home", guardrails.TREATMENT),
        ("My mole is bleeding and it won't stop", guardrails.URGENT),
        ("the spot is growing really fast", guardrails.URGENT),
        ("I want to kill myself", guardrails.SELF_HARM),
        ("I've been thinking about suicide", guardrails.SELF_HARM),
    ],
)
def test_input_guardrails(client: TestClient, alice: Account, text: str, reason: str) -> None:
    body = ask(client, alice, text)
    assert body["safety"] == {"redirected": True, "reason": reason}
    assert body["provider"] == "knowledge_base"
    assert body["disclaimer"] == DISCLAIMER
    assert not guardrails.output_violates(body["reply"])


def test_self_harm_response_has_crisis_lines(client: TestClient, alice: Account) -> None:
    reply = ask(client, alice, "I don't want to live anymore")["reply"]
    assert "988" in reply and "116 123" in reply and "emergency" in reply


def test_guardrails_run_before_model(client: TestClient, alice: Account, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "test-key")

    def fail(*_: Any, **__: Any) -> None:
        raise AssertionError("model must not be called for guarded input")

    monkeypatch.setattr(claude_provider, "_client", fail)
    assert ask(client, alice, "is this melanoma?")["safety"]["redirected"] is True


@pytest.mark.parametrize(
    "text",
    ["UV index 3 or above means protection", "Spots that change are worth checking with a dermatologist."],
)
def test_output_filter_allows_educational_text(text: str) -> None:
    assert not guardrails.output_violates(text)


@pytest.mark.parametrize(
    "text",
    [
        "You have melanoma.",
        "This is a benign mole, nothing to worry about.",
        "You should take 400 mg of ibuprofen.",
        "Apply imiquimod twice daily.",
        "You don't need to see a doctor.",
    ],
)
def test_output_filter_blocks_diagnostic_text(text: str) -> None:
    assert guardrails.output_violates(text)


class FakeMessages:
    def __init__(self, response: Any = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


def fake_client(monkeypatch: pytest.MonkeyPatch, messages: FakeMessages) -> None:
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "test-key")
    client = SimpleNamespace(beta=SimpleNamespace(messages=messages))
    monkeypatch.setattr(claude_provider, "_client", lambda: client)


def response(text: str, stop_reason: str = "end_turn") -> Any:
    return SimpleNamespace(
        stop_reason=stop_reason,
        model="claude-opus-5-5",
        content=[SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text=text)],
    )


def test_claude_provider_used_with_expected_parameters(
    client: TestClient, alice: Account, monkeypatch: pytest.MonkeyPatch, irregular_jpeg: bytes
) -> None:
    scan = upload(client, alice, irregular_jpeg)
    messages = FakeMessages(response("Use broad-spectrum SPF 30+ and reapply every two hours."))
    fake_client(monkeypatch, messages)
    body = client.post(
        "/api/v1/assistant/chat",
        headers=alice.headers,
        json={
            "messages": [
                {"role": "assistant", "content": "Hi! How can I help?"},
                {"role": "user", "content": "How should I use sunscreen?"},
            ],
            "context": {"scan_id": scan["id"]},
        },
    ).json()
    assert body["provider"] == "claude"
    assert body["reply"].startswith("Use broad-spectrum")
    assert body["disclaimer"] == DISCLAIMER and body["sources"]

    call = messages.calls[0]
    assert call["model"] == "claude-opus-5-5"
    assert call["max_tokens"] == 2048
    assert call["betas"] == ["server-side-fallback-2026-07-01"]
    assert call["fallbacks"] == "default"
    assert call["output_config"] == {"effort": "low"}
    assert "temperature" not in call and "top_p" not in call
    assert call["messages"] == [{"role": "user", "content": "How should I use sunscreen?"}]
    assert "Never diagnose" in call["system"]
    assert "Concern level: higher" in call["system"]
    assert "probabilit" not in call["system"].lower()


def test_claude_output_filtered(client: TestClient, alice: Account, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client(monkeypatch, FakeMessages(response("Based on your description you have melanoma.")))
    body = ask(client, alice, "Tell me about moles")
    assert body["safety"] == {"redirected": True, "reason": "output_filtered"}
    assert "melanoma" not in body["reply"].lower()
    assert body["provider"] == "knowledge_base"


def test_claude_refusal_falls_back_to_kb(client: TestClient, alice: Account, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client(monkeypatch, FakeMessages(response("", stop_reason="refusal")))
    body = ask(client, alice, "What is the ABCDE rule?")
    assert body["provider"] == "knowledge_base" and "ABCDE" in body["reply"]


def test_claude_errors_fall_back_to_kb(client: TestClient, alice: Account, monkeypatch: pytest.MonkeyPatch) -> None:
    import anthropic

    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    for error in (
        anthropic.APIConnectionError(request=request),
        anthropic.RateLimitError("slow down", response=httpx.Response(429, request=request), body=None),
        anthropic.InternalServerError("boom", response=httpx.Response(500, request=request), body=None),
    ):
        fake_client(monkeypatch, FakeMessages(error=error))
        body = ask(client, alice, "How do I read the UV index?")
        assert body["provider"] == "knowledge_base" and "UV index" in body["reply"]


def test_scan_context_must_be_owned(client: TestClient, alice: Account, bob: Account, regular_jpeg: bytes) -> None:
    scan = upload(client, bob, regular_jpeg)
    r = client.post(
        "/api/v1/assistant/chat",
        headers=alice.headers,
        json={"messages": [{"role": "user", "content": "explain"}], "context": {"scan_id": scan["id"]}},
    )
    assert r.status_code == 404


def test_scan_context_kb_answer(client: TestClient, alice: Account, regular_jpeg: bytes) -> None:
    scan = upload(client, alice, regular_jpeg)
    body = ask(client, alice, "what does this mean", context={"scan_id": scan["id"]})
    assert "OncoAI" in body["reply"] and body["safety"]["redirected"] is False


def test_chat_validation_and_auth(client: TestClient, alice: Account) -> None:
    assert client.post("/api/v1/assistant/chat", json={"messages": [{"role": "user", "content": "hi"}]}).status_code == 401
    assert client.post("/api/v1/assistant/chat", headers=alice.headers, json={"messages": []}).status_code == 422
    assert client.post(
        "/api/v1/assistant/chat", headers=alice.headers, json={"messages": [{"role": "system", "content": "x"}]}
    ).status_code == 422
