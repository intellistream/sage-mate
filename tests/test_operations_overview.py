from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sage_faculty_twin.analytics_store import ConversationAnalyticsStore
from sage_faculty_twin.api import app, service
from sage_faculty_twin.config import settings
from sage_faculty_twin.escalation_store import EscalationQueueStore
from sage_faculty_twin.follow_up_store import FollowUpQueueStore
from sage_faculty_twin.knowledge_base import LocalKnowledgeStore
from sage_faculty_twin.knowledge_gap_draft_store import KnowledgeGapDraftStore
from sage_faculty_twin.meeting import MeetingService
from sage_faculty_twin.memory_store import NeuroMemConversationStore
from sage_faculty_twin.models import (
    AnonymousSuggestionCreate,
    ChatRequest,
    KnowledgeDocumentCreate,
)
from sage_faculty_twin.suggestion_store import SuggestionBoardStore


client = TestClient(app)


@pytest.fixture
def isolated_operations_stores(tmp_path: Path):
    original_knowledge_store = service._knowledge_store
    original_conversation_store = service._conversation_store
    original_analytics_store = service._analytics_store
    original_knowledge_gap_draft_store = service._knowledge_gap_draft_store
    original_escalation_store = service._escalation_store
    original_follow_up_store = service._follow_up_store
    original_suggestion_store = service._suggestion_store
    original_meeting_service = service._meeting_service

    isolated_settings = settings.model_copy(
        update={
            "knowledge_base_dir": tmp_path / "knowledge",
            "conversation_memory_dir": tmp_path / "memory",
            "knowledge_gap_draft_dir": tmp_path / "knowledge-gap-drafts",
            "escalation_queue_dir": tmp_path / "escalations",
            "follow_up_queue_dir": tmp_path / "follow-ups",
            "suggestion_board_dir": tmp_path / "suggestions",
            "availability_schedule_path": tmp_path / "availability" / "current_week.json",
        }
    )
    service._knowledge_store = LocalKnowledgeStore(isolated_settings)
    service._conversation_store = NeuroMemConversationStore(isolated_settings)
    service._analytics_store = ConversationAnalyticsStore(isolated_settings, service._conversation_store)
    service._knowledge_gap_draft_store = KnowledgeGapDraftStore(isolated_settings)
    service._escalation_store = EscalationQueueStore(isolated_settings)
    service._follow_up_store = FollowUpQueueStore(isolated_settings)
    service._suggestion_store = SuggestionBoardStore(isolated_settings)
    service._meeting_service = MeetingService(isolated_settings)
    try:
        yield
    finally:
        service._knowledge_store = original_knowledge_store
        service._conversation_store = original_conversation_store
        service._analytics_store = original_analytics_store
        service._knowledge_gap_draft_store = original_knowledge_gap_draft_store
        service._escalation_store = original_escalation_store
        service._follow_up_store = original_follow_up_store
        service._suggestion_store = original_suggestion_store
        service._meeting_service = original_meeting_service


def test_operations_overview_requires_admin_session(isolated_operations_stores) -> None:
    client.cookies.clear()

    overview_response = client.get("/operations/overview")
    workbench_response = client.get("/operations/workbench")

    assert overview_response.status_code == 403
    assert overview_response.json()["detail"] == "需要管理员身份验证。"
    assert workbench_response.status_code == 403
    assert workbench_response.json()["detail"] == "需要管理员身份验证。"


def test_operations_overview_aggregates_existing_work_queues(isolated_operations_stores) -> None:
    client.cookies.clear()
    service._knowledge_store.add_document(
        KnowledgeDocumentCreate(
            title="FAQ｜预约准备",
            content="预约前请准备 agenda、当前 blocker 和相关材料。",
            tags=["meeting", "faq"],
            source_name="manual:booking-prep",
        )
    )
    service._knowledge_gap_draft_store.upsert_generated_draft(
        cluster_id="cluster-booking-prep",
        interaction_domain="booking",
        label="预约准备",
        reason="多名学生询问预约前需要准备什么。",
        suggested_action="补充预约 FAQ。",
        sample_questions=["预约前要准备什么？"],
        title="FAQ草稿｜预约准备",
        content="预约前请准备 agenda、当前 blocker 和相关材料。",
        tags=["analytics-gap", "draft", "booking"],
        source_name="analytics-gap:cluster-booking-prep",
    )
    service._escalation_store.create_request(
        ChatRequest(
            student_name="Alice",
            student_email="alice@example.com",
            question="这个问题需要老师本人判断。",
            course_context="科研指导",
        ),
        conversation_id="conv-escalation",
        route="human_handoff",
        reason="需要人工接管",
    )
    service._follow_up_store.queue_action(
        booking_id=None,
        student_name="Alice",
        student_email="alice@example.com",
        action_type="reading_nudge",
        title="发送阅读提醒",
        detail="提醒学生阅读预约准备材料。",
        subject="预约前阅读提醒",
        lines=["请先阅读预约准备材料。"],
        due_at=datetime.now(UTC) + timedelta(hours=1),
    )
    service._suggestion_store.create_suggestion(
        AnonymousSuggestionCreate(message="希望后台有运营总览。", category="功能建议")
    )

    login_response = client.post(
        "/auth/admin/login",
        json={"username": settings.admin_username, "password": settings.admin_password},
    )
    assert login_response.status_code == 200

    response = client.get("/operations/overview?days=14")

    assert response.status_code == 200
    payload = response.json()
    queues = {item["queue_key"]: item for item in payload["queues"]}
    assert payload["window_days"] == 14
    assert payload["totals"]["knowledge_documents"] == 1
    assert payload["totals"]["suggestions"] == 1
    assert queues["knowledge_gap_drafts"]["open_count"] == 1
    assert queues["human_handoff"]["open_count"] == 1
    assert queues["follow_ups"]["open_count"] == 1
    assert queues["anonymous_suggestions"]["total_count"] == 1
    assert payload["question_analytics"]["total_exchanges"] == 0


def test_operations_workbench_returns_actionable_admin_records(isolated_operations_stores) -> None:
    client.cookies.clear()
    first_exchange = service._conversation_store.add_exchange(
        ChatRequest(
            student_name="Carol",
            student_email="carol@example.com",
            question="加入课题组前我应该准备什么材料？",
            course_context="科研指导",
        ),
        conversation_id="conv-gap-carol",
        answer="建议先准备简历、项目经历和想研究的问题。",
        workflow_action="answer",
        interaction_domain="advising",
        knowledge_hit_count=0,
        booking_result=None,
    )
    service._conversation_store.add_exchange(
        ChatRequest(
            student_name="Dave",
            student_email="dave@example.com",
            question="加入课题组前我应该准备什么材料？",
            course_context="科研指导",
        ),
        conversation_id="conv-gap-dave",
        answer="建议先准备简历、项目经历和想研究的问题。",
        workflow_action="answer",
        interaction_domain="advising",
        knowledge_hit_count=0,
        booking_result=None,
    )
    service._analytics_store.submit_feedback(
        exchange_id=first_exchange.memory_id,
        rating="down",
        resolved=False,
        needs_human_followup=False,
        issue_summary="缺少标准准备清单。",
    )
    draft = service._knowledge_gap_draft_store.upsert_generated_draft(
        cluster_id="cluster-research-onboarding",
        interaction_domain="research",
        label="科研入门",
        reason="访客反复询问如何加入研究项目。",
        suggested_action="补充科研入门 FAQ。",
        sample_questions=["我想加入课题组应该怎么准备？"],
        title="FAQ草稿｜科研入门",
        content="建议先阅读主页研究方向并准备简历。",
        tags=["analytics-gap", "draft", "research"],
        source_name="analytics-gap:cluster-research-onboarding",
    )
    escalation = service._escalation_store.create_request(
        ChatRequest(
            student_name="Bob",
            student_email="bob@example.com",
            question="这件事情需要老师本人判断。",
            course_context="科研指导",
        ),
        conversation_id="conv-handoff",
        route="human_handoff",
        reason="需要人工接管",
    )
    follow_up = service._follow_up_store.queue_action(
        booking_id=None,
        student_name="Bob",
        student_email="bob@example.com",
        action_type="owner_review",
        title="人工复核",
        detail="请复核这位同学的问题。",
        subject="人工复核提醒",
        lines=["请复核这位同学的问题。"],
        due_at=datetime.now(UTC),
    )
    suggestion = service._suggestion_store.create_suggestion(
        AnonymousSuggestionCreate(message="希望能看到待处理事项。", category="运营后台")
    )

    login_response = client.post(
        "/auth/admin/login",
        json={"username": settings.admin_username, "password": settings.admin_password},
    )
    assert login_response.status_code == 200

    response = client.get("/operations/workbench?days=7&limit=5")

    assert response.status_code == 200
    payload = response.json()
    assert payload["overview"]["queues"]
    assert payload["knowledge_gap_drafts"][0]["draft_id"] == draft.draft_id
    assert payload["question_analytics"]["knowledge_gap_suggestions"]
    assert payload["question_analytics"]["knowledge_gap_suggestions"][0]["sample_questions"]
    assert payload["escalations"][0]["escalation_id"] == escalation.escalation_id
    assert payload["follow_up_actions"][0]["action_id"] == follow_up.action_id
    assert payload["anonymous_suggestions"][0]["suggestion_id"] == suggestion.suggestion_id
    assert payload["anonymous_suggestions"][0]["message"] == "希望能看到待处理事项。"
    assert payload["question_analytics"]["overview"]["total_exchanges"] == 2