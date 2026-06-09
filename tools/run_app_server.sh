#!/usr/bin/env bash
# run_app_server.sh — Start the sage-faculty-twin uvicorn server.
# Requires .venv to be bootstrapped first (see tools/bootstrap_venv.sh).

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
venv_dir="$repo_root/.venv"
app_port="${APP_PORT:-55601}"
python_exec=""
source_mode="false"

# --- Resolve Python runtime ---
if [[ -x "$venv_dir/bin/python" ]]; then
    python_exec="$venv_dir/bin/python"
elif [[ -n "${PYTHON_BIN:-}" && -x "${PYTHON_BIN}" ]]; then
    python_exec="${PYTHON_BIN}"
    source_mode="true"
else
    echo "ERROR: No usable Python runtime found." >&2
    echo "  Broken or missing venv: $venv_dir/bin/python" >&2
    echo "  Either run: bash tools/bootstrap_venv.sh" >&2
    echo "  Or set:   PYTHON_BIN=/path/to/python3.11" >&2
    exit 1
fi

if [[ "$source_mode" == "true" ]]; then
    pythonpath_entries=(
        "$repo_root/src"
        "$repo_root/../SAGE/src"
        "$repo_root/../sageVDB"
        "$repo_root/../neuromem"
    )
    resolved_pythonpath=""
    for entry in "${pythonpath_entries[@]}"; do
        if [[ -d "$entry" ]]; then
            if [[ -n "$resolved_pythonpath" ]]; then
                resolved_pythonpath+=":"
            fi
            resolved_pythonpath+="$entry"
        fi
    done
    if [[ -n "$resolved_pythonpath" ]]; then
        export PYTHONPATH="$resolved_pythonpath${PYTHONPATH:+:$PYTHONPATH}"
    fi
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
exec "$python_exec" -m uvicorn sage_faculty_twin.api:app \
    --host 127.0.0.1 --port "$app_port"
