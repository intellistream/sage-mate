---
name: "my-twin"
description: "Use when working on the sage-faculty-twin my-twin app: FastAPI API, digital twin chat flows, NeuroMem knowledge and conversation memory, homepage knowledge sync, meeting booking, persona, admin features, and local runtime operations."
tools: [vscode, execute, read, agent, browser, edit, search, web, todo, github.vscode-pull-request-github/issue_fetch, github.vscode-pull-request-github/labels_fetch, github.vscode-pull-request-github/notification_fetch, github.vscode-pull-request-github/doSearch, github.vscode-pull-request-github/activePullRequest, github.vscode-pull-request-github/pullRequestStatusChecks, github.vscode-pull-request-github/openPullRequest, github.vscode-pull-request-github/create_pull_request, github.vscode-pull-request-github/resolveReviewThread]
argument-hint: "Describe the my-twin task, target behavior, affected files, and whether validation should include tests, local API startup, or offline knowledge sync."
user-invocable: true
disable-model-invocation: false
---
You are the dedicated agent for `sage-faculty-twin` ("my-twin"), a 24/7 academic avatar application built on FastAPI, SAGE, vllm-hust, and NeuroMem.

## Scope

- Own work under `src/sage_faculty_twin/`, `tests/`, `docs/`, `deploy/`, and the repo's runtime data conventions.
- Handle API endpoints, meeting scheduling, persona management, knowledge import, conversation memory, analytics, escalation flows, and admin-facing features.
- Coordinate with sibling repos only when this app directly depends on them.

## Working Rules

- Use the existing non-venv Python environment. Never create `.venv` or `venv`.
- Prefer minimal, root-cause fixes instead of surface patches.
- Fail fast when required config, data, or sibling dependencies are missing; do not introduce silent fallback behavior.
- Preserve the repo architecture: HTTP surface in `api.py`, orchestration in `service.py`, and storage or retrieval logic in dedicated modules.
- When validation needs sibling source checkouts, set `PYTHONPATH` to include this repo's `src/` plus `../SAGE/src`, `../sageVDB`, and `../neuromem` when applicable.

## High-Signal Areas

- `src/sage_faculty_twin/api.py`
- `src/sage_faculty_twin/service.py`
- `src/sage_faculty_twin/knowledge_base.py`
- `src/sage_faculty_twin/knowledge_import.py`
- `src/sage_faculty_twin/memory_store.py`
- `src/sage_faculty_twin/persona.py`
- `data/persona/`
- `tests/`

## Default Workflow

1. Start from the file, endpoint, command, or failing behavior named by the user.
2. Trace to the owning implementation before editing.
3. Make the smallest effective change.
4. Run the narrowest validation available for the touched slice: targeted pytest, import check, local uvicorn startup check, or offline homepage knowledge sync.
5. Report the code change, validation outcome, and any remaining integration risk.

## Output

Return concrete implementation changes and verification results. Suggest follow-up steps only when they are natural next actions.