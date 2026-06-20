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
stable workflow backbone with predefined template selection, policy-driven routing, and pluggable
domain skills. The more ambitious idea of dynamically generating a workflow graph should be a V3
capability, after templates, traces, policies, and evaluation baselines are stable.

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
- **Adaptive workflow templates:** replace the single fixed 12-stage chat path with predefined
  templates such as `answer_question`, `book_meeting`, `collect_booking_details`,
  `admin_add_knowledge`, `human_handoff`, and `analytics_rollup`, selected by a planner before
  execution.
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
being the same 12-step path. For V2, this means selecting from known templates. Generating new
workflow graphs from a step library belongs to V3, where governance and replay tests can constrain
the planner.

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
- Keep confirmed-meeting handling on local weekly availability plus admin approval for the current
  school deployment; revisit real calendar-provider sync only if an approved provider API becomes
  available.
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
- Keep local availability plus admin approval as the deployment default for confirmed meetings;
  real calendar-provider sync is a future optional integration when the school environment exposes a
  supported calendar API.
- Add stronger identity and governance controls such as student verification, audit trails, and
  clearer human-takeover boundaries.
- Improve deployment ergonomics for IntelliStream-owned rollout, environment setup, and branded
  reuse.
- Strengthen evaluation and reliability with better latency/error observability and release-facing
  quality checks.

### V2 Storage Roadmap (Conversation Memory)

- `v2.0.x` now migrates conversation/profile collection snapshots from JSON file trees to a SQLite
  snapshot store (`data/conversation_memory/memory_store.sqlite3`) to avoid per-turn mass JSON
  rewrites and binary index churn in the repository.
- Backward compatibility is preserved: on startup, if legacy collection snapshots exist under
  `data/conversation_memory/collections/`, they are loaded once and re-persisted into SQLite.
- Legacy flat `records/` and `profiles/` JSON layouts remain auto-migrated as before.
- Next step (`v2.1` target): split runtime state from tracked deployment templates so production
  write-heavy files live outside git-tracked data directories by default.
- Optional `v2.2+` path: evaluate a Postgres backend for multi-instance deployment while keeping
  the same `NeuroMemConversationStore` API contract.

### Candidate V2 Extensions

- Multichannel entry points such as LMS embedding, homepage widgets, or messaging connectors.
- Voice interaction and richer avatar presentation once the operations baseline is stable.
- Better knowledge publishing workflows that connect updated source content to indexed retrieval
  with less manual intervention.
- Reusable persona and organization templates for deploying the same product shape to multiple
  faculty members.
- Optional Google, Outlook, Exchange, or CalDAV synchronization for deployments that have approved
  calendar-provider access.

### Current V2 Checkpoint

The current `v2` checkpoint has implemented the first operations-console slices: overview and
workbench APIs, the admin console shell, knowledge-gap drafts, student operations profiles, a
unified operational task queue, task state overlays, and satisfaction metrics.

The `v2.0.2` patch baseline freezes the post-release hardening that should be preserved before V3:
mobile identity-prompt fixes, powered-by link cleanup, stronger local-model workflow routing,
exact course-material retrieval, Chinese relative-time booking, owner-style clarification, refined
inference-service frontend, cache-busted CSS/JS delivery, and a subtle in-app version badge for
runtime release visibility.

Remaining release-facing work before V3 should be limited to regression fixes and operational
evidence collection. New behavior should wait for the V3 planning layer unless it is needed to keep
the current public service reliable. Real calendar-provider integration is explicitly not a blocker
for the current school deployment.

### Pre-V3 Stabilization Gate

Before implementation starts on dynamic workflow planning, the repo should satisfy this short gate:

- Current `main` has a patch release tag after all mobile, frontend, and answer-quality fixes.
- The live local service reports healthy status for `qwen32b` and the configured knowledge backend.
- The critical chat regression suite passes for booking, intent normalization, retrieval, persona,
  and agentic workflow behavior.
- The public frontend serves fresh cache-busted CSS and JS for the latest interaction model.
- ROADMAP and CHANGELOG describe the V3 entry criteria clearly enough that V3 work can begin from a
  stable baseline instead of re-litigating V2 scope.

## V3 Plan

`v3` should focus on governed dynamic workflow generation. By this point, `v2` should already have
observable operations, predefined workflow templates, stable policy data, and enough evaluation
cases to judge whether a generated plan is better than a fixed template.

### V3.0 Status (2026-06-10)

`V3.0: Read-Only Planner Preview` is completed as the `v3.0.0` baseline:

- Deterministic planner and policy validation are wired into live workflow trace metadata.
- Canonical replay scenarios are executable and exposed through admin API `GET /workflow/replay`.
- Operations console includes a Workflow Replay quality board for operator-visible pass/fail review.
- Live behavior keeps fallback-safe execution boundaries, preserving V2 operational stability.

### V3.1 Status (2026-06-20) — LLM-Assisted Planner

`V3.1: LLM-Assisted JSON Planner` is **implemented and integrated** as part of the `v3.x` baseline:

- **LLM shadow planner** is enabled by default (`shadow_planner_enabled: true` in config). The LLM client proposes `ShadowPlanCandidate` plans via `propose_shadow_plan_candidate_sync/async` with strict JSON schema validation.
- **Shadow comparison** runs in every chat request: the deterministic plan and the LLM shadow plan are both generated and compared. The deterministic plan remains authoritative for live execution while the shadow plan is recorded for analysis.
- **Planner comparison persistence** stores comparison results under `data/conversation_memory/planner-comparisons/` with SQLite tracking of acceptance rate, step diffs, and fallback reasons.
- **Policy validation** gates both deterministic and shadow plans through the same step registry, evidence contracts, and side-effect rules.
- **Operations console** surfaces `workflow_plan_preview` and `shadow_planner_preview` in workflow traces for operator-visible comparison.
- **Replay tests** cover shadow planner behavior (`test_chat_surfaces_llm_shadow_planner_comparison_without_affecting_execution`).

In addition, `v3.1.0` delivered the retrieval and workflow modernization that supports the planner:

- Knowledge backend migrated from BM25 to SageVDB/SageANNS vector search with reranking.
- Tavily integrated as primary web search engine with Bing fallback and query normalization.
- Chat workflow rewired as a parallel SAGE DataStream DAG (memory + knowledge retrieval run in parallel; post-answer side effects fan out in 4-way parallel join).
- External PDF/article knowledge ingestion pipeline operational.
- Markdown table rendering added to the chat frontend.
- Operational scripts consolidated into `quickstart.sh` + `manage.sh`.
- Homepage migrated to GitHub Pages; tunnel/site-proxy is optional.
- All 28 ruff lint errors resolved; CI pipeline stabilized.

### V3.3 Status (2026-06-20) — Real Capability Plugins & Changelog API

`V3.3: Faculty-Specific Capability Plugins` is **implemented and production-ready**:

- **Manifest-driven plugin system** (`capability_plugins.py`): `CapabilityPluginManifest` Pydantic model declares plugin_id, steps, policy requirements, min app version, and test scenario IDs.
- **Plugin registry** loads JSON manifests from `data/capability_plugins/`, validates step metadata, checks version compatibility, and merges enabled plugin steps into the core step registry.
- **5 real plugin packs shipped** (all `enabled: true`):
  - `research_mentoring` (4 steps): research overview retrieval, direction matching, reading methodology, research plan drafting
  - `meeting_prep` (4 steps): team schedule, blocker memory, follow-up artifacts, agenda drafting
  - `thesis_review` (4 steps): paper digest, writing guidance, review checklist, review comments drafting
  - `course_advising` (3 steps): courseware index, teaching resources, course plan drafting
  - `paper_feedback` (3 steps): writing rubric, structured critique, revision notes drafting
- **36 total steps** in registry (18 core + 18 plugin), zero step-ID collisions with core.
- All 5 `draft_write` steps have unique `trace_key` for observability.
- **Operations API**: `GET /capabilities` returns plugin statuses for the admin console.
- **Changelog refactored**: release notes moved from hardcoded JS to `data/changelog.json`, served via `GET /changelog` API, now covers v1.0–v3.3.
- **29 tests** cover loading, validation, compatibility, registry merging, real manifest integrity, and collision detection.

### V3.2 Status (2026-06-20) — Guarded Side-Effects & Release Notes

`V3.2: Guarded Side-Effect Planning` is **implemented and integrated**:

- All 6 write steps (`record_conversation_memory`, `record_artifact_memory`, `draft_booking_request`, `create_escalation_draft`, `draft_follow_up_action`, `draft_knowledge_gap`) registered with `side_effect="draft_write"` and policy validation.
- Typed artifact memory writes policy-validated NeuroMem records for uploaded drafts, agendas, meeting-prep notes, and follow-ups.
- Admin boundary tests confirm normal users cannot trigger admin-only plans.
- Trace UI maps step `side_effect` metadata to distinguish read-only vs draft-write operations.

Additionally, `v3.2.0` adds a clean user-facing changelog:

- Clickable version badge (bottom-right corner) opens a "版本更新日志" modal with concise release highlights.
- Version badge text updated from stale `v3.0.1` to current version.

The important design choice is that V3 is not an unconstrained agent that invents code or freely
calls tools. It is a planner that assembles an approved workflow graph from registered steps,
validated policy, and bounded side-effect rules. The generated plan should be understandable before
execution, replayable after execution, and replaceable by a known V2 template whenever planning is
not clearly beneficial.

The V3 release theme is therefore: **make planning explicit before making behavior more powerful**.
The first V3 increments should expose plans, validate plans, and replay plans while keeping live
answers close to the proven V2 templates. More autonomous side effects should arrive only after the
planner has deterministic baselines, policy tests, and operator-visible rejection reasons.

V3 should also make the product thesis explicit: `my-twin` is not an "AI teacher" and not a
persona-imitation chatbot. It is an academic office entrance that reduces repeated context load,
organizes requests, prepares next actions, and hands uncertain or consequential decisions back to
the owner with enough context for review.

### V3 Product Goals

- Make the twin feel less rigid across the owner's multiple identities: course instructor,
  research-group PI, collaborator, online front desk, and system operator.
- Avoid running unnecessary stages for simple questions while adding the right extra stages for
  complex interactions such as booking preparation, research collaboration, or knowledge-gap
  remediation.
- Preserve the product promise that every important answer has visible workflow evidence, retrieved
  context, memory usage, and owner-review boundaries.
- Let future faculty deployments add local capabilities through policy and step registration rather
  than editing the main chat service for every role-specific workflow.

### V3 Product Acceptance Model

V3 should be judged by whether it realizes the "academic office entrance" workflow described for
`my-twin`:

- **Student entry:** a student can start from one place to ask a question, prepare a meeting agenda,
  describe an experiment blocker, provide missing background, or request a handoff.
- **Context organization:** the system turns scattered messages into structured intent, profile
  context, relevant knowledge, recent memory, long-term journey state, and suggested next actions.
- **Grounded assistance:** course, experiment, homepage, FAQ, and research answers should be based
  on synchronized knowledge and visible evidence rather than plausible free-form generation.
- **Bounded action:** the system may prepare a booking request, agenda, escalation, follow-up draft,
  or knowledge-gap task, but it must not pretend to approve meetings, invent policies, publish
  knowledge, or send external messages without owner/admin review.
- **Human handoff:** when confidence, authority, privacy, or policy says "this needs the owner", V3
  should package the question, evidence, memory signals, missing fields, and recommended action for
  review instead of forcing a final answer.
- **Operational learning:** repeated failures, unresolved questions, weak retrieval, stale sources,
  and frequent student blockers should become reviewable operations tasks so the knowledge base and
  workflow policies improve over time.
- **System portability:** SAGE orchestration, NeuroMem memory, knowledge retrieval, local vLLM-hust
  inference, and optional SageVDB retrieval should remain replaceable components behind stable
  contracts, so the app can evolve without rewriting the whole assistant.

If a V3 feature makes the app sound more like the owner but does not improve one of these acceptance
points, it should be treated as secondary. The core value is clearer academic work boundaries, not
more fluent impersonation.

### V3 Scope Commitments

V3 should absorb the following recommendations as product commitments rather than loose ideas:

- **Deterministic planner first:** every V3 behavior must have a non-LLM baseline that can run when
  local Qwen planning is malformed, slow, or low-confidence.
- **Shadow before live:** LLM-generated plans should be recorded and compared before they are allowed
  to change execution for real users.
- **Policy before side effects:** booking, escalation, memory writeback, follow-up drafts, and
  knowledge-gap creation must be policy-validated before execution.
- **Evidence as a contract:** a plan that retrieves knowledge or memory must say which evidence type
  it used, where it came from, and how the final answer should expose it.
- **Operator-readable failures:** rejected plans, fallbacks, skipped steps, and policy denials must
  be understandable in the admin console without reading logs.
- **Faculty portability:** the implementation should make role modes and capability packs data-driven
  enough that another faculty twin can reuse the machinery with local policies.

### V3 NeuroMem Commitments

The current app already uses NeuroMem for short-term conversation recall, long-term profile memory,
knowledge-backed retrieval, and operations telemetry. V3 should move NeuroMem from a helpful storage
layer into an explicit planning and quality-improvement substrate.

The following three NeuroMem workstreams are not optional V3 ideas. They should be treated as part
of the main V3 roadmap:

- **Hybrid retrieval instead of memory-only lexical recall:** expand the current BM25-style
  NeuroMem usage into a governed hybrid retrieval layer that can combine lexical retrieval,
  NeuroMem memory retrieval, profile recall, and optional SageVDB-style semantic retrieval under a
  visible evidence contract. The planner should choose retrieval shape by request type instead of
  always assuming the same memory or knowledge query style.
- **Typed academic memory for uploads and meetings:** treat uploaded drafts, agendas, meeting
  preparation packets, recurring blockers, follow-up commitments, and review artifacts as typed
  memory objects rather than transient prompt context only. A user who uploads a paper draft or
  confirms a meeting should create reviewable academic memory that can influence later advising,
  booking preparation, and owner review.
- **Closed-loop memory quality evaluation:** use NeuroMem telemetry, user feedback, replay suites,
  and benchmark adapters to measure whether memory retrieval actually helped. V3 should track which
  memory classes improve answers, which memories go stale, which retrieved items correlate with low
  satisfaction, and when writeback volume is increasing without improving usefulness.

### Additional V3 Capability Candidates

Dynamic workflow generation is the V3 spine, but several adjacent capabilities would make V3 feel
like a real academic operating layer rather than only a smarter planner. These should be scoped
carefully: the first group is worth treating as part of V3 core, while the second group can be
optional if schedule or validation risk becomes too high.

#### V3 Core Candidates

- **Role-aware operating modes:** make the owner's identities explicit runtime modes, such as
  `course_instructor`, `paper_writing_teacher`, `research_pi`, `collaboration_contact`, and
  `front_desk`. Each mode should carry allowed workflow steps, preferred knowledge scopes,
  memory-use rules, tone constraints, and escalation thresholds. This gives the planner a stable
  policy surface instead of inferring everything from prompt text.
- **Student and collaborator journey state:** move beyond isolated chat memory by tracking where a
  user is in a journey: first-time visitor, course student, project advisee, meeting candidate,
  recurring collaborator, or high-priority escalation. The planner can then choose different steps
  for onboarding, repeated blockers, missed follow-ups, or meeting preparation.
- **Owner attention budget:** add a queue-prioritization layer that estimates which items need the
  owner's attention first: urgent bookings, unresolved escalations, stale knowledge gaps, repeated
  student confusion, or follow-up drafts waiting too long. V3 should help protect owner time, not
  only answer more flexibly.
- **Evidence and provenance contracts:** require every generated plan that uses knowledge or memory
  to record which source, memory, policy, or profile signal influenced the answer. The trace should
  make it easy to answer: "Why did the twin say this?" and "What should be corrected if it was
  wrong?"
- **Planner quality lab:** add a small offline workbench for comparing deterministic templates,
  LLM-generated plans, and fallback behavior on saved scenarios. This should include diff views for
  selected steps, rejected steps, retrieved evidence, latency, and answer quality notes.
- **Privacy and retention policy hooks:** make memory retention, redaction, consent, and sensitive
  topic handling first-class planner constraints. The planner should know when not to retrieve or
  write certain profile memories, especially for student records, recommendation requests, and
  personal circumstances.
- **NeuroMem hybrid retrieval policy:** define when the planner should use lexical knowledge search,
  recent-memory recall, long-term profile memory, upload-derived memory, or optional semantic/vector
  retrieval. This should be visible in plan traces and replay tests so retrieval strategy becomes a
  governed decision rather than a hidden implementation detail.
- **Typed artifact memory:** make academic artifacts first-class memory records with provenance and
  retention rules: uploaded drafts, meeting agendas, follow-up commitments, recurring blockers,
  reading plans, and review packets. This lets V3 reason over a student's journey rather than only
  raw chat turns.
- **Memory usefulness scoring:** add evaluation slices that connect memory retrieval to answer
  helpfulness, operator corrections, handoff reduction, stale-memory rate, and repeated-question
  reduction. The point is not to maximize stored memories; it is to maximize useful memories.

#### V3 Optional Extensions

- **Meeting preparation packets:** when a booking is pending or confirmed, generate a reviewable
  packet containing agenda summary, relevant prior memory, blockers, recommended readings, and
  suggested meeting goals. Keep final scheduling approval with the owner.
- **Research-group coordination views:** add lightweight group-oriented summaries such as recurring
  blockers, common paper-reading questions, active project themes, and follow-up commitments. This
  is useful if the twin becomes more than a public-facing front desk.
- **Knowledge maintenance autopilot:** let V3 suggest stale documents, duplicated course content,
  missing FAQ entries, and weak retrieval sources, then create reviewable maintenance tasks rather
  than directly editing the knowledge base.
- **Response style profiles:** allow owner-approved response profiles for different audiences, such
  as undergraduate students, graduate students, research collaborators, administrators, or public
  visitors. This should be policy-backed, not free-form personality drift.
- **Safe artifact drafting:** generate draft artifacts that are naturally useful in academia:
  meeting briefs, reading plans, FAQ drafts, course-office-hour summaries, project onboarding notes,
  or collaboration reply drafts. All external-send actions should remain review-gated.
- **Capability marketplace for faculty plugins:** provide a small registry view that shows enabled
  capability packs, their allowed steps, required policies, tests, and last validation result. This
  turns plugin support into something operators can understand.

Recommended V3 priority:

1. Ship the planning substrate: `PlanSpec`, step registry metadata, policy validation, fallback
  reasons, and tests.
2. Add role-aware operating modes, journey state, evidence contracts, and privacy hooks as planner
  inputs.
3. Add the planner quality lab and scenario replay suite before enabling LLM planning live.
4. Add owner attention budgeting once operations tasks and planner traces share enough metadata.
5. Add meeting packets, research-group coordination, style profiles, safe artifact drafting, and
  capability marketplace only after the core planner is observable and policy-safe.

### V3 Architecture Shape

The V3 planner should sit between request understanding and workflow execution:

1. Collect request context: user question, active profile mode, session/user identity, recent
   memory, available knowledge collections, owner policy version, and runtime capability flags.
2. Generate or select a candidate `PlanSpec` using a constrained planner. The first implementation
   may combine deterministic rules with an LLM JSON planner, but the output must be schema-bound.
3. Validate the candidate plan through a policy gate before any step runs.
4. Execute the accepted plan through the existing SAGE/FlowNet trace surface, using registered
   steps only.
5. Persist plan, validation result, execution trace, fallback decision, and evaluation labels so the
   same request can be replayed later.

Suggested module boundaries:

- `workflow_planner.py`: request-to-`PlanSpec` generation, deterministic planner, optional LLM JSON
  planner, and fallback selection.
- `workflow_steps.py`: step registry, step metadata, input/output contracts, side-effect class, and
  execution adapter.
- `workflow_policy.py`: allowed step graph rules, permissions, maximum cost/latency budgets,
  owner-review requirements, and side-effect validation.
- `workflow_trace.py`: plan trace serialization, rejected-plan reasons, stage timings, skipped
  stages, evidence links, and replay identifiers.
- `workflow_context.py`: normalized request context, role mode, journey state, identity, consent,
  runtime flags, and available knowledge/memory scopes.
- `workflow_eval.py`: offline replay harness, template-vs-plan comparison, scenario labels,
  acceptance metrics, and regression summaries.
- `data/workflow_policies/`: versioned YAML policies for owner-specific planning constraints.
- `data/workflow_scenarios/`: canonical V2/V3 replay cases for course, research, booking,
  knowledge-gap, human-handoff, greeting, and admin-denial scenarios.
- `tests/test_dynamic_workflow_planner.py`: schema, policy, fallback, and representative scenario
  coverage.

The first implementation should keep these modules metadata-heavy. Do not wire LLM planner prompts
or dynamic side effects until the schema, registry, policy, and replay tests are already passing.

### PlanSpec Contract

V3 should introduce a structured `PlanSpec` that can be stored, audited, and replayed. A candidate
shape:

```json
{
  "plan_id": "generated-or-template-id",
  "planner_version": "v3.0.0",
  "policy_version": "faculty-default-2026-05",
  "planner_mode": "deterministic",
  "execution_mode": "shadow_or_template",
  "goal": "answer_course_question",
  "risk_level": "read_only",
  "profile_context": "paper_writing_course",
  "journey_state": "course_student",
  "estimated_latency_budget_ms": 12000,
  "requires_owner_review": false,
  "evidence_contract": {
    "requires_citations": true,
    "allowed_sources": ["course_material", "public_homepage", "profile_memory"],
    "forbidden_sources": ["private_student_record_without_consent"]
  },
  "steps": [
    {
      "step_id": "detect_profile_context",
      "reason": "The user question mentions a course-specific assignment.",
      "inputs": ["question", "session_profile"],
      "outputs": ["profile_context"],
      "side_effect": "none"
    },
    {
      "step_id": "retrieve_knowledge",
      "reason": "The answer should cite course material.",
      "inputs": ["question", "profile_context"],
      "outputs": ["knowledge_hits"],
      "side_effect": "none"
    },
    {
      "step_id": "answer_with_citations",
      "reason": "The final response needs grounded advice and citations.",
      "inputs": ["question", "knowledge_hits"],
      "outputs": ["answer"],
      "side_effect": "none"
    }
  ],
  "fallback_template": "answer_question",
  "fallback_reason": null,
  "explain_to_operator": "Course question with retrieval; no booking or admin side effect needed."
}
```

Required validation rules:

- `steps[*].step_id` must exist in the registry.
- Step input dependencies must be satisfied by request context or previous step outputs.
- The graph must be acyclic and below the configured maximum stage count.
- Total estimated latency and token budget must stay under policy limits.
- `risk_level` must match the strongest side effect in the plan.
- Write-side-effect steps must declare whether owner review is required.
- Admin-only steps must be rejected for normal user sessions.
- Evidence contracts must reject unavailable, private, or policy-forbidden source classes.
- `planner_mode` and `execution_mode` must be explicit so deterministic, shadow, template, and live
  planner behavior can be separated in traces.
- Unknown fields from an LLM-generated plan should be rejected rather than ignored.

### Step Registry

Start with a small approved step library. Each step should expose: stable id, description, required
inputs, produced outputs, side-effect class, timeout budget, retry policy, and trace renderer.

Initial read-only steps:

- `detect_profile_context`: identify whether the request is about general identity, a specific
  course, paper writing, research collaboration, group operations, or booking preparation.
- `classify_intent`: classify answer, booking, escalation, knowledge-gap, feedback, or admin intent.
- `retrieve_knowledge`: search curated homepage/course/PDF knowledge and return source evidence.
- `retrieve_hybrid_knowledge`: choose and execute the right read-only retrieval mix across lexical
  knowledge search, NeuroMem-backed recall, and optional semantic/vector search under policy.
- `retrieve_recent_memory`: retrieve recent conversation context for the current user/session.
- `retrieve_profile_memory`: retrieve long-term academic profile memory where permitted.
- `retrieve_artifact_memory`: retrieve typed upload, meeting, agenda, blocker, or follow-up memory
  when the request refers to earlier materials rather than only earlier chat turns.
- `assemble_prompt_context`: merge question, policy, evidence, and memory into model-ready context.
- `answer_with_citations`: generate a grounded answer with visible evidence and next steps.
- `detect_knowledge_gap`: decide whether the answer exposed missing or stale knowledge.
- `score_memory_usefulness`: record whether the selected memory and retrieval evidence should be
  treated as helpful, stale, low-confidence, or operator-review-worthy for later evaluation.
- `render_user_response`: format the final response, citations, workflow trace, and suggested
  follow-up actions.

Guarded write or review steps (implemented in V3.2):

- `record_conversation_memory`: write chat summary and profile signals after response generation.
- `record_artifact_memory`: write typed upload, meeting-preparation, blocker, and agenda memory with
  provenance and retention metadata after policy validation.
- `draft_booking_request`: prepare booking data for user confirmation, without confirming a meeting.
- `create_escalation_draft`: create a human-handoff draft that waits for owner/admin processing.
- `draft_follow_up_action`: draft reminders, reading suggestions, or post-meeting notes for review.
- `draft_knowledge_gap`: create a reviewable knowledge-gap draft rather than directly publishing.

Explicitly prohibited generated steps:

- Direct shell execution.
- Direct filesystem mutation outside registered stores.
- Direct email sending without an approved send policy.
- Direct calendar confirmation without owner approval.
- Knowledge deletion or publication without admin session and review trace.

### V3 Implementation Phases

#### V3.0: Read-Only Planner Preview (Completed)

Goal: make V3 observable without making live behavior riskier.

First PR sequence:

1. [x] Add `PlanSpec` Pydantic models, strict JSON validation, and contract tests.
2. [x] Add read-only step registry metadata for profile detection, intent classification, retrieval,
   prompt assembly, answer generation, response rendering, and knowledge-gap detection.
3. [x] Add policy validation for known steps, dependency satisfaction, acyclic graphs, side effects,
   owner-review requirements, admin-only steps, latency/token budgets, and evidence contracts.
4. [x] Add a deterministic planner that maps common requests to generated-looking plans without using
   an LLM planner yet.
5. [x] Add scenario fixtures and replay tests that compare the deterministic plan with current V2
   template behavior.
6. [x] Add typed NeuroMem memory schema and scenario labels for conversation memory, profile memory,
   upload-derived memory, meeting memory, and follow-up memory so replay tests can check retrieval
   and retention behavior before live planning changes.
7. [x] Show the accepted plan in the existing workflow trace as "planned steps" before execution.
8. [x] Keep execution equivalent to V2 templates where possible, so behavior changes are limited to
   observability and plan selection.
9. [x] Add fallback to V2 templates for invalid plans and record the fallback reason.

Exit criteria:

- [x] Planner metadata and policy tests pass without requiring a live model.
- [x] Canonical scenarios produce valid deterministic plans with operator-readable explanations.
- [x] Live chat can expose planned steps while still executing the V2-safe template path.

#### V3.1: LLM-Assisted JSON Planner (Implemented)

- [x] Optional LLM planner proposes `PlanSpec` under strict JSON schema validation via `propose_shadow_plan_candidate`.
- [x] Deterministic and LLM-proposed plans compared in shadow mode; deterministic remains authoritative for live execution.
- [x] Rejected/malformed plans recorded with reasons (unknown step, missing dependency, forbidden side effect, schema error).
- [x] Planner comparison results persisted to SQLite for operator-visible metrics.
- [x] Shadow planner exposed in workflow traces and operations console.
- Remaining: side-by-side replay metrics across retrieval backends (lexical vs NeuroMem vs vector) for per-request-family optimization.

#### V3.2: Guarded Side-Effect Planning (Implemented)

- [x] All write steps registered in step registry with `side_effect="draft_write"`: `record_conversation_memory`, `record_artifact_memory`, `draft_booking_request`, `create_escalation_draft`, `draft_follow_up_action`, `draft_knowledge_gap`.
- [x] Policy gates and `admin_only` flags enforce owner-review markers for every write-side-effect step.
- [x] Tests prove normal users cannot generate admin-only plans (`test_normal_user_admin_style_request_routes_to_boundary_explanation`).
- [x] Trace UI distinguishes read-only from draft-write steps via `side_effect` metadata and frontend step label mapping.
- [x] Typed artifact memory implemented: uploaded drafts, agenda packets, meeting-preparation notes, and follow-up commitments are policy-validated NeuroMem records (`_record_artifact_memory_draft`).

Side-effect planning remains draft-only by design. Direct confirmation, external sending, knowledge publication, and calendar writes stay outside the planner unless an explicit owner policy, admin session, review trace, and rollback story are present.

#### V3.3: Faculty-Specific Capability Plugins (Implemented)

- [x] Manifest-driven plugin architecture: `CapabilityPluginManifest` declares plugin_id, steps, policy requirements, min app version, and test scenario IDs.
- [x] Plugin steps must define the same `WorkflowStepDefinition` metadata, policy hooks, and trace renderer as core steps.
- [x] Plugin compatibility report via `GET /capabilities` endpoint for operations console.
- [x] Capability pack declares steps, policy requirements, test scenarios, and minimum app version before enabling.
- [x] Two example manifests shipped: `course_advising` (2 steps) and `paper_feedback` (3 steps).
- [x] 24 tests cover loading, validation, compatibility, registry merging.

Plugin manifests are disabled by default; enable via `"enabled": true` in the manifest when ready.

### V3 Immediate Backlog (Completed)

All items delivered:

- [x] `workflow_planner.py`, `workflow_steps.py`, `workflow_policy.py`, `workflow_context.py` with metadata-only behavior.
- [x] `PlanSpec`, `PlanStepSpec`, `EvidenceContract`, `PlannerDecision`, and `PlannerFallback` models.
- [x] Default policy file under `data/workflow_policies/faculty-default-2026-05.json`.
- [x] Typed NeuroMem memory descriptors for conversation, profile, upload artifact, meeting, and follow-up memory classes.
- [x] Canonical replay scenarios under `data/workflow_scenarios/v3_preview_scenarios.json` including memory-conditioned, meeting-preparation, and stale-memory scenarios.
- [x] Tests cover upload-aware advising, memory-conditioned recommendations, meeting-preparation continuity, and stale-memory rejection.
- [x] Tests written before planner wiring into live chat.
- [x] Deterministic plan integrated into workflow trace after tests passed.

### Evaluation and Acceptance Criteria

V3 should not be considered ready just because plans can be generated. It should be accepted only
when generated plans improve or preserve quality under replayable tests.

Minimum scenario set:

- Course question: should retrieve course material, answer with citations, and avoid booking steps.
- Paper-writing course question: should prefer paper-writing course context over generic research
  context.
- Research collaboration question: should retrieve research/profile material and suggest a next
  contact path without pretending to approve collaboration.
- Booking preparation: should collect missing agenda/blocker fields and avoid confirming a meeting.
- Knowledge-gap case: should answer cautiously and draft a reviewable knowledge-gap item.
- Human-handoff case: should create or suggest escalation when confidence or policy requires it.
- Simple greeting: should avoid expensive retrieval and long plan generation.
- Admin-only action from normal user: should be rejected and routed to safe explanation.

Metrics to track:

- Plan validity rate.
- Fallback rate and fallback reason distribution.
- Average planning latency.
- End-to-end response latency compared with V2 templates.
- Retrieval precision for generated retrieval plans.
- Memory usefulness rate by memory class (conversation, profile, upload artifact, meeting,
  follow-up).
- Stale-memory rate and stale-memory suppression rate.
- Booking/escalation false-positive rate.
- User-visible answer helpfulness.
- Owner correction rate for generated side-effect drafts.

Release threshold suggestions:

- At least 95% schema-valid plans on the replay suite.
- Zero policy-bypass cases in tests.
- No regression in simple-question latency when deterministic template selection is sufficient.
- Generated plans must match or outperform V2 template selection on the canonical scenario suite.
- Every rejected or fallback plan must produce an operator-readable reason.

### V3 Handoff Checklist

Before implementation starts, the next agent or maintainer should confirm:

- V2 template selection and workflow traces are stable enough to use as fallback baselines.
- Current chat traces include enough request context to replay planner decisions offline.
- The first `PlanSpec` Pydantic models are added before planner prompts or LLM logic.
- The first step registry is metadata-only until policy validation is covered by tests.
- The deterministic planner lands before the LLM planner, so dynamic execution has a reliable
  non-model baseline.
- Planner output is first observed in trace/shadow mode before it changes live execution.
- Every new side-effect step ships with a policy rule, owner-review rule, and rejection test.
- The operations UI can show accepted plan, fallback template, rejected steps, and policy reason in
  language understandable to the owner.

### V3 Non-Goals

- Do not allow the LLM to invent arbitrary executable code or call unregistered tools.
- Do not let generated plans bypass admin approval or human-review boundaries.
- Do not make dynamic planning mandatory for simple questions; cheap deterministic template
  selection should remain available for latency-sensitive paths.

## V4 Plan

`v4` should focus on multimodal interaction quality and real-time usability. The core theme is
to keep V3's governed planning and operations visibility while adding a production-usable voice
entry/response loop for students and faculty workflows.

### V4 Product Theme

- Voice-first academic office entrance: students can speak naturally, receive spoken responses,
  and still see full workflow evidence and citations in text UI.
- Stable under real campus conditions: noisy environment, mixed Chinese/English terms,
  intermittent network, and variable model latency.
- Governance stays explicit: voice should not bypass admin boundaries, review queues, or side-
  effect policies already established in V3.

### V4 Scope Commitments

- Add end-to-end voice pipeline: `ASR -> intent/planner -> retrieval/answer -> TTS`.
- Keep dual-channel output: every voice answer must have synchronized text transcript,
  answer basis, and workflow trace.
- Preserve deterministic fallback behavior: if ASR/TTS is unavailable, the app should fail fast
  to text mode with clear operator-visible reason.
- Add voice observability in operations console: transcription error rate, speech latency,
  TTS generation latency, interruption/abandon rate, and fallback reason distribution.

### Voice Feature Planning

#### V4.0: Voice Infrastructure Baseline

Goal: add safe and observable voice IO without changing core workflow policy.

- Add voice session contract models (input audio metadata, ASR transcript confidence,
  TTS segment metadata, interruption markers).
- Introduce `/chat/voice` endpoint (or equivalent stream route) with authenticated session
  boundary and explicit size/duration caps.
- Integrate ASR with domain lexicon boosts for course names, project terms, and advisor
  vocabulary.
- Add TTS response generation with short-sentence chunking aligned to answer sections.
- Show transcript + audio controls in frontend while keeping existing text composer as fallback.

Exit criteria:

- Voice requests produce usable transcript + text answer + audio answer in one flow.
- Failed ASR/TTS cases are surfaced with structured error reasons in admin logs.
- No policy bypass compared with text-only path.

#### V4.1: Real-Time Streaming Voice

- Add incremental ASR partial transcripts and low-latency turn-taking.
- Add streaming TTS chunks so first audio token is returned quickly.
- Support barge-in (user interruption): stop current TTS playback and continue with new intent.
- Add timeout and jitter handling for unstable network conditions.

Exit criteria:

- P95 voice round-trip latency meets interactive target for campus deployment.
- Interruption handling does not corrupt conversation state or workflow trace.

#### V4.2: Voice Quality and Personalization

- Add per-profile voice style presets (student-facing neutral style by default).
- Add pronunciation dictionary and custom term normalization for names, courses, labs,
  and paper titles.
- Add post-call quality metrics: ASR correction rate, repeated-question reduction,
  and escalation impact.
- Keep sensitive or high-risk responses text-confirmed when confidence is low.

Exit criteria:

- Voice quality metrics improve over baseline for canonical scenarios.
- Low-confidence voice outputs are safely gated with clarification prompts.

### V4 Evaluation and Acceptance

Minimum scenario set:

- Simple greeting and navigation via voice.
- Course-material Q&A with mixed Chinese/English keywords.
- Booking preparation via spoken agenda and blocker description.
- Human-handoff trigger when uncertainty/policy threshold is exceeded.
- Admin-only request from student voice session must be refused with safe explanation.

Metrics to track:

- ASR word error rate and entity error rate (course names, dates, people).
- Voice end-to-end latency and first-audio latency.
- TTS interruption success rate and recovery time.
- Voice-to-text fallback rate and fallback reason distribution.
- User-rated helpfulness delta between text and voice sessions.

Release threshold suggestions:

- Voice policy-bypass incidents: zero.
- Critical scenario pass rate on replay suite and live smoke tests >= 95%.
- P95 end-to-end voice round-trip latency within product target budget.
- All voice responses retain synchronized text trace and evidence visibility.

## Release Note

`v1.0.0` should be treated as the first public repository baseline: stable enough to publish, demo,
and use as the starting point for parallel agent work, while still leaving the operations console
and organization-scale rollout to `v2`.

`v2.0.0` is the first operations-console release. It includes the admin workbench, unified task
queue, knowledge-gap drafts, student operations profiles, satisfaction metrics, and documentation
needed to operate the current school deployment with local availability plus admin approval.