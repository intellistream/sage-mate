"""Tests for the /lucky-question endpoint and LLM question generation."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# LLM client: onboarding_step prompt integration
# ---------------------------------------------------------------------------


def test_generate_lucky_question_includes_onboarding_step_in_prompt() -> None:
    """When onboarding_step is provided, the system prompt must reference it."""
    from sage_faculty_twin.llm_client import VllmChatClient

    client = object.__new__(VllmChatClient)
    # Minimal stubs so we can inspect the prompt without a real server.
    client._intent_model_name = "test-model"
    client._intent_client = MagicMock()
    client._extract_json_object = MagicMock(return_value={
        "question": "你想研究什么问题？",
        "context": "七步提问法 · 问题定义",
    })

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"question": "test", "context": "test"}'}}]
    }
    mock_response.raise_for_status = MagicMock()
    client._intent_client.post.return_value = mock_response

    client._record_request_start = MagicMock()
    client._record_request_success = MagicMock()
    client._record_request_error = MagicMock()

    client.generate_lucky_question_sync(
        owner_name="张老师",
        owner_role="教授",
        visitor_profile="lab_member",
        onboarding_step="七步提问法 · 问题定义",
    )

    # Inspect the system prompt that was sent to the model
    call_args = client._intent_client.post.call_args
    payload = call_args[1]["json"] if "json" in call_args[1] else call_args[0][1]
    system_msg = payload["messages"][0]["content"]
    assert "七步提问法 · 问题定义" in system_msg
    assert "onboarding step" in system_msg.lower() or "七步提问法" in system_msg


def test_generate_lucky_question_without_onboarding_step_works() -> None:
    """Without onboarding_step, the prompt should not mention onboarding."""
    from sage_faculty_twin.llm_client import VllmChatClient

    client = object.__new__(VllmChatClient)
    client._intent_model_name = "test-model"
    client._intent_client = MagicMock()
    client._extract_json_object = MagicMock(return_value={
        "question": "张老师主要研究什么方向？",
        "context": "初次来访",
    })

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"question": "test", "context": "test"}'}}]
    }
    mock_response.raise_for_status = MagicMock()
    client._intent_client.post.return_value = mock_response

    client._record_request_start = MagicMock()
    client._record_request_success = MagicMock()
    client._record_request_error = MagicMock()

    client.generate_lucky_question_sync(
        owner_name="张老师",
        owner_role="教授",
        visitor_profile="general_visitor",
    )

    # Verify no onboarding hint in prompt
    call_args = client._intent_client.post.call_args
    payload = call_args[1]["json"] if "json" in call_args[1] else call_args[0][1]
    system_msg = payload["messages"][0]["content"]
    assert "onboarding step" not in system_msg.lower()


# ---------------------------------------------------------------------------
# Service layer: parameter passthrough
# ---------------------------------------------------------------------------


def test_service_passes_onboarding_step_to_llm_client() -> None:
    """The service layer must forward onboarding_step to the LLM client."""
    from sage_faculty_twin.service import DigitalTwinService

    # Use object.__new__ to skip __init__ (heavy setup)
    svc = object.__new__(DigitalTwinService)
    svc._settings = MagicMock()
    svc._settings.owner_name = "\u5f20\u8001\u5e08"
    svc._settings.owner_role = "\u6559\u6388"

    mock_llm = MagicMock()
    mock_llm.generate_lucky_question_sync.return_value = {
        "question": "\u6d4b\u8bd5\u95ee\u9898",
        "context": "\u6d4b\u8bd5",
    }
    svc._llm_client = mock_llm

    result = svc.generate_lucky_question(
        visitor_profile="lab_member",
        recent_questions=["\u95ee\u98981"],
        onboarding_step="\u4e03\u6b65\u63d0\u95ee\u6cd5 \u00b7 \u91cd\u8981\u6027",
    )

    mock_llm.generate_lucky_question_sync.assert_called_once_with(
        owner_name="\u5f20\u8001\u5e08",
        owner_role="\u6559\u6388",
        visitor_profile="lab_member",
        recent_questions=["\u95ee\u98981"],
        onboarding_step="\u4e03\u6b65\u63d0\u95ee\u6cd5 \u00b7 \u91cd\u8981\u6027",
    )
    assert result["question"] == "\u6d4b\u8bd5\u95ee\u9898"


def test_service_returns_empty_dict_on_llm_failure() -> None:
    """When the LLM client raises an exception, return empty dict for fallback."""
    from sage_faculty_twin.service import DigitalTwinService

    svc = object.__new__(DigitalTwinService)
    svc._settings = MagicMock()
    svc._settings.owner_name = "\u5f20\u8001\u5e08"
    svc._settings.owner_role = "\u6559\u6388"

    mock_llm = MagicMock()
    mock_llm.generate_lucky_question_sync.side_effect = RuntimeError("LLM down")
    svc._llm_client = mock_llm

    result = svc.generate_lucky_question(
        visitor_profile="general_visitor",
        onboarding_step="\u4e03\u6b65\u63d0\u95ee\u6cd5 \u00b7 \u95ee\u9898\u5b9a\u4e49",
    )
    assert result == {}


def test_service_returns_empty_dict_when_no_llm_client_method() -> None:
    """When the LLM client doesn't have generate_lucky_question_sync, return {}."""
    from sage_faculty_twin.service import DigitalTwinService

    svc = object.__new__(DigitalTwinService)
    svc._settings = MagicMock()
    svc._settings.owner_name = "\u5f20\u8001\u5e08"
    svc._settings.owner_role = "\u6559\u6388"
    svc._llm_client = object()  # No generate_lucky_question_sync method

    result = svc.generate_lucky_question(
        visitor_profile="general_visitor",
        onboarding_step="test step",
    )
    assert result == {}


# ---------------------------------------------------------------------------
# Frontend: JS contains the LLM-enhanced seed chip logic
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="enhanceSeedChipsWithLLM feature not yet implemented")
def test_frontend_seed_chips_call_enhance_with_llm() -> None:
    """The renderSeedChips function must call enhanceSeedChipsWithLLM."""
    from pathlib import Path

    app_js = Path(__file__).resolve().parent.parent / "src" / "sage_faculty_twin" / "web" / "app.js"
    content = app_js.read_text(encoding="utf-8")
    assert "enhanceSeedChipsWithLLM" in content
    assert "async function enhanceSeedChipsWithLLM" in content


def test_frontend_onboarding_random_btn_calls_lucky_question_api() -> None:
    """The onboarding random button handler must call /lucky-question."""
    from pathlib import Path

    app_js = Path(__file__).resolve().parent.parent / "src" / "sage_faculty_twin" / "web" / "app.js"
    content = app_js.read_text(encoding="utf-8")
    # The handler should include onboarding_step in the API URL
    assert "onboarding_step=" in content
    # And reference the lucky-question endpoint
    assert "/lucky-question?" in content


def test_frontend_onboarding_random_btn_has_static_fallback() -> None:
    """The onboarding handler must fall back to ONBOARDING_RESEARCH_EXAMPLES."""
    from pathlib import Path

    app_js = Path(__file__).resolve().parent.parent / "src" / "sage_faculty_twin" / "web" / "app.js"
    content = app_js.read_text(encoding="utf-8")
    assert "ONBOARDING_RESEARCH_EXAMPLES" in content
