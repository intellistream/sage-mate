#!/usr/bin/env bash
# install_local_code_mode.sh — one-command Sage Mate local setup.
#
# Examples:
#   tools/install_local_code_mode.sh --workspace "$HOME/my-repo"
#   tools/install_local_code_mode.sh --workspace "$HOME/my-repo" --start
#   tools/install_local_code_mode.sh \
#     --workspace "$HOME/my-repo" \
#     --runtime-dir "$HOME/Library/Application Support/Sage Mate/runtime" \
#     --llm-base-url "https://your-vllm.example/v1" \
#     --api-key "..." \
#     --model-name "qwen3-32b"

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
venv_dir="$repo_root/.venv"
python_bin="${PYTHON_BIN:-}"
app_port="${APP_PORT:-55601}"
app_profile="${DIGITAL_TWIN_APP_PROFILE:-code_assistant}"
runtime_dir="${DIGITAL_TWIN_RUNTIME_DIR:-}"
runtime_dir_explicit=false
llm_base_url="${DIGITAL_TWIN_LLM_BASE_URL:-http://127.0.0.1:8000/v1}"
api_key="${DIGITAL_TWIN_API_KEY:-EMPTY}"
model_name="${DIGITAL_TWIN_MODEL_NAME:-}"
code_agent_backend="${DIGITAL_TWIN_CODE_AGENT_BACKEND:-auto}"
claude_hust_repo="${SAGE_MATE_CLAUDE_HUST_REPO:-https://github.com/vLLM-HUST/claude-code-hust.git}"
claude_hust_dir="${SAGE_MATE_CLAUDE_HUST_DIR:-$(dirname "$repo_root")/claude-code-hust}"
claude_hust_cli_path="${DIGITAL_TWIN_CLAUDE_HUST_CLI_PATH:-}"
skip_claude_hust=false
start_app=false
workspace_roots=()

prefill_env="${SAGE_MATE_PREFILL_ENV:-}"
if [[ -z "$prefill_env" ]]; then
    for candidate in \
        "$HOME/vllm-hust-dev-hub/.env" \
        "$HOME/Documents/vllm-hust-dev-hub/.env" \
        "$HOME/dev-hub/.env" \
        "$HOME/Documents/dev-hub/.env" \
        "$HOME/Documents/sage-faculty-twin-runtime-private/deployment/vllm-hust-cloudflare.env" \
        "$HOME/qixin-gaoke-sage-faculty-twin-runtime-private/deployment/vllm-hust-cloudflare.env" \
        "$HOME/Documents/qixin-gaoke-sage-faculty-twin-runtime-private/deployment/vllm-hust-cloudflare.env"; do
        if [[ -f "$candidate" ]]; then
            prefill_env="$candidate"
            break
        fi
    done
fi
llm_base_url_explicit=false
api_key_explicit=false
model_name_explicit=false

log()  { printf '\033[1;36m[local-code-install]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[local-code-install]\033[0m %s\n' "$*" >&2; }
fail() { printf '\033[1;31m[local-code-install]\033[0m %s\n' "$*" >&2; exit 1; }

usage() {
    sed -n '2,15p' "$0"
    cat <<'EOF'

Flags:
  --workspace PATH        Allowlist a local repository. Repeatable.
  --workspace-roots CSV   Comma-separated allowlist of local repositories.
  --profile NAME          App profile: faculty_twin or code_assistant.
  --runtime-dir PATH      Local runtime-data folder.
  --llm-base-url URL      OpenAI-compatible /v1 endpoint.
  --api-key KEY           API key for the LLM endpoint. Defaults to EMPTY.
  --model-name NAME       Model name sent to the LLM endpoint.
  --prefill-env PATH      Read default LLM URL/API key/model from this env file.
  --code-backend NAME     auto, internal, or claude_hust. Defaults to auto.
  --claude-hust-repo URL  Git URL for the local claude-code-hust dependency.
  --claude-hust-dir PATH  Sibling checkout for claude-code-hust. Defaults to ../claude-code-hust.
  --skip-claude-hust      Do not auto-install claude-code-hust.
  --port PORT             Local app port. Defaults to 55601.
  --python PATH           Python 3.11+ interpreter used to create the venv.
  --venv PATH             Virtualenv directory. Defaults to .venv.
  --start                 Start the local web app after installation.
  -h, --help              Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --workspace)
            [[ $# -ge 2 ]] || fail "--workspace requires a path"
            workspace_roots+=("$2")
            shift 2
            ;;
        --workspace-roots)
            [[ $# -ge 2 ]] || fail "--workspace-roots requires a comma-separated value"
            IFS=',' read -r -a _roots <<< "$2"
            for root in "${_roots[@]}"; do
                [[ -n "${root// }" ]] && workspace_roots+=("$root")
            done
            shift 2
            ;;
        --profile)
            [[ $# -ge 2 ]] || fail "--profile requires a value"
            app_profile="$2"
            shift 2
            ;;
        --llm-base-url)
            [[ $# -ge 2 ]] || fail "--llm-base-url requires a URL"
            llm_base_url="$2"
            llm_base_url_explicit=true
            shift 2
            ;;
        --runtime-dir)
            [[ $# -ge 2 ]] || fail "--runtime-dir requires a path"
            runtime_dir="$2"
            runtime_dir_explicit=true
            shift 2
            ;;
        --api-key)
            [[ $# -ge 2 ]] || fail "--api-key requires a value"
            api_key="$2"
            api_key_explicit=true
            shift 2
            ;;
        --model-name)
            [[ $# -ge 2 ]] || fail "--model-name requires a value"
            model_name="$2"
            model_name_explicit=true
            shift 2
            ;;
        --code-backend)
            [[ $# -ge 2 ]] || fail "--code-backend requires a value"
            code_agent_backend="$2"
            shift 2
            ;;
        --claude-hust-repo)
            [[ $# -ge 2 ]] || fail "--claude-hust-repo requires a git URL"
            claude_hust_repo="$2"
            shift 2
            ;;
        --claude-hust-dir)
            [[ $# -ge 2 ]] || fail "--claude-hust-dir requires a path"
            claude_hust_dir="${2/#\~/$HOME}"
            shift 2
            ;;
        --skip-claude-hust)
            skip_claude_hust=true
            shift
            ;;
        --prefill-env)
            [[ $# -ge 2 ]] || fail "--prefill-env requires a path"
            prefill_env="${2/#\~/$HOME}"
            shift 2
            ;;
        --port)
            [[ $# -ge 2 ]] || fail "--port requires a value"
            app_port="$2"
            shift 2
            ;;
        --python)
            [[ $# -ge 2 ]] || fail "--python requires a path"
            python_bin="$2"
            shift 2
            ;;
        --venv)
            [[ $# -ge 2 ]] || fail "--venv requires a path"
            venv_dir="$2"
            shift 2
            ;;
        --start)
            start_app=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            fail "Unknown argument: $1"
            ;;
    esac
done

[[ -f "$repo_root/pyproject.toml" ]] || fail "Run this script from a sage-faculty-twin checkout."
case "$app_profile" in
    faculty_twin|code_assistant) ;;
    *) fail "--profile must be one of: faculty_twin, code_assistant" ;;
esac
case "$code_agent_backend" in
    auto|internal|claude_hust) ;;
    *) fail "--code-backend must be one of: auto, internal, claude_hust" ;;
esac

if [[ -n "$prefill_env" && -f "$prefill_env" ]]; then
    set -a
    # shellcheck disable=SC1090
    . "$prefill_env"
    set +a
    if ! $llm_base_url_explicit; then
        llm_base_url="${DIGITAL_TWIN_LLM_BASE_URL:-${VLLM_HUST_API_BASE_URL:-$llm_base_url}}"
    fi
    if ! $api_key_explicit; then
        api_key="${DIGITAL_TWIN_API_KEY:-${VLLM_HUST_API_KEY:-$api_key}}"
    fi
    if ! $model_name_explicit; then
        model_name="${DIGITAL_TWIN_MODEL_NAME:-${VLLM_HUST_MODEL:-$model_name}}"
    fi
    log "Using local model prefill: $prefill_env"
fi

discover_existing_runtime_dir() {
    local candidate
    for candidate in \
        "$HOME/Documents/sage-faculty-twin-runtime-private" \
        "$HOME/sage-faculty-twin-runtime-private" \
        "$HOME/Documents/qixin-gaoke-sage-faculty-twin-runtime-private" \
        "$HOME/qixin-gaoke-sage-faculty-twin-runtime-private" \
        "$(dirname "$repo_root")/sage-faculty-twin-runtime-private" \
        "$(dirname "$repo_root")/qixin-gaoke-sage-faculty-twin-runtime-private"; do
        [[ -d "$candidate" ]] || continue
        if [[ -d "$candidate/.git" || -d "$candidate/data" || -d "$candidate/deployment" ]]; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done
    return 1
}

should_install_claude_hust() {
    [[ "$app_profile" == "code_assistant" ]] || return 1
    [[ "$code_agent_backend" != "internal" ]] || return 1
    ! $skip_claude_hust
}

github_clone_url() {
    local url="$1"
    if [[ -n "${GITHUB_TOKEN:-}" && "$url" =~ ^https://github.com/ ]]; then
        printf 'https://x-access-token:%s@%s' "$GITHUB_TOKEN" "${url#https://}"
    else
        printf '%s' "$url"
    fi
}

ensure_bun() {
    if command -v bun >/dev/null 2>&1; then
        command -v bun
        return 0
    fi
    if [[ -x "$HOME/.bun/bin/bun" ]]; then
        printf '%s\n' "$HOME/.bun/bin/bun"
        return 0
    fi
    command -v curl >/dev/null 2>&1 || return 1
    log "Installing Bun for local claude-code-hust runtime"
    if curl -fsSL https://bun.sh/install | bash >/dev/null; then
        [[ -x "$HOME/.bun/bin/bun" ]] && printf '%s\n' "$HOME/.bun/bin/bun"
        return 0
    fi
    return 1
}

install_claude_hust() {
    claude_hust_dir="${claude_hust_dir/#\~/$HOME}"
    local cli="$claude_hust_dir/bin/claude-hust"
    if [[ -x "$cli" && -d "$claude_hust_dir/node_modules" ]]; then
        if ! ensure_bun >/dev/null; then
            warn "Bun is required for claude-code-hust but could not be installed automatically."
            return 1
        fi
        claude_hust_cli_path="$cli"
        log "Using existing sibling claude-code-hust: $claude_hust_dir"
        return 0
    fi

    command -v git >/dev/null 2>&1 || return 1
    mkdir -p "$(dirname "$claude_hust_dir")"
    if [[ ! -d "$claude_hust_dir" ]]; then
        log "Cloning sibling claude-code-hust into: $claude_hust_dir"
        local clone_url
        clone_url=$(github_clone_url "$claude_hust_repo")
        if ! git clone --depth=1 "$clone_url" "$claude_hust_dir"; then
            warn "Could not clone claude-code-hust from $claude_hust_repo"
            return 1
        fi
    else
        log "Found sibling claude-code-hust directory: $claude_hust_dir"
    fi

    local bun_bin
    if ! bun_bin=$(ensure_bun); then
        warn "Bun is required for claude-code-hust but could not be installed automatically."
        return 1
    fi

    log "Installing claude-code-hust dependencies with Bun"
    if ! (cd "$claude_hust_dir" && PATH="$(dirname "$bun_bin"):$PATH" "$bun_bin" install); then
        warn "bun install failed for claude-code-hust"
        return 1
    fi

    chmod +x "$cli" 2>/dev/null || true
    [[ -x "$cli" ]] || return 1
    claude_hust_cli_path="$cli"
    return 0
}

if [[ -z "$python_bin" ]]; then
    candidates=()
    for name in python3.12 python3.11 python3; do
        if command -v "$name" >/dev/null 2>&1; then
            candidates+=("$(command -v "$name")")
        fi
    done
    shopt -s nullglob
    candidates+=(
        "$HOME"/.local/share/uv/python/*/bin/python3.12
        "$HOME"/.local/share/uv/python/*/bin/python3.11
        "$HOME"/miniforge3/envs/*/bin/python3.12
        "$HOME"/miniforge3/envs/*/bin/python3.11
        "$HOME"/miniconda3/envs/*/bin/python3.12
        "$HOME"/miniconda3/envs/*/bin/python3.11
        "$HOME"/anaconda3/envs/*/bin/python3.12
        "$HOME"/anaconda3/envs/*/bin/python3.11
        /opt/homebrew/bin/python3.12
        /opt/homebrew/bin/python3.11
        /usr/local/bin/python3.12
        /usr/local/bin/python3.11
    )
    shopt -u nullglob
    for candidate in "${candidates[@]}"; do
        [[ -x "$candidate" ]] || continue
        if "$candidate" - <<'PY' >/dev/null 2>&1; then
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
            python_bin="$candidate"
            break
        fi
    done
    [[ -n "$python_bin" ]] || fail "Python 3.11+ not found. Install Python 3.11+ or pass --python PATH."
fi

py_ver=$("$python_bin" -c 'import sys; print("%d.%d" % sys.version_info[:2])')
"$python_bin" - <<'PY' || fail "Python 3.11+ is required."
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
log "Using Python: $python_bin ($py_ver)"

resolved_roots=()
set +u
for root in "${workspace_roots[@]}"; do
    expanded="${root/#\~/$HOME}"
    [[ -d "$expanded" ]] || fail "Workspace does not exist: $root"
    resolved=$(cd "$expanded" && pwd -P)
    resolved_roots+=("$resolved")
done

workspace_csv=$(IFS=','; printf '%s' "${resolved_roots[*]}")
set -u
if [[ -z "$runtime_dir" ]]; then
    if discovered_runtime_dir=$(discover_existing_runtime_dir); then
        runtime_dir="$discovered_runtime_dir"
        log "Using existing runtime repository: $runtime_dir"
    else
        runtime_dir="$HOME/Library/Application Support/Sage Mate/runtime"
        log "No existing runtime repository found; creating a new local runtime folder."
    fi
elif ! $runtime_dir_explicit && [[ -n "${DIGITAL_TWIN_RUNTIME_DIR:-}" ]]; then
    log "Using runtime folder from DIGITAL_TWIN_RUNTIME_DIR: $runtime_dir"
fi
runtime_dir="${runtime_dir/#\~/$HOME}"
mkdir -p "$runtime_dir"
runtime_dir=$(cd "$runtime_dir" && pwd -P)

log "Preparing runtime data folder: $runtime_dir"
mkdir -p \
    "$runtime_dir/.runtime/online_presence" \
    "$runtime_dir/data/alerts" \
    "$runtime_dir/data/artifact_memory_drafts" \
    "$runtime_dir/data/availability/history" \
    "$runtime_dir/data/capability_plugins" \
    "$runtime_dir/data/conversation_memory/digests" \
    "$runtime_dir/data/escalations" \
    "$runtime_dir/data/follow_up_actions" \
    "$runtime_dir/data/homepage" \
    "$runtime_dir/data/installed_skills" \
    "$runtime_dir/data/knowledge_base" \
    "$runtime_dir/data/knowledge_gap_drafts" \
    "$runtime_dir/data/operations_task_state" \
    "$runtime_dir/data/persona" \
    "$runtime_dir/data/skills" \
    "$runtime_dir/data/slack_user_links" \
    "$runtime_dir/data/suggestions" \
    "$runtime_dir/data/user_accounts" \
    "$runtime_dir/data/workflow_policies" \
    "$runtime_dir/data/workflow_scenarios"

[[ -f "$runtime_dir/data/persona/style_profile.md" ]] || printf '%s\n' "# Local Sage Mate style profile" > "$runtime_dir/data/persona/style_profile.md"
[[ -f "$runtime_dir/data/availability/current_week.json" ]] || printf '%s\n' '{"timezone":"Asia/Shanghai","slots":[]}' > "$runtime_dir/data/availability/current_week.json"
[[ -f "$runtime_dir/data/changelog.json" ]] || printf '%s\n' '[]' > "$runtime_dir/data/changelog.json"
[[ -f "$runtime_dir/data/workflow_policies/faculty-default-2026-05.json" ]] || printf '%s\n' '{"policy_version":"faculty-default-2026-05"}' > "$runtime_dir/data/workflow_policies/faculty-default-2026-05.json"
[[ -f "$runtime_dir/data/workflow_scenarios/v3_preview_scenarios.json" ]] || printf '%s\n' '[]' > "$runtime_dir/data/workflow_scenarios/v3_preview_scenarios.json"

log "Creating virtualenv: $venv_dir"
"$python_bin" -m venv "$venv_dir"
venv_python="$venv_dir/bin/python"

log "Installing sage-faculty-twin into the virtualenv"
"$venv_python" -m pip install --quiet --upgrade pip
if ! "$venv_python" -m pip install --quiet -e "$repo_root[vdb-anns]"; then
    warn "vdb-anns extras failed; falling back to base install."
    "$venv_python" -m pip install --quiet -e "$repo_root"
fi

resolved_code_agent_backend="internal"
if [[ "$code_agent_backend" == "claude_hust" && "$app_profile" == "faculty_twin" ]]; then
    warn "claude_hust backend requested, but profile is faculty_twin; keeping code backend internal."
elif should_install_claude_hust; then
    if install_claude_hust; then
        resolved_code_agent_backend="claude_hust"
    elif [[ "$code_agent_backend" == "claude_hust" ]]; then
        fail "claude_hust backend was requested, but claude-code-hust could not be installed."
    else
        warn "Continuing with the internal propose-only code backend."
    fi
elif [[ "$code_agent_backend" == "claude_hust" ]]; then
    if [[ -n "$claude_hust_cli_path" && -x "$claude_hust_cli_path" ]]; then
        resolved_code_agent_backend="claude_hust"
    else
        fail "claude_hust backend requested, but no executable DIGITAL_TWIN_CLAUDE_HUST_CLI_PATH was found."
    fi
fi

env_file="$repo_root/.env"
if [[ ! -f "$env_file" ]]; then
    if [[ -f "$repo_root/.env.example" ]]; then
        cp "$repo_root/.env.example" "$env_file"
    else
        touch "$env_file"
    fi
fi

log "Writing local-code configuration: $env_file"
export INSTALL_APP_PROFILE="$app_profile"
export INSTALL_CODE_WORKSPACE_ROOTS="$workspace_csv"
export INSTALL_RUNTIME_DIR="$runtime_dir"
export INSTALL_LLM_BASE_URL="$llm_base_url"
export INSTALL_API_KEY="$api_key"
export INSTALL_MODEL_NAME="$model_name"
export INSTALL_CODE_AGENT_BACKEND="$resolved_code_agent_backend"
export INSTALL_CLAUDE_HUST_CLI_PATH="$claude_hust_cli_path"
"$venv_python" - "$env_file" <<'PY'
from __future__ import annotations

import os
import sys
from pathlib import Path

env_path = Path(sys.argv[1])
updates = {
    "DIGITAL_TWIN_APP_PROFILE": os.environ["INSTALL_APP_PROFILE"],
    "DIGITAL_TWIN_DEPLOYMENT_MODE": "local_code",
    "DIGITAL_TWIN_CODE_WORKBENCH_ENABLED": (
        "true" if os.environ["INSTALL_APP_PROFILE"] == "code_assistant" else "false"
    ),
    "DIGITAL_TWIN_CODE_WORKSPACE_ROOTS": (
        os.environ["INSTALL_CODE_WORKSPACE_ROOTS"]
        if os.environ["INSTALL_APP_PROFILE"] == "code_assistant"
        else ""
    ),
    "DIGITAL_TWIN_CODE_AGENT_BACKEND": os.environ["INSTALL_CODE_AGENT_BACKEND"],
    "DIGITAL_TWIN_CLAUDE_HUST_CLI_PATH": os.environ["INSTALL_CLAUDE_HUST_CLI_PATH"],
    "DIGITAL_TWIN_RUNTIME_DIR": os.environ["INSTALL_RUNTIME_DIR"],
    "DIGITAL_TWIN_HOMEPAGE_DIR": str(Path(os.environ["INSTALL_RUNTIME_DIR"]) / "data/homepage"),
    "DIGITAL_TWIN_KNOWLEDGE_BASE_DIR": str(Path(os.environ["INSTALL_RUNTIME_DIR"]) / "data/knowledge_base"),
    "DIGITAL_TWIN_CONVERSATION_MEMORY_DIR": str(Path(os.environ["INSTALL_RUNTIME_DIR"]) / "data/conversation_memory"),
    "DIGITAL_TWIN_AVAILABILITY_SCHEDULE_PATH": str(Path(os.environ["INSTALL_RUNTIME_DIR"]) / "data/availability/current_week.json"),
    "DIGITAL_TWIN_INSTALLED_SKILL_PROMPT_PATH": str(Path(os.environ["INSTALL_RUNTIME_DIR"]) / "data/installed_skills/fixed_prompt_skills.md"),
    "DIGITAL_TWIN_USER_ACCOUNT_STORE_DIR": str(Path(os.environ["INSTALL_RUNTIME_DIR"]) / "data/user_accounts"),
    "DIGITAL_TWIN_CAPABILITY_PLUGIN_DIR": str(Path(os.environ["INSTALL_RUNTIME_DIR"]) / "data/capability_plugins"),
    "DIGITAL_TWIN_WORKFLOW_POLICY_PATH": str(Path(os.environ["INSTALL_RUNTIME_DIR"]) / "data/workflow_policies/faculty-default-2026-05.json"),
    "DIGITAL_TWIN_WORKFLOW_SCENARIO_PATH": str(Path(os.environ["INSTALL_RUNTIME_DIR"]) / "data/workflow_scenarios/v3_preview_scenarios.json"),
    "DIGITAL_TWIN_LLM_BASE_URL": os.environ["INSTALL_LLM_BASE_URL"],
    "DIGITAL_TWIN_API_KEY": os.environ["INSTALL_API_KEY"],
    "DIGITAL_TWIN_KNOWLEDGE_BACKEND": "neuromem",
    "DIGITAL_TWIN_NEUROMEM_INDEX_TYPE": "bm25",
    "DIGITAL_TWIN_CONVERSATION_MEMORY_COLLECTION_TYPE": "unified",
    "DIGITAL_TWIN_CONVERSATION_MEMORY_INDEX_TYPE": "segment",
    "DIGITAL_TWIN_STREAM_CHAT_ANSWER": "true",
    "DIGITAL_TWIN_WARM_SERVICE_ON_STARTUP": "false",
}
model_name = os.environ.get("INSTALL_MODEL_NAME", "").strip()
if model_name:
    updates["DIGITAL_TWIN_MODEL_NAME"] = model_name

lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
seen: set[str] = set()
next_lines: list[str] = []
for line in lines:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in line:
        next_lines.append(line)
        continue
    key = line.split("=", 1)[0].strip()
    if key in updates:
        next_lines.append(f"{key}={updates[key]}")
        seen.add(key)
    else:
        next_lines.append(line)

for key, value in updates.items():
    if key not in seen:
        next_lines.append(f"{key}={value}")

env_path.write_text("\n".join(next_lines).rstrip() + "\n", encoding="utf-8")
PY

cat <<EOF

Sage Mate is installed.

App profile:
  $app_profile

Workspace allowlist:
$(set +u; if [[ ${#resolved_roots[@]} -gt 0 ]]; then printf '  - %s\n' "${resolved_roots[@]}"; else printf '  (configure in the web UI after startup)\n'; fi)

Runtime data folder:
  $runtime_dir

Code backend:
  $resolved_code_agent_backend
$(if [[ "$resolved_code_agent_backend" == "claude_hust" ]]; then printf '  %s\n' "$claude_hust_cli_path"; else printf '  internal propose-only harness\n'; fi)
$(if [[ "$resolved_code_agent_backend" == "claude_hust" ]]; then printf 'Sibling dependency:\n  %s\n' "$claude_hust_dir"; fi)

Run it with:
  PYTHON_BIN="$venv_python" APP_PORT="$app_port" tools/run_app_server.sh

Then open:
  http://127.0.0.1:$app_port/

Try in chat:
  /code workspaces

EOF

if $start_app; then
    log "Starting local app on http://127.0.0.1:$app_port/"
    if command -v open >/dev/null 2>&1; then
        (sleep 8; open "http://127.0.0.1:$app_port/?setup=local-code") >/dev/null 2>&1 &
    fi
    export PYTHON_BIN="$venv_python"
    export APP_PORT="$app_port"
    exec "$repo_root/tools/run_app_server.sh"
fi
