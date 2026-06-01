from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from .models import ChatRequest
from .workflow_context import WorkflowRequestContext
from .workflow_planner import DeterministicWorkflowPlanner, PlannerDecision


class WorkflowReplayScenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=256)
    request: ChatRequest
    expected_goal: str = Field(min_length=1, max_length=128)
    expected_fallback_template: str = Field(min_length=1, max_length=64)
    required_steps: list[str] = Field(default_factory=list)
    forbidden_steps: list[str] = Field(default_factory=list)
    is_admin_request: bool = False
    expect_accepted: bool = True


class WorkflowReplayResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(min_length=1, max_length=64)
    passed: bool
    errors: list[str] = Field(default_factory=list)
    decision: PlannerDecision


def default_scenarios_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "data"
        / "workflow_scenarios"
        / "v3_preview_scenarios.json"
    )


def load_workflow_replay_scenarios(
    path: Path | None = None,
) -> list[WorkflowReplayScenario]:
    scenario_path = path or default_scenarios_path()
    payload = json.loads(scenario_path.read_text(encoding="utf-8"))
    return [WorkflowReplayScenario.model_validate(item) for item in payload]


def evaluate_workflow_replay_scenarios(
    planner: DeterministicWorkflowPlanner,
    scenarios: list[WorkflowReplayScenario],
) -> list[WorkflowReplayResult]:
    results: list[WorkflowReplayResult] = []
    for scenario in scenarios:
        context = WorkflowRequestContext.from_chat_request(
            scenario.request,
            is_admin_request=scenario.is_admin_request,
        )
        decision = planner.plan(context)
        errors: list[str] = []
        if decision.accepted != scenario.expect_accepted:
            errors.append(
                f"accepted={decision.accepted} did not match expected {scenario.expect_accepted}"
            )
        if decision.plan.goal != scenario.expected_goal:
            errors.append(
                f"goal {decision.plan.goal} did not match expected {scenario.expected_goal}"
            )
        if decision.plan.fallback_template != scenario.expected_fallback_template:
            errors.append(
                f"fallback template {decision.plan.fallback_template} did not match expected {scenario.expected_fallback_template}"
            )

        step_ids = [step.step_id for step in decision.plan.steps]
        for required_step in scenario.required_steps:
            if required_step not in step_ids:
                errors.append(f"missing required step {required_step}")
        for forbidden_step in scenario.forbidden_steps:
            if forbidden_step in step_ids:
                errors.append(f"forbidden step {forbidden_step} was present")

        results.append(
            WorkflowReplayResult(
                scenario_id=scenario.scenario_id,
                passed=not errors,
                errors=errors,
                decision=decision,
            )
        )
    return results
