from pathlib import Path

from sage_faculty_twin.config import AppSettings
from sage_faculty_twin.models import ChatRequest, InteractionIntent
from sage_faculty_twin.service import (
    ChatWorkflowContext,
    FacultyTwinWorkflowSupport,
    _strip_internal_thinking_content,
)


def _build_context(*, deep_thinking: bool = True, deep_thinking_explicit: bool = False) -> ChatWorkflowContext:
    return ChatWorkflowContext(
        request=ChatRequest(
            student_name="Alice",
            question="请给我解释一下批处理调度。",
            deep_thinking=deep_thinking,
            deep_thinking_explicit=deep_thinking_explicit,
        ),
        conversation_id="conv-deep-thinking",
        owner_name="Prof. Zhang",
        used_model="Qwen3-32B",
        interaction_intent=InteractionIntent(
            action="answer",
            domain="general",
            decision_mode="direct_answer",
        ),
    )


def test_auto_disable_deep_thinking_for_simple_requests(tmp_path: Path) -> None:
    service = object.__new__(FacultyTwinWorkflowSupport)
    service._settings = AppSettings(knowledge_base_dir=tmp_path)

    assert service._should_enable_deep_thinking(_build_context()) is False


def test_explicit_deep_thinking_overrides_auto_disable(tmp_path: Path) -> None:
    service = object.__new__(FacultyTwinWorkflowSupport)
    service._settings = AppSettings(knowledge_base_dir=tmp_path)

    assert service._should_enable_deep_thinking(
        _build_context(deep_thinking=True, deep_thinking_explicit=True)
    ) is True


def test_strip_internal_thinking_content_removes_think_blocks() -> None:
    answer = "<think>internal chain</think>\n\n最终回答。"

    assert _strip_internal_thinking_content(answer) == "最终回答。"


def test_strip_internal_thinking_content_keeps_plain_answer() -> None:
    answer = "这是直接给用户的回答。"

    assert _strip_internal_thinking_content(answer) == answer