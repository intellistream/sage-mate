from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from .config import settings
from .workflow_context import WorkflowRequestContext
from .workflow_steps import WorkflowStepDefinition, get_default_step_registry

_SIDE_EFFECT_PATTERN = "^(none|draft_write|owner_review|admin_only)$"


class WorkflowPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_version: str = Field(min_length=1, max_length=64)
    max_stage_count: int = Field(default=10, ge=1, le=32)
    max_latency_budget_ms: int = Field(default=15000, ge=1000, le=120000)
    allow_admin_steps_for_normal_users: bool = False
    allowed_evidence_sources: list[str] = Field(
        default_factory=lambda: [
            "artifact_memory",
            "attachment_excerpt",
            "booking_policy",
            "course_material",
            "faq",
            "profile_memory",
            "public_homepage",
            "recent_memory",
            "recent_session_context",
        ]
    )
    forbidden_evidence_sources: list[str] = Field(
        default_factory=lambda: ["private_student_record_without_consent"]
    )
    allowed_write_step_ids: list[str] = Field(default_factory=list)


class PolicyValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accepted: bool
    errors: list[str] = Field(default_factory=list)
    strongest_side_effect: str = Field(default="none", pattern=_SIDE_EFFECT_PATTERN)
    estimated_latency_ms: int = Field(default=0, ge=0)


def default_workflow_policy_path() -> Path:
    return settings.workflow_policy_path


def load_workflow_policy(path: Path | None = None) -> WorkflowPolicy:
    policy_path = path or default_workflow_policy_path()
    payload = json.loads(policy_path.read_text(encoding="utf-8"))
    return WorkflowPolicy.model_validate(payload)


def build_default_workflow_policy(path: Path | None = None) -> WorkflowPolicy:
    return load_workflow_policy(path)


class WorkflowPolicyValidator:
    def __init__(
        self,
        *,
        policy: WorkflowPolicy | None = None,
        step_registry: dict[str, WorkflowStepDefinition] | None = None,
    ) -> None:
        self._policy = policy or build_default_workflow_policy()
        self._step_registry = step_registry or get_default_step_registry()

    def validate(
        self, plan: BaseModel, context: WorkflowRequestContext
    ) -> PolicyValidationResult:
        errors: list[str] = []
        strongest_side_effect = "none"
        available_values = {
            "course_context",
            "journey_state",
            "question",
            "session_identity",
            "visitor_profile",
        }
        total_latency = 0
        seen_steps: set[str] = set()

        if getattr(plan, "policy_version") != self._policy.policy_version:
            errors.append(
                f"plan policy version {getattr(plan, 'policy_version')} does not match {self._policy.policy_version}"
            )

        steps = list(getattr(plan, "steps"))
        if len(steps) > self._policy.max_stage_count:
            errors.append(
                f"plan exceeds max stage count {self._policy.max_stage_count}"
            )

        for step in steps:
            step_id = step.step_id
            if step_id in seen_steps:
                errors.append(
                    f"step {step_id} is duplicated; linear plan must remain acyclic"
                )
                continue
            seen_steps.add(step_id)

            definition = self._step_registry.get(step_id)
            if definition is None:
                errors.append(f"step {step_id} is not registered")
                continue

            if set(step.inputs) != set(definition.required_inputs):
                errors.append(f"step {step_id} inputs do not match registry definition")
            if set(step.outputs) != set(definition.produces_outputs):
                errors.append(
                    f"step {step_id} outputs do not match registry definition"
                )
            if step.side_effect != definition.side_effect:
                errors.append(
                    f"step {step_id} side effect does not match registry definition"
                )

            for required_input in definition.required_inputs:
                if required_input not in available_values:
                    errors.append(
                        f"step {step_id} requires unavailable input {required_input}"
                    )

            available_values.update(definition.produces_outputs)
            total_latency += definition.timeout_budget_ms
            strongest_side_effect = _strongest_side_effect(
                strongest_side_effect, definition.side_effect
            )

            if definition.admin_only and context.session_identity != "admin":
                errors.append(f"step {step_id} requires an admin session")

            if definition.side_effect != "none":
                if not context.allow_draft_write:
                    errors.append(f"step {step_id} requires draft-write capability")
                if step_id not in self._policy.allowed_write_step_ids:
                    errors.append(f"step {step_id} is not enabled by policy")

        risk_level = getattr(plan, "risk_level")
        if risk_level != strongest_side_effect_to_risk_level(strongest_side_effect):
            errors.append(
                f"plan risk level {risk_level} does not match strongest side effect {strongest_side_effect}"
            )

        if total_latency > getattr(plan, "estimated_latency_budget_ms"):
            errors.append(
                "plan latency budget is lower than the registered step budget"
            )
        if (
            getattr(plan, "estimated_latency_budget_ms")
            > self._policy.max_latency_budget_ms
        ):
            errors.append(
                f"plan exceeds max latency budget {self._policy.max_latency_budget_ms} ms"
            )

        evidence_contract = getattr(plan, "evidence_contract")
        allowed_sources = set(evidence_contract.allowed_sources)
        unavailable_sources = allowed_sources - set(context.available_evidence_sources)
        if unavailable_sources:
            errors.append(
                "plan references unavailable evidence sources: "
                + ", ".join(sorted(unavailable_sources))
            )

        policy_unknown_sources = allowed_sources - set(
            self._policy.allowed_evidence_sources
        )
        if policy_unknown_sources:
            errors.append(
                "plan references policy-unknown evidence sources: "
                + ", ".join(sorted(policy_unknown_sources))
            )

        forbidden_overlap = allowed_sources & set(
            self._policy.forbidden_evidence_sources
        )
        if forbidden_overlap:
            errors.append(
                "plan references forbidden evidence sources: "
                + ", ".join(sorted(forbidden_overlap))
            )

        if "profile_memory" in allowed_sources and not context.consent_profile_memory:
            errors.append("plan references profile_memory without consent")

        return PolicyValidationResult(
            accepted=not errors,
            errors=errors,
            strongest_side_effect=strongest_side_effect,
            estimated_latency_ms=total_latency,
        )


def _strongest_side_effect(current: str, candidate: str) -> str:
    order = {"none": 0, "draft_write": 1, "owner_review": 2, "admin_only": 3}
    return candidate if order[candidate] > order[current] else current


def strongest_side_effect_to_risk_level(side_effect: str) -> str:
    mapping = {
        "none": "read_only",
        "draft_write": "draft_write",
        "owner_review": "owner_review",
        "admin_only": "admin_only",
    }
    return mapping[side_effect]
