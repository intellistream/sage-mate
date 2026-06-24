from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

from fastapi.testclient import TestClient

from sage_faculty_twin import api as api_module
from sage_faculty_twin.api import app
from sage_faculty_twin.models import ChatResponse, UserAccountResponse, UserSessionResponse
from sage_faculty_twin.slack_link_store import SlackUserLinkStore


client = TestClient(app)


def _slack_signature(body: bytes, secret: str) -> tuple[str, str]:
    timestamp = str(int(time.time()))
    base = b"v0:" + timestamp.encode("ascii") + b":" + body
    signature = "v0=" + hmac.new(secret.encode(), base, hashlib.sha256).hexdigest()
    return timestamp, signature


def _signed_headers(body: bytes, secret: str) -> dict[str, str]:
    timestamp, signature = _slack_signature(body, secret)
    return {
        "content-type": "application/x-www-form-urlencoded",
        "x-slack-request-timestamp": timestamp,
        "x-slack-signature": signature,
    }


def _signed_json_headers(body: bytes, secret: str) -> dict[str, str]:
    timestamp, signature = _slack_signature(body, secret)
    return {
        "content-type": "application/json",
        "x-slack-request-timestamp": timestamp,
        "x-slack-signature": signature,
    }


def _body(**overrides: str) -> bytes:
    payload = {
        "token": "legacy-token",
        "team_id": "T123",
        "team_domain": "intellistream",
        "channel_id": "D123",
        "channel_name": "directmessage",
        "user_id": "U013T91JDQT",
        "user_name": "shuhao",
        "command": "/twin",
        "text": "研究路线是什么？",
        "response_url": "https://hooks.slack.test/response",
    }
    payload.update(overrides)
    return urlencode(payload).encode()


def _event_body(**event_overrides: object) -> bytes:
    event = {
        "type": "message",
        "channel": "D123",
        "channel_type": "im",
        "user": "U013T91JDQT",
        "text": "研究路线是什么？",
        "ts": "1719200000.000100",
    }
    event.update(event_overrides)
    payload = {
        "type": "event_callback",
        "team_id": "T123",
        "api_app_id": "A123",
        "event": event,
        "event_id": "Ev123",
        "event_time": 1719200000,
    }
    return json.dumps(payload, ensure_ascii=False).encode()


def test_normalize_slack_twin_question():
    assert api_module._normalize_slack_twin_question("<@UAPP> 研究路线是什么？") == "研究路线是什么？"
    assert api_module._normalize_slack_twin_question("<@UAPP> <@UAPP2> 研究路线是什么？") == "研究路线是什么？"
    assert api_module._normalize_slack_twin_question("研究路线是什么？") == "研究路线是什么？"


def _session(visitor_profile: str) -> UserSessionResponse:
    return UserSessionResponse(
        is_authenticated=True,
        mode="user",
        account=UserAccountResponse(
            user_id=f"user-{visitor_profile}",
            name="Test User",
            email=f"{visitor_profile}@example.com",
            visitor_profile=visitor_profile,
            created_at="2026-06-23T00:00:00+00:00",
        ),
    )


def test_slack_twin_command_rejects_bad_signature(monkeypatch):
    monkeypatch.setattr(api_module, "SLACK_TWIN_SIGNING_SECRET", "secret")

    response = client.post(
        "/slack/commands/twin",
        data=_body(),
        headers={
            "content-type": "application/x-www-form-urlencoded",
            "x-slack-request-timestamp": str(int(time.time())),
            "x-slack-signature": "v0=bad",
        },
    )

    assert response.status_code == 401


def test_slack_twin_link_code_requires_lab_member(monkeypatch, tmp_path):
    monkeypatch.setattr(api_module, "slack_link_store", SlackUserLinkStore(tmp_path))
    monkeypatch.setattr(api_module.service, "get_user_session", lambda _token: _session("general_visitor"))

    response = client.post("/slack/twin-link/code")

    assert response.status_code == 200
    payload = response.json()
    assert payload["can_link"] is False
    assert payload["code"] is None
    assert "邀请码升级" in payload["message"]


def test_slack_twin_link_code_created_for_lab_member(monkeypatch, tmp_path):
    store = SlackUserLinkStore(tmp_path)
    monkeypatch.setattr(api_module, "slack_link_store", store)
    monkeypatch.setattr(api_module.service, "get_user_session", lambda _token: _session("lab_member"))

    response = client.post("/slack/twin-link/code")

    assert response.status_code == 200
    payload = response.json()
    assert payload["can_link"] is True
    assert len(payload["code"]) == 8
    assert store.consume_code(payload["code"], slack_user_id="UOTHER") is not None


def test_slack_twin_command_guides_unlinked_user(monkeypatch, tmp_path):
    secret = "secret"
    monkeypatch.setattr(api_module, "SLACK_TWIN_SIGNING_SECRET", secret)
    monkeypatch.setattr(api_module, "SLACK_TWIN_ALLOWED_USER_IDS", {"U013T91JDQT"})
    monkeypatch.setattr(api_module, "slack_link_store", SlackUserLinkStore(tmp_path))
    body = _body(user_id="UOTHER")

    response = client.post(
        "/slack/commands/twin",
        data=body,
        headers=_signed_headers(body, secret),
    )

    assert response.status_code == 200
    assert "生成 Slack 绑定码" in response.json()["text"]


def test_slack_twin_bind_invalid_code(monkeypatch, tmp_path):
    secret = "secret"
    monkeypatch.setattr(api_module, "SLACK_TWIN_SIGNING_SECRET", secret)
    monkeypatch.setattr(api_module, "SLACK_TWIN_ALLOWED_USER_IDS", {"U013T91JDQT"})
    monkeypatch.setattr(api_module, "slack_link_store", SlackUserLinkStore(tmp_path))
    body = _body(user_id="UOTHER", text="bind BADCODE")

    response = client.post(
        "/slack/commands/twin",
        data=body,
        headers=_signed_headers(body, secret),
    )

    assert response.status_code == 200
    assert "无效或已过期" in response.json()["text"]


def test_slack_twin_bind_code_success(monkeypatch, tmp_path):
    secret = "secret"
    store = SlackUserLinkStore(tmp_path)
    code = store.create_code(
        user_id="user-1",
        email="lab@example.com",
        visitor_profile="lab_member",
    )
    monkeypatch.setattr(api_module, "SLACK_TWIN_SIGNING_SECRET", secret)
    monkeypatch.setattr(api_module, "SLACK_TWIN_ALLOWED_USER_IDS", {"U013T91JDQT"})
    monkeypatch.setattr(api_module, "slack_link_store", store)
    body = _body(user_id="UOTHER", text=f"bind {code.code}")

    response = client.post(
        "/slack/commands/twin",
        data=body,
        headers=_signed_headers(body, secret),
    )

    assert response.status_code == 200
    assert "绑定成功" in response.json()["text"]
    assert store.get_link_for_slack_user("UOTHER").email == "lab@example.com"


def test_slack_twin_bound_non_lab_user_cannot_ask(monkeypatch, tmp_path):
    secret = "secret"
    store = SlackUserLinkStore(tmp_path)
    code = store.create_code(
        user_id="user-2",
        email="visitor@example.com",
        visitor_profile="general_visitor",
    )
    assert store.consume_code(code.code, slack_user_id="UOTHER") is not None
    monkeypatch.setattr(api_module, "SLACK_TWIN_SIGNING_SECRET", secret)
    monkeypatch.setattr(api_module, "SLACK_TWIN_ALLOWED_USER_IDS", {"U013T91JDQT"})
    monkeypatch.setattr(api_module, "slack_link_store", store)
    body = _body(user_id="UOTHER", text="研究路线是什么？")

    response = client.post(
        "/slack/commands/twin",
        data=body,
        headers=_signed_headers(body, secret),
    )

    assert response.status_code == 200
    assert "不是课题组成员" in response.json()["text"]


def test_slack_twin_bound_lab_member_can_ask(monkeypatch, tmp_path):
    secret = "secret"
    store = SlackUserLinkStore(tmp_path)
    code = store.create_code(
        user_id="user-3",
        email="lab@example.com",
        visitor_profile="lab_member",
    )
    assert store.consume_code(code.code, slack_user_id="UOTHER") is not None
    posted: list[tuple[str, str]] = []
    seen: list[tuple[str, str | None]] = []

    async def fake_answer(request):
        seen.append((request.visitor_profile, request.student_email))
        return ChatResponse(answer="绑定回答。", owner_name="张书豪", used_model="fake-model")

    def fake_post(response_url: str, text: str, *, response_type: str = "ephemeral") -> None:
        posted.append((response_url, text))

    monkeypatch.setattr(api_module, "SLACK_TWIN_SIGNING_SECRET", secret)
    monkeypatch.setattr(api_module, "SLACK_TWIN_ALLOWED_USER_IDS", {"U013T91JDQT"})
    monkeypatch.setattr(api_module, "slack_link_store", store)
    monkeypatch.setattr(api_module.service, "answer", fake_answer)
    monkeypatch.setattr(api_module, "_post_slack_response", fake_post)
    body = _body(user_id="UOTHER", text="研究路线是什么？")

    response = client.post(
        "/slack/commands/twin",
        data=body,
        headers=_signed_headers(body, secret),
    )

    assert response.status_code == 200
    assert seen == [("lab_member", "lab@example.com")]
    assert posted == [
        (
            "https://hooks.slack.test/response",
            "你问：研究路线是什么？\n绑定回答。\n\n模型：`fake-model`",
        )
    ]


def test_slack_twin_command_whitelist_answers_in_background(monkeypatch, tmp_path):
    secret = "secret"
    posted: list[tuple[str, str]] = []
    seen_questions: list[str] = []

    async def fake_answer(request):
        seen_questions.append(request.question)
        assert request.visitor_profile == "lab_member"
        return ChatResponse(answer="这是回答。", owner_name="张书豪", used_model="fake-model")

    def fake_post(response_url: str, text: str, *, response_type: str = "ephemeral") -> None:
        posted.append((response_url, text))

    monkeypatch.setattr(api_module, "SLACK_TWIN_SIGNING_SECRET", secret)
    monkeypatch.setattr(api_module, "SLACK_TWIN_ALLOWED_USER_IDS", {"U013T91JDQT"})
    monkeypatch.setattr(api_module, "slack_link_store", SlackUserLinkStore(tmp_path))
    monkeypatch.setattr(api_module, "SLACK_TWIN_VISITOR_PROFILE", "lab_member")
    monkeypatch.setattr(api_module.service, "answer", fake_answer)
    monkeypatch.setattr(api_module, "_post_slack_response", fake_post)
    body = _body(text="研究路线是什么？")

    response = client.post(
        "/slack/commands/twin",
        data=body,
        headers=_signed_headers(body, secret),
    )

    assert response.status_code == 200
    assert "正在问 twin" in response.json()["text"]
    assert "你问：研究路线是什么？" in response.json()["text"]
    assert seen_questions == ["研究路线是什么？"]
    assert posted == [
        (
            "https://hooks.slack.test/response",
            "你问：研究路线是什么？\n这是回答。\n\n模型：`fake-model`",
        )
    ]


def test_slack_twin_response_url_failure_does_not_break_background_task(
    monkeypatch, tmp_path
):
    secret = "secret"
    seen_questions: list[str] = []

    async def fake_answer(request):
        seen_questions.append(request.question)
        return ChatResponse(answer="这是回答。", owner_name="张书豪", used_model="fake-model")

    def failing_post(response_url: str, text: str, *, response_type: str = "ephemeral") -> None:
        raise OSError("response url unavailable")

    monkeypatch.setattr(api_module, "SLACK_TWIN_SIGNING_SECRET", secret)
    monkeypatch.setattr(api_module, "SLACK_TWIN_ALLOWED_USER_IDS", {"U013T91JDQT"})
    monkeypatch.setattr(api_module, "slack_link_store", SlackUserLinkStore(tmp_path))
    monkeypatch.setattr(api_module.service, "answer", fake_answer)
    monkeypatch.setattr(api_module, "_post_slack_response", failing_post)
    body = _body(text="研究路线是什么？")

    response = client.post(
        "/slack/commands/twin",
        data=body,
        headers=_signed_headers(body, secret),
    )

    assert response.status_code == 200
    assert "正在问 twin" in response.json()["text"]
    assert seen_questions == ["研究路线是什么？"]


def test_slack_events_url_verification(monkeypatch):
    secret = "secret"
    monkeypatch.setattr(api_module, "SLACK_TWIN_SIGNING_SECRET", secret)
    body = json.dumps({"type": "url_verification", "challenge": "abc123"}).encode()

    response = client.post(
        "/slack/events",
        data=body,
        headers=_signed_json_headers(body, secret),
    )

    assert response.status_code == 200
    assert response.json() == {"challenge": "abc123"}


def test_slack_events_bind_code_success(monkeypatch, tmp_path):
    secret = "secret"
    store = SlackUserLinkStore(tmp_path)
    code = store.create_code(
        user_id="user-1",
        email="lab@example.com",
        visitor_profile="lab_member",
    )
    posted: list[tuple[str, str, str | None]] = []

    def fake_post(channel_id: str, text: str, *, thread_ts: str | None = None) -> None:
        posted.append((channel_id, text, thread_ts))

    monkeypatch.setattr(api_module, "SLACK_TWIN_SIGNING_SECRET", secret)
    monkeypatch.setattr(api_module, "slack_link_store", store)
    monkeypatch.setattr(api_module, "_post_slack_message", fake_post)
    body = _event_body(user="UOTHER", text=f"bind {code.code}")

    response = client.post(
        "/slack/events",
        data=body,
        headers=_signed_json_headers(body, secret),
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert posted == [("D123", "绑定成功。以后可以直接输入 `/twin 你的问题`，或者直接给 twin 发私信。已绑定账号：lab@example.com", None)]


def test_slack_events_unlinked_user_gets_guidance(monkeypatch, tmp_path):
    secret = "secret"
    posted: list[tuple[str, str, str | None]] = []

    def fake_post(channel_id: str, text: str, *, thread_ts: str | None = None) -> None:
        posted.append((channel_id, text, thread_ts))

    monkeypatch.setattr(api_module, "SLACK_TWIN_SIGNING_SECRET", secret)
    monkeypatch.setattr(api_module, "SLACK_TWIN_ALLOWED_USER_IDS", {"U013T91JDQT"})
    monkeypatch.setattr(api_module, "slack_link_store", SlackUserLinkStore(tmp_path))
    monkeypatch.setattr(api_module, "_post_slack_message", fake_post)
    body = _event_body(user="UOTHER")

    response = client.post(
        "/slack/events",
        data=body,
        headers=_signed_json_headers(body, secret),
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert len(posted) == 1
    assert posted[0][0] == "D123"
    assert "生成 Slack 绑定码" in posted[0][1]


def test_slack_events_bound_lab_member_can_ask(monkeypatch, tmp_path):
    secret = "secret"
    store = SlackUserLinkStore(tmp_path)
    code = store.create_code(
        user_id="user-3",
        email="lab@example.com",
        visitor_profile="lab_member",
    )
    assert store.consume_code(code.code, slack_user_id="UOTHER") is not None
    posted: list[tuple[str, str, str | None]] = []
    seen: list[tuple[str, str | None, str]] = []

    async def fake_answer(request):
        seen.append((request.visitor_profile, request.student_email, request.course_context))
        return ChatResponse(answer="DM 回答。", owner_name="张书豪", used_model="fake-model")

    def fake_post(channel_id: str, text: str, *, thread_ts: str | None = None) -> None:
        posted.append((channel_id, text, thread_ts))

    monkeypatch.setattr(api_module, "SLACK_TWIN_SIGNING_SECRET", secret)
    monkeypatch.setattr(api_module, "SLACK_TWIN_ALLOWED_USER_IDS", {"U013T91JDQT"})
    monkeypatch.setattr(api_module, "slack_link_store", store)
    monkeypatch.setattr(api_module.service, "answer", fake_answer)
    monkeypatch.setattr(api_module, "_post_slack_message", fake_post)
    body = _event_body(user="UOTHER", text="这个课题组的研究路线和一般企业 R&D 有什么区别？")

    response = client.post(
        "/slack/events",
        data=body,
        headers=_signed_json_headers(body, secret),
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert seen == [("lab_member", "lab@example.com", "Slack DM")]
    assert posted == [
        (
            "D123",
            "你问：这个课题组的研究路线和一般企业 R&D 有什么区别？\nDM 回答。\n\n模型：`fake-model`",
            None,
        )
    ]


def test_slack_events_app_mention_without_question_shows_usage(monkeypatch, tmp_path):
    secret = "secret"
    posted: list[tuple[str, str, str | None]] = []

    def fake_post(channel_id: str, text: str, *, thread_ts: str | None = None) -> None:
        posted.append((channel_id, text, thread_ts))

    monkeypatch.setattr(api_module, "SLACK_TWIN_SIGNING_SECRET", secret)
    monkeypatch.setattr(api_module, "slack_link_store", SlackUserLinkStore(tmp_path))
    monkeypatch.setattr(api_module, "_post_slack_message", fake_post)
    body = _event_body(type="app_mention", channel_type="channel", text="<@UAPP>", ts="1719200000.000100")

    response = client.post(
        "/slack/events",
        data=body,
        headers=_signed_json_headers(body, secret),
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert posted == [(
        "D123",
        "用法：`@twin 你的问题`、`/twin 你的问题`，或者直接给 twin 发私信。",
        "1719200000.000100",
    )]


def test_slack_events_app_mention_bound_lab_member_replies_in_thread(monkeypatch, tmp_path):
    secret = "secret"
    store = SlackUserLinkStore(tmp_path)
    code = store.create_code(
        user_id="user-4",
        email="lab@example.com",
        visitor_profile="lab_member",
    )
    assert store.consume_code(code.code, slack_user_id="UOTHER") is not None
    posted: list[tuple[str, str, str | None]] = []
    seen: list[tuple[str, str | None, str, str]] = []

    async def fake_answer(request):
        seen.append((request.visitor_profile, request.student_email, request.course_context, request.question))
        return ChatResponse(answer="公开回答。", owner_name="张书豪", used_model="fake-model")

    def fake_post(channel_id: str, text: str, *, thread_ts: str | None = None) -> None:
        posted.append((channel_id, text, thread_ts))

    monkeypatch.setattr(api_module, "SLACK_TWIN_SIGNING_SECRET", secret)
    monkeypatch.setattr(api_module, "SLACK_TWIN_ALLOWED_USER_IDS", {"U013T91JDQT"})
    monkeypatch.setattr(api_module, "slack_link_store", store)
    monkeypatch.setattr(api_module.service, "answer", fake_answer)
    monkeypatch.setattr(api_module, "_post_slack_message", fake_post)
    body = _event_body(
        type="app_mention",
        channel_type="channel",
        user="UOTHER",
        text="<@UAPP> 这个课题组的研究路线和一般企业 R&D 有什么区别？",
        ts="1719200000.000100",
    )

    response = client.post(
        "/slack/events",
        data=body,
        headers=_signed_json_headers(body, secret),
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert seen == [(
        "lab_member",
        "lab@example.com",
        "Slack @twin",
        "这个课题组的研究路线和一般企业 R&D 有什么区别？",
    )]
    assert posted == [(
        "D123",
        "你问：这个课题组的研究路线和一般企业 R&D 有什么区别？\n公开回答。\n\n模型：`fake-model`",
        "1719200000.000100",
    )]
