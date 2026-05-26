#!/usr/bin/env bash

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
runtime_dir="$repo_root/.runtime"
config_path="${TUNNEL_CONFIG_PATH:-$repo_root/.runtime/cloudflared/config.yml}"
protocol="${TUNNEL_PROTOCOL:-http2}"
startup_timeout_seconds="${TUNNEL_SITE_TIMEOUT_SECONDS:-30}"

if [[ ! -f "$config_path" ]]; then
    echo "Missing tunnel config: $config_path" >&2
    echo "Copy tools/cloudflared-config.example.yml to $config_path and fill in the tunnel id first." >&2
    exit 1
fi

deadline=$((SECONDS + startup_timeout_seconds))
until curl -fsS http://127.0.0.1:8088/ >/dev/null 2>&1; do
    if (( SECONDS >= deadline )); then
        echo "Local proxy is not reachable on 127.0.0.1:8088 after ${startup_timeout_seconds}s." >&2
        exit 1
    fi
    sleep 1
done

mkdir -p "$runtime_dir/cloudflared"
exec cloudflared tunnel --protocol "$protocol" --config "$config_path" run
