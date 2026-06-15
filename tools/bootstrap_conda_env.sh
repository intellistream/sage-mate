#!/usr/bin/env bash
# bootstrap_conda_env.sh — Create a dedicated conda env for sage-faculty-twin.
#
# Usage:
#   bash tools/bootstrap_conda_env.sh
#   CONDA_ENV_NAME=sage-faculty-twin bash tools/bootstrap_conda_env.sh
#   CONDA_ENV_NAME=sage-faculty-twin bash tools/bootstrap_conda_env.sh --recreate

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
parent_dir="${FACULTY_TWIN_PARENT_DIR:-$(dirname "$repo_root")}"
env_name="${CONDA_ENV_NAME:-sage-faculty-twin}"
python_version="${CONDA_PYTHON_VERSION:-3.11}"
marker_file="$repo_root/.python-bin"
recreate_env="false"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --recreate)
            recreate_env="true"
            ;;
        *)
            echo "Unsupported option: $1" >&2
            exit 1
            ;;
    esac
    shift
done

resolve_conda() {
    if [[ -n "${CONDA_EXE:-}" && -x "${CONDA_EXE}" ]]; then
        printf '%s\n' "$CONDA_EXE"
        return 0
    fi

    if command -v conda >/dev/null 2>&1; then
        command -v conda
        return 0
    fi

    for candidate in "$HOME/miniconda3/bin/conda" "$HOME/miniforge3/bin/conda"; do
        if [[ -x "$candidate" ]]; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done

    return 1
}

conda_bin=$(resolve_conda) || {
    echo "ERROR: Cannot find a usable conda executable." >&2
    echo "  Install Miniconda/Miniforge first, or set CONDA_EXE=/path/to/conda" >&2
    exit 1
}

require_repo() {
    local path="$1"
    local label="$2"
    if [[ ! -f "$path/pyproject.toml" ]]; then
        echo "ERROR: Missing $label repo at $path" >&2
        echo "  Set FACULTY_TWIN_PARENT_DIR to the directory that contains SAGE, neuromem, and sageVDB." >&2
        exit 1
    fi
}

require_repo "$parent_dir/SAGE" "SAGE"
require_repo "$parent_dir/neuromem" "neuromem"
require_repo "$parent_dir/sageVDB" "sageVDB"

env_prefix="$($conda_bin env list | awk -v name="$env_name" '$1 == name {print $NF; found=1} END {if (!found) exit 1}')" || env_prefix=""

if [[ "$recreate_env" == "true" && -n "$env_prefix" ]]; then
    echo "Removing existing conda env: $env_name"
    "$conda_bin" env remove -y -n "$env_name"
    env_prefix=""
fi

if [[ -z "$env_prefix" ]]; then
    echo "Creating conda env: $env_name (Python $python_version)"
    "$conda_bin" create -y -n "$env_name" "python=$python_version" pip setuptools wheel
    env_prefix="$($conda_bin env list | awk -v name="$env_name" '$1 == name {print $NF; found=1} END {if (!found) exit 1}')"
fi

python_bin="$env_prefix/bin/python"
if [[ ! -x "$python_bin" ]]; then
    echo "ERROR: Created env does not expose an executable python: $python_bin" >&2
    exit 1
fi

echo "Using conda env: $env_name"
echo "Python: $python_bin ($($python_bin --version 2>&1))"

"$conda_bin" run -n "$env_name" python -m pip install --upgrade pip setuptools wheel

echo "Installing runtime dependencies"
"$conda_bin" run -n "$env_name" python -m pip install \
    fastapi \
    httpx \
    pydantic \
    pydantic-settings \
    pypdf \
    uvicorn \
    cloudpickle \
    isage-anns>=0.1.3 \
    bm25s \
    sentence-transformers \
    faiss-cpu

echo "Installing editable package with vdb-anns extras: $repo_root"
"$conda_bin" run -n "$env_name" python -m pip install --no-deps -e "$repo_root[vdb-anns]"

# --- Link sageVDB compiled .so into source checkout ---------------------------
# The source sageVDB is on PYTHONPATH but does not ship compiled C extensions.
# Symlink the .so files from the PyPI install so the source checkout works.
if [[ -x "$parent_dir/sageVDB/scripts/link_shared_libs.sh" ]]; then
    echo "Linking sageVDB shared libraries into source checkout"
    PYTHON_BIN="$python_bin" bash "$parent_dir/sageVDB/scripts/link_shared_libs.sh"
else
    echo "WARNING: sageVDB link_shared_libs.sh not found — source checkout may fail at runtime."
    echo "  Expected: $parent_dir/sageVDB/scripts/link_shared_libs.sh"
fi

printf '%s\n' "$python_bin" > "$marker_file"

echo ""
echo "=== Conda bootstrap complete ==="
echo "Environment: $env_name"
echo "Marker:      $marker_file"
echo "Python:      $python_bin"
echo ""
echo "Start the app with: bash tools/run_app_server.sh"