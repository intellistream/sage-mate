# Roadmap

This document marks the first organized release baseline for `sage-faculty-twin` under the
IntelliStream organization plan.

For the parallel implementation order of the `v2` workstreams, see
[`docs/agent-rollout-plan.md`](docs/agent-rollout-plan.md).

## V1 Baseline

`v1.0.0` defines the first usable faculty twin baseline: a personal academic digital twin that can
answer common student questions, guide office-hour preparation, and route actionable requests
through explicit workflows instead of a single opaque chat completion.

### V1 Scope

- Student-facing Chinese-first chat interface with a simple ChatGPT-like workflow view.
- SAGE/FlowNet-based agentic orchestration for answering, booking, escalation, and follow-up.
- Retrieval-aware answers grounded in imported homepage content, curated notes, course pages, and
  PDFs.
- NeuroMem-backed short-term memory and long-term student profile memory.
- Booking workflow with weekly availability management, admin approval, rejection reasons, and
  email notifications.
- Admin capabilities for knowledge updates, booking review, escalation review, memory profile
  inspection, and question analytics.
- Offline homepage/course material ingestion and local deployment scripts for app, site, and
  tunnel-based access.

### What V1 Is Meant To Prove

- A faculty twin should behave like an academic office workflow, not just a Q&A bot.
- SAGE workflows can coordinate model calls, retrieval, approvals, and follow-up actions in a
  transparent way.
- Memory, knowledge, and booking state can be persisted locally and audited by the owner.
- The product can already support real student interactions while keeping sensitive approval steps
  with the human owner.

## Current SAGE Workflow Assessment

The current architecture is directionally sound. FastAPI owns the HTTP and static-web surface,
while `DigitalTwinService` uses SAGE/FlowNet stages to express the core chat workflow as an
auditable pipeline: request bootstrap, intent understanding, booking preparation/execution, memory
retrieval, knowledge retrieval, prompt construction, LLM answer generation, memory persistence,
profile consolidation, follow-up planning, and response rendering.

This is a good fit for a faculty twin because the product is not a single chat-completion call. It
has explicit workflow state, human-review boundaries, retrieval evidence, student memory, booking
side effects, escalation queues, and follow-up actions. SAGE gives the system a stable place to make
those steps visible and testable instead of hiding them inside one handler.

The main improvement area is not replacing the SAGE workflow. It is making the workflow more
operational: easier to configure, easier to observe, more consistently used across admin actions,
and better prepared for latency, quality, and governance requirements.

The current chat workflow is intentionally explicit, but it is also still somewhat rigid: every chat
request passes through the same fixed sequence of stages, and most branching happens inside stage
methods through `route`, `workflow_action`, and skipped trace entries. That is acceptable for the
v1 baseline because it keeps behavior understandable and testable. For v2, the better shape is a
stable workflow backbone with dynamic stage selection, policy-driven routing, and pluggable domain
skills.

### SAGE Capability Expansion

The current system should be understood as a SAGE/FlowNet-driven faculty app, not yet a full
stream-first SAGE inference service. It already uses SAGE where it matters most for v1: explicit
FlowNet stages, auditable workflow traces, SAGE Edge mounting, and SAGE ecosystem integrations such
as NeuroMem and optional SageVDB retrieval. That is enough to prove the product direction, but not
enough to claim that the app fully exercises SAGE's broader runtime, serving, and operations model.

The next roadmap step is to move from request-scoped FlowNet execution toward a fuller SAGE system:

- **Stream-first workflows:** turn repeated background and operational flows into SAGE streams or
  jobs, including homepage sync, knowledge reindexing, follow-up dispatch, analytics rollups,
  stale-knowledge scans, and profile consolidation.
- **Adaptive workflow templates:** replace the single fixed 12-stage chat path with templates such
  as `answer_question`, `book_meeting`, `collect_booking_details`, `admin_add_knowledge`,
  `human_handoff`, and `analytics_rollup`, selected by a planner before execution.
- **Parallel retrieval and context assembly:** run knowledge retrieval, recent-memory retrieval,
  long-term profile retrieval, availability lookup, and policy lookup as parallel SAGE branches
  when the selected workflow needs them.
- **SAGE runtime operations:** expose workflow jobs, stage latency, failure counts, retry state,
  and queue depth in the admin console instead of keeping them as transient UI traces only.
- **SAGE serving integration:** use SAGE serving/gateway contracts to probe model health, surface
  model latency, manage endpoint readiness, and make LLM failures visible to operators.
- **Governed side effects:** represent bookings, knowledge publishing, escalation resolution, and
  follow-up dispatch as explicit SAGE side-effect stages with audit records and owner-review
  boundaries.

In short, v1 proves that the app can be an agentic academic workflow. V2 should prove that the same
product can be operated as a SAGE-native, observable, stream-oriented workflow system.

### Workflow Flexibility Direction

The next iteration should keep the auditable SAGE pipeline, but make the pipeline adaptive rather
than purely linear:

- Use an intent-to-workflow planner that selects a workflow template such as `answer_question`,
  `book_meeting`, `prepare_meeting`, `review_request`, `human_handoff`, `knowledge_admin`, or
  `follow_up_dispatch`.
- Split the current single chat pipeline into reusable subflows: identity/session context,
  retrieval, memory, booking, escalation, answer generation, memory writeback, analytics, and
  follow-up planning.
- Let cheap deterministic gates skip expensive stages before they run, especially LLM answer
  generation, knowledge retrieval, and profile consolidation when a request is already resolved by
  booking, clarification, or escalation.
- Represent review and handoff rules as policy data with versioned ownership, thresholds, and
  examples, so the owner can tune behavior without editing stage code.
- Add a plugin registry for faculty-specific capabilities such as course advising, paper feedback,
  recommendation-letter triage, project matching, or lab onboarding.
- Preserve traceability by recording both the selected workflow template and the stages that were
  skipped, not just the stages that executed.

This would make the system less brittle without making it vague. The product should still expose
clear workflow state, but the workflow graph should be chosen by the situation instead of always
being the same 12-step path.

### SAGE Ecosystem Leverage Plan

The faculty twin can become a stronger showcase for the wider SAGE ecosystem by treating each group
component as an explicit capability layer rather than an incidental dependency.

#### SAGE Runtime, SageFlow/FlowNet, and Stream Processing

- Use the SAGE workflow layer as the canonical orchestration contract: local execution for normal
  development, FlowNet-backed execution for heavier batch jobs such as knowledge reindexing,
  analytics clustering, and evaluation suites.
- Introduce stream-style background workflows for recurring work: homepage/course sync, stale
  knowledge detection, follow-up dispatch, escalation aging, student profile consolidation, and
  nightly quality reports.
- Use operator `parallelism` hints for expensive fan-out stages such as document chunk embedding,
  batch retrieval evaluation, and multi-scenario regression tests.
- Reuse the `sage-examples` pattern where workflow nodes call explicit state services instead of
  mutating stores directly. This would make my-twin workflows easier to test, replay, and later move
  from local execution to FlowNet.

#### SAGE Serving and Edge Integration

- Align LLM access with `sage.serving` contracts and gateway probing so the app can switch between
  local vLLM-hust fork deployments, hosted OpenAI-compatible endpoints, and future SAGE-managed
  model services through the same health/status surface.
- Use the SAGE edge shell as the longer-term deployment boundary for a professor-facing service:
  one edge entry point can expose chat, admin operations, model gateway health, and static homepage
  integration.
- Surface model lifecycle information in the admin console: configured model, gateway health,
  average latency, timeout rate, cache hit rate, and active fallback policy.

#### NeuroMem and Long-Term Academic Memory

- Move beyond raw conversation recall by defining typed academic memories: research interests,
  collaboration style, course progress, meeting preferences, recurring blockers, and follow-up
  commitments.
- Add owner-reviewable memory consolidation workflows so sensitive or low-confidence summaries are
  queued before becoming long-term profile memory.
- Use memory provenance in answers and traces: which memory record influenced the response, when it
  was last updated, and whether it is user-confirmed or inferred.

#### SageVDB and Retrieval Quality

- Use SageVDB as the high-performance retrieval backend for larger homepage/course/PDF corpora,
  with explicit indexing jobs and retrieval-quality reports.
- Track retrieval health metrics: empty-hit rate, stale-hit rate, low-score answer rate,
  source-diversity, and answer satisfaction after using a given document.
- Add side-by-side retrieval evaluation for local lexical search, NeuroMem-backed retrieval, and
  SageVDB vector search so the best backend can be chosen per data source.

#### vLLM-hust and Model Serving Research

- Treat the twin as a realistic workload for local inference research: Chinese student advising,
  structured intent JSON, long-context grounding, and low-latency repeated questions.
- Add benchmark prompts and traces that can be replayed against vLLM-hust changes to measure first
  token latency, total latency, JSON validity, routing accuracy, and answer helpfulness.
- Explore model specialization paths such as small intent classifiers, response rerankers, or
  owner-style adapters before routing every step to the same large chat model.

#### SAGE Examples, Tutorials, and Demo Reuse

- Convert stable twin workflows into tutorial-grade examples: stateful academic advising,
  reviewable booking, knowledge-gap remediation, and long-term memory governance.
- Pull proven patterns from `ticket_triage` and `student_improvement`: explicit workflow runners,
  state service boundaries, focused workflow tests, and replayable demo data.
- Publish a reusable faculty-twin template that demonstrates how SAGE, NeuroMem, SageVDB, serving,
  and FlowNet cooperate in one end-to-end application.

#### Research and Operations Feedback Loop

- Use the twin as a living integration benchmark for the group: each SAGE component should be able
  to improve at least one visible metric such as latency, retrieval quality, workflow correctness,
  memory usefulness, or operator workload.
- Maintain a cross-repo integration matrix that records which versions of SAGE, NeuroMem, SageVDB,
  vLLM-hust, and the twin have been validated together.
- Feed real operational pain points back into component roadmaps: slow model calls to serving/vLLM-hust,
  weak retrieval to SageVDB/NeuroMem, rigid routing to workflow/SageFlow, and admin friction to
  SAGE apps/examples.

### Recommended Improvements

#### P0: Workflow Hardening

- Persist per-stage workflow traces and latency summaries so the admin console can answer: which
  step was slow, skipped, failed, or produced a low-confidence decision?
- Add a lightweight workflow evaluation suite with canonical student scenarios for booking,
  advising, course-material lookup, research questions, escalation, and memory reuse. The goal is to
  catch prompt, retrieval, and routing regressions before real student use.
- Make intent-routing thresholds and review/handoff policy configurable through versioned policy
  files rather than only prompt text and code constants.
- Add structured failure modes for slow or unavailable LLM calls: timeout classification, retry
  policy, visible admin diagnostics, and user-facing status that does not silently pretend the model
  answered normally.
- Bring more admin-side operations into explicit SAGE workflows where side effects matter,
  especially knowledge publishing, follow-up dispatch, escalation resolution, and booking
  confirmation/rejection.
- Introduce workflow templates and a small planner layer so common paths do not all execute the
  same fixed chat pipeline.

#### P1: Product and Operations Enhancements

- Turn the current workflow trace into a first-class operations timeline in the admin UI, including
  stage duration, decision source, retrieved evidence, memory usage, and generated follow-up actions.
- Show the selected workflow template and skipped-stage reasons in the operations timeline, so
  operators can tell whether the system chose the right path before inspecting the final answer.
- Add knowledge freshness tracking: source file or homepage URL, last sync time, changed/removed
  source detection, stale-document warnings, and one-click reindex for affected documents.
- Add a closed-loop knowledge gap workflow: cluster unresolved questions, draft FAQ entries, review
  and publish them, then measure whether similar future questions are resolved better.
- Improve student memory governance with explicit profile categories, retention controls, owner
  review, and the ability to edit or forget sensitive profile summaries.
- Integrate real calendar providers for confirmed meetings while keeping the current local weekly
  availability file as a development and offline mode.
- Add follow-up automation policies, such as post-meeting summary drafts, todo reminders, reading
  nudges, and escalation aging alerts, with admin approval where needed.

#### P2: Advanced Capability Expansion

- Make the chat workflow definition more declarative so alternate faculty twins can add, remove, or
  reorder stages without editing the main service implementation.
- Add faculty-specific workflow plugins with explicit contracts for inputs, outputs, side effects,
  trace entries, and owner-review requirements.
- Add multichannel entry points such as homepage widget embed, LMS integration, and email-assisted
  intake while preserving the same SAGE workflow contracts.
- Add optional voice/avatar presentation after the operations console is stable; keep the workflow
  evidence and human-review boundaries visible even when the interface becomes richer.
- Support multi-owner deployment templates with reusable persona, policy, knowledge-source, and
  calendar configurations for different faculty members.
- Add longitudinal quality metrics: answer helpfulness trend, human-handoff rate, booking approval
  rate, stale-knowledge rate, and repeated-question reduction after FAQ publication.

## V2 Plan

`v2` is planned as the operations and deployment expansion release. The main goal is to move from a
working faculty twin to a reusable, organization-owned service that is easier to operate, improve,
and extend.

### V2 Focus Areas

- Upgrade the current admin area into a true operations console covering question distribution,
  knowledge gaps, student segmentation, satisfaction trends, human handoff queues, and follow-up
  tasks.
- Add stronger operational data models so analytics, feedback, escalations, and follow-up actions
  form one closed loop.
- Integrate real calendar providers instead of repo-only availability for confirmed meetings.
- Add stronger identity and governance controls such as student verification, audit trails, and
  clearer human-takeover boundaries.
- Improve deployment ergonomics for IntelliStream-owned rollout, environment setup, and branded
  reuse.
- Strengthen evaluation and reliability with better latency/error observability and release-facing
  quality checks.

### Candidate V2 Extensions

- Multichannel entry points such as LMS embedding, homepage widgets, or messaging connectors.
- Voice interaction and richer avatar presentation once the operations baseline is stable.
- Better knowledge publishing workflows that connect updated source content to indexed retrieval
  with less manual intervention.
- Reusable persona and organization templates for deploying the same product shape to multiple
  faculty members.

## Release Note

`v1.0.0` should be treated as the first public repository baseline: stable enough to publish, demo,
and use as the starting point for parallel agent work, while still leaving the operations console
and organization-scale rollout to `v2`.