#!/usr/bin/env bash

# Shared runtime helpers for sage-faculty-twin scripts.
# Goal: keep interpreter/PYTHONPATH selection deterministic across entrypoints.

set -euo pipefail

resolve_repo_python() {
    local repo_root="$1"
    local marker_file="$repo_root/.python-bin"
    local candidate=""

    if [[ -n "${PYTHON_BIN:-}" && -x "${PYTHON_BIN}" ]]; then
        printf '%s\n' "${PYTHON_BIN}"
        return 0
    fi

    if [[ -f "$marker_file" ]]; then
        candidate=$(sed -n '1p' "$marker_file" | tr -d '\r')
        if [[ -x "$candidate" ]]; then
            printf '%s\n' "$candidate"
            return 0
        fi
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
}

print_repo_runtime_summary() {
    local repo_root="$1"
    echo "[runtime] repo_root=$repo_root"
    echo "[runtime] PYTHON_BIN=${PYTHON_BIN:-<unset>}"
    echo "[runtime] TORCH_DEVICE_BACKEND_AUTOLOAD=${TORCH_DEVICE_BACKEND_AUTOLOAD:-<unset>}"
    echo "[runtime] PYTHONPATH=${PYTHONPATH:-<unset>}"
}
