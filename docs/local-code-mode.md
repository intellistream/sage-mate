# Sage Mate Local Profiles

Sage Mate is the local desktop app built from this repository. It should not be confused with
`sage-studio`, the separate intellistream SAGE canvas / low-code pipeline UI.

Faculty Twin still has two deployment profiles:

- `hosted`: multi-user server mode for chat, scheduling, knowledge, and voice. It must not read,
  clone, store, or execute user repositories.
- `local_code`: user-installed mode where the Faculty Twin harness runs on the user's own machine
  next to their code, while the LLM endpoint may still be a remote vLLM-HUST/OpenAI-compatible
  service.

## Recommended Architecture

```text
User machine
  Faculty Twin local_code
    - chat UI and harness
    - workflow planner
    - code tools
    - local workspace allowlist
    - local command execution

Remote server
  vLLM-HUST / OpenAI-compatible endpoint
    - model inference only
    - no user repository storage
    - no user command execution
```

This keeps the harness close to the code and avoids routing local file and command operations
through a hosted Faculty Twin server.

## Configuration

On macOS, the easiest local install is:

```text
Open dist/sage-mate-macos.dmg and double-click:
Sage Mate.app
```

The DMG contains a standalone macOS app. On first launch it creates a local virtualenv, installs
Faculty Twin under `~/Library/Application Support/Sage Mate/app`, writes safe `local_code`
defaults, initializes a local runtime-data folder, starts the private local backend, and opens the
embedded app window. It should not open the user's browser. Configure model service, runtime data,
and workspace allowlist from the Settings screen after the first launch.

The app-level profile is:

- `faculty_twin`: digital twin, knowledge, chat, scheduling, and workflow features; code tools off.
- `code_assistant`: local code assistant features; code tools on for allowlisted repositories.

The important first-run settings in the UI are:

- LLM endpoint: `DIGITAL_TWIN_LLM_BASE_URL`, `DIGITAL_TWIN_API_KEY`, and optionally
  `DIGITAL_TWIN_MODEL_NAME`. This can point at a vLLM-HUST/OpenAI-compatible server.
  The local app pre-fills these fields from `SAGE_MATE_PREFILL_ENV` when set, otherwise from common
  local checkouts such as `~/vllm-hust-dev-hub/.env` or the private runtime repository's
  `deployment/vllm-hust-cloudflare.env`. The values are shown only in the local setup UI and are
  persisted back to the app's local `.env` after the user saves.
- Runtime data: `DIGITAL_TWIN_RUNTIME_DIR`. On first install, Sage Mate first looks for an existing
  private runtime-data checkout such as `~/Documents/sage-faculty-twin-runtime-private` or
  `~/Documents/qixin-gaoke-sage-faculty-twin-runtime-private` and uses it automatically. Only when no
  runtime repository is found does it create a clean local folder under
  `~/Library/Application Support/Sage Mate/runtime`. Users can still override this in the setup UI or
  with `--runtime-dir`.

To build a DMG package for other Mac users:

```bash
./quickstart.sh --target mac-dmg
```

Share `dist/sage-mate-macos.dmg`; the recipient opens it and double-clicks `Sage Mate.app`.
Pass `--zip` only if you also need a zip fallback.

For scripted installs:

```bash
./quickstart.sh --target local-mac-app \
  --app-profile code_assistant \
  --workspace "$HOME/my-repo" \
  --runtime-dir "$HOME/Library/Application Support/Sage Mate/runtime" \
  --prefill-env "$HOME/vllm-hust-dev-hub/.env" \
  --llm-base-url "https://your-vllm-hust.example/v1" \
  --api-key "..." \
  --model-name "qwen3-32b"
```

Manual environment equivalent:

```bash
export DIGITAL_TWIN_DEPLOYMENT_MODE=local_code
export DIGITAL_TWIN_APP_PROFILE=code_assistant
export DIGITAL_TWIN_CODE_WORKBENCH_ENABLED=true
export DIGITAL_TWIN_CODE_WORKSPACE_ROOTS="$HOME/my-repo,$HOME/another-repo"
export DIGITAL_TWIN_RUNTIME_DIR="$HOME/Library/Application Support/Sage Mate/runtime"
export DIGITAL_TWIN_LLM_BASE_URL="https://your-vllm-hust.example/v1"
export DIGITAL_TWIN_API_KEY="..."
```

In hosted deployments, code tools remain disabled even if workspace paths are configured.

### Optional Claude Code Hust Backend

Sage Mate's default code backend is `internal`: a small Python/FastAPI local harness with
propose-only behavior. Local macOS installs now try to install `claude-code-hust` automatically
when the selected profile is `code_assistant`. If that succeeds, the installer writes
the local `bin/claude-hust` path into `.env` and switches Sage Mate to the external CLI adapter:

```bash
./quickstart.sh --target local-mac-app --app-profile code_assistant --workspace "$HOME/my-repo"
```

The checkout is managed as a Sage Mate sibling repository, matching the existing source-checkout
pattern used by `SAGE`, `neuromem`, and `sageVDB`:

```text
parent/
  faculty-twin/
  SAGE/
  neuromem/
  sageVDB/
  claude-code-hust/
```

When `FACULTY_TWIN_PARENT_DIR` is set, `quickstart.sh --target local-mac-app` places the sibling at
`$FACULTY_TWIN_PARENT_DIR/claude-code-hust`. Otherwise it defaults to `../claude-code-hust` relative
to this repository. In the packaged DMG app, the equivalent sibling lives under
`~/Library/Application Support/Sage Mate/claude-code-hust`, next to the installed app source.

Useful installer controls:

```bash
./quickstart.sh --target local-mac-app --code-backend internal
./quickstart.sh --target local-mac-app --code-backend claude_hust
./quickstart.sh --target local-mac-app --claude-hust-repo https://github.com/vLLM-HUST/claude-code-hust.git
./quickstart.sh --target local-mac-app --claude-hust-dir "$HOME/Documents/claude-code-hust"
./quickstart.sh --target local-mac-app --skip-claude-hust
```

The app launches `claude-hust --print --no-session-persistence` with `CC_HUST_SKIP_DOTENV=1`.
When the configured model service is OpenAI-compatible only, such as a plain vLLM `/v1` endpoint,
Sage Mate starts a short-lived local compatibility proxy and points `claude-hust` at that local
proxy. `/code ask` and `/code propose` run against a temporary local copy of the selected
allowlisted workspace, so the external agent can inspect code with its own tools while real user
files remain untouched by Sage Mate's MVP propose-only flows.

`claude-hust` is not the outer harness. Sage Mate remains the workflow owner: it selects and
validates the workspace, builds git/file context, controls provider settings, records
`workflow_trace` steps, parses proposals, and returns observable execution paths to the same UI used
by the Faculty Twin profile. The external CLI is treated as a local code-analysis node inside that
workflow.

## Current Code Commands

The first local-code surface is intentionally narrow:

```text
/code workspaces
/code ls <workspace> [path]
/code search <workspace> <query> [--glob <pattern>]
/code read <workspace> <path> [start_line] [max_lines]
/code status <workspace>
/code diff <workspace> [path] [--staged]
/code context <workspace> [path] ...
/code run <workspace> <read-only command>
/code ask <workspace> <task> [-- <path> ...]
/code propose <workspace> <task> [-- <path> ...]
```

The workbench now supports repository orientation before model assistance:

- `/code ls` lists files and directories inside the selected workspace.
- `/code status` and `/code diff` expose git state without mutating the repository.
- `/code context` bundles git state and selected files into a single prompt-ready context pack.
- `/code propose` asks the LLM for a propose-only change plan. The prompt includes workspace
  identity, git status, current git diff, and any explicitly selected file context. The response
  is structured as summary, affected files, unified diff suggestion, risks, and suggested tests.

`/code run` is restricted to allowlisted commands and defaults to read-only behavior. Write
operations should be introduced later through a diff proposal plus explicit confirmation flow.

## HTTP API

Local installs can call the same propose-only flow through:

```text
POST /code/propose
```

Request body:

```json
{
  "workspace_id": "my-repo",
  "task": "Fix the parser edge case without changing public API",
  "paths": ["src/parser.py", "tests/test_parser.py"]
}
```

Response body includes:

- `summary`
- `affected_files`
- `unified_diff`
- `risks`
- `suggested_tests`
- `proposal` (raw model response)
- `context_paths`
- `used_model`

This endpoint does not apply patches or write files. Apply support is intentionally absent in the
MVP; if added later it should stay behind a default-off explicit configuration switch and require
user confirmation.

## Safety Boundaries

- Hosted mode must not expose local code workspaces, commands, or proposal tools.
- Workspace roots are allowlisted with `DIGITAL_TWIN_CODE_WORKSPACE_ROOTS`.
- Every file path is resolved under its selected workspace; path escapes are rejected.
- Propose-only flows read git status, git diff, and selected file content, then call the LLM. They
  never write repository files.

## Claude Code Hust Integration Boundary

`claude-code-hust` is available on the internal 180-ascend-bench host at
`/home/shuhao/claude-code-hust`, with origin `git@github.com:vLLM-HUST/claude-code-hust.git`.
Its package exposes a `claude-hust` CLI through `bin/claude-hust`, and its headless path supports
`--print`, `--input-format`, and `--output-format` flows.

Do not vendor or copy its source into Sage Mate. The repository's own LICENSE/README state that it
was repaired from leaked Anthropic Claude Code source and is limited to educational/research use.
Sage Mate integrates it as a separate local dependency installed by the local macOS installer.
Hosted web deployments must not install it, expose it, or enable code tools.

The intended split is:

- Sage Mate owns the macOS app shell, local settings, workspace allowlist, profile selection,
  hosted/local deployment boundary, and user-facing conversation UI.
- A `claude-hust` adapter may be configured for local installs to run workspace-first code sessions
  through an external command, with `CC_HUST_SKIP_DOTENV=1` so Sage Mate controls provider settings.
- Hosted web deployments still run with `DIGITAL_TWIN_DEPLOYMENT_MODE=hosted` and
  `DIGITAL_TWIN_CODE_WORKBENCH_ENABLED=false`, regardless of whether `claude-hust` exists on the
  server.
