#!/usr/bin/env bash

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
runtime_dir="$repo_root/.runtime"
app_port="${APP_PORT:-55601}"
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
for candidate in "$repo_root/../SAGE/src" "$repo_root/../sageVDB" "$repo_root/../neuromem"; do
	if [[ -e "$candidate" ]]; then
		pythonpath_entries+=("$candidate")
	fi
done
pythonpath_default=$(IFS=:; printf '%s' "${pythonpath_entries[*]}")
export PYTHONPATH="${PYTHONPATH:-$pythonpath_default}"

mkdir -p "$runtime_dir"
cd "$repo_root"

# Load .env so module-level os.environ.get(...) calls (e.g. DIGITAL_TWIN_STREAM_CHAT_ANSWER)
# see the same values pydantic-settings reads via env_file=".env". Existing process-env
# entries take precedence over .env file lines.
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

exec "$python_bin" -m uvicorn sage_faculty_twin.api:app --host 127.0.0.1 --port "$app_port"
