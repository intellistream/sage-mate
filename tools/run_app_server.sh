#!/usr/bin/env bash
# run_app_server.sh — Start the sage-faculty-twin uvicorn server.

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source "$repo_root/tools/lib/runtime_env.sh"
app_port="${APP_PORT:-55601}"

# --- Load .env before runtime defaults so installer-written paths take effect. ---
if [[ -f "$repo_root/.env" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        key="${line%%=*}"
        key="${key// /}"
        [[ -z "$key" || -n "${!key:-}" ]] && continue
        export "$line"
    done < "$repo_root/.env"
fi

export_repo_runtime_env "$repo_root"
python_exec="$PYTHON_BIN"

# --- HuggingFace cache setup (always use writable local cache) ---
hf_home="$HOME/.cache/hf-models"
mkdir -p "$hf_home/hub"
export HF_HOME="$hf_home"
export HUGGINGFACE_HUB_CACHE="$hf_home/hub"
export HF_HUB_CACHE="$hf_home/hub"
export TRANSFORMERS_CACHE="$hf_home/hub"
export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"

# --- Validate and auto-install knowledge backend dependencies ---
# sagevdb (C extension) and sage-anns (ANNS algorithms) are required when
# DIGITAL_TWIN_KNOWLEDGE_BACKEND=sagevdb.  Auto-install if missing.
_ensure_knowledge_deps() {
    local py="$1"
    local missing=()

    if ! "$py" -c "from sagevdb import DatabaseConfig" 2>/dev/null; then
        missing+=("isage-vdb>=0.2.0.9")
    fi
    if ! "$py" -c "from sage_anns import create_index" 2>/dev/null; then
        missing+=("isage-anns>=0.2.0")
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        echo "[runtime] Missing knowledge deps: ${missing[*]}" >&2
        echo "[runtime] Auto-installing: ${missing[*]}" >&2
        "$py" -m pip install --quiet "${missing[@]}"
        echo "[runtime] Knowledge deps installed." >&2
    fi
}
if [[ "${DIGITAL_TWIN_KNOWLEDGE_BACKEND:-neuromem}" == "sagevdb" ]]; then
    _ensure_knowledge_deps "$python_exec"
fi

# --- Start server ---
cd "$repo_root"
exec "$python_exec" -m uvicorn sage_faculty_twin.api:app \
    --host 127.0.0.1 --port "$app_port"
