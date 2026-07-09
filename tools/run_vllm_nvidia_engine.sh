#!/usr/bin/env bash
# run_vllm_nvidia_engine.sh - local OpenAI-compatible vLLM server for NVIDIA/CUDA hosts.

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source "$repo_root/tools/lib/runtime_env.sh"
source "$repo_root/tools/lib/deploy_common.sh"

export_repo_runtime_env "$repo_root"
python_bin="$PYTHON_BIN"
python_bin_dir=$(dirname "$python_bin")
export PATH="$python_bin_dir:$PATH"

load_dotenv_file "$repo_root/.env"
assert_nvidia_vllm_host
check_nvidia_driver_for_vllm_hust

vllm_hust_root="${VLLM_HUST_ROOT:-$repo_root/deps/vllm-hust}"
assert_pinned_vllm_hust_checkout "$vllm_hust_root"

export PYTHONPATH="$vllm_hust_root${PYTHONPATH:+:$PYTHONPATH}"
export VLLM_TARGET_DEVICE="${VLLM_TARGET_DEVICE:-cuda}"
export VLLM_USE_V1="${VLLM_USE_V1:-1}"
export VLLM_USE_FLASHINFER_SAMPLER="${VLLM_USE_FLASHINFER_SAMPLER:-0}"

gpu_busy_threshold_mib="${VLLM_NVIDIA_REFUSE_IF_USED_MIB:-1024}"
gpu_used_mib=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | awk '{ total += $1 } END { print total+0 }')
if [[ "$gpu_busy_threshold_mib" =~ ^[0-9]+$ ]] && (( gpu_used_mib > gpu_busy_threshold_mib )); then
    echo "ERROR: NVIDIA GPU memory already in use (${gpu_used_mib} MiB > ${gpu_busy_threshold_mib} MiB); refusing to start local vLLM." >&2
    exit 1
fi

assert_python_imports_pinned_vllm_hust "$python_bin" "$vllm_hust_root"

model="${VLLM_NVIDIA_MODEL:-${VLLM_NVIDIA_MODEL_PATH:-}}"
if [[ -z "$model" ]]; then
    model="${VLLM_ENGINE_MODEL_PATH:-Qwen/Qwen2.5-14B-Instruct-AWQ}"
fi

served_model_name="${VLLM_NVIDIA_SERVED_MODEL_NAME:-${DIGITAL_TWIN_MODEL_NAME:-faculty-twin-model}}"
if [[ "$served_model_name" == "\${DIGITAL_TWIN_MODEL_NAME}" ]]; then
    served_model_name="${DIGITAL_TWIN_MODEL_NAME:-faculty-twin-model}"
fi

host="${VLLM_NVIDIA_HOST:-127.0.0.1}"
port="${VLLM_NVIDIA_PORT:-8000}"
gpu_mem="${VLLM_NVIDIA_GPU_MEMORY_UTILIZATION:-0.88}"
max_model_len="${VLLM_NVIDIA_MAX_MODEL_LEN:-16384}"
max_num_seqs="${VLLM_NVIDIA_MAX_NUM_SEQS:-8}"
dtype="${VLLM_NVIDIA_DTYPE:-auto}"
quantization="${VLLM_NVIDIA_QUANTIZATION:-}"
tensor_parallel_size="${VLLM_NVIDIA_TENSOR_PARALLEL_SIZE:-1}"
download_dir="${VLLM_NVIDIA_DOWNLOAD_DIR:-}"
chat_template="${VLLM_NVIDIA_CHAT_TEMPLATE:-}"

args=(
    -m vllm.entrypoints.cli.main
    serve
    "$model"
    --host "$host"
    --port "$port"
    --served-model-name "$served_model_name"
    --tensor-parallel-size "$tensor_parallel_size"
    --gpu-memory-utilization "$gpu_mem"
    --max-model-len "$max_model_len"
    --max-num-seqs "$max_num_seqs"
    --dtype "$dtype"
)

if [[ -n "$quantization" ]]; then
    args+=(--quantization "$quantization")
fi
if [[ -n "$download_dir" ]]; then
    mkdir -p "$download_dir"
    args+=(--download-dir "$download_dir")
fi
if [[ -n "$chat_template" ]]; then
    args+=(--chat-template "$chat_template")
fi
if [[ -n "${HF_TOKEN:-}" && -z "${HUGGING_FACE_HUB_TOKEN:-}" ]]; then
    export HUGGING_FACE_HUB_TOKEN="$HF_TOKEN"
fi

echo "[faculty-twin] starting local NVIDIA vLLM engine on ${host}:${port} model=${served_model_name}"
exec "$python_bin" "${args[@]}"
