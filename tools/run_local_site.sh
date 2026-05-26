#!/usr/bin/env bash

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
runtime_dir="$repo_root/.runtime"
nginx_prefix="$runtime_dir/nginx"
nginx_template="$repo_root/tools/nginx-local.conf"
nginx_conf="$nginx_prefix/nginx.conf"
default_app_port=55601
default_site_port=8088
app_port="${APP_PORT:-$default_app_port}"
site_port="${SITE_PORT:-$default_site_port}"
homepage_upstream_host="${HOMEPAGE_UPSTREAM_HOST:-example.invalid}"
homepage_upstream_scheme="${HOMEPAGE_UPSTREAM_SCHEME:-https}"
pythonpath_entries=("$repo_root/src")
for candidate in "$repo_root/../SAGE/src" "$repo_root/../sageVDB" "$repo_root/../neuromem"; do
    if [[ -e "$candidate" ]]; then
        pythonpath_entries+=("$candidate")
    fi
done
pythonpath_default=$(IFS=:; printf '%s' "${pythonpath_entries[*]}")
export PYTHONPATH="${PYTHONPATH:-$pythonpath_default}"

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

find_available_port() {
    local preferred_port="$1"
    local bind_host="$2"
    "$python_bin" - "$preferred_port" "$bind_host" <<'PY'
import socket
import sys

start = int(sys.argv[1])
host = sys.argv[2]

for port in range(start, start + 100):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            continue
    print(port)
    break
else:
    raise SystemExit(f"No free port available starting from {start}")
PY
}

port_is_available() {
    local port="$1"
    local bind_host="$2"
    "$python_bin" - "$port" "$bind_host" <<'PY'
import socket
import sys

port = int(sys.argv[1])
host = sys.argv[2]

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((host, port))
    except OSError:
        raise SystemExit(1)
PY
}

mkdir -p "$runtime_dir" "$nginx_prefix/logs" "$nginx_prefix/client_body_temp" "$nginx_prefix/proxy_temp"

if curl -fsS "http://127.0.0.1:${app_port}/" >/dev/null 2>&1; then
    app_ready=1
else
    app_ready=0
    if [[ -z "${APP_PORT:-}" ]]; then
        resolved_app_port=$(find_available_port "$app_port" "127.0.0.1")
        if [[ "$resolved_app_port" != "$app_port" ]]; then
            echo "APP_PORT ${app_port} is busy; using ${resolved_app_port} instead"
            app_port="$resolved_app_port"
        fi
    elif ! port_is_available "$app_port" "127.0.0.1"; then
        echo "APP_PORT ${app_port} is already in use and is not serving this app." >&2
        exit 1
    fi
fi

if [[ -z "${SITE_PORT:-}" ]]; then
    resolved_site_port=$(find_available_port "$site_port" "0.0.0.0")
    if [[ "$resolved_site_port" != "$site_port" ]]; then
        echo "SITE_PORT ${site_port} is busy; using ${resolved_site_port} instead"
        site_port="$resolved_site_port"
    fi
elif ! port_is_available "$site_port" "0.0.0.0"; then
    echo "SITE_PORT ${site_port} is already in use." >&2
    exit 1
fi

sed \
    -e "s|__SITE_PORT__|$site_port|g" \
    -e "s|__APP_PORT__|$app_port|g" \
    -e "s|__HOMEPAGE_UPSTREAM_HOST__|$homepage_upstream_host|g" \
    -e "s|__HOMEPAGE_UPSTREAM_SCHEME__|$homepage_upstream_scheme|g" \
    "$nginx_template" >"$nginx_conf"

if [[ "$app_ready" -eq 0 ]]; then
    echo "Starting app on 127.0.0.1:${app_port}"
    nohup env PYTHONPATH="$PYTHONPATH" \
        "$python_bin" -m uvicorn sage_faculty_twin.api:app --host 127.0.0.1 --port "$app_port" \
        >"$runtime_dir/app.log" 2>&1 &
    echo $! >"$runtime_dir/app.pid"
fi

cat <<EOF
Local site runtime
- app:  http://127.0.0.1:${app_port}
- site: http://127.0.0.1:${site_port}
- logs: $nginx_prefix/logs/error.log
EOF

exec nginx \
    -p "$nginx_prefix" \
    -c "$nginx_conf" \
    -g "error_log logs/error.log notice; daemon off;"