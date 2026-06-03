"""Regression tests for the /chat request budget guard.

Cloudflare's free/Pro tier enforces an ~100s edge timeout. The backend wraps
``service.answer`` in :func:`asyncio.wait_for` with a slightly smaller budget
(`CHAT_REQUEST_TIMEOUT_SECONDS`) so we can return a structured 504 *before*
the proxy gives up. These tests pin that contract.
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from sage_faculty_twin import api as api_module
from sage_faculty_twin.api import app, service

client = TestClient(app)


@pytest.fixture
def short_chat_budget(monkeypatch: pytest.MonkeyPatch) -> float:
    """Shrink the /chat budget so tests run in well under a second."""

    monkeypatch.setattr(api_module, "CHAT_REQUEST_TIMEOUT_SECONDS", 0.2)
    return 0.2


def test_chat_returns_504_when_service_exceeds_budget(
    short_chat_budget: float, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A slow ``service.answer`` triggers the ``asyncio.wait_for`` guard and
    returns HTTP 504 with the Chinese, user-friendly detail message."""

    async def slow_answer(*_args, **_kwargs):
        await asyncio.sleep(5.0)  # well above the 0.2s budget
        raise AssertionError("wait_for guard should have fired before this runs")

    monkeypatch.setattr(service, "answer", slow_answer)
    client.cookies.clear()

    response = client.post(
        "/chat",
        json={
            "student_name": "Alice",
            "student_email": "alice@example.com",
            "course_context": None,
            "conversation_id": "conv-timeout-test",
            "question": "请耐心等我一下。",
        },
    )

    assert response.status_code == 504
    detail = response.json().get("detail", "")
    assert "未完成响应" in detail
    assert "重试" in detail


def test_chat_with_request_id_publishes_timeout_to_workflow_stream(
    short_chat_budget: float, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When the caller supplies ``request_id``, a timeout must surface on the
    workflow-events SSE stream so the UI can render the 504 inline instead of
    leaving the rail spinning forever."""

    async def slow_answer(*_args, **_kwargs):
        await asyncio.sleep(5.0)
        raise AssertionError("wait_for guard should have fired before this runs")

    monkeypatch.setattr(service, "answer", slow_answer)

    published_errors: list[tuple[str, str]] = []
    real_publish_error = api_module.workflow_event_broker.publish_error

    def spy_publish_error(request_id: str, message: str) -> None:
        published_errors.append((request_id, message))
        real_publish_error(request_id, message)

    monkeypatch.setattr(api_module.workflow_event_broker, "publish_error", spy_publish_error)

    client.cookies.clear()

    response = client.post(
        "/chat?request_id=test-rid-timeout",
        json={
            "student_name": "Alice",
            "student_email": "alice@example.com",
            "course_context": None,
            "conversation_id": "conv-timeout-rid-test",
            "question": "请耐心等我一下。",
        },
    )

    assert response.status_code == 504
    assert any(
        rid == "test-rid-timeout" and "未完成响应" in msg for rid, msg in published_errors
    ), published_errors
