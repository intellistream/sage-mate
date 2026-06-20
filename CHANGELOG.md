# Changelog

## Unreleased

## v4.2.0 - 2026-06-20

`v4.2.0` adds on-demand context compression, letting users manually trigger conversation context compression from the token usage panel.

### Added

- **Manual context compression trigger**: a "压缩上下文" button inside the token usage detail panel (accessible by clicking the token icon in the composer). When clicked, the service compresses all unsummarized conversation turns into a rolling digest immediately, bypassing the automatic turn-threshold check.
- **`POST /context/compress` API endpoint**: accepts `{ "conversation_id": "..." }` and forces immediate digest compression. Returns `{ ok, turns_compressed, total_turns, digest_chars }`.
- **`DigitalTwinService.compress_conversation_context()`**: public method that forces digest update for all unsummarized turns (up to 32 turns per call).
- **Button UX states**: loading (spinning icon), success (green, shows turns compressed), error (red), idle (auto-reverts after 3s). Distinguishes timeout, HTTP error, and connection failure.

### Changed

- **Footer banner two-row layout**: restructured the footer into row 1 (hardware + LLM metrics, gradient background) and row 2 (Powered by stack chips, neutral background) for better visual separation.
- **LLM metrics status fix**: status chip now correctly recognizes `"ok"` status value from health endpoint (previously only checked for `"healthy"`).

### Technical

- `service.py`: Added `compress_conversation_context()` method.
- `api.py`: Added `/context/compress` endpoint, imported `JSONResponse`.
- `index.html`: Added compress button in token detail panel.
- `app.js`: Added compress click handler with progress states.
- `styles.css`: Added compress button CSS with loading/success/error animations.
- Tests: 35 passed (frontend contract + conversation digest + chat pipeline DAG).

## v4.0.1 - 2026-06-20

`v4.0.1` simplifies deployment by making Docker the only path for the vLLM inference engine and fixing a skill-routing attribute bug.

- **Docker-only engine deployment**: removed host-binary mode from `run_vllm_engine.sh`. The engine now always runs inside a Docker container (`VLLM_ENGINE_CONTAINER` required in `.env`). Auto-escalates to `sudo docker` when needed.
- **Removed venv support**: deleted `--with-venv` flag from `quickstart.sh`, removed `.python-bin` marker file, cleaned up `.python-bin`/`.venv` references from `runtime_env.sh`, `.gitignore`, `README.md`, and `CONTRIBUTING.md`.
- **Bug fix**: skill routing referenced `request.session_id` (non-existent field on `ChatRequest`) — fixed to `request.conversation_id`.
- **CI**: all 336 tests pass. Engine test updated to verify Docker container-not-found error path.

## v3.4.0 - 2026-06-20

`v3.4.0` connects the capability plugin system to the deterministic workflow planner. Plugin steps are now **automatically injected** into execution plans when the query matches the plugin's routing pattern.

### Added

- **Plugin routing in deterministic planner**: `_plugin_steps_for()` method inspects the question and returns applicable plugin read-only + draft-write steps.
- **5 routing patterns**: meeting prep (booking prep), research mentoring (research + mentoring keywords), thesis review, course advising, paper feedback.
- **Safe fallback**: plugin steps are only injected if they exist in the step registry. Without plugins loaded, the planner behaves identically to v3.3.
- **`step_registry` constructor parameter**: `DeterministicWorkflowPlanner` now accepts an optional merged registry.
- **18 plugin step reason strings** added to the planner's explanation mapping.
- **7 new tests** covering all 5 routing patterns, ordering guarantees, safe fallback, and risk-level upgrade. Total: 308 tests.

## v3.3.1 - 2026-06-20

`v3.3.1` ships 5 real, enabled capability plugin packs covering core academic workflows.

### Changed

- **5 real capability plugin packs** (all `enabled: true`) replace the previous example manifests:
  - `research_mentoring`: research direction matching, reading methodology retrieval, research plan drafting
  - `meeting_prep`: team schedule lookup, blocker memory retrieval, meeting agenda drafting
  - `thesis_review`: paper digest retrieval, review checklist generation, review comments drafting
  - `course_advising`: courseware index retrieval, teaching resources, course plan drafting
  - `paper_feedback`: writing rubric retrieval, structured critique generation, revision notes drafting
- Registry now merges **36 total steps** (18 core + 18 plugin)
- 29 tests cover all plugin manifests including collision and trace-key validation

## v3.3.0 - 2026-06-20

`v3.3.0` delivers V3.3 Faculty-Specific Capability Plugins and replaces the hardcoded changelog with a data-driven API.

### Added

- **Capability Plugin System** (`capability_plugins.py`): manifest-driven plugin architecture with `CapabilityPluginManifest`, `CapabilityPluginRegistry`, validation, compatibility checks, and step registry merging.
- **Two example plugin manifests** shipped in `data/capability_plugins/`:
  - `course_advising.json`: syllabus lookup + prerequisite check steps
  - `paper_feedback.json`: rubric retrieval + structured critique + revision draft steps
- **`GET /changelog` endpoint**: serves release notes from `data/changelog.json` (no auth required).
- **`GET /capabilities` endpoint**: returns plugin statuses for the operations console (admin auth required).
- **`capability_plugin_dir` and `changelog_path`** added to `AppSettings`.
- **24 tests** covering manifest loading, compatibility, validation, registry merging, and real manifest loading.

### Changed

- Changelog modal now fetches from `/changelog` API instead of hardcoded `CHANGELOG_DATA` in `app.js`.
- Release notes content simplified and moved to `data/changelog.json`.
- Plugin manifests are disabled by default (`"enabled": false`); enable via manifest edit when ready.

## v3.2.0 - 2026-06-20

`v3.2.0` adds a user-facing version changelog modal and completes a full ROADMAP audit.

### Added

- Clickable version badge (bottom-right) now opens a "版本更新日志" modal showing concise highlights for each release.
- Changelog modal with clean, scrollable layout and accent-styled version tags.

### Changed

- ROADMAP full audit: V3.0 (Read-Only Planner) all 9 items marked complete, V3.1 (LLM-Assisted Planner) marked as implemented, V3.2 (Guarded Side-Effect Planning) marked as implemented (all 6 write steps live with `side_effect="draft_write"`), V3 Immediate Backlog all 8 items marked complete.
- Version badge text updated from stale `v3.0.1` to current `v3.2.0`.

## v3.1.1 - 2026-06-20

`v3.1.1` is a targeted fix for the evidence/support panel rendering and adds a manual retry button for failed inference.

### Added

- Retry button ("重试") appears on error chat bubbles when inference fails. Clicking it restores the original question to the input and re-submits automatically. Uses event delegation on `chatStream` and a module-level `lastFailedQuestion` tracker.

### Fixed

- Knowledge base content in the "回答依据" (answer evidence) panel now renders with proper markdown formatting (headers, tables, bold, lists) instead of a single collapsed line of raw text.
- `cleanAnswerBasisDetail` preserves markdown structure and truncates at ~600 chars (line boundary) instead of collapsing all whitespace into a single line.
- `buildAnswerBasisItemHtml` now uses `formatMessageContent()` for the detail field (same markdown renderer as chat messages) and wraps it in `<div>` instead of `<p>`.
- Added scrollable max-height (240px) and compact typography for basis detail cards so long knowledge entries don't overflow the card.

## v3.1.0 - 2026-06-20

`v3.1.0` is the retrieval and workflow modernization release. It replaces the BM25 knowledge backend with SageVDB/SageANNS, adds Tavily-powered web search, migrates the chat workflow to a parallel SAGE DataStream DAG, and introduces markdown table rendering and external knowledge ingestion.

### Added

- Integrated Tavily as primary web search engine with Bing as fallback, including conversational filler stripping from search queries and search result count surfaced in UI capability chips.
- Added markdown table rendering to the chat frontend (`| col | col |` syntax now renders as proper HTML tables with styled headers and borders).
- Added external PDF/article knowledge ingestion pipeline (first entry: S. Keshav's "How to Read a Paper" three-pass methodology).
- Added SageVDB and SageANNS version chips to the Powered By footer, using a unified `_resolve_source_version()` helper that resolves versions from pip metadata, module import, or pyproject.toml.
- Added auto-detect model name from connected LLM `/v1/models` endpoint — no more hardcoded model display names.
- Created `.env.template` with all environment variables documented and secrets replaced by `<placeholder>` markers.
- Added `tools/start_all_services.sh` orchestration script for multi-service startup.
- Persisted lucky question history to localStorage for cross-session continuity.

### Changed

- Migrated knowledge backend from BM25 lexical search to SageVDB/SageANNS vector search with reranking, significantly improving retrieval quality for large knowledge corpora.
- Rewired the chat workflow as a SAGE `DataStream` DAG instead of a 13-stage linear chain. Memory and knowledge retrieval now run in parallel through a 2-way `connect`/`comap` join, and post-answer side-effect stages fan out through a 4-way parallel join. The `workflow_trace` contract (canonical key order and statuses) is preserved via deterministic post-processing normalization.
- Upgraded Neuromem integration to `isage-neuromem>=0.2.1.12` with numpy BM25 as the default backend path.
- Consolidated operational scripts into `quickstart.sh` + `manage.sh` (CI uses consolidated entry points per two-script root policy).
- Migrated homepage hosting to GitHub Pages; tunnel/site-proxy is now optional.
- Widened chat content area to reduce side whitespace in the UI.
- Bumped `isage` to `0.3.2.4` and fixed version constraint definitions.
- Migrated conversation memory databases to updated schema.

### Fixed

- `PipelineCompiler._normalize_outputs` no longer fragments arbitrary iterable results from `Map`/`CoMap` transformations — flattens only when the caller opts in (`flatten=True`), fixing `Map` outputs that return Pydantic `BaseModel` instances.
- Fixed all 28 ruff lint errors across the codebase.
- Fixed web search running regardless of clarification or planner skip paths.
- Auto-linked SageVDB shared libs on bootstrap — no manual `ldconfig` or symlink step required.
- Prevented tests from downloading embedding models from the network.
- Fixed duplicate CI workflow content and added `--no-siblings` flag for CI isolation.
- Consolidated `retrieve_knowledge` traces for cleaner workflow visibility.

### Validation

- `PYTHONPATH=src:../SAGE/src pytest tests/ -q`
- `node --check src/sage_faculty_twin/web/app.js`
- `ruff check src/ tests/`
- Live smoke tests against `qwen32b` with SageVDB knowledge backend and Tavily web search.

## v3.0.0 - 2026-06-10

`v3.0.0` marks the first governed planning release (`V3.0: Read-Only Planner Preview`).

### Added

- Added admin replay report API `GET /workflow/replay` with deterministic planner scenario summary.
- Added operations-console Workflow Replay quality board with pass/fail summary, scenario highlights,
  and step chips for quick operator diagnosis.

### Changed

- Promoted package/app version metadata to `3.0.0` and updated frontend cache-busting tokens.
- Updated in-app bottom-right version badge to `v3.0.0`.
- Hardened V3 planner boundary test to avoid host-dependent Neuromem/FAISS embedding initialization,
  keeping regression checks stable in offline environments.

### Validation

- `node --check src/sage_faculty_twin/web/app.js`
- Live admin smoke validation for `/workflow/replay` (planner version, policy version, and scenario pass summary).

## v2.0.2 - 2026-06-10

`v2.0.2` is a quick stabilization patch focused on pre-v3 release hygiene and
runtime visibility.

### Fixed

- Updated frontend cache-busting so both CSS and JS assets ship with the same
  fresh release token, reducing stale-browser UI behavior after deploy.

### Changed

- Added a subtle bottom-right in-app version badge (`v2.0.2`) so operators can
  verify the running UI build without opening developer tools.
- Bumped package version metadata to `2.0.2` and exported
  `sage_faculty_twin.__version__` for runtime/version checks.

## v2.0.1 - 2026-05-29

`v2.0.1` is the pre-v3 stabilization baseline. It keeps the `v2` operations-console scope but
captures the production hardening that landed after the initial `v2.0.0` tag.

### Fixed

- Restored mobile first-open identity selection visibility and prevented first-login modal overlap.
- Hardened critical chat workflows for local Qwen2.5-32B, including deterministic booking routing,
  exact tutorial retrieval, and Chinese relative-time booking such as `明天下午三点`.
- Corrected footer acknowledgements and public links for SAGE, vLLM-HUST, and NeuroMem.

### Changed

- Refined the chat frontend with clearer context labels, folded runtime status, compact workflow
  capability chips, and a more explicit processing state.
- Updated the default owner style profile so current research directions are answered consistently
  before older historical database or stream-processing background.
- Expanded the V3 roadmap with governed planning candidates, architecture shape, step-registry
  constraints, and acceptance criteria.

### Validation

- `PYTHONPATH=src:../SAGE/src:../sageVDB:../neuromem pytest tests/test_agentic_workflow.py tests/test_llm_client.py tests/test_knowledge_base.py tests/test_persona.py -q`
- `node --check src/sage_faculty_twin/web/app.js`
- Live local smoke tests against `qwen32b` and `neuromem` for SAGE/ICML, research direction,
  database lab, Tutorial 7, and Chinese-time booking scenarios.

## v2.0.0 - 2026-05-27

`v2.0.0` is the operations-console release for `sage-faculty-twin`. It moves the app from a
student-facing faculty twin with admin panels into a daily operations workbench for running,
reviewing, and improving the service.

### Added

- Operations overview and workbench APIs for admin-authenticated service review.
- Unified operations task queue covering pending bookings, knowledge gaps, escalations,
  follow-ups, and anonymous suggestions.
- Persistent operations task state overlays with status, assignee, note, and update timestamp.
- Student operations profiles derived from NeuroMem conversation and profile memory.
- Knowledge-gap draft workflow for turning repeated or unresolved question clusters into reviewable
  knowledge entries.
- Satisfaction metrics covering positive rate, unresolved rate, human-handoff rate, feedback
  coverage, reason summaries, and daily trend points.
- Chinese admin operations-console UI sections for task handling, booking review, student profiles,
  satisfaction, knowledge gaps, escalations, follow-ups, and suggestions.
- Operations-console documentation and runtime-data guidance for ignored task-state storage.

### Changed

- Real calendar-provider sync is no longer a `v2` blocker. The supported deployment default is local
  weekly availability plus admin approval, with provider sync left as a future optional integration
  for environments that expose an approved API.
- Roadmap language now treats `v3` as the future governed dynamic-workflow planning release, after
  `v2` operations and observability stabilize.

### Validation

- `PYTHONPATH=src pytest tests/test_operations_overview.py`
- Related backend and full-suite validation were run during the `v2` operations-console workstream.
- `node --check src/sage_faculty_twin/web/app.js`
- `ruff check` on touched backend and test files
- `git diff --check`

## v1.0.1

Maintenance release after the first public baseline.

## v1.0.0

First public repository baseline for the personal academic faculty twin.
