#!/usr/bin/env bash
# run_vllm_engine.sh — Launch the vLLM-HUST inference engine for Qwen3-32B.
#
# All tuneable knobs are read from the repo .env file (or the process
# environment).  Defaults are conservative for a 4× Ascend 910B3 TP=4
# deployment with graph mode enabled (no --enforce-eager).

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

# ── Load .env (same pattern as run_vllm_openai_proxy.sh) ──────────────────────
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
model_path="${VLLM_ENGINE_MODEL_PATH:-/data/shared-models/Qwen3-32B}"
served_model_name="${DIGITAL_TWIN_MODEL_NAME:-Qwen3-32B}"
host="${VLLM_ENGINE_HOST:-0.0.0.0}"
port="${VLLM_ENGINE_PORT:-18000}"
tp_size="${VLLM_ENGINE_TP_SIZE:-4}"
max_model_len="${VLLM_ENGINE_MAX_MODEL_LEN:-32768}"
gpu_mem_util="${VLLM_ENGINE_GPU_MEM_UTIL:-0.85}"
api_key="${DIGITAL_TWIN_API_KEY:-EMPTY}"

# NPU device selection (Ascend).  Leave empty to let the runtime pick.
# Example: "4,5,6,7" for NPU 4-7.
npu_devices="${ASCEND_RT_VISIBLE_DEVICES:-}"

# ── Resolve vllm-hust binary ─────────────────────────────────────────────────
vllm_bin="${VLLM_ENGINE_BIN:-vllm-hust}"
if ! command -v "$vllm_bin" >/dev/null 2>&1; then
    echo "ERROR: '$vllm_bin' not found on PATH." >&2
    echo "  Install vllm-hust or set VLLM_ENGINE_BIN in .env." >&2
    exit 1
fi

# ── Set NPU visibility if specified ───────────────────────────────────────────
if [[ -n "$npu_devices" ]]; then
    export ASCEND_RT_VISIBLE_DEVICES="$npu_devices"
    echo "[vllm-engine] ASCEND_RT_VISIBLE_DEVICES=$npu_devices"
fi

# ── Print config summary ─────────────────────────────────────────────────────
echo "[vllm-engine] model_path       = $model_path"
echo "[vllm-engine] served_model_name = $served_model_name"
echo "[vllm-engine] host:port         = $host:$port"
echo "[vllm-engine] tp_size           = $tp_size"
echo "[vllm-engine] max_model_len     = $max_model_len"
echo "[vllm-engine] gpu_mem_util      = $gpu_mem_util"
echo "[vllm-engine] graph_mode        = ON (no --enforce-eager)"

# ── Launch ────────────────────────────────────────────────────────────────────
exec "$vllm_bin" serve "$model_path" \
    --served-model-name "$served_model_name" \
    --host "$host" \
    --port "$port" \
    --tensor-parallel-size "$tp_size" \
    --max-model-len "$max_model_len" \
    --gpu-memory-utilization "$gpu_mem_util" \
    --api-key "$api_key"
