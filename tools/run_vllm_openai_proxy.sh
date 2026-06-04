#!/usr/bin/env bash

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
runtime_dir="$repo_root/.runtime"

if [[ -n "${PYTHON_BIN:-}" ]]; then
    python_bin="$PYTHON_BIN"
elif command -v python3 >/dev/null 2>&1; then
    python_bin=$(command -v python3)
elif command -v python >/dev/null 2>&1; then
    python_bin=$(command -v python)
else
    echo "Unable to locate a usable Python interpreter. Set PYTHON_BIN explicitly." >&2
    exit 1
fi

pythonpath_entries=("$repo_root/src")
pythonpath_default=$(IFS=:; printf '%s' "${pythonpath_entries[*]}")
export PYTHONPATH="${PYTHONPATH:-$pythonpath_default}"

mkdir -p "$runtime_dir"
cd "$repo_root"

if [[ -f "$repo_root/.env" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        key="${line%%=*}"
        key="${key// /}"
        [[ -z "$key" || -n "${!key:-}" ]] && continue
        export "$line"
    done < "$repo_root/.env"
fi

if [[ ! -x "$python_bin" ]]; then
    echo "Python interpreter not found or not executable: $python_bin" >&2
    exit 1
fi

if "$python_bin" - <<'PY' >/dev/null 2>&1
import importlib.util
raise SystemExit(0 if importlib.util.find_spec("uvicorn") else 1)
PY
then
    exec "$python_bin" -m uvicorn sage_faculty_twin.vllm_openai_proxy:app --host "${VLLM_PROXY_HOST:-127.0.0.1}" --port "${VLLM_PROXY_PORT:-18001}"
fi

exec "$python_bin" "$repo_root/tools/openai_key_proxy.py"
