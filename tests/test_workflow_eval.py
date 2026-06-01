from __future__ import annotations

from sage_faculty_twin.workflow_eval import (
    default_scenarios_path,
    evaluate_workflow_replay_scenarios,
    load_workflow_replay_scenarios,
)
from sage_faculty_twin.workflow_planner import DeterministicWorkflowPlanner


def test_can_load_default_workflow_replay_scenarios() -> None:
    scenarios = load_workflow_replay_scenarios()

    assert default_scenarios_path().is_file()
    assert len(scenarios) >= 7
    assert scenarios[0].scenario_id == "tutorial7-course-grounding"


def test_default_workflow_replay_scenarios_pass_against_deterministic_planner() -> None:
    scenarios = load_workflow_replay_scenarios()
    planner = DeterministicWorkflowPlanner()

    results = evaluate_workflow_replay_scenarios(planner, scenarios)

    assert len(results) == len(scenarios)
    assert all(result.passed for result in results), [
        result.model_dump() for result in results if not result.passed
    ]
