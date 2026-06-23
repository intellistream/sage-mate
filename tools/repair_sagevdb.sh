#!/usr/bin/env bash
# One-command sageVDB repair for this repo.

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

pick_python() {
    if [[ -n "${SAGEVDB_REPAIR_PYTHON_BIN:-}" && -x "${SAGEVDB_REPAIR_PYTHON_BIN}" ]]; then
        printf '%s\n' "$SAGEVDB_REPAIR_PYTHON_BIN"
        return 0
    fi
    if [[ "${SAGEVDB_REPAIR_IGNORE_PYTHON_BIN:-0}" != "1" && -n "${PYTHON_BIN:-}" && -x "${PYTHON_BIN}" ]]; then
        printf '%s\n' "$PYTHON_BIN"
        return 0
    fi
    local conda_env_name="${CONDA_ENV_NAME:-vllm-hust-dev}"
    local conda_root="${CONDA_EXE:-}"
    if [[ -n "$conda_root" ]]; then
        conda_root=$(cd "$(dirname "$conda_root")/.." && pwd)
        if [[ -x "$conda_root/envs/$conda_env_name/bin/python3.12" ]]; then
            printf '%s\n' "$conda_root/envs/$conda_env_name/bin/python3.12"
            return 0
        fi
    fi
    if [[ -x "$HOME/miniconda3/envs/$conda_env_name/bin/python3.12" ]]; then
        printf '%s\n' "$HOME/miniconda3/envs/$conda_env_name/bin/python3.12"
        return 0
    fi
    if command -v python3 >/dev/null 2>&1; then
        command -v python3
        return 0
    fi
    if command -v python >/dev/null 2>&1; then
        command -v python
        return 0
    fi
    return 1
}

python_bin=$(pick_python) || {
    echo "Unable to locate Python. Set SAGEVDB_REPAIR_PYTHON_BIN=/path/to/python." >&2
    exit 1
}

exec "$python_bin" "$repo_root/tools/repair_sagevdb.py" --sagevdb-root "$repo_root/../sageVDB" "$@"
