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
- [test_dynamic_workflow_planner.py](file://tests/test_dynamic_workflow_planner.py)
- [test_workflow_policy.py](file://tests/test_workflow_policy.py)
- [test_workflow_eval.py](file://tests/test_workflow_eval.py)
</cite>

## Update Summary
**Changes Made**
- Added comprehensive documentation for Enhanced V3.1 LLM-Assisted JSON Planner implementation
- Documented shadow comparison functionality with shadow planner evaluation
- Added planner metrics storage and analytics capabilities
- Updated architecture diagrams to reflect new shadow planning and metrics components
- Enhanced troubleshooting guide with shadow planner and metrics monitoring

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Enhanced V3.1 LLM-Assisted JSON Planner](#enhanced-v31-llm-assisted-json-planner)
7. [Shadow Comparison and Safety Mechanisms](#shadow-comparison-and-safety-mechanisms)
8. [Planner Metrics Storage and Analytics](#planner-metrics-storage-and-analytics)
9. [Dependency Analysis](#dependency-analysis)
10. [Performance Considerations](#performance-considerations)
11. [Troubleshooting Guide](#troubleshooting-guide)
12. [Conclusion](#conclusion)
13. [Appendices](#appendices)

## Introduction
This document explains the workflow planning and execution system that powers deterministic, step-based, policy-driven interactions. The system has been enhanced with V3.1 capabilities including LLM-assisted JSON planning, shadow comparison functionality, and comprehensive planner metrics storage. It covers:
- Deterministic workflow architecture and step-based processing model
- Policy-driven decision making and risk/risk-level mapping
- Enhanced LLM-assisted JSON planner implementation with shadow comparison
- Planner metrics storage and analytics for performance monitoring
- Fallback mechanisms and planner comparison
- Integration with memory systems, knowledge retrieval, and LLM processing
- Guidance for extending the system with custom steps and policies

## Project Structure
The workflow system is centered around five core modules with enhanced V3.1 capabilities:
- Planner: builds plans from natural-language intents and context with LLM assistance
- Steps: a registry of executable steps with side effects and timeouts
- Policy: enforces constraints on evidence sources, write steps, latency, and risk
- Context: captures request metadata, roles, journey state, and available evidence sources
- Metrics: stores and analyzes planner performance and comparison data
- Comparison: tracks deterministic vs shadow planner outcomes

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
subgraph "Execution"
DEC["PlannerDecision"]
EVAL["Workflow Replay Evaluator"]
end
CTX --> WP
WP --> ST
WP --> PC
WP --> LLM
WP --> SC
SC --> PM
SC --> PCOMP
DEC --> EVAL
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

**Section sources**
- [workflow_planner.py:90-134](file://src/sage_faculty_twin/workflow_planner.py#L90-L134)
- [workflow_steps.py:179-184](file://src/sage_faculty_twin/workflow_steps.py#L179-L184)
- [workflow_policy.py:64-199](file://src/sage_faculty_twin/workflow_policy.py#L64-L199)
- [workflow_context.py:12-37](file://src/sage_faculty_twin/workflow_context.py#L12-L37)
- [workflow_eval.py:53-94](file://src/sage_faculty_twin/workflow_eval.py#L53-L94)
- [service.py:5544-5583](file://src/sage_faculty_twin/service.py#L5544-L5583)
- [planner_metrics_store.py:75-85](file://src/sage_faculty_twin/planner_metrics_store.py#L75-L85)
- [planner_comparison_store.py:75-85](file://src/sage_faculty_twin/planner_comparison_store.py#L75-L85)

## Core Components
- DeterministicWorkflowPlanner: constructs a PlanSpec from a WorkflowRequestContext, selects steps based on intent and context, computes risk level, and validates against policy.
- WorkflowStepDefinition: defines step semantics, required inputs, produced outputs, side effects, timeouts, and retry policy.
- WorkflowPolicy and WorkflowPolicyValidator: enforce allowed evidence sources, write-step enablement, latency budgets, and risk alignment.
- WorkflowRequestContext: normalizes request metadata into role_mode, journey_state, identity, and available evidence sources.
- PlannerDecision: encapsulates acceptance, validation errors, fallback, and the final PlanSpec.
- WorkflowReplayScenario and evaluator: define expected goals, fallback templates, required/forbidden steps, and validate planner decisions.
- **Enhanced V3.1**: LLM-assisted JSON planner with shadow comparison and metrics storage capabilities.

**Section sources**
- [workflow_planner.py:90-134](file://src/sage_faculty_twin/workflow_planner.py#L90-L134)
- [workflow_steps.py:9-21](file://src/sage_faculty_twin/workflow_steps.py#L9-L21)
- [workflow_policy.py:15-48](file://src/sage_faculty_twin/workflow_policy.py#L15-L48)
- [workflow_context.py:12-37](file://src/sage_faculty_twin/workflow_context.py#L12-L37)
- [workflow_eval.py:13-34](file://src/sage_faculty_twin/workflow_eval.py#L13-L34)

## Architecture Overview
The enhanced V3.1 system follows a deterministic planner with LLM-assisted capabilities that:
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
participant Planner as "DeterministicWorkflowPlanner"
participant LLM as "LLM Client"
participant Shadow as "Shadow Planner"
participant Policy as "WorkflowPolicyValidator"
participant Registry as "Step Registry"
participant Metrics as "Planner Metrics Store"
Client->>Service : "ChatRequest"
Service->>Planner : "plan(context)"
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
- [service.py:5390-5412](file://src/sage_faculty_twin/service.py#L5390-L5412)
- [service.py:5544-5583](file://src/sage_faculty_twin/service.py#L5544-L5583)
- [workflow_planner.py:110-134](file://src/sage_faculty_twin/workflow_planner.py#L110-L134)
- [workflow_planner.py:135-177](file://src/sage_faculty_twin/workflow_planner.py#L135-L177)
- [planner_metrics_store.py:87-121](file://src/sage_faculty_twin/planner_metrics_store.py#L87-L121)

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
- Tests validate:
  - Policy loading and enforcement
  - Scenario-based replay acceptance
  - Shadow candidate evaluation and fallback behavior
  - Metrics collection and analytics

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
```

**Diagram sources**
- [workflow_planner.py:90-134](file://src/sage_faculty_twin/workflow_planner.py#L90-L134)
- [workflow_policy.py:64-199](file://src/sage_faculty_twin/workflow_policy.py#L64-L199)
- [workflow_steps.py:179-184](file://src/sage_faculty_twin/workflow_steps.py#L179-L184)
- [workflow_eval.py:53-94](file://src/sage_faculty_twin/workflow_eval.py#L53-L94)
- [service.py:5544-5583](file://src/sage_faculty_twin/service.py#L5544-L5583)
- [planner_metrics_store.py:75-85](file://src/sage_faculty_twin/planner_metrics_store.py#L75-L85)
- [planner_comparison_store.py:75-85](file://src/sage_faculty_twin/planner_comparison_store.py#L75-L85)

**Section sources**
- [workflow_planner.py:90-134](file://src/sage_faculty_twin/workflow_planner.py#L90-L134)
- [workflow_policy.py:64-199](file://src/sage_faculty_twin/workflow_policy.py#L64-L199)
- [workflow_steps.py:179-184](file://src/sage_faculty_twin/workflow_steps.py#L179-L184)
- [workflow_eval.py:53-94](file://src/sage_faculty_twin/workflow_eval.py#L53-L94)
- [service.py:5544-5583](file://src/sage_faculty_twin/service.py#L5544-L5583)
- [planner_metrics_store.py:75-85](file://src/sage_faculty_twin/planner_metrics_store.py#L75-L85)
- [planner_comparison_store.py:75-85](file://src/sage_faculty_twin/planner_comparison_store.py#L75-L85)

## Performance Considerations
- Timeout budgets: Each step defines a timeout_budget_ms; total latency is compared against the plan's estimated_latency_budget_ms.
- Latency budget limits: Policy enforces max_latency_budget_ms to cap end-to-end cost.
- Deterministic planning avoids expensive retrieval for simple greetings and reduces redundant memory retrievals when recent session context is attached.
- Shadow planning can be disabled for benchmark scenarios to minimize overhead.
- **Enhanced V3.1**: Shadow planning adds minimal overhead for comparison while providing valuable safety insights.
- **Metrics Overhead**: Persistent metrics storage uses SQLite database with efficient indexing and JSON serialization.
- **Configuration Control**: Shadow planner can be globally enabled/disabled via configuration settings.

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

**Section sources**
- [workflow_policy.py:74-199](file://src/sage_faculty_twin/workflow_policy.py#L74-L199)
- [test_workflow_policy.py:60-99](file://tests/test_workflow_policy.py#L60-L99)
- [service.py:5559-5568](file://src/sage_faculty_twin/service.py#L5559-L5568)
- [planner_metrics_store.py:75-85](file://src/sage_faculty_twin/planner_metrics_store.py#L75-L85)

## Conclusion
The enhanced V3.1 workflow system combines deterministic planning, strict step registry validation, and policy-driven enforcement with advanced LLM-assisted capabilities. The addition of shadow comparison functionality and comprehensive metrics storage provides unprecedented visibility into planner performance and safety. Extensibility is achieved through configurable LLM integration, modular step definitions, and comprehensive analytics infrastructure.

## Appendices

### Example Workflows and Execution Patterns
- Course grounding: Detect profile context → classify intent → hybrid knowledge retrieval → assemble prompt → answer with citations → score memory usefulness → render user response.
- Booking preparation: Stay read-only; avoid booking drafts; leverage knowledge and memory to advise.
- Artifact-aware research: Combine research knowledge with artifact memory and profile memory when consent and context permit.
- Simple greeting: Minimal steps; skip retrieval to reduce latency.
- **Enhanced V3.1 Shadow Comparison**: Automatic shadow planning for complex queries with detailed metrics tracking and comparison reporting.

**Section sources**
- [test_dynamic_workflow_planner.py:47-79](file://tests/test_dynamic_workflow_planner.py#L47-L79)
- [test_dynamic_workflow_planner.py:81-102](file://tests/test_dynamic_workflow_planner.py#L81-L102)
- [test_dynamic_workflow_planner.py:191-220](file://tests/test_dynamic_workflow_planner.py#L191-L220)
- [test_dynamic_workflow_planner.py:263-288](file://tests/test_dynamic_workflow_planner.py#L263-L288)

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

**Section sources**
- [workflow_steps.py:23-174](file://src/sage_faculty_twin/workflow_steps.py#L23-L174)
- [workflow_steps.py:179-184](file://src/sage_faculty_twin/workflow_steps.py#L179-L184)
- [workflow_policy.py:54-62](file://src/sage_faculty_twin/workflow_policy.py#L54-L62)
- [test_workflow_policy.py:60-99](file://tests/test_workflow_policy.py#L60-L99)
- [config.py:90-100](file://src/sage_faculty_twin/config.py#L90-L100)
- [service.py:5562-5572](file://src/sage_faculty_twin/service.py#L5562-L5572)
- [planner_metrics_store.py:75-85](file://src/sage_faculty_twin/planner_metrics_store.py#L75-L85)
- [planner_comparison_store.py:75-85](file://src/sage_faculty_twin/planner_comparison_store.py#L75-L85)

### Configuration Settings
Key configuration parameters for V3.1 enhancements:
- `shadow_planner_enabled`: Global toggle for shadow planning functionality
- `shadow_planner_temperature`: LLM sampling temperature for shadow candidates
- `shadow_planner_max_tokens`: Maximum tokens for shadow plan generation
- `planner_metrics_dir`: Directory for metrics storage and analytics
- `planner_comparison_dir`: Directory for comparison result tracking

**Section sources**
- [config.py:90-100](file://src/sage_faculty_twin/config.py#L90-L100)
- [models.py:579](file://src/sage_faculty_twin/models.py#L579)