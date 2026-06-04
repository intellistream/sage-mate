#!/usr/bin/env bash

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
runtime_dir="$repo_root/.runtime"
nginx_prefix="$runtime_dir/nginx"
nginx_template="$repo_root/tools/nginx-local.conf"
nginx_conf="$nginx_prefix/nginx.conf"
app_port="${APP_PORT:-55601}"
site_port="${SITE_PORT:-8088}"
startup_timeout_seconds="${APP_STARTUP_TIMEOUT_SECONDS:-30}"
fallback_proxy="$repo_root/tools/local_site_proxy.py"

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

mkdir -p "$runtime_dir" "$nginx_prefix/logs" "$nginx_prefix/client_body_temp" "$nginx_prefix/proxy_temp" "$nginx_prefix/cache/home_proxy"

deadline=$((SECONDS + startup_timeout_seconds))
until curl -fsS "http://127.0.0.1:${app_port}/" >/dev/null 2>&1; do
    if (( SECONDS >= deadline )); then
        echo "App is not reachable on 127.0.0.1:${app_port} after ${startup_timeout_seconds}s." >&2
        exit 1
    fi
    sleep 1
done

sed \
    -e "s|__SITE_PORT__|$site_port|g" \
    -e "s|__APP_PORT__|$app_port|g" \
    "$nginx_template" >"$nginx_conf"

if command -v nginx >/dev/null 2>&1; then
    exec nginx \
        -p "$nginx_prefix" \
        -c "$nginx_conf" \
        -g "error_log logs/error.log notice; daemon off;"
fi

exec "$python_bin" "$fallback_proxy"
