#!/usr/bin/env bash
# run_app_server.sh — Start the sage-faculty-twin uvicorn server.
# Requires .venv to be bootstrapped first (see tools/bootstrap_venv.sh).

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
venv_dir="$repo_root/.venv"
app_port="${APP_PORT:-55601}"

# --- Validate venv ---
if [[ ! -x "$venv_dir/bin/python" ]]; then
    echo "ERROR: Venv not found at $venv_dir" >&2
    echo "  Run:  bash tools/bootstrap_venv.sh" >&2
    exit 1
fi

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
exec "$venv_dir/bin/python" -m uvicorn sage_faculty_twin.api:app \
    --host 127.0.0.1 --port "$app_port"
