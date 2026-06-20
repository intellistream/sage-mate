# Workflow System

<cite>
**Referenced Files in This Document**
- [workflow_planner.py](file://src/sage_faculty_twin/workflow_planner.py)
- [workflow_steps.py](file://src/sage_faculty_twin/workflow_steps.py)
- [workflow_policy.py](file://src/sage_faculty_twin/workflow_policy.py)
- [workflow_context.py](file://src/sage_faculty_twin/workflow_context.py)
- [workflow_eval.py](file://src/sage_faculty_twin/workflow_eval.py)
- [service.py](file://src/sage_faculty_twin/service.py)
- [planner_metrics_store.py](file://src/sage_faculty_twin/planner_metrics_store.py)
- [planner_comparison_store.py](file://src/sage_faculty_twin/planner_comparison_store.py)
- [config.py](file://src/sage_faculty_twin/config.py)
- [models.py](file://src/sage_faculty_twin/models.py)
- [skill_router.py](file://src/sage_faculty_twin/skill_router.py)
- [skill_runner.py](file://src/sage_faculty_twin/skill_runner.py)
- [skills.py](file://src/sage_faculty_twin/skills.py)
- [skill_tools.py](file://src/sage_faculty_twin/skill_tools.py)
- [course_advising.json](file://data/skills/course_advising.json)
- [meeting_prep.json](file://data/skills/meeting_prep.json)
- [test_dynamic_workflow_planner.py](file://tests/test_dynamic_workflow_planner.py)
- [test_workflow_policy.py](file://tests/test_workflow_policy.py)
- [test_workflow_eval.py](file://tests/test_workflow_eval.py)
- [test_skills.py](file://tests/test_skills.py)
</cite>

## Update Summary
**Changes Made**
- Added comprehensive documentation for the new agent skill system integration
- Documented skill router and skill runner components that handle specialized queries before standard pipeline execution
- Added skill manifest structure, tool registry system, and multi-turn reasoning loops
- Updated architecture diagrams to reflect the skill system alongside workflow planner
- Enhanced troubleshooting guide with skill system monitoring and debugging
- Added examples of skill manifests and integration patterns

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Agent Skill System Integration](#agent-skill-system-integration)
7. [Skill Router and Pattern Matching](#skill-router-and-pattern-matching)
8. [Skill Runner and Multi-Turn Reasoning](#skill-runner-and-multi-turn-reasoning)
9. [Skill Tool Registry and Function Calling](#skill-tool-registry-and-function-calling)
10. [Skill Manifest Structure and Examples](#skill-manifest-structure-and-examples)
11. [Enhanced V3.1 LLM-Assisted JSON Planner](#enhanced-v31-llm-assisted-json-planner)
12. [Shadow Comparison and Safety Mechanisms](#shadow-comparison-and-safety-mechanisms)
13. [Planner Metrics Storage and Analytics](#planner-metrics-storage-and-analytics)
14. [Dependency Analysis](#dependency-analysis)
15. [Performance Considerations](#performance-considerations)
16. [Troubleshooting Guide](#troubleshooting-guide)
17. [Conclusion](#conclusion)
18. [Appendices](#appendices)

## Introduction
This document explains the workflow planning and execution system that powers deterministic, step-based, policy-driven interactions. The system has been enhanced with V3.1 capabilities including LLM-assisted JSON planning, shadow comparison functionality, comprehensive planner metrics storage, and a new agent skill system. It covers:
- Deterministic workflow architecture and step-based processing model
- Policy-driven decision making and risk/risk-level mapping
- Enhanced LLM-assisted JSON planner implementation with shadow comparison
- Agent skill system with pattern-matching router and multi-turn reasoning loops
- Planner metrics storage and analytics for performance monitoring
- Fallback mechanisms and planner comparison
- Integration with memory systems, knowledge retrieval, and LLM processing
- Guidance for extending the system with custom steps, policies, and skills

## Project Structure
The workflow system is centered around six core modules with enhanced V3.1 capabilities:
- Planner: builds plans from natural-language intents and context with LLM assistance
- Steps: a registry of executable steps with side effects and timeouts
- Policy: enforces constraints on evidence sources, write steps, latency, and risk
- Context: captures request metadata, roles, journey state, and available evidence sources
- Metrics: stores and analyzes planner performance and comparison data
- Comparison: tracks deterministic vs shadow planner outcomes
- **New**: Skill Router: routes user questions to matching skills based on trigger patterns
- **New**: Skill Runner: executes skills with multi-turn tool-calling reasoning loops
- **New**: Skill Tools: registry of built-in tool handlers for knowledge and memory access

```mermaid
graph TB
subgraph "Workflow Core"
WP["DeterministicWorkflowPlanner<br/>builds PlanSpec"]
ST["Step Registry<br/>WorkflowStepDefinition"]
PC["Policy Validator<br/>WorkflowPolicy"]
CTX["WorkflowRequestContext"]
end
subgraph "Enhanced V3.1 Features"
LLM["LLM Client<br/>JSON Planner Proposals"]
SC["Shadow Comparison<br/>PlannerDecision"]
PM["Planner Metrics Store<br/>Performance Analytics"]
PCOMP["Planner Comparison Store<br/>Outcome Tracking"]
end
subgraph "Agent Skill System"
SR["SkillRouter<br/>Pattern Matching"]
SKR["SkillRunner<br/>Multi-turn Reasoning"]
STR["SkillToolRegistry<br/>Built-in Handlers"]
SK["SkillDefinition<br/>Manifest Schema"]
end
subgraph "Execution"
DEC["PlannerDecision"]
EVAL["Workflow Replay Evaluator"]
END["ChatResponse"]
SR --> SKR
SKR --> STR
STR --> LLM
WP --> DEC
DEC --> EVAL
DEC --> END
SC --> PM
SC --> PCOMP
```

**Diagram sources**
- [workflow_planner.py:90-134](file://src/sage_faculty_twin/workflow_planner.py#L90-L134)
- [workflow_steps.py:9-21](file://src/sage_faculty_twin/workflow_steps.py#L9-L21)
- [workflow_policy.py:64-199](file://src/sage_faculty_twin/workflow_policy.py#L64-L199)
- [workflow_context.py:12-37](file://src/sage_faculty_twin/workflow_context.py#L12-L37)
- [workflow_eval.py:53-94](file://src/sage_faculty_twin/workflow_eval.py#L53-L94)
- [service.py:5544-5583](file://src/sage_faculty_twin/service.py#L5544-L5583)
- [planner_metrics_store.py:75-85](file://src/sage_faculty_twin/planner_metrics_store.py#L75-L85)
- [planner_comparison_store.py:75-85](file://src/sage_faculty_twin/planner_comparison_store.py#L75-L85)
- [skill_router.py:22-123](file://src/sage_faculty_twin/skill_router.py#L22-L123)
- [skill_runner.py:24-219](file://src/sage_faculty_twin/skill_runner.py#L24-L219)
- [skill_tools.py:22-284](file://src/sage_faculty_twin/skill_tools.py#L22-L284)
- [skills.py:70-164](file://src/sage_faculty_twin/skills.py#L70-L164)

**Section sources**
- [workflow_planner.py:90-134](file://src/sage_faculty_twin/workflow_planner.py#L90-L134)
- [workflow_steps.py:179-184](file://src/sage_faculty_twin/workflow_steps.py#L179-L184)
- [workflow_policy.py:64-199](file://src/sage_faculty_twin/workflow_policy.py#L64-L199)
- [workflow_context.py:12-37](file://src/sage_faculty_twin/workflow_context.py#L12-L37)
- [workflow_eval.py:53-94](file://src/sage_faculty_twin/workflow_eval.py#L53-L94)
- [service.py:5544-5583](file://src/sage_faculty_twin/service.py#L5544-L5583)
- [planner_metrics_store.py:75-85](file://src/sage_faculty_twin/planner_metrics_store.py#L75-L85)
- [planner_comparison_store.py:75-85](file://src/sage_faculty_twin/planner_comparison_store.py#L75-L85)
- [skill_router.py:22-123](file://src/sage_faculty_twin/skill_router.py#L22-L123)
- [skill_runner.py:24-219](file://src/sage_faculty_twin/skill_runner.py#L24-L219)
- [skill_tools.py:22-284](file://src/sage_faculty_twin/skill_tools.py#L22-L284)
- [skills.py:70-164](file://src/sage_faculty_twin/skills.py#L70-L164)

## Core Components
- DeterministicWorkflowPlanner: constructs a PlanSpec from a WorkflowRequestContext, selects steps based on intent and context, computes risk level, and validates against policy.
- WorkflowStepDefinition: defines step semantics, required inputs, produced outputs, side effects, timeouts, and retry policy.
- WorkflowPolicy and WorkflowPolicyValidator: enforce allowed evidence sources, write-step enablement, latency budgets, and risk alignment.
- WorkflowRequestContext: normalizes request metadata into role_mode, journey_state, identity, and available evidence sources.
- PlannerDecision: encapsulates acceptance, validation errors, fallback, and the final PlanSpec.
- WorkflowReplayScenario and evaluator: define expected goals, fallback templates, required/forbidden steps, and validate planner decisions.
- **Enhanced V3.1**: LLM-assisted JSON planner with shadow comparison and metrics storage capabilities.
- **New**: SkillRouter: routes user questions to matching skills based on trigger patterns and compatibility checks.
- **New**: SkillRunner: executes skills with multi-turn tool-calling reasoning loops and manages conversation with LLM.
- **New**: SkillToolRegistry: maps handler names to Python callables for skill tool execution with built-in handlers.

**Section sources**
- [workflow_planner.py:90-134](file://src/sage_faculty_twin/workflow_planner.py#L90-L134)
- [workflow_steps.py:9-21](file://src/sage_faculty_twin/workflow_steps.py#L9-L21)
- [workflow_policy.py:15-48](file://src/sage_faculty_twin/workflow_policy.py#L15-L48)
- [workflow_context.py:12-37](file://src/sage_faculty_twin/workflow_context.py#L12-L37)
- [workflow_eval.py:13-34](file://src/sage_faculty_twin/workflow_eval.py#L13-L34)
- [skill_router.py:22-123](file://src/sage_faculty_twin/skill_router.py#L22-L123)
- [skill_runner.py:24-219](file://src/sage_faculty_twin/skill_runner.py#L24-L219)
- [skill_tools.py:22-284](file://src/sage_faculty_twin/skill_tools.py#L22-L284)

## Architecture Overview
The enhanced V3.1 system follows a deterministic planner with LLM-assisted capabilities and integrated skill system that:
- First checks for matching skills via pattern-matching router before building workflow plans
- Infers intent and context from the incoming request
- Builds a linear sequence of steps tailored to the intent
- Computes risk level from the strongest side effect among steps
- Validates the plan against policy constraints
- Generates shadow planner candidates for comparison
- Records metrics and comparison data for performance analysis
- Produces a PlannerDecision with optional fallback

```mermaid
sequenceDiagram
participant Client as "Caller"
participant Service as "DigitalTwinService"
participant SR as "SkillRouter"
participant SKR as "SkillRunner"
participant Planner as "DeterministicWorkflowPlanner"
participant LLM as "LLM Client"
participant Shadow as "Shadow Planner"
participant Policy as "WorkflowPolicyValidator"
participant Registry as "Step Registry"
participant Metrics as "Planner Metrics Store"
Client->>Service : "ChatRequest"
Service->>SR : "match(question)"
SR-->>Service : "matched_skill or None"
alt Skill Found
Service->>SKR : "run(matched_skill, skill_context)"
SKR->>LLM : "multi-turn tool-calling"
SKR-->>Service : "SkillResult(success/failure)"
alt Skill Success
Service-->>Client : "ChatResponse(skill_answer)"
else Skill Failure
Service->>Planner : "plan(context)"
end
else No Skill Match
Service->>Planner : "plan(context)"
end
Planner->>Registry : "lookup step definitions"
Planner-->>Service : "PlannerDecision(plan)"
Service->>Policy : "validate(plan, context)"
Policy-->>Service : "validation result"
Service->>LLM : "propose_shadow_plan_candidate_sync"
LLM-->>Service : "ShadowPlanCandidate"
Service->>Shadow : "evaluate_shadow_candidate"
Shadow->>Registry : "lookup step definitions"
Shadow-->>Service : "ShadowDecision"
Service->>Metrics : "record_entry(shadow)"
Service-->>Client : "PlannerDecision + shadow comparison"
```

**Diagram sources**
- [service.py:5406-5448](file://src/sage_faculty_twin/service.py#L5406-L5448)
- [service.py:5544-5583](file://src/sage_faculty_twin/service.py#L5544-L5583)
- [workflow_planner.py:110-134](file://src/sage_faculty_twin/workflow_planner.py#L110-L134)
- [workflow_planner.py:135-177](file://src/sage_faculty_twin/workflow_planner.py#L135-L177)
- [planner_metrics_store.py:87-121](file://src/sage_faculty_twin/planner_metrics_store.py#L87-L121)
- [skill_router.py:65-87](file://src/sage_faculty_twin/skill_router.py#L65-L87)
- [skill_runner.py:35-178](file://src/sage_faculty_twin/skill_runner.py#L35-L178)

## Detailed Component Analysis

### DeterministicWorkflowPlanner
- Purpose: Build a deterministic PlanSpec from a request context, compute risk level, and produce a PlannerDecision.
- Key behaviors:
  - Goal selection based on intent detection and context flags
  - Step assembly from a shared registry
  - Risk computation from the strongest side effect across steps
  - Evidence contract construction limiting allowed and forbidden sources
  - Validation via WorkflowPolicyValidator and fallback creation when rejected
  - Shadow candidate evaluation for safety checks

```mermaid
classDiagram
class DeterministicWorkflowPlanner {
+plan(context) PlannerDecision
+evaluate_plan(plan, context) PlannerDecision
+evaluate_shadow_candidate(candidate, context) PlannerDecision
-_build_plan(context) PlanSpec
-_build_evidence_contract(context, include_...) EvidenceContract
-_build_step_spec(step_id, goal) PlanStepSpec
-_merge_side_effect(current, candidate) str
}
class WorkflowPolicyValidator {
+validate(plan, context) PolicyValidationResult
}
class PlanSpec {
+plan_id : str
+planner_version : str
+policy_version : str
+planner_mode : str
+execution_mode : str
+goal : str
+risk_level : str
+profile_context : str
+journey_state : str
+estimated_latency_budget_ms : int
+requires_owner_review : bool
+evidence_contract : EvidenceContract
+steps : PlanStepSpec[]
+fallback_template : str
+fallback_reason : str?
+explain_to_operator : str
}
class PlanStepSpec {
+step_id : str
+reason : str
+inputs : str[]
+outputs : str[]
+side_effect : str
}
DeterministicWorkflowPlanner --> PlanSpec : "builds"
DeterministicWorkflowPlanner --> WorkflowPolicyValidator : "uses"
PlanSpec --> PlanStepSpec : "contains"
```

**Diagram sources**
- [workflow_planner.py:90-134](file://src/sage_faculty_twin/workflow_planner.py#L90-L134)
- [workflow_planner.py:53-88](file://src/sage_faculty_twin/workflow_planner.py#L53-L88)
- [workflow_planner.py:32-40](file://src/sage_faculty_twin/workflow_planner.py#L32-L40)
- [workflow_policy.py:64-199](file://src/sage_faculty_twin/workflow_policy.py#L64-L199)

**Section sources**
- [workflow_planner.py:110-134](file://src/sage_faculty_twin/workflow_planner.py#L110-L134)
- [workflow_planner.py:179-425](file://src/sage_faculty_twin/workflow_planner.py#L179-L425)
- [workflow_planner.py:427-446](file://src/sage_faculty_twin/workflow_planner.py#L427-L446)
- [workflow_planner.py:448-476](file://src/sage_faculty_twin/workflow_planner.py#L448-L476)

### Step Registry and Side Effects
- WorkflowStepDefinition defines:
  - step_id, description, required_inputs, produces_outputs
  - side_effect: none, draft_write, owner_review, admin_only
  - timeout_budget_ms and retry_policy
  - trace_key for observability
- The default registry includes retrieval, assembly, answer, scoring, rendering, and write-back steps.

```mermaid
classDiagram
class WorkflowStepDefinition {
+step_id : str
+description : str
+required_inputs : str[]
+produces_outputs : str[]
+side_effect : str
+admin_only : bool
+timeout_budget_ms : int
+retry_policy : str
+trace_key : str?
}
class StepRegistry {
+get_default_step_registry() dict~str, WorkflowStepDefinition~
}
StepRegistry --> WorkflowStepDefinition : "provides"
```

**Diagram sources**
- [workflow_steps.py:9-21](file://src/sage_faculty_twin/workflow_steps.py#L9-L21)
- [workflow_steps.py:179-184](file://src/sage_faculty_twin/workflow_steps.py#L179-L184)

**Section sources**
- [workflow_steps.py:9-21](file://src/sage_faculty_twin/workflow_steps.py#L9-L21)
- [workflow_steps.py:23-174](file://src/sage_faculty_twin/workflow_steps.py#L23-L174)
- [workflow_steps.py:179-184](file://src/sage_faculty_twin/workflow_steps.py#L179-L184)

### Policy and Risk Mapping
- WorkflowPolicy enforces:
  - max_stage_count, max_latency_budget_ms
  - allowed_evidence_sources and forbidden_evidence_sources
  - allowed_write_step_ids
- WorkflowPolicyValidator checks:
  - plan policy version alignment
  - step presence, uniqueness, and signature matching
  - admin-only step constraints and draft-write capability
  - evidence source validity per policy
  - latency budget alignment
  - risk level correctness via strongest side effect mapping

```mermaid
flowchart TD
Start(["Validate Plan"]) --> Version["Check policy version"]
Version --> StageCount["Check max stages"]
StageCount --> StepLoop["For each step:<br/>- lookup definition<br/>- compare inputs/outputs/side-effect<br/>- track side effect<br/>- update available values"]
StepLoop --> AdminCheck["Admin-only step requires admin identity"]
AdminCheck --> DraftCap["Non-none side effect requires draft-write capability"]
DraftCap --> EnabledCheck["Step enabled by allowed_write_step_ids"]
EnabledCheck --> LatencyBudget["Compare total vs plan latency budget"]
LatencyBudget --> EvidenceSources["Allowed sources vs context + policy"]
EvidenceSources --> RiskLevel["Risk level equals mapped strongest side effect"]
RiskLevel --> End(["Accept/Reject"])
```

**Diagram sources**
- [workflow_policy.py:74-199](file://src/sage_faculty_twin/workflow_policy.py#L74-L199)
- [workflow_policy.py:207-214](file://src/sage_faculty_twin/workflow_policy.py#L207-L214)

**Section sources**
- [workflow_policy.py:15-48](file://src/sage_faculty_twin/workflow_policy.py#L15-L48)
- [workflow_policy.py:64-199](file://src/sage_faculty_twin/workflow_policy.py#L64-L199)
- [workflow_policy.py:207-214](file://src/sage_faculty_twin/workflow_policy.py#L207-L214)

### Context Management
- WorkflowRequestContext normalizes:
  - role_mode (instructor, PI, researcher, collaboration contact, system operator)
  - journey_state (first-time visitor, course student, meeting candidate, etc.)
  - session_identity (anonymous, user, admin)
  - available_evidence_sources based on question, attachments, and flags
- Helper inference functions detect artifacts, booking intent, and profile/memory availability.

```mermaid
flowchart TD
Q["Incoming Question"] --> Role["Infer role_mode"]
Q --> Journey["Infer journey_state"]
Q --> Attachments["Compute attachment_count/media_types"]
Q --> Artifacts["Mention artifact?"]
Flags["Flags: recent/profile/artifact available"] --> Sources["Build available_evidence_sources"]
Role --> Ctx["Construct WorkflowRequestContext"]
Journey --> Ctx
Attachments --> Ctx
Artifacts --> Ctx
Sources --> Ctx
```

**Diagram sources**
- [workflow_context.py:38-112](file://src/sage_faculty_twin/workflow_context.py#L38-L112)
- [workflow_context.py:210-239](file://src/sage_faculty_twin/workflow_context.py#L210-L239)

**Section sources**
- [workflow_context.py:12-37](file://src/sage_faculty_twin/workflow_context.py#L12-L37)
- [workflow_context.py:38-112](file://src/sage_faculty_twin/workflow_context.py#L38-L112)
- [workflow_context.py:210-239](file://src/sage_faculty_twin/workflow_context.py#L210-L239)

### Shadow Planning and Safety
- ShadowPlanCandidate enables evaluating a read-only candidate plan with a subset of steps and evidence sources.
- Planner evaluates the candidate and returns a PlannerDecision with risk level computed from the strongest side effect.
- Tests demonstrate enabling artifact memory writes only under explicit archive requests and with draft-write capability.

```mermaid
sequenceDiagram
participant Planner as "DeterministicWorkflowPlanner"
participant Candidate as "ShadowPlanCandidate"
participant Registry as "Step Registry"
participant Policy as "WorkflowPolicyValidator"
Planner->>Planner : "_build_candidate_step_spec(step_id)"
Planner->>Registry : "lookup step definition"
Planner->>Planner : "compute estimated latency budget"
Planner->>Planner : "merge side effects"
Planner->>Policy : "evaluate_plan(plan, context)"
Policy-->>Planner : "PlannerDecision(accepted/validation_errors/fallback?)"
```

**Diagram sources**
- [workflow_planner.py:135-177](file://src/sage_faculty_twin/workflow_planner.py#L135-L177)
- [workflow_planner.py:462-472](file://src/sage_faculty_twin/workflow_planner.py#L462-L472)

**Section sources**
- [workflow_planner.py:135-177](file://src/sage_faculty_twin/workflow_planner.py#L135-L177)
- [test_dynamic_workflow_planner.py:308-355](file://tests/test_dynamic_workflow_planner.py#L308-L355)
- [test_dynamic_workflow_planner.py:357-400](file://tests/test_dynamic_workflow_planner.py#L357-L400)

### Planner Evaluation and Replay Scenarios
- WorkflowReplayScenario defines expected outcomes for a given ChatRequest.
- WorkflowReplayResult compares actual planner outputs to expectations.
- Tests validate deterministic planner behavior against curated scenarios.

```mermaid
sequenceDiagram
participant Loader as "load_workflow_replay_scenarios"
participant Planner as "DeterministicWorkflowPlanner"
participant Evaluator as "evaluate_workflow_replay_scenarios"
Loader-->>Evaluator : "list of scenarios"
loop for each scenario
Evaluator->>Planner : "plan(context)"
Planner-->>Evaluator : "PlannerDecision"
Evaluator-->>Evaluator : "compare goal/fallback/required/forbidden steps"
end
Evaluator-->>Caller : "list of results"
```

**Diagram sources**
- [workflow_eval.py:45-94](file://src/sage_faculty_twin/workflow_eval.py#L45-L94)
- [test_workflow_eval.py:11-28](file://tests/test_workflow_eval.py#L11-L28)

**Section sources**
- [workflow_eval.py:13-34](file://src/sage_faculty_twin/workflow_eval.py#L13-L34)
- [workflow_eval.py:45-94](file://src/sage_faculty_twin/workflow_eval.py#L45-L94)
- [test_workflow_eval.py:11-28](file://tests/test_workflow_eval.py#L11-L28)

## Agent Skill System Integration

### Service Integration Points
The DigitalTwinService now integrates the skill system as the first line of defense before standard workflow execution:
- **Skill Routing Phase**: Check if a skill matches the user's question before building workflow plans
- **Skill Execution Phase**: If matched, execute the skill with multi-turn reasoning and tool-calling
- **Fallback Logic**: If skill fails or returns non-success, fall back to standard workflow planner
- **Response Handling**: Return skill answers with workflow_action="skill_answer" and decision_mode="skill:{skill_id}"

```mermaid
flowchart TD
Start(["ChatRequest Received"]) --> CheckSkill["SkillRouter.match(question)"]
CheckSkill --> HasSkill{"Skill Matched?"}
HasSkill --> |Yes| BuildContext["Build SkillContext"]
BuildContext --> ExecuteSkill["SkillRunner.run(skill, context)"]
ExecuteSkill --> SkillSuccess{"Skill Success?"}
SkillSuccess --> |Yes| ReturnSkill["Return ChatResponse(skill_answer)"]
SkillSuccess --> |No| BuildWorkflow["Build WorkflowRequestContext"]
HasSkill --> |No| BuildWorkflow
BuildWorkflow --> StandardPipeline["Standard Workflow Pipeline"]
StandardPipeline --> ReturnWorkflow["Return PlannerDecision Response"]
```

**Diagram sources**
- [service.py:5406-5448](file://src/sage_faculty_twin/service.py#L5406-L5448)
- [service.py:5450-5523](file://src/sage_faculty_twin/service.py#L5450-L5523)

**Section sources**
- [service.py:5406-5448](file://src/sage_faculty_twin/service.py#L5406-L5448)
- [service.py:5450-5523](file://src/sage_faculty_twin/service.py#L5450-L5523)

## Skill Router and Pattern Matching

### Pattern-Matching Algorithm
The SkillRouter implements intelligent pattern-matching to select appropriate skills:
- **Trigger Pattern Matching**: Case-insensitive substring matching within user questions
- **Priority Ordering**: First matching enabled skill wins (order matters)
- **Compatibility Checking**: Filters skills by minimum app version requirements
- **Logging and Debugging**: Comprehensive logging for skill matching events

```mermaid
classDiagram
class SkillRouter {
+__init__(skill_dir : Path, current_version : str)
+_load(skill_dir : Path | str)
+match(question : str) SkillDefinition | None
+match_all(question : str) SkillDefinition[]
+get_all_skills() SkillDefinition[]
+get_enabled_skills() SkillDefinition[]
+get_skill_by_id(skill_id : str) SkillDefinition | None
}
class SkillDefinition {
+skill_id : str
+name : str
+description : str
+trigger_patterns : str[]
+system_prompt : str
+user_prompt_template : str
+tools : SkillToolDefinition[]
+max_turns : int
+output_format : str
+enabled : bool
+min_app_version : str
}
SkillRouter --> SkillDefinition : "manages"
```

**Diagram sources**
- [skill_router.py:22-123](file://src/sage_faculty_twin/skill_router.py#L22-L123)
- [skills.py:70-94](file://src/sage_faculty_twin/skills.py#L70-L94)

**Section sources**
- [skill_router.py:22-123](file://src/sage_faculty_twin/skill_router.py#L22-L123)
- [skills.py:70-94](file://src/sage_faculty_twin/skills.py#L70-L94)

### Skill Loading and Compatibility
- **Manifest Loading**: Loads all skill JSON manifests from the configured skill directory
- **Filtering Logic**: Excludes disabled skills and incompatible versions
- **Version Compatibility**: Uses semantic version comparison for minimum app version requirements
- **Logging**: Detailed logging for loaded skills, disabled skills, and compatibility issues

**Section sources**
- [skill_router.py:35-63](file://src/sage_faculty_twin/skill_router.py#L35-L63)
- [skills.py:122-129](file://src/sage_faculty_twin/skills.py#L122-L129)

## Skill Runner and Multi-Turn Reasoning

### Multi-Turn Tool-Calling Loop
The SkillRunner executes skills with sophisticated multi-turn reasoning:
- **Initial Message Building**: Formats system and user prompts with template variables
- **Tool Definition Conversion**: Converts skill tools to OpenAI function-calling format
- **Multi-Turn Loop**: Iterative reasoning with LLM tool-calling until completion or max turns
- **Result Aggregation**: Collects tool results and maintains conversation context
- **Error Handling**: Graceful degradation with detailed error reporting

```mermaid
sequenceDiagram
participant Runner as "SkillRunner"
participant LLM as "VllmChatClient"
participant Tools as "SkillToolRegistry"
Runner->>Runner : "Build initial messages"
Runner->>LLM : "chat_with_tools_sync(messages, tools)"
LLM-->>Runner : "response(tool_calls/content)"
alt Has Tool Calls
Runner->>Tools : "execute(handler, arguments)"
Tools-->>Runner : "tool_result"
Runner->>Runner : "append tool result to messages"
Runner->>LLM : "next iteration"
else No Tool Calls
Runner-->>Caller : "SkillResult(final answer)"
end
```

**Diagram sources**
- [skill_runner.py:35-178](file://src/sage_faculty_twin/skill_runner.py#L35-L178)
- [skill_runner.py:213-218](file://src/sage_faculty_twin/skill_runner.py#L213-L218)

**Section sources**
- [skill_runner.py:24-219](file://src/sage_faculty_twin/skill_runner.py#L24-L219)

### Single-Turn Execution
Skills without tools execute as single-turn responses:
- **Template Processing**: Formats system and user prompts
- **Direct LLM Call**: Uses answer_question_sync for tool-less skills
- **Error Recovery**: Graceful handling of LLM failures
- **Result Packaging**: Returns SkillResult with appropriate metadata

**Section sources**
- [skill_runner.py:180-212](file://src/sage_faculty_twin/skill_runner.py#L180-L212)

## Skill Tool Registry and Function Calling

### Built-in Tool Handlers
The SkillToolRegistry provides essential functionality for skills:
- **Knowledge Search**: Query knowledge base with filtering by tags and limits
- **Memory Search**: Search conversation memory with context scoping
- **Team Schedule**: Retrieve team availability and meeting schedules
- **Blockers**: Get unresolved items and pending issues
- **Paper Digest**: Extract paper summaries and research highlights
- **Courseware**: Access course materials and teaching resources
- **Writing Rubric**: Retrieve evaluation criteria and assessment guidelines

```mermaid
classDiagram
class SkillToolRegistry {
+__init__(knowledge_store : LocalKnowledgeStore, memory_store : ConversationMemoryStore)
+_register_builtins()
+register(handler_name : str, handler : Callable) void
+has_handler(handler_name : str) bool
+execute(handler_name : str, arguments : dict) str
+list_handlers() str[]
}
class KnowledgeStore {
+search(query : str, top_k : int) SearchHit[]
}
class MemoryStore {
+search(query : str, limit : int, conversation_id : str) dict
}
SkillToolRegistry --> KnowledgeStore : "uses"
SkillToolRegistry --> MemoryStore : "uses"
```

**Diagram sources**
- [skill_tools.py:22-71](file://src/sage_faculty_twin/skill_tools.py#L22-L71)
- [skill_tools.py:74-284](file://src/sage_faculty_twin/skill_tools.py#L74-L284)

**Section sources**
- [skill_tools.py:22-284](file://src/sage_faculty_twin/skill_tools.py#L22-L284)

### Tool Handler Implementation
Each built-in handler provides specific functionality:
- **Knowledge Search**: Full-text search with tag filtering and result limiting
- **Memory Search**: Context-aware conversation memory retrieval
- **Schedule Retrieval**: Team availability and meeting slot discovery
- **Progress Tracking**: Blocker identification and unresolved item management
- **Resource Discovery**: Paper summaries and course materials
- **Assessment Criteria**: Writing rubrics and evaluation standards

**Section sources**
- [skill_tools.py:74-284](file://src/sage_faculty_twin/skill_tools.py#L74-L284)

## Skill Manifest Structure and Examples

### Skill Definition Schema
Skills are defined through JSON manifests with comprehensive structure:
- **Core Identity**: skill_id, name, description for clear identification
- **Trigger Patterns**: Multiple keywords/phrases for flexible matching
- **Prompt Templates**: System and user prompt templates with variable substitution
- **Tool Definitions**: Function-calling specifications with parameters
- **Execution Configuration**: Turn limits, output formats, and composition rules
- **Lifecycle Management**: Enable/disable flags and version compatibility

```mermaid
classDiagram
class SkillDefinition {
+skill_id : str
+name : str
+description : str
+trigger_patterns : str[]
+system_prompt : str
+user_prompt_template : str
+tools : SkillToolDefinition[]
+max_turns : int
+output_format : str
+composes_with : str[]
+enabled : bool
+min_app_version : str
}
class SkillToolDefinition {
+tool_id : str
+name : str
+description : str
+parameters : dict~str, SkillToolParameter~
+handler : str
}
class SkillToolParameter {
+type : str
+description : str
+default : Any
+required : bool
}
SkillDefinition --> SkillToolDefinition : "contains"
SkillToolDefinition --> SkillToolParameter : "uses"
```

**Diagram sources**
- [skills.py:70-94](file://src/sage_faculty_twin/skills.py#L70-L94)
- [skills.py:37-67](file://src/sage_faculty_twin/skills.py#L37-L67)
- [skills.py:19-35](file://src/sage_faculty_twin/skills.py#L19-L35)

**Section sources**
- [skills.py:70-164](file://src/sage_faculty_twin/skills.py#L70-L164)

### Real-World Skill Examples

#### Course Advising Skill
Provides academic guidance for course selection and study planning:
- **Trigger Patterns**: "选课", "课程推荐", "course recommendation", "study plan"
- **Tools**: Courseware search, knowledge base queries, memory context
- **Output Format**: Free-form responses with personalized recommendations
- **Purpose**: Help students navigate course selection and academic planning

#### Meeting Preparation Skill
Assists with organizing team meetings and preparation:
- **Trigger Patterns**: "组会", "准备会议", "meeting prep", "weekly meeting"
- **Tools**: Team schedule retrieval, blocker identification, progress searches
- **Output Format**: Structured JSON for meeting agendas and preparation
- **Purpose**: Streamline meeting coordination and preparation processes

**Section sources**
- [course_advising.json:1-77](file://data/skills/course_advising.json#L1-L77)
- [meeting_prep.json:1-85](file://data/skills/meeting_prep.json#L1-L85)

## Enhanced V3.1 LLM-Assisted JSON Planner

### LLM Client Integration
The V3.1 system introduces enhanced LLM-assisted planning capabilities through the LLM client integration:
- **JSON Planner Proposals**: The LLM client generates structured JSON plan candidates for shadow evaluation
- **Shadow Plan Candidates**: Structured proposals with step IDs, goals, and evidence requirements
- **Configurable Parameters**: Temperature, max tokens, and enablement controls for shadow planning

```mermaid
classDiagram
class LLMClient {
+propose_shadow_plan_candidate_sync(context, plan) ShadowPlanCandidate
+shadow_planner_enabled : bool
+shadow_planner_temperature : float
+shadow_planner_max_tokens : int
}
class ShadowPlanCandidate {
+goal : str
+step_ids : str[]
+requires_citations : bool
+allowed_sources : set~str~
+fallback_template : str
+explain_to_operator : str
}
LLMClient --> ShadowPlanCandidate : "generates"
```

**Diagram sources**
- [service.py:5562-5572](file://src/sage_faculty_twin/service.py#L5562-L5572)
- [config.py:98-100](file://src/sage_faculty_twin/config.py#L98-L100)

**Section sources**
- [service.py:5544-5583](file://src/sage_faculty_twin/service.py#L5544-L5583)
- [config.py:98-100](file://src/sage_faculty_twin/config.py#L98-L100)

### Shadow Planner Evaluation Process
The enhanced shadow comparison process includes:
- **Benchmark Filtering**: Automatic disabling for benchmark evaluation requests
- **Client Capability Detection**: Checks for `propose_shadow_plan_candidate_sync` method
- **Exception Handling**: Graceful degradation with shadow_error status
- **Status Classification**: shadow_disabled, shadow_ready, shadow_error states

```mermaid
flowchart TD
Start(["Shadow Planning Request"]) --> Benchmark{"Benchmark Request?"}
Benchmark --> |Yes| Disabled["Return shadow_disabled"]
Benchmark --> |No| Enabled{"Shadow Planner Enabled?"}
Enabled --> |No| Disabled
Enabled --> |Yes| ClientCheck{"LLM Client Supports Proposal?"}
ClientCheck --> |No| Disabled
ClientCheck --> |Yes| Generate["Generate Shadow Candidate"]
Generate --> Evaluate["Evaluate Shadow Candidate"]
Evaluate --> Success{"Evaluation Success?"}
Success --> |Yes| Ready["Return shadow_ready"]
Success --> |No| Error["Return shadow_error"]
```

**Diagram sources**
- [service.py:5544-5583](file://src/sage_faculty_twin/service.py#L5544-L5583)

**Section sources**
- [service.py:5544-5583](file://src/sage_faculty_twin/service.py#L5544-L5583)

## Shadow Comparison and Safety Mechanisms

### Planner Comparison Store
The system maintains detailed comparison records between deterministic and shadow planner outcomes:
- **Comparison Status Tracking**: different_steps, different_goal, shadow_error, shadow_disabled
- **Actionable Insights**: automatic filtering for operational review
- **Historical Analysis**: persistent storage for trend monitoring

```mermaid
classDiagram
class PlannerComparisonStore {
+record_comparison(conversation_id, workflow_action, question, comparison_status, deterministic_goal, shadow_goal, same_goal, same_fallback_template, deterministic_only_steps, shadow_only_steps, summary) PlannerComparisonEntry
+list_records(limit, actionable_only) PlannerComparisonEntry[]
+count_records() int
+count_actionable_records() int
+count_status(comparison_status) int
}
class PlannerComparisonEntry {
+record_id : str
+conversation_id : str
+workflow_action : str
+question : str
+comparison_status : str
+deterministic_goal : str
+shadow_goal : str
+same_goal : bool
+same_fallback_template : bool
+deterministic_only_steps : str[]
+shadow_only_steps : str[]
+summary : str
+created_at : datetime
}
PlannerComparisonStore --> PlannerComparisonEntry : "stores"
```

**Diagram sources**
- [planner_comparison_store.py:75-121](file://src/sage_faculty_twin/planner_comparison_store.py#L75-L121)
- [planner_comparison_store.py:14-33](file://src/sage_faculty_twin/planner_comparison_store.py#L14-L33)

**Section sources**
- [planner_comparison_store.py:75-121](file://src/sage_faculty_twin/planner_comparison_store.py#L75-L121)
- [planner_comparison_store.py:14-33](file://src/sage_faculty_twin/planner_comparison_store.py#L14-L33)

### Shadow Preview Generation
The system provides comprehensive preview capabilities for shadow planner outcomes:
- **Disabled State**: Clear messaging when shadow planning is not available
- **Pending State**: Indicates ongoing shadow evaluation
- **Error State**: Captures and reports shadow planner failures
- **Explainability**: Operator-facing explanations for shadow planner decisions

**Section sources**
- [service.py:2049-2076](file://src/sage_faculty_twin/service.py#L2049-L2076)

## Planner Metrics Storage and Analytics

### Metrics Data Model
The planner metrics system captures comprehensive performance data:
- **Stage Classification**: deterministic vs shadow planning stages
- **Performance Metrics**: latency measurements, acceptance rates, fallback statistics
- **Operational Insights**: rejection reasons, step-specific failures, template usage
- **Quality Indicators**: average/max latency, error rates, acceptance rates

```mermaid
classDiagram
class PlannerMetricsStore {
+record_entry(conversation_id, planner_stage, planner_mode, question, goal, accepted, status, fallback_template, fallback_reason, validation_errors, planned_steps, latency_ms) PlannerMetricsEntry
+list_entries(limit) PlannerMetricsEntry[]
+count_entries() int
+build_summary() dict~str, object~
}
class PlannerMetricsEntry {
+record_id : str
+conversation_id : str
+planner_stage : str
+planner_mode : str
+question : str
+goal : str
+accepted : bool
+status : str
+fallback_template : str
+fallback_reason : str
+validation_errors : str[]
+planned_steps : str[]
+latency_ms : float
+created_at : datetime
}
PlannerMetricsStore --> PlannerMetricsEntry : "stores"
```

**Diagram sources**
- [planner_metrics_store.py:75-121](file://src/sage_faculty_twin/planner_metrics_store.py#L75-L121)
- [planner_metrics_store.py:16-31](file://src/sage_faculty_twin/planner_metrics_store.py#L16-L31)

**Section sources**
- [planner_metrics_store.py:75-121](file://src/sage_faculty_twin/planner_metrics_store.py#L75-L121)
- [planner_metrics_store.py:16-31](file://src/sage_faculty_twin/planner_metrics_store.py#L16-L31)

### Metrics Collection Process
The metrics collection process captures data at multiple stages:
- **Deterministic Planning**: Records baseline performance and outcomes
- **Shadow Planning**: Captures comparison results and performance differences
- **Fallback Analysis**: Tracks rejection reasons and template usage
- **Step-Level Insights**: Identifies problematic steps and patterns

```mermaid
sequenceDiagram
participant Service as "DigitalTwinService"
participant Metrics as "PlannerMetricsStore"
participant Decision as "PlannerDecision"
Service->>Metrics : "record_entry(deterministic)"
Service->>Service : "shadow planning"
Service->>Metrics : "record_entry(shadow)"
Service->>Service : "comparison analysis"
Service->>Service : "persist comparison result"
```

**Diagram sources**
- [service.py:5404-5412](file://src/sage_faculty_twin/service.py#L5404-L5412)
- [service.py:6710-6723](file://src/sage_faculty_twin/service.py#L6710-L6723)
- [service.py:6725-6756](file://src/sage_faculty_twin/service.py#L6725-L6756)

**Section sources**
- [service.py:5404-5412](file://src/sage_faculty_twin/service.py#L5404-L5412)
- [service.py:6710-6723](file://src/sage_faculty_twin/service.py#L6710-L6723)
- [service.py:6725-6756](file://src/sage_faculty_twin/service.py#L6725-L6756)

### Analytics and Reporting
The system provides comprehensive analytics capabilities:
- **Acceptance Rates**: Deterministic vs shadow planner acceptance metrics
- **Latency Analysis**: Average and maximum latency comparisons
- **Error Pattern Recognition**: Common rejection reasons and step failures
- **Template Usage**: Fallback template effectiveness tracking
- **Operational Dashboards**: Real-time monitoring of planner performance

**Section sources**
- [planner_metrics_store.py:132-186](file://src/sage_faculty_twin/planner_metrics_store.py#L132-L186)

## Dependency Analysis
- Planner depends on:
  - Step registry for step semantics
  - Policy for constraints and risk mapping
  - Context for intent and evidence source inference
  - LLM client for shadow planning proposals
- Policy validator depends on:
  - Policy configuration
  - Step registry for signature checks
  - Context for input availability
- Metrics store depends on:
  - App settings for configuration
  - SQLite database for persistence
  - JSON serialization for data interchange
- **New**: Skill Router depends on:
  - Skill definitions loaded from JSON manifests
  - Version compatibility checking
  - Logging for skill matching events
- **New**: Skill Runner depends on:
  - LLM client for multi-turn reasoning
  - Skill tool registry for function calling
  - Template processing for prompt formatting
- Tests validate:
  - Policy loading and enforcement
  - Scenario-based replay acceptance
  - Shadow candidate evaluation and fallback behavior
  - Metrics collection and analytics
  - **New**: Skill manifest loading and compatibility
  - **New**: Skill routing and execution patterns

```mermaid
graph LR
CTX["WorkflowRequestContext"] --> PLAN["DeterministicWorkflowPlanner"]
PLAN --> REG["Step Registry"]
PLAN --> POL["WorkflowPolicy"]
PLAN --> LLM["LLM Client"]
PLAN --> DEC["PlannerDecision"]
POL --> VAL["WorkflowPolicyValidator"]
VAL --> REG
VAL --> CTX
LLM --> SHADOW["Shadow Plan Candidate"]
SHADOW --> METRICS["Planner Metrics Store"]
SHADOW --> COMPARE["Planner Comparison Store"]
EVAL["Workflow Replay Evaluator"] --> DEC
SR["SkillRouter"] --> SKR["SkillRunner"]
SKR --> STR["SkillToolRegistry"]
STR --> LLM
SR --> SK["SkillDefinition"]
```

**Diagram sources**
- [workflow_planner.py:90-134](file://src/sage_faculty_twin/workflow_planner.py#L90-L134)
- [workflow_policy.py:64-199](file://src/sage_faculty_twin/workflow_policy.py#L64-L199)
- [workflow_steps.py:179-184](file://src/sage_faculty_twin/workflow_steps.py#L179-L184)
- [workflow_eval.py:53-94](file://src/sage_faculty_twin/workflow_eval.py#L53-L94)
- [service.py:5544-5583](file://src/sage_faculty_twin/service.py#L5544-L5583)
- [planner_metrics_store.py:75-85](file://src/sage_faculty_twin/planner_metrics_store.py#L75-L85)
- [planner_comparison_store.py:75-85](file://src/sage_faculty_twin/planner_comparison_store.py#L75-L85)
- [skill_router.py:22-123](file://src/sage_faculty_twin/skill_router.py#L22-L123)
- [skill_runner.py:24-219](file://src/sage_faculty_twin/skill_runner.py#L24-L219)
- [skill_tools.py:22-284](file://src/sage_faculty_twin/skill_tools.py#L22-L284)

**Section sources**
- [workflow_planner.py:90-134](file://src/sage_faculty_twin/workflow_planner.py#L90-L134)
- [workflow_policy.py:64-199](file://src/sage_faculty_twin/workflow_policy.py#L64-L199)
- [workflow_steps.py:179-184](file://src/sage_faculty_twin/workflow_steps.py#L179-L184)
- [workflow_eval.py:53-94](file://src/sage_faculty_twin/workflow_eval.py#L53-L94)
- [service.py:5544-5583](file://src/sage_faculty_twin/service.py#L5544-L5583)
- [planner_metrics_store.py:75-85](file://src/sage_faculty_twin/planner_metrics_store.py#L75-L85)
- [planner_comparison_store.py:75-85](file://src/sage_faculty_twin/planner_comparison_store.py#L75-L85)
- [skill_router.py:22-123](file://src/sage_faculty_twin/skill_router.py#L22-L123)
- [skill_runner.py:24-219](file://src/sage_faculty_twin/skill_runner.py#L24-L219)
- [skill_tools.py:22-284](file://src/sage_faculty_twin/skill_tools.py#L22-L284)

## Performance Considerations
- Timeout budgets: Each step defines a timeout_budget_ms; total latency is compared against the plan's estimated_latency_budget_ms.
- Latency budget limits: Policy enforces max_latency_budget_ms to cap end-to-end cost.
- Deterministic planning avoids expensive retrieval for simple greetings and reduces redundant memory retrievals when recent session context is attached.
- Shadow planning can be disabled for benchmark scenarios to minimize overhead.
- **Enhanced V3.1**: Shadow planning adds minimal overhead for comparison while providing valuable safety insights.
- **Metrics Overhead**: Persistent metrics storage uses SQLite database with efficient indexing and JSON serialization.
- **Configuration Control**: Shadow planner can be globally enabled/disabled via configuration settings.
- **Skill System Overhead**: Pattern matching and skill execution add minimal latency compared to full workflow planning.
- **Skill Tool Calls**: Each tool execution adds LLM call overhead; consider tool call limits and caching strategies.

## Troubleshooting Guide
Common issues and resolutions:
- Plan rejected due to mismatched step signatures: Ensure step inputs/outputs/side-effect match the registry definition.
- Forbidden evidence sources: Remove references to forbidden sources (e.g., private_student_record_without_consent) or adjust policy.
- Exceeded stage or latency budget: Reduce step count or increase estimated_latency_budget_ms within policy limits.
- Admin-only steps: Verify session_identity is admin or remove admin-only steps.
- Missing draft-write capability: Enable allow_draft_write when appropriate for write-side-effect steps.
- **Shadow Planner Issues**: 
  - Check LLM client implementation supports `propose_shadow_plan_candidate_sync`
  - Verify `shadow_planner_enabled` configuration is True
  - Review shadow planner temperature and max_tokens settings
  - Monitor shadow_error status codes for detailed failure information
- **Metrics and Analytics**:
  - Verify planner_metrics_dir configuration points to writable location
  - Check SQLite database connectivity for metrics storage
  - Review comparison store for actionable insights
  - Monitor acceptance rates and error patterns for system health
- **Skill System Issues**:
  - Verify skill_dir configuration points to valid directory
  - Check skill manifest JSON syntax and required fields
  - Ensure skill trigger patterns are case-insensitive and match user queries
  - Verify skill tool handlers are properly registered in SkillToolRegistry
  - Monitor skill execution logs for tool call failures and template errors
  - Check version compatibility between skills and application
- **Integration Issues**:
  - Verify SkillRouter loads skills successfully during service initialization
  - Check that SkillRunner receives proper SkillContext with all required fields
  - Ensure LLM client is properly configured for both workflow and skill execution
  - Monitor fallback behavior when skills fail or return non-success results

**Section sources**
- [workflow_policy.py:74-199](file://src/sage_faculty_twin/workflow_policy.py#L74-L199)
- [test_workflow_policy.py:60-99](file://tests/test_workflow_policy.py#L60-L99)
- [service.py:5559-5568](file://src/sage_faculty_twin/service.py#L5559-L5568)
- [planner_metrics_store.py:75-85](file://src/sage_faculty_twin/planner_metrics_store.py#L75-L85)
- [skill_router.py:35-63](file://src/sage_faculty_twin/skill_router.py#L35-L63)
- [skill_runner.py:91-98](file://src/sage_faculty_twin/skill_runner.py#L91-L98)
- [skill_tools.py:61-66](file://src/sage_faculty_twin/skill_tools.py#L61-L66)

## Conclusion
The enhanced V3.1 workflow system combines deterministic planning, strict step registry validation, and policy-driven enforcement with advanced LLM-assisted capabilities and a powerful agent skill system. The integration of the skill router and skill runner provides intelligent query routing for specialized tasks, while the workflow planner handles general-purpose interactions. The addition of shadow comparison functionality and comprehensive metrics storage provides unprecedented visibility into planner performance and safety. The agent skill system offers extensible, self-contained capabilities through skill manifests, pattern matching, and multi-turn reasoning loops. Extensibility is achieved through configurable LLM integration, modular step definitions, comprehensive analytics infrastructure, and the skill system's manifest-based approach.

## Appendices

### Example Workflows and Execution Patterns
- Course grounding: Detect profile context → classify intent → hybrid knowledge retrieval → assemble prompt → answer with citations → score memory usefulness → render user response.
- Booking preparation: Stay read-only; avoid booking drafts; leverage knowledge and memory to advise.
- Artifact-aware research: Combine research knowledge with artifact memory and profile memory when consent and context permit.
- Simple greeting: Minimal steps; skip retrieval to reduce latency.
- **Enhanced V3.1 Shadow Comparison**: Automatic shadow planning for complex queries with detailed metrics tracking and comparison reporting.
- **New Skill System Integration**: Pattern-matching router identifies specialized queries → skill execution with multi-turn reasoning → fallback to workflow planner when needed.

**Section sources**
- [test_dynamic_workflow_planner.py:47-79](file://tests/test_dynamic_workflow_planner.py#L47-L79)
- [test_dynamic_workflow_planner.py:81-102](file://tests/test_dynamic_workflow_planner.py#L81-L102)
- [test_dynamic_workflow_planner.py:191-220](file://tests/test_dynamic_workflow_planner.py#L191-L220)
- [test_dynamic_workflow_planner.py:263-288](file://tests/test_dynamic_workflow_planner.py#L263-L288)
- [course_advising.json:1-77](file://data/skills/course_advising.json#L1-L77)
- [meeting_prep.json:1-85](file://data/skills/meeting_prep.json#L1-L85)

### Extending the System
- Adding a new step:
  - Define a new WorkflowStepDefinition with required_inputs, produces_outputs, side_effect, and timeout_budget_ms.
  - Register it in the default registry and ensure policy allows it if it has side effects.
- Updating policy:
  - Modify allowed_evidence_sources, allowed_write_step_ids, or max_latency_budget_ms.
  - Load custom policy via service initialization to override defaults.
- **Enhanced V3.1 Integration**:
  - Implement LLM client with `propose_shadow_plan_candidate_sync` method for shadow planning
  - Configure shadow planner settings in AppSettings
  - Set up metrics storage directories for performance tracking
  - Integrate comparison store for operational monitoring
- **New Skill System Extension**:
  - Create skill manifest JSON with required fields (skill_id, trigger_patterns, system_prompt, etc.)
  - Implement tool handlers in SkillToolRegistry for custom functionality
  - Test skill loading and compatibility with SkillRouter
  - Configure skill directory in AppSettings (skill_dir)
  - Monitor skill execution logs and performance metrics

**Section sources**
- [workflow_steps.py:23-174](file://src/sage_faculty_twin/workflow_steps.py#L23-L174)
- [workflow_steps.py:179-184](file://src/sage_faculty_twin/workflow_steps.py#L179-L184)
- [workflow_policy.py:54-62](file://src/sage_faculty_twin/workflow_policy.py#L54-L62)
- [test_workflow_policy.py:60-99](file://tests/test_workflow_policy.py#L60-L99)
- [config.py:90-100](file://src/sage_faculty_twin/config.py#L90-L100)
- [service.py:5562-5572](file://src/sage_faculty_twin/service.py#L5562-L5572)
- [planner_metrics_store.py:75-85](file://src/sage_faculty_twin/planner_metrics_store.py#L75-L85)
- [planner_comparison_store.py:75-85](file://src/sage_faculty_twin/planner_comparison_store.py#L75-L85)
- [skill_router.py:35-63](file://src/sage_faculty_twin/skill_router.py#L35-L63)
- [skill_tools.py:35-44](file://src/sage_faculty_twin/skill_tools.py#L35-L44)
- [config.py:123](file://src/sage_faculty_twin/config.py#L123)

### Configuration Settings
Key configuration parameters for V3.1 enhancements:
- `shadow_planner_enabled`: Global toggle for shadow planning functionality
- `shadow_planner_temperature`: LLM sampling temperature for shadow candidates
- `shadow_planner_max_tokens`: Maximum tokens for shadow plan generation
- `planner_metrics_dir`: Directory for metrics storage and analytics
- `planner_comparison_dir`: Directory for comparison result tracking
- `skill_dir`: Directory containing skill manifest JSON files
- `llm_policy_enabled`: Policy-driven LLM configuration for adaptive control

**Section sources**
- [config.py:90-100](file://src/sage_faculty_twin/config.py#L90-L100)
- [config.py:123](file://src/sage_faculty_twin/config.py#L123)
- [models.py:579](file://src/sage_faculty_twin/models.py#L579)
- [test_skills.py:39-44](file://tests/test_skills.py#L39-L44)