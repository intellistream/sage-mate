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


def test_explicit_deep_thinking_adds_deep_answer_guidance() -> None:
    context = _build_context(deep_thinking=True, deep_thinking_explicit=True)

    guidance = FacultyTwinWorkflowSupport._build_deep_answer_guidance(context.request)

    assert "deeper analysis" in guidance
    assert "<think>" in guidance


def test_strip_internal_thinking_content_removes_think_blocks() -> None:
    answer = "<think>internal chain</think>\n\n最终回答。"

    assert _strip_internal_thinking_content(answer) == "最终回答。"


def test_strip_internal_thinking_content_removes_unclosed_think_blocks() -> None:
    answer = "最终回答。\n\n<think>internal chain"

    assert _strip_internal_thinking_content(answer) == "最终回答。"


def test_strip_internal_thinking_content_keeps_plain_answer() -> None:
    answer = "这是直接给用户的回答。"

    assert _strip_internal_thinking_content(answer) == answer


def test_degenerate_answer_detection_rejects_empty_and_repeated_symbols() -> None:
    assert FacultyTwinWorkflowSupport._is_degenerate_answer("")
    assert FacultyTwinWorkflowSupport._is_degenerate_answer("   ")
    assert FacultyTwinWorkflowSupport._is_degenerate_answer("<think>internal</think>最终回答")
    assert FacultyTwinWorkflowSupport._is_degenerate_answer("*" * 200)
    assert FacultyTwinWorkflowSupport._is_degenerate_answer("-FIRST  `")
    assert FacultyTwinWorkflowSupport._is_degenerate_answer("-FIRST" + "\t " * 200)
    assert FacultyTwinWorkflowSupport._is_degenerate_answer("正常开头" + "F" * 100)
    assert FacultyTwinWorkflowSupport._is_degenerate_answer("不便讨论。" * 80)
    assert FacultyTwinWorkflowSupport._is_degenerate_answer(
        "Response instructions: Respond as the digital twin of the faculty owner."
    )
    assert FacultyTwinWorkflowSupport._is_degenerate_answer(
        "这类内部信息不便在此讨论，请直接联系张老师。"
    )
    assert FacultyTwinWorkflowSupport._is_degenerate_answer(
        "Answer: 这个问题是关于大模型推理服务系统的核心权衡。"
    )
    assert FacultyTwinWorkflowSupport._is_degenerate_answer(
        "实践经验总结的实践经验的实践经验总结"
    )


def test_degenerate_answer_detection_keeps_normal_short_and_structured_answers() -> None:
    assert not FacultyTwinWorkflowSupport._is_degenerate_answer("OK")
    assert not FacultyTwinWorkflowSupport._is_degenerate_answer(
        "可以从算子融合、KV Cache 管理、批处理调度和通信重叠几个方向优化。"
    )


def test_deterministic_fallback_answer_handles_ascend_question() -> None:
    context = _build_context()
    context.request.question = "如何优化大模型在Ascend NPU上的推理效率？"

    answer = FacultyTwinWorkflowSupport._build_deterministic_fallback_answer(context)

    assert "先定位瓶颈" in answer
    assert "吞吐" in answer
    assert not FacultyTwinWorkflowSupport._is_degenerate_answer(answer)


def test_deterministic_fallback_answer_handles_three_question_guidance() -> None:
    context = _build_context()
    context.request.question = "如果我想快速了解张老师的研究路线，最值得先问哪三个问题？"

    answer = FacultyTwinWorkflowSupport._build_deterministic_fallback_answer(context)

    assert "三个问题" in answer
    assert "现在最核心的问题" in answer
    assert not FacultyTwinWorkflowSupport._is_degenerate_answer(answer)


def test_deterministic_fallback_answer_handles_first_token_throughput_tradeoff() -> None:
    context = _build_context()
    context.request.question = "为什么大模型推理服务同时优化首 token 延迟和吞吐会有冲突？"

    answer = FacultyTwinWorkflowSupport._build_deterministic_fallback_answer(context)

    assert "首 token 延迟" in answer
    assert "吞吐" in answer
    assert "调度目标不同" in answer
    assert not FacultyTwinWorkflowSupport._is_degenerate_answer(answer)


def test_hosted_web_deep_call_does_not_enable_engine_thinking(tmp_path: Path) -> None:
    class FakeLlmClient:
        def __init__(self) -> None:
            self.kwargs: dict[str, object] | None = None

        def answer_question_sync(
            self,
            system_prompt: str,
            user_prompt: str,
            *,
            enable_thinking: bool = True,
            thinking_token_budget: int | None = None,
            **kwargs: object,
        ) -> str:
            kwargs["enable_thinking"] = enable_thinking
            if thinking_token_budget is not None:
                kwargs["thinking_token_budget"] = thinking_token_budget
            self.kwargs = kwargs
            return "OK"

    fake_llm = FakeLlmClient()
    service = object.__new__(FacultyTwinWorkflowSupport)
    service._settings = AppSettings(knowledge_base_dir=tmp_path)
    service._llm_client = fake_llm
    context = _build_context(deep_thinking=True, deep_thinking_explicit=True)

    answer = service._call_answer_question_sync(
        "system",
        "user",
        context=context,
        enable_thinking=True,
    )

    assert answer == "OK"
    assert fake_llm.kwargs is not None
    assert fake_llm.kwargs["enable_thinking"] is False
    assert "thinking_token_budget" not in fake_llm.kwargs
