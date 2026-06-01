from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import BaseModel, ConfigDict, Field

from sage_faculty_twin.config import AppSettings
from sage_faculty_twin.models import ChatRequest, KnowledgeDocumentCreate
from sage_faculty_twin.service import DigitalTwinService
from sage_faculty_twin.workflow_context import WorkflowRequestContext
from sage_faculty_twin.workflow_planner import DeterministicWorkflowPlanner


class IdentityEvalExpectedContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_mode: str = Field(min_length=1, max_length=64)
    journey_state: str = Field(min_length=1, max_length=64)
    session_identity: str = Field(min_length=1, max_length=32)


class IdentityEvalExpectedPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal: str = Field(min_length=1, max_length=128)
    fallback_template: str = Field(min_length=1, max_length=64)


class IdentityEvalScenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(min_length=1, max_length=64)
    request: ChatRequest
    expected_context: IdentityEvalExpectedContext
    expected_plan: IdentityEvalExpectedPlan
    expected_search_top_title: str | None = Field(default=None, max_length=256)
    expected_search_top_tag: str | None = Field(default=None, max_length=64)
    is_admin_request: bool = False


def default_identity_eval_scenarios_path() -> Path:
    return Path(__file__).with_name("data") / "identity_eval_scenarios.json"


def load_identity_eval_scenarios(
    path: Path | None = None,
) -> list[IdentityEvalScenario]:
    scenario_path = path or default_identity_eval_scenarios_path()
    payload = json.loads(scenario_path.read_text(encoding="utf-8"))
    return [IdentityEvalScenario.model_validate(item) for item in payload]


def _build_identity_eval_service(tmp_path: Path) -> DigitalTwinService:
    settings = AppSettings(knowledge_base_dir=tmp_path, knowledge_backend="local")
    service = DigitalTwinService(settings)
    documents = [
        KnowledgeDocumentCreate(
            title="主页资料｜个人简介",
            content="张书豪是华中科技大学计算机学院教师，主要从事大模型系统与智能体基础设施相关研究。",
            tags=["homepage", "profile", "overview"],
            source_name="homepage:contents/home.md#bio",
        ),
        KnowledgeDocumentCreate(
            title="课程资料｜大模型推理基础设施 Tutorial 7",
            content="Tutorial 7 主要讨论执行优化与异构路径，以及为什么局部 kernel 提升不必然转化为端到端收益。",
            tags=[
                "homepage",
                "teaching",
                "courseware",
                "tutorial",
                "course:llm-inference",
            ],
            source_name="homepage:contents/teaching/intro-to-llm-inference-engines.md#tutorial-7",
        ),
        KnowledgeDocumentCreate(
            title="课程资料｜研究生论文写作课程材料",
            content="论文写作课程覆盖论文结构、related work、投稿准备和毕业论文常见问题。",
            tags=[
                "homepage",
                "teaching",
                "courseware",
                "lecture",
                "course:paper-writing",
            ],
            source_name="homepage:contents/teaching/graduate-paper-writing-course.md#intro",
        ),
        KnowledgeDocumentCreate(
            title="研究总览｜研究主线",
            content="当前研究主线聚焦大模型推理引擎、推理服务系统与记忆智能体中间件。",
            tags=["homepage", "research", "publication", "overview"],
            source_name="homepage:contents/publications.md#overview",
        ),
        KnowledgeDocumentCreate(
            title="指导建议｜会前准备清单",
            content="预约前建议准备 agenda、current blocker、进度总结或 draft，以及 2-3 个具体问题。",
            tags=["meeting", "policy", "preparation", "qa"],
            source_name="advisor-note:meeting-prep",
        ),
    ]
    for document in documents:
        service.add_knowledge(document)
    return service


def test_can_load_identity_eval_scenarios() -> None:
    scenarios = load_identity_eval_scenarios()

    assert default_identity_eval_scenarios_path().is_file()
    assert len(scenarios) >= 6
    assert scenarios[0].scenario_id == "general-visitor-bio"


@pytest.mark.parametrize(
    "scenario",
    load_identity_eval_scenarios(),
    ids=lambda scenario: scenario.scenario_id,
)
def test_identity_eval_context_and_plan_matrix(
    tmp_path: Path, scenario: IdentityEvalScenario
) -> None:
    context = WorkflowRequestContext.from_chat_request(
        scenario.request,
        is_admin_request=scenario.is_admin_request,
    )

    assert context.role_mode == scenario.expected_context.role_mode
    assert context.journey_state == scenario.expected_context.journey_state
    assert context.session_identity == scenario.expected_context.session_identity

    decision = DeterministicWorkflowPlanner().plan(context)

    assert decision.plan.goal == scenario.expected_plan.goal
    assert decision.plan.fallback_template == scenario.expected_plan.fallback_template


@pytest.mark.parametrize(
    "scenario",
    [
        item
        for item in load_identity_eval_scenarios()
        if item.expected_search_top_title is not None
    ],
    ids=lambda scenario: scenario.scenario_id,
)
def test_identity_eval_search_ranking_matrix(
    tmp_path: Path, scenario: IdentityEvalScenario
) -> None:
    service = _build_identity_eval_service(tmp_path)

    try:
        response = service.search_knowledge(
            scenario.request.question,
            visitor_profile=scenario.request.visitor_profile,
        )
    finally:
        import asyncio

        asyncio.run(service.aclose())

    assert response.hits
    assert response.hits[0].title == scenario.expected_search_top_title
    assert scenario.expected_search_top_tag in response.hits[0].tags
