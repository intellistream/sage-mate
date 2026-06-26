# Local Code Mode

Faculty Twin has two deployment profiles:

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

```bash
export DIGITAL_TWIN_DEPLOYMENT_MODE=local_code
export DIGITAL_TWIN_CODE_WORKBENCH_ENABLED=true
export DIGITAL_TWIN_CODE_WORKSPACE_ROOTS="$HOME/my-repo,$HOME/another-repo"
export DIGITAL_TWIN_LLM_BASE_URL="https://your-vllm-hust.example/v1"
export DIGITAL_TWIN_API_KEY="..."
```

In hosted deployments, code tools remain disabled even if workspace paths are configured.

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
```

The workbench now supports repository orientation before model assistance:

- `/code ls` lists files and directories inside the selected workspace.
- `/code status` and `/code diff` expose git state without mutating the repository.
- `/code context` bundles git state and selected files into a single prompt-ready context pack.

`/code run` is restricted to allowlisted commands and defaults to read-only behavior. Write
operations should be introduced later through a diff proposal plus explicit confirmation flow.

## Claude Code Reference Boundary

Claude Code HUST is useful as architecture research material for:

- tool-driven harness design,
- shell task lifecycle,
- command guardrails,
- output truncation and summaries,
- worktree isolation,
- approval UX.

Do not vendor or copy Claude Code HUST source into Faculty Twin. Its repository declares that it is
based on leaked Anthropic source and is limited to educational/research use. Faculty Twin should
implement a clean-room, CC-inspired local code harness in Python/FastAPI.
