# Changelog

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
