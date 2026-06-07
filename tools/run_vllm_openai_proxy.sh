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

proxy_host="${VLLM_PROXY_HOST:-127.0.0.1}"
proxy_port="${VLLM_PROXY_PORT:-18001}"

if ! "$python_bin" - "$proxy_host" "$proxy_port" <<'PY' >/dev/null 2>&1
import socket
import sys

host = sys.argv[1]
port = int(sys.argv[2])
family = socket.AF_INET6 if ":" in host and host != "0.0.0.0" else socket.AF_INET
sock = socket.socket(family, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    sock.bind((host, port))
except OSError:
    raise SystemExit(1)
else:
    sock.close()
    raise SystemExit(0)
PY
then
    echo "VLLM proxy listen address ${proxy_host}:${proxy_port} is already in use. Stop the conflicting process or choose a different VLLM_PROXY_PORT before enabling sage-faculty-twin-vllm-openai-proxy.service." >&2
    exit 1
fi

if "$python_bin" - <<'PY' >/dev/null 2>&1
import importlib.util
raise SystemExit(0 if importlib.util.find_spec("uvicorn") else 1)
PY
then
    exec "$python_bin" -m uvicorn sage_faculty_twin.vllm_openai_proxy:app --host "$proxy_host" --port "$proxy_port"
fi

exec "$python_bin" "$repo_root/tools/openai_key_proxy.py"
