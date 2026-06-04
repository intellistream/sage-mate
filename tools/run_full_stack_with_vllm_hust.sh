#!/usr/bin/env bash

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

# Defaults can be overridden via env vars.
VLLM_HOST="${VLLM_HOST:-127.0.0.1}"
VLLM_PORT="${VLLM_PORT:-18000}"
VLLM_MODEL="${VLLM_MODEL:-/data/shared-models/Qwen2.5-7B-Instruct}"
VLLM_SERVED_MODEL_NAME="${VLLM_SERVED_MODEL_NAME:-meta-llama/Llama-3.1-8B-Instruct}"
VLLM_LOG_PATH="${VLLM_LOG_PATH:-$HOME/logs/vllm-hust-twin.log}"
DIGITAL_TWIN_API_KEY="${DIGITAL_TWIN_API_KEY:-EMPTY}"
START_VLLM_IF_MISSING="${START_VLLM_IF_MISSING:-1}"
WAIT_SECONDS="${WAIT_SECONDS:-180}"

mkdir -p "$(dirname "$VLLM_LOG_PATH")"

require_cmd() {
    local cmd="$1"
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Missing required command: $cmd" >&2
        exit 1
    fi
}

wait_for_vllm() {
    local deadline=$((SECONDS + WAIT_SECONDS))
    while (( SECONDS < deadline )); do
        if curl -fsS "http://${VLLM_HOST}:${VLLM_PORT}/v1/models" >/dev/null 2>&1; then
            return 0
        fi
        sleep 2
    done
    return 1
}

update_env_file() {
    local env_file="$repo_root/.env"
    [[ -f "$env_file" ]] || cp "$repo_root/.env.example" "$env_file"

    python3 - "$env_file" <<'PY'
import sys
from pathlib import Path

p = Path(sys.argv[1])
text = p.read_text(encoding="utf-8").splitlines()
updates = {
    "DIGITAL_TWIN_LLM_BASE_URL": "__BASE_URL__",
    "DIGITAL_TWIN_API_KEY": "__API_KEY__",
    "DIGITAL_TWIN_MODEL_NAME": "__MODEL_NAME__",
    "DIGITAL_TWIN_STREAM_CHAT_ANSWER": "true",
}
out = []
seen = set()
for line in text:
    s = line.strip()
    if not s or s.startswith("#") or "=" not in line:
        out.append(line)
        continue
    key = line.split("=", 1)[0].strip()
    if key in updates:
        if key not in seen:
            out.append(f"{key}={updates[key]}")
            seen.add(key)
        continue
    out.append(line)
for key, value in updates.items():
    if key not in seen:
        out.append(f"{key}={value}")
p.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
PY

    python3 - "$env_file" "http://${VLLM_HOST}:${VLLM_PORT}/v1" "$DIGITAL_TWIN_API_KEY" "$VLLM_SERVED_MODEL_NAME" <<'PY'
import sys
from pathlib import Path

env_file = Path(sys.argv[1])
base_url = sys.argv[2]
api_key = sys.argv[3]
model_name = sys.argv[4]

text = env_file.read_text(encoding="utf-8")
text = text.replace("__BASE_URL__", base_url)
text = text.replace("__API_KEY__", api_key)
text = text.replace("__MODEL_NAME__", model_name)
env_file.write_text(text, encoding="utf-8")
PY
}

start_vllm_if_needed() {
    if curl -fsS "http://${VLLM_HOST}:${VLLM_PORT}/v1/models" >/dev/null 2>&1; then
        echo "vllm-hust already reachable at http://${VLLM_HOST}:${VLLM_PORT}"
        return 0
    fi

    if [[ "$START_VLLM_IF_MISSING" != "1" ]]; then
        echo "vllm-hust is not reachable and START_VLLM_IF_MISSING=0" >&2
        return 1
    fi

    require_cmd vllm-hust
    echo "Starting vllm-hust on ${VLLM_HOST}:${VLLM_PORT} ..."
    nohup vllm-hust serve "$VLLM_MODEL" \
        --served-model-name "$VLLM_SERVED_MODEL_NAME" \
        --host "$VLLM_HOST" \
        --port "$VLLM_PORT" \
        --tensor-parallel-size 1 \
        --max-model-len 8192 \
        --enforce-eager \
        >>"$VLLM_LOG_PATH" 2>&1 &

    if ! wait_for_vllm; then
        echo "vllm-hust failed to become ready in ${WAIT_SECONDS}s" >&2
        echo "Check log: $VLLM_LOG_PATH" >&2
        return 1
    fi
    echo "vllm-hust is ready"
}

main() {
    require_cmd curl
    require_cmd python3

    start_vllm_if_needed
    update_env_file

    export PYTHONPATH="$repo_root/src:$repo_root/../SAGE/src:$repo_root/../neuromem:$repo_root/../sageVDB:${PYTHONPATH:-}"

    echo "Launching my-twin with LLM base URL: http://${VLLM_HOST}:${VLLM_PORT}/v1"
    exec bash "$repo_root/tools/run_app_server.sh"
}

main "$@"
