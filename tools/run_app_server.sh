#!/usr/bin/env bash
# run_app_server.sh — Start the sage-faculty-twin uvicorn server.
# Prefers the repo-managed conda marker created by tools/bootstrap_conda_env.sh.

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source "$repo_root/tools/lib/runtime_env.sh"
app_port="${APP_PORT:-55601}"

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

# --- Load .env (existing env vars take precedence, but HF_HOME above wins) ---
if [[ -f "$repo_root/.env" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        key="${line%%=*}"
        key="${key// /}"
        [[ -z "$key" || -n "${!key:-}" ]] && continue
        export "$line"
    done < "$repo_root/.env"
fi

# --- Start server ---
cd "$repo_root"
exec "$python_exec" -m uvicorn sage_faculty_twin.api:app \
    --host 127.0.0.1 --port "$app_port"
