#!/usr/bin/env bash
# Run the local Apple Silicon vLLM Metal OpenAI-compatible engine.

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

load_home_model_download_env() {
    local env_file="$HOME/.env"
    [[ -f "$env_file" ]] || return 0
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# || "$line" != *"="* ]] && continue
        local key="${line%%=*}"
        key="${key// /}"
        case "$key" in
            HF_TOKEN|HUGGING_FACE_HUB_TOKEN|HF_ENDPOINT|HF_HOME|HF_HUB_CACHE|HF_HUB_ENABLE_HF_TRANSFER|HF_HUB_DISABLE_XET|TRANSFORMERS_CACHE) ;;
            *) continue ;;
        esac
        [[ -z "$key" || -n "${!key:-}" ]] && continue
        export "$line"
    done < "$env_file"
}

if [[ -f "$repo_root/tools/lib/runtime_env.sh" ]]; then
    # shellcheck source=/dev/null
    source "$repo_root/tools/lib/runtime_env.sh"
    export_repo_runtime_env "$repo_root" 2>/dev/null || true
fi
if [[ -f "$repo_root/tools/lib/deploy_common.sh" ]]; then
    # shellcheck source=/dev/null
    source "$repo_root/tools/lib/deploy_common.sh"
    load_dotenv_file "$repo_root/.env" 2>/dev/null || true
    load_home_model_download_env 2>/dev/null || true
elif [[ -f "$repo_root/.env" ]]; then
    load_dotenv_without_override() {
        local env_file="$1"
        [[ -f "$env_file" ]] || return 0
        while IFS= read -r line || [[ -n "$line" ]]; do
            [[ -z "$line" || "$line" =~ ^[[:space:]]*# || "$line" != *"="* ]] && continue
            local key="${line%%=*}"
            key="${key// /}"
            [[ -z "$key" || -n "${!key:-}" ]] && continue
            export "$line"
        done < "$env_file"
    }
    set -a
    # shellcheck disable=SC1090
    . "$repo_root/.env"
    set +a
    load_home_model_download_env 2>/dev/null || true
fi

install_root="${SAGE_MATE_VLLM_METAL_INSTALL_ROOT:-$HOME/Library/Application Support/Sage Mate/vllm-metal-hust}"
runtime_source="${SAGE_MATE_VLLM_METAL_RUNTIME_DIR:-$install_root/source}"
venv_python="${SAGE_MATE_VLLM_METAL_PYTHON:-$runtime_source/.venv-vllm-metal/bin/python}"

if [[ ! -x "$venv_python" ]]; then
    echo "vllm-metal runtime is not installed. Run: tools/install_vllm_metal_runtime.sh" >&2
    exit 1
fi

if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
    echo "vllm-metal requires macOS on Apple Silicon arm64." >&2
    exit 1
fi

host="${VLLM_METAL_HOST:-127.0.0.1}"
port="${VLLM_METAL_PORT:-8000}"
default_model="mlx-community/Qwen2.5-7B-Instruct-4bit"
model="${VLLM_METAL_MODEL:-${DIGITAL_TWIN_MODEL_NAME:-$default_model}}"
served_model_name="${VLLM_METAL_SERVED_MODEL_NAME:-${DIGITAL_TWIN_MODEL_NAME:-$model}}"
max_model_len="${VLLM_METAL_MAX_MODEL_LEN:-4096}"
max_num_seqs="${VLLM_METAL_MAX_NUM_SEQS:-4}"
gpu_memory_utilization="${VLLM_METAL_GPU_MEMORY_UTILIZATION:-0.80}"
download_dir="${VLLM_METAL_DOWNLOAD_DIR:-}"
chat_template="${VLLM_METAL_CHAT_TEMPLATE:-}"

export VLLM_USE_V1="${VLLM_USE_V1:-1}"
export VLLM_METAL_BUILD_FROM_SOURCE="${VLLM_METAL_BUILD_FROM_SOURCE:-1}"
if [[ -n "${HF_TOKEN:-}" && -z "${HUGGING_FACE_HUB_TOKEN:-}" ]]; then
    export HUGGING_FACE_HUB_TOKEN="$HF_TOKEN"
fi

args=(
    -m vllm.entrypoints.cli.main
    serve
    "$model"
    --host "$host"
    --port "$port"
    --served-model-name "$served_model_name"
    --max-model-len "$max_model_len"
    --max-num-seqs "$max_num_seqs"
    --gpu-memory-utilization "$gpu_memory_utilization"
)

if [[ -n "$download_dir" ]]; then
    mkdir -p "$download_dir"
    args+=(--download-dir "$download_dir")
fi
if [[ -n "$chat_template" ]]; then
    args+=(--chat-template "$chat_template")
fi

echo "[sage-mate] starting local vllm-metal-hust engine on ${host}:${port} model=${served_model_name}"
exec "$venv_python" "${args[@]}"
