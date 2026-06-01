from __future__ import annotations

import json

from sage_faculty_twin.config import AppSettings
from sage_faculty_twin.models import ChatRequest
from sage_faculty_twin.service import DigitalTwinService
from sage_faculty_twin.workflow_context import WorkflowRequestContext
from sage_faculty_twin.workflow_planner import DeterministicWorkflowPlanner
from sage_faculty_twin.workflow_policy import (
    WorkflowPolicyValidator,
    default_workflow_policy_path,
    load_workflow_policy,
)


def test_can_load_default_workflow_policy_file() -> None:
    policy = load_workflow_policy()

    assert default_workflow_policy_path().is_file()
    assert policy.policy_version == "faculty-default-2026-05"
    assert policy.max_stage_count == 10
    assert "artifact_memory" in policy.allowed_evidence_sources
    assert "attachment_excerpt" in policy.allowed_evidence_sources
    assert "course_material" in policy.allowed_evidence_sources
    assert "record_artifact_memory" in policy.allowed_write_step_ids


def test_default_policy_accepts_current_read_only_course_plan() -> None:
    planner = DeterministicWorkflowPlanner()
    context = WorkflowRequestContext(
        question="Tutorial 7 主要讲了什么？",
        course_context="大模型推理基础设施课程",
        visitor_profile="hust_undergraduate",
        role_mode="course_instructor",
        journey_state="course_student",
        session_identity="user",
        recent_memory_available=True,
        profile_memory_available=False,
        consent_profile_memory=False,
        allow_draft_write=False,
        available_evidence_sources=[
            "course_material",
            "faq",
            "public_homepage",
            "recent_memory",
        ],
    )

    decision = planner.plan(context)
    validation = WorkflowPolicyValidator(policy=load_workflow_policy()).validate(
        decision.plan, context
    )

    assert decision.accepted is True
    assert validation.accepted is True
    assert validation.errors == []


def test_service_uses_custom_workflow_policy_path(tmp_path) -> None:
    custom_policy_path = tmp_path / "custom-policy.json"
    custom_policy_path.write_text(
        json.dumps(
            {
                "policy_version": "faculty-custom-tight",
                "max_stage_count": 2,
                "max_latency_budget_ms": 15000,
                "allow_admin_steps_for_normal_users": False,
                "allowed_evidence_sources": [
                    "course_material",
                    "faq",
                    "public_homepage",
                    "recent_memory",
                ],
                "forbidden_evidence_sources": [
                    "private_student_record_without_consent"
                ],
                "allowed_write_step_ids": [],
            }
        ),
        encoding="utf-8",
    )
    settings = AppSettings(workflow_policy_path=custom_policy_path)
    service = DigitalTwinService(settings)

    decision = service.preview_workflow_plan(
        ChatRequest(
            student_name="Alice",
            student_email="alice@example.com",
            course_context="大模型推理基础设施课程",
            visitor_profile="hust_undergraduate",
            conversation_id="conv-course",
            question="Tutorial 7 主要讲了什么？",
        )
    )

    assert decision.plan.policy_version == "faculty-custom-tight"
    assert decision.accepted is False
    assert any("max stage count 2" in error for error in decision.validation_errors)
