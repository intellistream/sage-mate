import json
import threading
from collections import OrderedDict
from pathlib import Path

import httpx
import pytest

from sage_faculty_twin.benchmark_adapter import (
    build_lamp_request,
    load_local_lamp_scenarios,
)
from sage_faculty_twin.config import AppSettings
from sage_faculty_twin.llm_client import VllmChatClient
from sage_faculty_twin.models import InteractionIntent


def test_normalize_interaction_intent_for_explicit_teaching_question() -> None:
    client = object.__new__(VllmChatClient)
    raw_intent = InteractionIntent(
        action="answer",
        domain="research",
        retrieval_scopes=["publications"],
        exclude_scopes=["courseware"],
        confidence=0.4,
    )

    normalized = client._normalize_interaction_intent(
        "第 7 讲 发表高水平论文讲什么？",
        None,
        raw_intent,
    )

    assert normalized.action == "answer"
    assert normalized.domain == "teaching"
    assert normalized.retrieval_scopes == ["courseware"]
    assert normalized.exclude_scopes == ["publications"]


def test_normalize_interaction_intent_for_course_question_logistics() -> None:
    client = object.__new__(VllmChatClient)
    raw_intent = InteractionIntent(
        action="ask_followup",
        domain="general",
        retrieval_scopes=[],
        exclude_scopes=[],
        needs_clarification=True,
        clarification_message="你是想问课程内容还是沟通方式？",
        confidence=0.4,
    )

    normalized = client._normalize_interaction_intent(
        "结合我的情况，我下次问课上问题时应该先整理哪几类信息？作业里端到端性能分析不清楚，而且问题比较碎。",
        "LaMP personalization benchmark",
        raw_intent,
    )

    assert normalized.action == "answer"
    assert normalized.domain == "teaching"
    assert normalized.needs_clarification is False
    assert normalized.retrieval_scopes == ["courseware"]
    assert normalized.exclude_scopes == ["publications"]


def test_normalize_interaction_intent_for_explicit_booking_request() -> None:
    client = object.__new__(VllmChatClient)
    raw_intent = InteractionIntent(
        action="answer",
        domain="research",
        retrieval_scopes=["publications", "profile"],
        exclude_scopes=["courseware"],
        confidence=0.5,
    )

    normalized = client._normalize_interaction_intent(
        "请帮我预约 2026-05-26 15:00 讨论论文进展",
        "科研指导",
        raw_intent,
    )

    assert normalized.action == "book_meeting"
    assert normalized.domain == "booking"
    assert normalized.retrieval_scopes == ["meeting_policy"]
    assert normalized.exclude_scopes == ["courseware", "publications"]


def test_normalize_interaction_intent_for_preparation_question() -> None:
    client = object.__new__(VllmChatClient)
    raw_intent = InteractionIntent(
        action="ask_followup",
        domain="advising",
        retrieval_scopes=["preparation"],
        exclude_scopes=["courseware"],
        needs_clarification=True,
        clarification_message="你是想问研究方向还是预约流程？",
        confidence=0.6,
    )

    normalized = client._normalize_interaction_intent(
        "和老师约时间前，我应该先准备什么？",
        "科研指导",
        raw_intent,
    )

    assert normalized.action == "answer"
    assert normalized.domain == "advising"
    assert normalized.needs_clarification is False
    assert normalized.retrieval_scopes == ["preparation", "meeting_policy", "profile"]


def test_normalize_interaction_intent_for_office_hour_information_query() -> None:
    client = object.__new__(VllmChatClient)
    raw_intent = InteractionIntent(
        action="book_meeting",
        domain="booking",
        retrieval_scopes=["meeting_policy"],
        exclude_scopes=["courseware", "publications"],
        decision_mode="review_queue",
        confidence=0.7,
    )

    normalized = client._normalize_interaction_intent(
        "能否告诉我张老师这周的 office hours？我想了解以便预约。",
        "科研指导",
        raw_intent,
    )

    assert normalized.action == "answer"
    assert normalized.domain == "advising"
    assert normalized.decision_mode == "direct_answer"
    assert normalized.retrieval_scopes == ["meeting_policy", "profile"]
    assert normalized.exclude_scopes == ["courseware"]


def test_normalize_interaction_intent_for_project_scoping_guidance() -> None:
    client = object.__new__(VllmChatClient)
    raw_intent = InteractionIntent(
        action="ask_followup",
        domain="general",
        retrieval_scopes=[],
        exclude_scopes=[],
        needs_clarification=True,
        clarification_message="请先说明是哪一类项目。",
        confidence=0.45,
    )

    normalized = client._normalize_interaction_intent(
        "老师，我现在想做一个跟推理系统有关的项目。如果题目太大，您一般会建议怎么收窄？",
        "科研指导",
        raw_intent,
    )

    assert normalized.action == "answer"
    assert normalized.domain == "advising"
    assert normalized.decision_mode == "advise_only"
    assert normalized.needs_clarification is False


def test_normalize_interaction_intent_for_draft_preparation_question() -> None:
    client = object.__new__(VllmChatClient)
    raw_intent = InteractionIntent(
        action="book_meeting",
        domain="booking",
        retrieval_scopes=["meeting_policy"],
        exclude_scopes=["courseware", "publications"],
        decision_mode="review_queue",
        confidence=0.55,
    )

    normalized = client._normalize_interaction_intent(
        "老师，我下周想带一个初稿来请您看。在您看之前，我自己最好先整理哪些信息，能让反馈更集中？",
        "科研指导",
        raw_intent,
    )

    assert normalized.action == "answer"
    assert normalized.domain == "advising"
    assert normalized.decision_mode == "advise_only"
    assert normalized.needs_clarification is False


def test_normalize_interaction_intent_for_email_vs_meeting_boundary_question() -> None:
    client = object.__new__(VllmChatClient)
    raw_intent = InteractionIntent(
        action="book_meeting",
        domain="booking",
        retrieval_scopes=["meeting_policy"],
        exclude_scopes=["courseware", "publications"],
        confidence=0.5,
    )

    normalized = client._normalize_interaction_intent(
        "老师，如果只是两个比较具体的小问题，您会更希望我直接发邮件，还是等有更多内容再约时间？",
        "科研指导",
        raw_intent,
    )

    assert normalized.action == "answer"
    assert normalized.domain == "advising"
    assert normalized.decision_mode == "advise_only"
    assert normalized.needs_clarification is False


def test_normalize_interaction_intent_for_mixed_course_research_boundary_question() -> None:
    client = object.__new__(VllmChatClient)
    raw_intent = InteractionIntent(
        action="ask_followup",
        domain="general",
        retrieval_scopes=[],
        exclude_scopes=[],
        needs_clarification=True,
        clarification_message="你是想问课程还是研究？",
        confidence=0.4,
    )

    normalized = client._normalize_interaction_intent(
        "老师，我既想问课程作业，也想顺便聊下研究。这种情况您一般建议一次都问完，还是分开准备？",
        "科研指导",
        raw_intent,
    )

    assert normalized.action == "answer"
    assert normalized.domain == "advising"
    assert normalized.decision_mode == "advise_only"
    assert normalized.needs_clarification is False


def test_normalize_interaction_intent_for_progress_followup_lamp_question() -> None:
    client = object.__new__(VllmChatClient)
    scenario = next(
        item
        for item in load_local_lamp_scenarios(
            Path("tests/data/lamp_personalization_weak_subset.json")
        )
        if item.scenario_id == "memory-followup-personalization"
    )
    request = build_lamp_request(scenario, task_name=scenario.task_name)
    raw_intent = InteractionIntent(
        action="ask_followup",
        domain="general",
        retrieval_scopes=[],
        exclude_scopes=[],
        needs_clarification=True,
        clarification_message="你是想发邮件还是补实验？",
        confidence=0.4,
    )

    normalized = client._normalize_interaction_intent(
        request.question,
        request.course_context,
        raw_intent,
    )

    assert normalized.action == "answer"
    assert normalized.domain == "advising"
    assert normalized.decision_mode == "advise_only"
    assert normalized.needs_clarification is False


def test_coerce_interaction_intent_uses_internal_confidence_policy() -> None:
    client = object.__new__(VllmChatClient)
    payload = client._parse_interaction_intent_payload(
        """
        {
            "action": "book_meeting",
            "domain": "booking",
            "retrieval_scopes": ["meeting_policy"],
            "exclude_scopes": ["courseware"],
            "decision_mode": "review_queue",
            "needs_clarification": false,
            "clarification_message": null,
            "escalation_reason": null,
            "confidence": "high"
        }
        """
    )

    intent = client._coerce_interaction_intent(payload)

    assert intent.action == "book_meeting"
    assert intent.domain == "booking"
    assert intent.confidence == 0.85


def test_parse_interaction_intent_payload_repairs_invalid_shape() -> None:
    client = object.__new__(VllmChatClient)
    repair_calls: list[tuple[str, str]] = []

    def answer_question_sync(
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.2,
        max_tokens: int | None = 256,
    ) -> str:
        repair_calls.append((system_prompt, user_prompt))
        return json.dumps(
            {
                "action": "book_meeting",
                "domain": "booking",
                "retrieval_scopes": ["meeting_policy"],
                "exclude_scopes": ["courseware"],
                "decision_mode": "review_queue",
                "needs_clarification": False,
                "clarification_message": None,
                "escalation_reason": None,
            }
        )

    client.answer_question_sync = answer_question_sync

    payload = client._parse_interaction_intent_payload(
        '{"action":"book_meeting","domain":"booking","retrieval_scopes":"meeting_policy"}'
    )

    assert payload.action == "book_meeting"
    assert payload.retrieval_scopes == ["meeting_policy"]
    assert len(repair_calls) == 1


def test_classify_booking_intent_sync_returns_false_on_classifier_failure() -> None:
    client = object.__new__(VllmChatClient)

    def classify_interaction_intent_sync(
        question: str, course_context: str | None = None
    ) -> InteractionIntent:
        raise RuntimeError("llm unavailable")

    client.classify_interaction_intent_sync = classify_interaction_intent_sync

    assert client.classify_booking_intent_sync("帮我预约明天上午讨论论文", "科研指导") is False


class _FakeChatCompletionResponse:
    def __init__(self, content: str) -> None:
        self._content = content

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"choices": [{"message": {"content": self._content}}]}


class _CapturingIntentClient:
    def __init__(self, content: str = '{"action":"answer","domain":"general","retrieval_scopes":[],"exclude_scopes":[],"decision_mode":"direct_answer","needs_clarification":false,"clarification_message":null,"escalation_reason":null}') -> None:
        self._content = content
        self.calls: list[tuple[str, dict]] = []

    def post(self, path: str, json: dict) -> _FakeChatCompletionResponse:
        self.calls.append((path, json))
        return _FakeChatCompletionResponse(self._content)

    def close(self) -> None:
        return None


class _FlakyHttpxClient:
    def __init__(self, failures_before_success: int, *, content: str = "ok") -> None:
        self._failures_before_success = failures_before_success
        self._content = content
        self.calls = 0

    def post(self, path: str, json: dict) -> _FakeChatCompletionResponse:
        self.calls += 1
        if self.calls <= self._failures_before_success:
            raise httpx.ReadTimeout("timed out")
        return _FakeChatCompletionResponse(self._content)

    def close(self) -> None:
        return None


def _build_retry_test_client(settings: AppSettings, transport) -> VllmChatClient:
    client = object.__new__(VllmChatClient)
    client._settings = settings
    client._client = transport
    client._cache_lock = threading.Lock()
    client._response_cache = OrderedDict()
    client._metrics_lock = threading.Lock()
    client._request_count = 0
    client._success_count = 0
    client._error_count = 0
    client._cache_hit_count = 0
    client._last_request_at = None
    client._last_success_at = None
    client._last_error_at = None
    client._last_error_message = None
    return client


def _build_intent_test_client(settings: AppSettings, transport: _CapturingIntentClient) -> VllmChatClient:
    client = object.__new__(VllmChatClient)
    client._settings = settings
    client._client = None
    client._intent_client = transport
    client._intent_model_name = settings.intent_model_name or settings.model_name
    client._cache_lock = threading.Lock()
    client._response_cache = OrderedDict()
    client._metrics_lock = threading.Lock()
    client._request_count = 0
    client._success_count = 0
    client._error_count = 0
    client._cache_hit_count = 0
    client._last_request_at = None
    client._last_success_at = None
    client._last_error_at = None
    client._last_error_message = None
    return client


def test_request_intent_classification_disables_thinking_even_when_answer_llm_can_think() -> None:
    settings = AppSettings(model_name="Qwen3-32B", intent_model_name="Qwen3-8B")
    transport = _CapturingIntentClient()
    client = _build_intent_test_client(settings, transport)

    content = client._request_intent_classification("system", "user")

    assert content
    assert len(transport.calls) == 1
    path, payload = transport.calls[0]
    assert path == "/chat/completions"
    assert payload["model"] == "Qwen3-8B"
    assert payload["chat_template_kwargs"] == {"enable_thinking": False}
    assert payload["temperature"] == 0.0


def test_request_chat_completion_retries_timeout_then_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleep_calls: list[float] = []
    monkeypatch.setattr("sage_faculty_twin.llm_client.time.sleep", sleep_calls.append)
    settings = AppSettings(
        llm_cache_ttl_seconds=0,
        llm_cache_max_entries=0,
        llm_retry_attempts=2,
        llm_retry_backoff_seconds=0.25,
    )
    transport = _FlakyHttpxClient(failures_before_success=2, content="retried ok")
    client = _build_retry_test_client(settings, transport)

    answer = client._request_chat_completion_sync({"model": "demo", "messages": []})

    assert answer == "retried ok"
    assert transport.calls == 3
    assert sleep_calls == [0.25, 0.5]
    snapshot = client.runtime_snapshot()
    assert snapshot["llm_request_count"] == "1"
    assert snapshot["llm_success_count"] == "1"
    assert snapshot["llm_error_count"] == "0"
    assert snapshot["llm_last_error"] == ""


def test_app_settings_defaults_to_lower_llm_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DIGITAL_TWIN_LLM_TIMEOUT_SECONDS", raising=False)
    settings = AppSettings(_env_file=None)

    # Chat Latency Optimizations Task 1 lowered the default LLM timeout to
    # 60s so the request budget (80s) surfaces 504 well below Cloudflare's
    # 100s edge cap. ge=1, le=300 still allows operator overrides.
    assert settings.llm_timeout_seconds == 60


def test_app_settings_does_not_load_sibling_sage_env(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DIGITAL_TWIN_TAVILY_TOKEN", raising=False)
    monkeypatch.delenv("TAVILY_TOKEN", raising=False)

    settings = AppSettings(_env_file=None)

    assert settings.tavily_token == ""


def test_request_chat_completion_raises_after_retry_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleep_calls: list[float] = []
    monkeypatch.setattr("sage_faculty_twin.llm_client.time.sleep", sleep_calls.append)
    settings = AppSettings(
        llm_cache_ttl_seconds=0,
        llm_cache_max_entries=0,
        llm_retry_attempts=1,
        llm_retry_backoff_seconds=0.1,
    )
    transport = _FlakyHttpxClient(failures_before_success=5)
    client = _build_retry_test_client(settings, transport)

    with pytest.raises(httpx.ReadTimeout):
        client._request_chat_completion_sync({"model": "demo", "messages": []})

    assert transport.calls == 2
    assert sleep_calls == [0.1]
    snapshot = client.runtime_snapshot()
    assert snapshot["llm_request_count"] == "1"
    assert snapshot["llm_success_count"] == "0"
    assert snapshot["llm_error_count"] == "1"
    assert "timed out" in snapshot["llm_last_error"]
