#!/usr/bin/env bash

# Shared runtime helpers for sage-faculty-twin scripts.
# Goal: keep interpreter/PYTHONPATH selection deterministic across entrypoints.

set -euo pipefail

resolve_repo_python() {
    local repo_root="$1"

    if [[ -n "${PYTHON_BIN:-}" && -x "${PYTHON_BIN}" ]]; then
        printf '%s\n' "${PYTHON_BIN}"
        return 0
    fi

    local conda_env_name="${CONDA_ENV_NAME:-vllm-hust-dev}"
    local conda_root=""
    if [[ -n "${CONDA_EXE:-}" ]]; then
        conda_root=$(cd "$(dirname "${CONDA_EXE}")/.." && pwd)
    fi

    local candidate=""
    for candidate in \
        "$conda_root/envs/$conda_env_name/bin/python" \
        "$conda_root/envs/$conda_env_name/bin/python3" \
        "$HOME/miniconda3/envs/$conda_env_name/bin/python" \
        "$HOME/miniconda3/envs/$conda_env_name/bin/python3" \
        "$HOME/anaconda3/envs/$conda_env_name/bin/python" \
        "$HOME/anaconda3/envs/$conda_env_name/bin/python3"; do
        if [[ -n "$candidate" && -x "$candidate" ]]; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done

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

build_repo_pythonpath() {
    local repo_root="$1"
    local entries=(
        "$repo_root/src"
        "$repo_root/../SAGE/src"
        "$repo_root/../sageVDB"
        "$repo_root/../neuromem"
    )

    local resolved=""
    local entry=""
    for entry in "${entries[@]}"; do
        if [[ -d "$entry" ]]; then
            if [[ -n "$resolved" ]]; then
                resolved+=":"
            fi
            resolved+="$entry"
        fi
    done

    printf '%s\n' "$resolved"
}

export_repo_runtime_env() {
    local repo_root="$1"
    local resolved_python=""
    resolved_python=$(resolve_repo_python "$repo_root") || {
        echo "Unable to locate a usable Python interpreter. Set PYTHON_BIN explicitly." >&2
        return 1
    }

    export PYTHON_BIN="$resolved_python"

    local base_pythonpath=""
    base_pythonpath=$(build_repo_pythonpath "$repo_root")
    if [[ -n "$base_pythonpath" ]]; then
        if [[ "${ALLOW_EXTERNAL_PYTHONPATH:-0}" == "1" && -n "${PYTHONPATH:-}" ]]; then
            export PYTHONPATH="$base_pythonpath:$PYTHONPATH"
        else
            export PYTHONPATH="$base_pythonpath"
        fi
    fi

    # Prevent torch auto-loading optional device backends (e.g. torch_npu) unless explicitly enabled.
    export TORCH_DEVICE_BACKEND_AUTOLOAD="${TORCH_DEVICE_BACKEND_AUTOLOAD:-0}"
    export DIGITAL_TWIN_RUNTIME_DIR="${DIGITAL_TWIN_RUNTIME_DIR:-$repo_root/../sage-faculty-twin-runtime-private}"
}

print_repo_runtime_summary() {
    local repo_root="$1"
    echo "[runtime] repo_root=$repo_root"
    echo "[runtime] PYTHON_BIN=${PYTHON_BIN:-<unset>}"
    echo "[runtime] TORCH_DEVICE_BACKEND_AUTOLOAD=${TORCH_DEVICE_BACKEND_AUTOLOAD:-<unset>}"
    echo "[runtime] PYTHONPATH=${PYTHONPATH:-<unset>}"
}
