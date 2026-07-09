#!/usr/bin/env bash
# Start Sage Mate local services: optional local model engine plus the app server.

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
app_port="${APP_PORT:-55601}"
model_pid=""

load_env_if_unset() {
    local env_file="$repo_root/.env"
    [[ -f "$env_file" ]] || return 0
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# || "$line" != *=* ]] && continue
        key="${line%%=*}"
        key="${key// /}"
        [[ -z "$key" || -n "${!key:-}" ]] && continue
        export "$line"
    done < "$env_file"
}

cleanup() {
    if [[ -n "$model_pid" ]] && kill -0 "$model_pid" >/dev/null 2>&1; then
        echo "[local-services] stopping local model engine pid=$model_pid" >&2
        kill "$model_pid" >/dev/null 2>&1 || true
        wait "$model_pid" >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT INT TERM

load_env_if_unset

if [[ "${DIGITAL_TWIN_LOCAL_MODEL_BACKEND:-none}" == "vllm_metal" ]]; then
    log_dir="$repo_root/.runtime"
    mkdir -p "$log_dir"
    echo "[local-services] starting vllm-metal-hust model engine; log: $log_dir/vllm-metal.log" >&2
    "$repo_root/tools/run_vllm_metal_engine.sh" >"$log_dir/vllm-metal.log" 2>&1 &
    model_pid="$!"
fi

echo "[local-services] starting Sage Mate app on http://127.0.0.1:$app_port/" >&2
"$repo_root/tools/run_app_server.sh"
