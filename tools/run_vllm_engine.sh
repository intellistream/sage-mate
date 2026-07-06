#!/usr/bin/env bash
# run_vllm_engine.sh — Faculty Twin compatibility wrapper for vLLM-HUST.
#
# The real vLLM-HUST launch path lives in vllm-hust-dev-hub:
#   host -> docker exec -> conda activation -> Ascend/CANN env -> vLLM-HUST.
# Keep this file thin so the Faculty Twin systemd unit can stay stable without
# maintaining a second, drifting copy of the engine launcher.

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
default_dev_hub_root="$repo_root/deps/vllm-hust-dev-hub"
if [[ ! -x "$default_dev_hub_root/scripts/run_vllm_hust_engine.sh" ]]; then
    default_dev_hub_root="/home/shuhao/vllm-hust-dev-hub"
fi
dev_hub_root="${VLLM_HUST_DEV_HUB_ROOT:-$default_dev_hub_root}"
launcher="$dev_hub_root/scripts/run_vllm_hust_engine.sh"

if [[ ! -x "$launcher" ]]; then
    echo "ERROR: vLLM-HUST dev-hub launcher not found or not executable: $launcher" >&2
    exit 1
fi

load_dotenv() {
    local env_file="$1"
    [[ -f "$env_file" ]] || return 0
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        local key="${line%%=*}"
        key="${key// /}"
        [[ -z "$key" || -n "${!key:-}" ]] && continue
        export "$line"
    done < "$env_file"
}

load_dotenv "$repo_root/.env"

# Map Faculty Twin's historical engine variables onto dev-hub's canonical
# launcher variables. Existing env always wins so operators can override from
# systemd without editing this repo.
export VLLM_ENGINE_CONTAINER="${VLLM_ENGINE_CONTAINER:-vllm_hust_ws_21rc}"
export VLLM_ENGINE_MODEL_PATH="${VLLM_ENGINE_MODEL_PATH:-/data/shared_models/modelscope_cache/Qwen/Qwen3-32B}"
export VLLM_ENGINE_SERVED_MODEL_NAME="${VLLM_ENGINE_SERVED_MODEL_NAME:-${DIGITAL_TWIN_MODEL_NAME:-qwen3-32b}}"
export VLLM_ENGINE_HOST="${VLLM_ENGINE_HOST:-0.0.0.0}"
export VLLM_ENGINE_PORT="${VLLM_ENGINE_PORT:-8000}"
export VLLM_ENGINE_TP_SIZE="${VLLM_ENGINE_TP_SIZE:-4}"
export VLLM_ENGINE_MAX_MODEL_LEN="${VLLM_ENGINE_MAX_MODEL_LEN:-32768}"
export VLLM_ENGINE_MAX_NUM_BATCHED_TOKENS="${VLLM_ENGINE_MAX_NUM_BATCHED_TOKENS:-$VLLM_ENGINE_MAX_MODEL_LEN}"
export VLLM_ENGINE_GPU_MEM_UTIL="${VLLM_ENGINE_GPU_MEM_UTIL:-0.9}"
export VLLM_ENGINE_MAX_NUM_SEQS="${VLLM_ENGINE_MAX_NUM_SEQS:-16}"
export VLLM_ENGINE_DTYPE="${VLLM_ENGINE_DTYPE:-bfloat16}"
export VLLM_ENGINE_NPU_DEVICES="${VLLM_ENGINE_NPU_DEVICES:-${ASCEND_RT_VISIBLE_DEVICES:-0,1,2,3}}"
export ASCEND_RT_VISIBLE_DEVICES="${ASCEND_RT_VISIBLE_DEVICES:-$VLLM_ENGINE_NPU_DEVICES}"
export ASCEND_VISIBLE_DEVICES="${ASCEND_VISIBLE_DEVICES:-$VLLM_ENGINE_NPU_DEVICES}"
export VLLM_ENGINE_CONDA_ENV="${VLLM_ENGINE_CONDA_ENV:-vllm-hust-dev}"
export VLLM_ENGINE_BIN="${VLLM_ENGINE_BIN:-vllm-hust}"
export VLLM_ENGINE_BASE_PYTHONPATH="${VLLM_ENGINE_BASE_PYTHONPATH:-/workspace/vllm-hust:/workspace/vllm-ascend-hust}"
export VLLM_ENGINE_CONTAINER_LOG_FILE="${VLLM_ENGINE_CONTAINER_LOG_FILE:-/tmp/sage-faculty-twin-vllm-engine.redacted.log}"
export VLLM_ENGINE_AUTO_CREATE_CONTAINER="${VLLM_ENGINE_AUTO_CREATE_CONTAINER:-false}"
export VLLM_ENGINE_REPLACE_EXISTING="${VLLM_ENGINE_REPLACE_EXISTING:-true}"
export VLLM_ENGINE_AUTO_PREPARE_ENV="${VLLM_ENGINE_AUTO_PREPARE_ENV:-0}"
export VLLM_ENGINE_LOAD_REPO_ENV=false

if [[ -z "${VLLM_HUST_API_KEY:-}" && -n "${DIGITAL_TWIN_API_KEY:-}" ]]; then
    export VLLM_ENGINE_API_KEY="$DIGITAL_TWIN_API_KEY"
fi

echo "[faculty-twin] delegating vLLM-HUST launch to $launcher"
exec "$launcher"
