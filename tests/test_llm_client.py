import json

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

    def classify_interaction_intent_sync(question: str, course_context: str | None = None) -> InteractionIntent:
        raise RuntimeError("llm unavailable")

    client.classify_interaction_intent_sync = classify_interaction_intent_sync

    assert client.classify_booking_intent_sync("帮我预约明天上午讨论论文", "科研指导") is False