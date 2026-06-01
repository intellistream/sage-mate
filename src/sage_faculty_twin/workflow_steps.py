from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

_SIDE_EFFECT_PATTERN = "^(none|draft_write|owner_review|admin_only)$"
_RETRY_POLICY_PATTERN = "^(none|idempotent)$"


class WorkflowStepDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(min_length=1, max_length=64)
    description: str = Field(min_length=1, max_length=256)
    required_inputs: list[str] = Field(default_factory=list)
    produces_outputs: list[str] = Field(default_factory=list)
    side_effect: str = Field(default="none", pattern=_SIDE_EFFECT_PATTERN)
    admin_only: bool = False
    timeout_budget_ms: int = Field(default=1000, ge=0, le=60000)
    retry_policy: str = Field(default="none", pattern=_RETRY_POLICY_PATTERN)
    trace_key: str | None = Field(default=None, max_length=64)


_DEFAULT_STEP_DEFINITIONS = [
    WorkflowStepDefinition(
        step_id="detect_profile_context",
        description="Normalize the request into a faculty role/profile context.",
        required_inputs=["question", "visitor_profile", "course_context"],
        produces_outputs=["profile_context"],
        timeout_budget_ms=200,
        trace_key="planner_profile_context",
    ),
    WorkflowStepDefinition(
        step_id="classify_intent",
        description="Classify the interaction intent before selecting execution.",
        required_inputs=["question", "course_context", "profile_context"],
        produces_outputs=["interaction_intent"],
        timeout_budget_ms=300,
        trace_key="planner_intent",
    ),
    WorkflowStepDefinition(
        step_id="retrieve_knowledge",
        description="Retrieve grounded knowledge candidates for the request.",
        required_inputs=["question", "profile_context"],
        produces_outputs=["knowledge_hits"],
        timeout_budget_ms=2000,
        trace_key="planner_knowledge",
    ),
    WorkflowStepDefinition(
        step_id="retrieve_hybrid_knowledge",
        description="Choose and execute the best read-only retrieval mix across knowledge and memory backends.",
        required_inputs=["question", "profile_context", "interaction_intent"],
        produces_outputs=["knowledge_hits", "retrieval_path"],
        timeout_budget_ms=2400,
        trace_key="planner_hybrid_knowledge",
    ),
    WorkflowStepDefinition(
        step_id="retrieve_recent_memory",
        description="Retrieve recent conversation memory for the current session or user.",
        required_inputs=["question", "session_identity"],
        produces_outputs=["recent_memory_hits"],
        timeout_budget_ms=1200,
        trace_key="planner_recent_memory",
    ),
    WorkflowStepDefinition(
        step_id="retrieve_profile_memory",
        description="Retrieve longer-term profile memory when policy allows it.",
        required_inputs=["question", "journey_state"],
        produces_outputs=["profile_memory_hits"],
        timeout_budget_ms=1200,
        trace_key="planner_profile_memory",
    ),
    WorkflowStepDefinition(
        step_id="retrieve_artifact_memory",
        description="Retrieve typed upload, agenda, blocker, or follow-up memory when the request refers to prior artifacts.",
        required_inputs=["question", "session_identity", "interaction_intent"],
        produces_outputs=["artifact_memory_hits"],
        timeout_budget_ms=1400,
        trace_key="planner_artifact_memory",
    ),
    WorkflowStepDefinition(
        step_id="assemble_prompt_context",
        description="Assemble the grounded prompt context for downstream response generation.",
        required_inputs=["question", "interaction_intent"],
        produces_outputs=["prompt_context"],
        timeout_budget_ms=300,
        trace_key="planner_prompt_context",
    ),
    WorkflowStepDefinition(
        step_id="answer_with_citations",
        description="Generate a grounded answer with citations and explicit evidence.",
        required_inputs=["question", "prompt_context"],
        produces_outputs=["answer"],
        timeout_budget_ms=4000,
        trace_key="planner_answer",
    ),
    WorkflowStepDefinition(
        step_id="detect_knowledge_gap",
        description="Detect whether the answer exposed a missing or stale knowledge gap.",
        required_inputs=["answer", "knowledge_hits"],
        produces_outputs=["knowledge_gap_signal"],
        timeout_budget_ms=400,
        trace_key="planner_knowledge_gap",
    ),
    WorkflowStepDefinition(
        step_id="score_memory_usefulness",
        description="Score whether the selected memory and retrieval evidence was helpful, stale, or review-worthy.",
        required_inputs=["answer"],
        produces_outputs=["memory_usefulness_signal"],
        timeout_budget_ms=250,
        trace_key="planner_memory_usefulness",
    ),
    WorkflowStepDefinition(
        step_id="render_user_response",
        description="Render the final user-visible response payload.",
        required_inputs=["answer"],
        produces_outputs=["response_payload"],
        timeout_budget_ms=200,
        trace_key="planner_response_render",
    ),
    WorkflowStepDefinition(
        step_id="record_conversation_memory",
        description="Persist the summarized conversation memory for later retrieval.",
        required_inputs=["answer", "response_payload"],
        produces_outputs=["memory_writeback"],
        side_effect="draft_write",
        timeout_budget_ms=600,
        trace_key="planner_memory_writeback",
    ),
    WorkflowStepDefinition(
        step_id="record_artifact_memory",
        description="Persist typed upload, agenda, blocker, and follow-up memory with provenance and retention metadata.",
        required_inputs=["interaction_intent", "response_payload"],
        produces_outputs=["artifact_memory_writeback"],
        side_effect="draft_write",
        timeout_budget_ms=700,
        trace_key="planner_artifact_memory_writeback",
    ),
    WorkflowStepDefinition(
        step_id="draft_booking_request",
        description="Prepare a booking draft for owner or admin review.",
        required_inputs=["interaction_intent", "recent_memory_hits"],
        produces_outputs=["booking_draft"],
        side_effect="draft_write",
        timeout_budget_ms=500,
        trace_key="planner_booking_draft",
    ),
    WorkflowStepDefinition(
        step_id="create_escalation_draft",
        description="Create a reviewable escalation draft for human handoff.",
        required_inputs=["interaction_intent", "knowledge_hits"],
        produces_outputs=["escalation_draft"],
        side_effect="draft_write",
        timeout_budget_ms=500,
        trace_key="planner_escalation_draft",
    ),
    WorkflowStepDefinition(
        step_id="draft_follow_up_action",
        description="Create a reviewable follow-up action draft.",
        required_inputs=["answer", "recent_memory_hits"],
        produces_outputs=["follow_up_draft"],
        side_effect="draft_write",
        timeout_budget_ms=500,
        trace_key="planner_follow_up_draft",
    ),
    WorkflowStepDefinition(
        step_id="draft_knowledge_gap",
        description="Create a reviewable knowledge-gap draft instead of publishing knowledge.",
        required_inputs=["knowledge_gap_signal", "knowledge_hits"],
        produces_outputs=["knowledge_gap_draft"],
        side_effect="draft_write",
        timeout_budget_ms=500,
        trace_key="planner_knowledge_gap_draft",
    ),
]

DEFAULT_STEP_REGISTRY = {step.step_id: step for step in _DEFAULT_STEP_DEFINITIONS}


def get_default_step_registry() -> dict[str, WorkflowStepDefinition]:
    return {
        step_id: step.model_copy(deep=True)
        for step_id, step in DEFAULT_STEP_REGISTRY.items()
    }
