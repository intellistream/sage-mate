#!/usr/bin/env bash
# bootstrap_venv.sh — Create a self-contained .venv for sage-faculty-twin
# with all SAGE ecosystem dependencies installed in editable mode.
#
# Usage:
#   bash tools/bootstrap_venv.sh
#   PYTHON_BASE=/path/to/python3.11 bash tools/bootstrap_venv.sh

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
venv_dir="$repo_root/.venv"

# --- Resolve a Python >=3.11 interpreter ---
resolve_python() {
    # Explicit override
    if [[ -n "${PYTHON_BASE:-}" ]] && command -v "$PYTHON_BASE" >/dev/null 2>&1; then
        printf '%s\n' "$PYTHON_BASE"
        return 0
    fi
    # Prefer python3.11 on PATH
    for candidate in python3.11 python3.12 python3; do
        if command -v "$candidate" >/dev/null 2>&1; then
            local ver
            ver=$("$candidate" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null) || continue
            local major minor
            major=${ver%%.*}
            minor=${ver#*.}
            if (( major == 3 && minor >= 11 )); then
                command -v "$candidate"
                return 0
            fi
        fi
    done
    # Search conda envs as last resort
    local found
    found=$(find "$HOME/miniconda3/envs" "$HOME/anaconda3/envs" /opt/conda/envs \
        -maxdepth 2 -name "python3.11" -o -name "python3.12" 2>/dev/null | head -1) || true
    if [[ -n "$found" && -x "$found" ]]; then
        printf '%s\n' "$found"
        return 0
    fi
    return 1
}

python_base=$(resolve_python) || {
    echo "ERROR: Cannot find Python >=3.11. Set PYTHON_BASE=/path/to/python3.11" >&2
    exit 1
}
echo "Using base interpreter: $python_base ($($python_base --version 2>&1))"

# --- Create venv ---
if [[ -d "$venv_dir" ]]; then
    echo "Removing existing venv at $venv_dir ..."
    rm -rf "$venv_dir"
fi

echo "Creating venv at $venv_dir ..."
"$python_base" -m venv "$venv_dir"
# shellcheck disable=SC1091
source "$venv_dir/bin/activate"

pip install --upgrade pip setuptools wheel 2>&1 | tail -3

# --- Locate SAGE monorepo (provides sage.edge, sage.foundation, sage.runtime) ---
sage_src=""
for candidate in \
    "$repo_root/../SAGE" \
    "/workspace/vamos/external/SAGE" \
    "$HOME/SAGE" \
    ; do
    if [[ -f "$candidate/pyproject.toml" ]]; then
        sage_src=$(cd "$candidate" && pwd)
        break
    fi
done

if [[ -z "$sage_src" ]]; then
    echo "WARNING: SAGE monorepo not found. sage.edge/foundation/runtime won't be available." >&2
    echo "  Set the path manually: pip install -e /path/to/SAGE" >&2
else
    echo "Installing SAGE (isage) from $sage_src ..."
    pip install -e "$sage_src" 2>&1 | tail -3
fi

# --- Locate neuromem repo (provides sage.neuromem) ---
neuromem_src=""
for candidate in \
    "$repo_root/../neuromem" \
    "$HOME/neuromem" \
    "/workspace/neuromem" \
    ; do
    if [[ -f "$candidate/pyproject.toml" ]]; then
        neuromem_src=$(cd "$candidate" && pwd)
        break
    fi
done

if [[ -z "$neuromem_src" ]]; then
    echo "WARNING: neuromem repo not found. sage.neuromem won't be available." >&2
    echo "  Set the path manually: pip install -e /path/to/neuromem" >&2
else
    echo "Installing neuromem (isage-neuromem) from $neuromem_src ..."
    pip install --no-deps -e "$neuromem_src" 2>&1 | tail -3
    # Install neuromem's own deps (skip isage-libs which may not exist for this Python)
    pip install bm25s sentence-transformers faiss-cpu 2>&1 | tail -3
fi

# --- Install sage-faculty-twin itself (editable) ---
echo "Installing sage-faculty-twin from $repo_root ..."
pip install --no-deps -e "$repo_root" 2>&1 | tail -3
# Install its deps (excluding isage/isage-neuromem which we already have)
pip install fastapi httpx pydantic pydantic-settings pypdf uvicorn cloudpickle 2>&1 | tail -3

echo ""
echo "=== Bootstrap complete ==="
echo "Venv:   $venv_dir"
echo "Python: $venv_dir/bin/python ($($venv_dir/bin/python --version 2>&1))"
echo ""
echo "Verify: $venv_dir/bin/python -c 'from sage_faculty_twin.api import app; print(\"OK\")'"
