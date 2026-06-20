#!/usr/bin/env bash
# run_vllm_engine.sh — Launch the vLLM-HUST inference engine inside Docker.
#
# All tuneable knobs are read from the repo .env file (or the process
# environment).  Defaults are conservative for a 4× Ascend 910B3 TP=4
# deployment with graph mode enabled (no --enforce-eager).
#
# The engine always runs inside a Docker container that already has NPU
# devices, CANN toolkit, and vllm-hust installed.  Set VLLM_ENGINE_CONTAINER
# in .env to the container name/id.

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

# ── Load .env ────────────────────────────────────────────────────────────────
if [[ -f "$repo_root/.env" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        key="${line%%=*}"
        key="${key// /}"
        [[ -z "$key" || -n "${!key:-}" ]] && continue
        export "$line"
    done < "$repo_root/.env"
fi

# ── Configuration (all overridable via env / .env) ────────────────────────────
container="${VLLM_ENGINE_CONTAINER:-}"
if [[ -z "$container" ]]; then
    echo "ERROR: VLLM_ENGINE_CONTAINER is not set." >&2
    echo "  Set it in .env to the name of a running Docker container" >&2
    echo "  with vllm-hust and Ascend NPU support." >&2
    exit 1
fi

model_path="${VLLM_ENGINE_MODEL_PATH:-/data/shared-models/Qwen3-32B}"
served_model_name="${DIGITAL_TWIN_MODEL_NAME:-Qwen3-32B}"
host="${VLLM_ENGINE_HOST:-0.0.0.0}"
port="${VLLM_ENGINE_PORT:-8000}"
tp_size="${VLLM_ENGINE_TP_SIZE:-4}"
max_model_len="${VLLM_ENGINE_MAX_MODEL_LEN:-32768}"
gpu_mem_util="${VLLM_ENGINE_GPU_MEM_UTIL:-0.85}"
max_num_seqs="${VLLM_ENGINE_MAX_NUM_SEQS:-16}"
dtype="${VLLM_ENGINE_DTYPE:-bfloat16}"
api_key="${DIGITAL_TWIN_API_KEY:-EMPTY}"
vllm_bin="${VLLM_ENGINE_BIN:-vllm-hust}"

# NPU device selection (Ascend).  Leave empty to let the runtime pick.
npu_devices="${ASCEND_RT_VISIBLE_DEVICES:-}"

# vllm-hust needs VLLM_TARGET_DEVICE=npu to detect Ascend hardware.
export VLLM_TARGET_DEVICE="${VLLM_TARGET_DEVICE:-npu}"

# ── Resolve Docker CLI ───────────────────────────────────────────────────────
docker_cmd="docker"
if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: docker not found on PATH." >&2; exit 1
fi
# Auto-escalate to sudo if the user cannot access the Docker socket.
if ! docker info >/dev/null 2>&1; then
    if sudo -n docker info >/dev/null 2>&1; then
        docker_cmd="sudo docker"
    else
        echo "ERROR: cannot access Docker socket (try adding user to docker group)." >&2
        exit 1
    fi
fi

# ── Verify container is running ────────────────────────────────────────────────
if ! $docker_cmd inspect "$container" >/dev/null 2>&1; then
    echo "ERROR: Docker container '$container' not found." >&2
    echo "  Start the container first." >&2
    exit 1
fi

# ── Print config summary ─────────────────────────────────────────────────────
echo "[vllm-engine] container        = $container"
echo "[vllm-engine] model_path       = $model_path"
echo "[vllm-engine] served_model_name = $served_model_name"
echo "[vllm-engine] host:port         = $host:$port"
echo "[vllm-engine] tp_size           = $tp_size"
echo "[vllm-engine] max_model_len     = $max_model_len"
echo "[vllm-engine] gpu_mem_util      = $gpu_mem_util"
echo "[vllm-engine] max_num_seqs      = $max_num_seqs"
echo "[vllm-engine] dtype             = $dtype"
echo "[vllm-engine] graph_mode        = ON (no --enforce-eager)"

# ── Build argument list ──────────────────────────────────────────────────────
vllm_args=(
    "$vllm_bin" serve "$model_path"
    --served-model-name "$served_model_name"
    --host "$host"
    --port "$port"
    --tensor-parallel-size "$tp_size"
    --max-model-len "$max_model_len"
    --max-num-batched-tokens "$max_model_len"
    --gpu-memory-utilization "$gpu_mem_util"
    --dtype "$dtype"
    --load-format auto
    --trust-remote-code
    --max-num-seqs "$max_num_seqs"
    --enable-prefix-caching
    --enable-chunked-prefill
    --api-key "$api_key"
)

# ── Launch inside Docker container ───────────────────────────────────────────
# Use login shell so CANN/NPU environment is sourced.
# Pass critical env vars through docker exec --env.
docker_env_args=(
    --env "VLLM_TARGET_DEVICE=$VLLM_TARGET_DEVICE"
)
[[ -n "$npu_devices" ]] && docker_env_args+=(--env "ASCEND_RT_VISIBLE_DEVICES=$npu_devices")
cmd_str="${vllm_args[*]}"
exec $docker_cmd exec "${docker_env_args[@]}" "$container" bash -lc "$cmd_str"
