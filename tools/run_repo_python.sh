#!/usr/bin/env bash

# Deterministic Python entrypoint for local dev/test/benchmark commands.
# Ensures one interpreter and one repo-owned PYTHONPATH layout.

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source "$repo_root/tools/lib/runtime_env.sh"

export_repo_runtime_env "$repo_root"

if [[ $# -eq 0 ]]; then
    echo "Usage: tools/run_repo_python.sh <python-args...>" >&2
    echo "Examples:" >&2
    echo "  tools/run_repo_python.sh -m pytest -q tests/test_llm_policy_integration.py" >&2
    echo "  tools/run_repo_python.sh -m sage_faculty_twin.benchmark_adapter --help" >&2
    exit 2
fi

exec "$PYTHON_BIN" "$@"
