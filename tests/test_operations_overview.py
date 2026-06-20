from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sage_faculty_twin.analytics_store import ConversationAnalyticsStore
from sage_faculty_twin.api import app, service
from sage_faculty_twin.artifact_memory_draft_store import ArtifactMemoryDraftStore
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
from sage_faculty_twin.operations_store import OperationsTaskStateStore
from sage_faculty_twin.planner_comparison_store import PlannerComparisonStore
from sage_faculty_twin.planner_metrics_store import PlannerMetricsStore
from sage_faculty_twin.suggestion_store import SuggestionBoardStore


client = TestClient(app)
service = service.ensure_initialized()


@pytest.fixture
def isolated_operations_stores(tmp_path: Path):
    original_knowledge_store = service._knowledge_store
    original_conversation_store = service._conversation_store
    original_analytics_store = service._analytics_store
    original_artifact_memory_draft_store = service._artifact_memory_draft_store
    original_knowledge_gap_draft_store = service._knowledge_gap_draft_store
    original_escalation_store = service._escalation_store
    original_follow_up_store = service._follow_up_store
    original_operations_task_state_store = service._operations_task_state_store
    original_planner_comparison_store = service._planner_comparison_store
    original_planner_metrics_store = service._planner_metrics_store
    original_suggestion_store = service._suggestion_store
    original_meeting_service = service._meeting_service

    isolated_settings = settings.model_copy(
        update={
            "knowledge_base_dir": tmp_path / "knowledge",
            "conversation_memory_dir": tmp_path / "memory",
            "artifact_memory_draft_dir": tmp_path / "artifact-memory-drafts",
            "knowledge_gap_draft_dir": tmp_path / "knowledge-gap-drafts",
            "escalation_queue_dir": tmp_path / "escalations",
            "follow_up_queue_dir": tmp_path / "follow-ups",
            "operations_task_state_dir": tmp_path / "operations-task-state",
            "planner_comparison_dir": tmp_path / "planner-comparisons",
            "planner_metrics_dir": tmp_path / "planner-metrics",
            "suggestion_board_dir": tmp_path / "suggestions",
            "availability_schedule_path": tmp_path
            / "availability"
            / "current_week.json",
        }
    )
    service._knowledge_store = LocalKnowledgeStore(isolated_settings)
    service._conversation_store = NeuroMemConversationStore(isolated_settings)
    service._analytics_store = ConversationAnalyticsStore(
        isolated_settings, service._conversation_store
    )
    service._artifact_memory_draft_store = ArtifactMemoryDraftStore(isolated_settings)
    service._knowledge_gap_draft_store = KnowledgeGapDraftStore(isolated_settings)
    service._escalation_store = EscalationQueueStore(isolated_settings)
    service._follow_up_store = FollowUpQueueStore(isolated_settings)
    service._operations_task_state_store = OperationsTaskStateStore(isolated_settings)
    service._planner_comparison_store = PlannerComparisonStore(isolated_settings)
    service._planner_metrics_store = PlannerMetricsStore(isolated_settings)
    service._suggestion_store = SuggestionBoardStore(isolated_settings)
    service._meeting_service = MeetingService(isolated_settings)
    try:
        yield
    finally:
        service._knowledge_store = original_knowledge_store
        service._conversation_store = original_conversation_store
        service._analytics_store = original_analytics_store
        service._artifact_memory_draft_store = original_artifact_memory_draft_store
        service._knowledge_gap_draft_store = original_knowledge_gap_draft_store
        service._escalation_store = original_escalation_store
        service._follow_up_store = original_follow_up_store
        service._operations_task_state_store = original_operations_task_state_store
        service._planner_comparison_store = original_planner_comparison_store
        service._planner_metrics_store = original_planner_metrics_store
        service._suggestion_store = original_suggestion_store
        service._meeting_service = original_meeting_service


def test_operations_overview_requires_admin_session(isolated_operations_stores) -> None:
    client.cookies.clear()

    overview_response = client.get("/operations/overview")
    workbench_response = client.get("/operations/workbench")
    replay_response = client.get("/workflow/replay")

    assert overview_response.status_code == 403
    assert overview_response.json()["detail"] == "需要管理员身份验证。"
    assert workbench_response.status_code == 403
    assert workbench_response.json()["detail"] == "需要管理员身份验证。"
    assert replay_response.status_code == 403
    assert replay_response.json()["detail"] == "需要管理员身份验证。"


def test_operations_overview_aggregates_existing_work_queues(
    isolated_operations_stores,
) -> None:
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
    service._artifact_memory_draft_store.create_draft(
        conversation_id="conv-artifact-draft",
        source_memory_id="memory-artifact-1",
        student_name="Alice",
        student_email="alice@example.com",
        interaction_domain="research",
        question="把我上传的 proposal 记录成后续跟进材料。",
        answer="已整理成 reviewable draft。",
        artifact_names=["proposal-draft.md"],
        artifact_sources=["historical_artifact:memory-artifact-1"],
        artifact_excerpt_count=1,
        provenance_note="材料草稿来自 1 条历史 artifact 线索；关联材料：proposal-draft.md。",
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
    service._planner_comparison_store.record_comparison(
        conversation_id="conv-planner-overview",
        exchange_id=None,
        workflow_action="advise_only",
        question="预约前我应该准备什么材料？",
        comparison_status="different_steps",
        deterministic_goal="prepare_booking_agenda",
        shadow_goal="prepare_booking_agenda",
        same_goal=True,
        same_fallback_template=True,
        deterministic_only_steps=["retrieve_recent_memory"],
        shadow_only_steps=[],
        summary="Shadow planner kept the same goal but skipped recent-memory retrieval.",
    )
    service._planner_metrics_store.record_entry(
        conversation_id="conv-planner-overview",
        planner_stage="deterministic",
        planner_mode="deterministic",
        question="预约前我应该准备什么材料？",
        goal="prepare_booking_agenda",
        accepted=False,
        status="fallback",
        fallback_template="advise_only",
        fallback_reason="plan exceeds max stage count 2",
        validation_errors=["plan exceeds max stage count 2"],
        planned_steps=["detect_profile_context", "classify_intent"],
        latency_ms=14.0,
    )
    service._planner_metrics_store.record_entry(
        conversation_id="conv-planner-overview",
        planner_stage="shadow",
        planner_mode="llm_shadow",
        question="预约前我应该准备什么材料？",
        goal="prepare_booking_agenda",
        accepted=False,
        status="shadow_error",
        fallback_template="advise_only",
        fallback_reason="shadow planner request timed out",
        validation_errors=[],
        planned_steps=[],
        latency_ms=42.0,
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
    assert payload["totals"]["planner_requests"] == 1
    assert payload["totals"]["planner_comparisons"] == 1
    assert payload["totals"]["planner_fallbacks"] == 1
    assert payload["totals"]["planner_shadow_drifts"] == 1
    assert payload["totals"]["planner_shadow_errors"] == 1
    assert payload["totals"]["artifact_memory_drafts"] == 1
    assert payload["totals"]["suggestions"] == 1
    assert payload["planner_metrics"]["deterministic_fallbacks"] == 1
    assert payload["planner_metrics"]["shadow_errors"] == 1
    assert (
        payload["planner_metrics"]["rejection_reasons"][
            "plan exceeds max stage count 2"
        ]
        == 1
    )
    assert queues["artifact_memory_drafts"]["open_count"] == 1
    assert queues["artifact_memory_drafts"]["total_count"] == 1
    assert queues["knowledge_gap_drafts"]["open_count"] == 1
    assert queues["planner_shadow_review"]["open_count"] == 1
    assert queues["planner_shadow_review"]["total_count"] == 1
    assert queues["human_handoff"]["open_count"] == 1
    assert queues["follow_ups"]["open_count"] == 1
    assert queues["anonymous_suggestions"]["total_count"] == 1
    assert payload["question_analytics"]["total_exchanges"] == 0


def test_operations_overview_includes_neuromem_runtime_snapshot(
    isolated_operations_stores,
) -> None:
    client.cookies.clear()
    service._conversation_store.add_exchange(
        ChatRequest(
            student_name="Alice",
            student_email="alice@example.com",
            question="我之前提到的 related work 应该怎么继续整理？",
            course_context="科研指导",
        ),
        conversation_id="conv-neuromem-ops",
        answer="先按主题整理 related work，再把 contribution framing 单独列出来。",
        workflow_action="answer",
        interaction_domain="advising",
        knowledge_hit_count=1,
        booking_result=None,
    )
    service._conversation_store.search(
        ChatRequest(
            student_name="Alice",
            student_email="alice@example.com",
            question="结合你记得的上下文，再给我一个下一步建议。",
            course_context="科研指导",
        ),
        conversation_id="conv-neuromem-ops",
    )

    login_response = client.post(
        "/auth/admin/login",
        json={"username": settings.admin_username, "password": settings.admin_password},
    )
    assert login_response.status_code == 200

    response = client.get("/operations/overview")

    assert response.status_code == 200
    payload = response.json()
    neuromem = payload["neuromem"]
    conversation_stats = neuromem["conversation_stats"]
    telemetry = conversation_stats["telemetry"]

    assert neuromem["backend"] == "neuromem-layered"
    assert conversation_stats["service_type"] in (
        "NeuroMemConversationStore", "online_continual_memory",
    )
    assert conversation_stats["collection_name"] == "conversation-memory"
    assert conversation_stats["total_entries"] >= 1
    assert conversation_stats["memory_scope"] == "short_term"
    assert telemetry["event_count"] >= 2
    assert telemetry["query_count"] >= 1
    assert telemetry["write_count"] >= 1
    assert any(event["event_type"] == "retrieve" for event in neuromem["recent_events"])


def test_workflow_replay_report_returns_v3_summary(isolated_operations_stores) -> None:
    client.cookies.clear()

    login_response = client.post(
        "/auth/admin/login",
        json={"username": settings.admin_username, "password": settings.admin_password},
    )
    assert login_response.status_code == 200

    response = client.get("/workflow/replay")

    assert response.status_code == 200
    payload = response.json()
    assert payload["planner_version"] == "v3.0.0"
    assert payload["policy_version"] == "faculty-default-2026-05"
    assert payload["scenario_source"].endswith("data/workflow_scenarios/v3_preview_scenarios.json")
    assert payload["total_scenarios"] >= 7
    assert payload["passed_scenarios"] == payload["total_scenarios"]
    assert payload["failed_scenarios"] == 0
    assert payload["results"]
    assert all(item["passed"] for item in payload["results"])


def test_operations_overview_includes_memory_usefulness_summary(
    isolated_operations_stores,
) -> None:
    client.cookies.clear()
    service._conversation_store.record_memory_usefulness(
        conversation_id="conv-memory-usefulness",
        signal="helpful",
        reason="Recent conversation memory and grounded knowledge both helped the answer.",
        memory_used=True,
        knowledge_used=True,
        memory_hit_count=2,
        short_term_hit_count=1,
        long_term_hit_count=1,
        knowledge_hit_count=2,
        top_memory_score=1.7,
        workflow_action="answer",
        duration_ms=12.5,
    )

    login_response = client.post(
        "/auth/admin/login",
        json={"username": settings.admin_username, "password": settings.admin_password},
    )
    assert login_response.status_code == 200

    response = client.get("/operations/overview")
    assert response.status_code == 200
    telemetry = response.json()["neuromem"]["conversation_stats"]["telemetry"]

    assert telemetry["memory_usefulness"]["score_count"] >= 1
    assert telemetry["memory_usefulness"]["by_signal"]["helpful"] >= 1
    assert telemetry["memory_usefulness"]["memory_used_count"] >= 1
    assert telemetry["memory_usefulness"]["knowledge_used_count"] >= 1
    assert telemetry["memory_usefulness"]["last_signal"] == "helpful"


def test_operations_overview_includes_planner_metrics_summary(
    isolated_operations_stores,
) -> None:
    service._planner_metrics_store.record_entry(
        conversation_id="conv-planner-metrics",
        planner_stage="deterministic",
        planner_mode="deterministic",
        question="帮我总结一下最近的问题。",
        goal="answer_course_question",
        accepted=True,
        status="accepted",
        fallback_template="answer_question",
        fallback_reason=None,
        validation_errors=[],
        planned_steps=["detect_profile_context", "classify_intent"],
        latency_ms=9.5,
    )
    service._planner_metrics_store.record_entry(
        conversation_id="conv-planner-metrics",
        planner_stage="shadow",
        planner_mode="llm_shadow",
        question="帮我总结一下最近的问题。",
        goal="answer_course_question",
        accepted=False,
        status="rejected",
        fallback_template="answer_question",
        fallback_reason="step retrieve_artifact_memory is not enabled by policy",
        validation_errors=["step retrieve_artifact_memory is not enabled by policy"],
        planned_steps=["retrieve_artifact_memory"],
        latency_ms=18.0,
    )

    overview = service.get_operations_overview(days=7)

    assert overview.planner_metrics.record_count == 2
    assert overview.planner_metrics.deterministic_total == 1
    assert overview.planner_metrics.shadow_total == 1
    assert overview.planner_metrics.shadow_rejected == 1
    assert overview.planner_metrics.rejected_steps["retrieve_artifact_memory"] == 1
    assert overview.planner_metrics.avg_shadow_latency_ms == 18.0


def test_operations_workbench_returns_actionable_admin_records(
    isolated_operations_stores,
) -> None:
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
    service._conversation_store.consolidate_profiles(first_exchange)
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
    service._artifact_memory_draft_store.create_draft(
        conversation_id="conv-artifact-review",
        source_memory_id=first_exchange.memory_id,
        student_name="Carol",
        student_email="carol@example.com",
        interaction_domain="advising",
        question="把我上次上传的 onboarding 材料记成后续跟进草稿。",
        answer="已整理成材料草稿，待继续审核。",
        artifact_names=["onboarding-notes.md"],
        artifact_sources=[f"historical_artifact:{first_exchange.memory_id}"],
        artifact_excerpt_count=1,
        provenance_note="材料草稿来自 1 条历史 artifact 线索；关联材料：onboarding-notes.md。",
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
    comparison = service._planner_comparison_store.record_comparison(
        conversation_id="conv-planner-task",
        exchange_id=None,
        workflow_action="advise_only",
        question="预约前我应该准备什么材料？",
        comparison_status="different_goal",
        deterministic_goal="prepare_booking_agenda",
        shadow_goal="answer_grounded_question",
        same_goal=False,
        same_fallback_template=False,
        deterministic_only_steps=["retrieve_recent_memory"],
        shadow_only_steps=["retrieve_knowledge"],
        summary="Shadow planner proposed a more generic grounded-answer goal than the deterministic agenda-preparation plan.",
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
    task_keys = {item["task_key"]: item for item in payload["operational_tasks"]}
    escalation_task_key = f"escalation:{escalation.escalation_id}"
    comparison_task_key = f"planner_comparison:{comparison.record_id}"
    artifact_task_key = next(
        key for key in task_keys if key.startswith("artifact_draft:")
    )
    assert escalation_task_key in task_keys
    assert comparison_task_key in task_keys
    assert task_keys[artifact_task_key]["task_type"] == "artifact_memory_draft"
    assert task_keys[artifact_task_key]["source_status"] == "draft"
    assert task_keys[comparison_task_key]["task_type"] == "planner_comparison"
    assert task_keys[comparison_task_key]["source_status"] == "different_goal"
    assert task_keys[escalation_task_key]["task_type"] == "human_handoff"
    assert task_keys[escalation_task_key]["operations_status"] == "open"
    assert f"follow_up:{follow_up.action_id}" in task_keys
    assert payload["overview"]["totals"]["student_profiles"] == 1
    assert payload["student_profiles"]
    assert payload["student_profiles"][0]["student_email"] == "carol@example.com"
    assert payload["student_profiles"][0]["segment"] in {
        "协作准备",
        "持续关注",
        "基础画像",
    }
    assert payload["student_profiles"][0]["profile_count"] >= 1
    assert payload["student_profiles"][0]["interaction_count"] == 1
    assert payload["student_profiles"][0]["recent_questions"] == [
        "加入课题组前我应该准备什么材料？"
    ]
    assert payload["student_profiles"][0]["key_summaries"]
    assert payload["student_profiles"][0]["suggested_next_action"]
    assert payload["artifact_memory_drafts"][0]["artifact_names"] == [
        "onboarding-notes.md"
    ]
    assert payload["artifact_memory_drafts"][0]["artifact_excerpt_count"] == 1
    assert payload["knowledge_gap_drafts"][0]["draft_id"] == draft.draft_id
    assert payload["question_analytics"]["knowledge_gap_suggestions"]
    assert payload["question_analytics"]["knowledge_gap_suggestions"][0][
        "sample_questions"
    ]
    assert payload["satisfaction"]["feedback_count"] == 1
    assert payload["satisfaction"]["negative_count"] == 1
    assert payload["satisfaction"]["positive_rate"] == 0.0
    assert payload["satisfaction"]["unresolved_rate"] == 1.0
    assert payload["satisfaction"]["feedback_coverage_rate"] == 0.5
    assert (
        payload["satisfaction"]["reason_summaries"][0]["reason_key"] == "knowledge_gap"
    )
    assert payload["satisfaction"]["reason_summaries"][0]["sample_issues"] == [
        "缺少标准准备清单。"
    ]
    assert payload["satisfaction"]["trend"][0]["feedback_count"] == 1
    assert payload["escalations"][0]["escalation_id"] == escalation.escalation_id
    assert payload["follow_up_actions"][0]["action_id"] == follow_up.action_id
    assert (
        payload["anonymous_suggestions"][0]["suggestion_id"] == suggestion.suggestion_id
    )
    assert payload["anonymous_suggestions"][0]["message"] == "希望能看到待处理事项。"
    assert payload["question_analytics"]["overview"]["total_exchanges"] == 2

    state_response = client.patch(
        f"/operations/tasks/{escalation_task_key}",
        json={
            "status": "in_progress",
            "assigned_to": "张老师",
            "note": "先看学生原始问题。",
        },
    )
    assert state_response.status_code == 200
    state = state_response.json()
    assert state["task_key"] == escalation_task_key
    assert state["status"] == "in_progress"
    assert state["assigned_to"] == "张老师"

    refreshed_response = client.get("/operations/workbench?days=7&limit=5")
    assert refreshed_response.status_code == 200
    refreshed_tasks = {
        item["task_key"]: item
        for item in refreshed_response.json()["operational_tasks"]
    }
    assert refreshed_tasks[escalation_task_key]["operations_status"] == "in_progress"
    assert refreshed_tasks[escalation_task_key]["assigned_to"] == "张老师"
    assert refreshed_tasks[escalation_task_key]["note"] == "先看学生原始问题。"

    artifact_response = client.get("/memory/artifact-drafts")
    assert artifact_response.status_code == 200
    artifact_payload = artifact_response.json()
    assert artifact_payload[0]["artifact_names"] == ["onboarding-notes.md"]


def test_admin_can_accept_and_reject_artifact_memory_drafts(
    isolated_operations_stores,
) -> None:
    client.cookies.clear()
    accepted = service._artifact_memory_draft_store.create_draft(
        conversation_id="conv-artifact-accept",
        source_memory_id="memory-artifact-accept",
        student_name="Alice",
        student_email="alice@example.com",
        interaction_domain="research",
        question="请把这份 proposal 保留下来。",
        answer="已生成待审核材料草稿。",
        artifact_names=["proposal-draft.md"],
        artifact_sources=["historical_artifact:memory-artifact-accept"],
        artifact_excerpt_count=1,
        provenance_note="材料草稿来自 1 条历史 artifact 线索；关联材料：proposal-draft.md。",
    )
    rejected = service._artifact_memory_draft_store.create_draft(
        conversation_id="conv-artifact-reject",
        source_memory_id="memory-artifact-reject",
        student_name="Bob",
        student_email="bob@example.com",
        interaction_domain="research",
        question="这份临时草稿先不要存。",
        answer="已生成待审核材料草稿。",
        artifact_names=["scratch-notes.md"],
        artifact_sources=["historical_artifact:memory-artifact-reject"],
        artifact_excerpt_count=1,
        provenance_note="材料草稿来自 1 条历史 artifact 线索；关联材料：scratch-notes.md。",
    )

    login_response = client.post(
        "/auth/admin/login",
        json={"username": settings.admin_username, "password": settings.admin_password},
    )
    assert login_response.status_code == 200

    accept_response = client.post(f"/memory/artifact-drafts/{accepted.draft_id}/accept")
    assert accept_response.status_code == 200
    assert accept_response.json()["status"] == "accepted"

    reject_response = client.post(f"/memory/artifact-drafts/{rejected.draft_id}/reject")
    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == "rejected"

    drafts_response = client.get("/memory/artifact-drafts")
    assert drafts_response.status_code == 200
    drafts_payload = {item["draft_id"]: item for item in drafts_response.json()}
    assert drafts_payload[accepted.draft_id]["status"] == "accepted"
    assert drafts_payload[rejected.draft_id]["status"] == "rejected"

    overview_response = client.get("/operations/overview")
    assert overview_response.status_code == 200
    overview_payload = overview_response.json()
    artifact_queue = next(
        item
        for item in overview_payload["queues"]
        if item["queue_key"] == "artifact_memory_drafts"
    )
    assert overview_payload["totals"]["artifact_memory_drafts"] == 2
    assert artifact_queue["open_count"] == 0
    assert artifact_queue["total_count"] == 2

    workbench_response = client.get("/operations/workbench?limit=10")
    assert workbench_response.status_code == 200
    workbench_payload = workbench_response.json()
    task_keys = {item["task_key"] for item in workbench_payload["operational_tasks"]}
    assert f"artifact_draft:{accepted.draft_id}" not in task_keys
    assert f"artifact_draft:{rejected.draft_id}" not in task_keys
