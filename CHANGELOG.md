# Changelog

## Unreleased

### Changed

- Added SageVDB and SageANNS version chips to the Powered By footer. Version
  resolution uses a unified `_resolve_source_version()` helper that tries pip
  metadata, module import, and pyproject.toml parsing in order, so all stack
  components (SAGE, NeuroMem, vLLM-HUST, SageVDB, SageANNS) show correct
  versions regardless of install method.
- `tools/run_app_server.sh` now validates `sagevdb` and `sage_anns` imports
  before starting uvicorn and auto-installs `isage-vdb` / `isage-anns` from
  PyPI if either is missing. No manual dependency installation required.
- Created `.env.template` with all environment variables documented and
  secrets replaced by `<placeholder>` markers.
- Upgraded the Neuromem integration baseline to `isage-neuromem>=0.2.1.12` and
  aligned the app's knowledge-memory path with the newer BM25/numpy backend
  behavior. Knowledge and conversation memory now keep the numpy BM25 path as
  the default integration choice so the app can consume the newer Neuromem
  runtime without relying on the old numba fallback path.
- Rewired the chat workflow as a SAGE `DataStream` DAG instead of a 13-stage linear
  chain. Memory and knowledge retrieval now run in parallel through a 2-way
  `connect`/`comap` join, and the four post-answer side-effect stages
  (`memory_persist`, `memory_profile_consolidate`, `follow_up_plan`,
  `memory_usefulness_score`) fan out through a 4-way `connect`/`comap` join.
  The legacy linear `_run_pipeline` is preserved for the admin / auth /
  booking single-stage callers. The `workflow_trace` contract (canonical key
  order and statuses) is unchanged: a deterministic post-processing pass in
  `ChatResponseRenderStage` re-sorts the trace into
  `_CANONICAL_TRACE_ORDER` so any out-of-order arrivals from parallel
  branches are normalised before the response leaves the service.

### Fixed

- (SAGE) `PipelineCompiler._normalize_outputs` no longer fragments arbitrary
  iterable results from `Map`/`CoMap` transformations. It now flattens only
  when the caller opts in (`flatten=True`), which is correct for `FlatMap`
  and `Join` (whose contracts emit zero-or-more items per input) but wrong
  for `Map`/`CoMap` (single output per input). Previously a `Map` returning
  a Pydantic `BaseModel` (e.g. `ChatResponse`) was shredded into one packet
  per `(field_name, value)` pair downstream of any non-linear topology.

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
