#!/usr/bin/env bash
# One-shot hosted/web installer for Faculty Twin.
#
# This file is intentionally standalone enough to publish as a GitHub Release
# asset. It clones/updates the repo, configures hosted/web safety defaults, then
# delegates installation and runtime management to quickstart.sh/manage.sh.

set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
repo_url="${FACULTY_TWIN_REPO_URL:-git@github.com:intellistream/sage-faculty-twin.git}"
https_repo_url="${FACULTY_TWIN_HTTPS_REPO_URL:-https://github.com/intellistream/sage-faculty-twin.git}"
branch="${FACULTY_TWIN_BRANCH:-main}"
parent_dir="${FACULTY_TWIN_PARENT_DIR:-$HOME}"
repo_dir="${FACULTY_TWIN_DIR:-$parent_dir/sage-faculty-twin}"
model_preset="${FACULTY_TWIN_MODEL_PRESET:-auto}"
model_override="${FACULTY_TWIN_MODEL:-}"
served_model_override="${FACULTY_TWIN_SERVED_MODEL_NAME:-}"
accelerator="${FACULTY_TWIN_ACCELERATOR:-auto}"
tp_override="${FACULTY_TWIN_TENSOR_PARALLEL_SIZE:-${VLLM_NVIDIA_TENSOR_PARALLEL_SIZE:-${VLLM_ENGINE_TP_SIZE:-}}}"
public_hostname="${FACULTY_TWIN_PUBLIC_HOSTNAME:-twin.sage.org.ai}"
tunnel_name="${FACULTY_TWIN_TUNNEL_NAME:-sage-faculty-twin-$(hostname -s)-hosted-web}"
encrypted_secrets_file="${FACULTY_TWIN_ENCRYPTED_SECRETS_FILE:-}"
secrets_key_file="${FACULTY_TWIN_SECRETS_KEY_FILE:-}"
use_encrypted_secrets=true
start_services=true
with_tunnel=true
yes=false
hf_endpoint_explicit=false

usage() {
    cat <<'EOF'
Usage: hosted-web.sh [options]

Options:
  --dir PATH                  Install/update repo at PATH.
  --repo-url URL              Primary git URL. Defaults to SSH intellistream repo.
  --branch NAME               Git branch/ref. Defaults to main.
  --accelerator KIND          auto|nvidia|ascend|none. Defaults to auto.
  --model-preset PRESET       auto|qwen3-32b-awq|qwen3-14b-awq|qwen3-32b|qwen3-next-80b-awq|qwen2.5-14b-awq.
  --model MODEL_OR_PATH       Explicit HF model id or local model path.
  --served-model-name NAME    Served OpenAI model name. Defaults to model value.
  --tensor-parallel-size N    Override tensor parallel size.
  --public-hostname HOSTNAME  Public Cloudflare hostname. Defaults to twin.sage.org.ai.
  --tunnel-name NAME          Cloudflare tunnel name to create/reuse.
  --encrypted-secrets PATH    OpenSSL-encrypted env bundle. Default: release/secrets.env.enc.
  --secrets-key-file PATH     File containing decrypt passphrase/key material.
  --no-secrets                Skip encrypted release secrets even if present.
  --with-tunnel               Install/start Cloudflare tunnel service. Default.
  --no-tunnel                 Do not configure/start Cloudflare tunnel.
  --no-start                  Install/configure only; do not start services.
  --yes                       Non-interactive mode.
  -h, --help                  Show this help.

Environment:
  FACULTY_TWIN_PARENT_DIR, FACULTY_TWIN_DIR, FACULTY_TWIN_ACCELERATOR,
  FACULTY_TWIN_MODEL_PRESET,
  FACULTY_TWIN_MODEL, FACULTY_TWIN_SERVED_MODEL_NAME,
  FACULTY_TWIN_PUBLIC_HOSTNAME, FACULTY_TWIN_TUNNEL_NAME, HF_ENDPOINT,
  FACULTY_TWIN_ENCRYPTED_SECRETS_FILE, FACULTY_TWIN_SECRETS_KEY_FILE,
  FACULTY_TWIN_SECRETS_PASSPHRASE, HF_TOKEN/HUGGING_FACE_HUB_TOKEN are honored when present.
EOF
}

log() { printf '[hosted-web] %s\n' "$*"; }
warn() { printf '[hosted-web] %s\n' "$*" >&2; }
fail() { printf '[hosted-web] ERROR: %s\n' "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dir)
            [[ $# -ge 2 ]] || fail "--dir requires a value"
            repo_dir="$2"
            shift 2
            ;;
        --repo-url)
            [[ $# -ge 2 ]] || fail "--repo-url requires a value"
            repo_url="$2"
            shift 2
            ;;
        --branch)
            [[ $# -ge 2 ]] || fail "--branch requires a value"
            branch="$2"
            shift 2
            ;;
        --accelerator)
            [[ $# -ge 2 ]] || fail "--accelerator requires a value"
            accelerator="$2"
            shift 2
            ;;
        --model-preset)
            [[ $# -ge 2 ]] || fail "--model-preset requires a value"
            model_preset="$2"
            shift 2
            ;;
        --model)
            [[ $# -ge 2 ]] || fail "--model requires a value"
            model_override="$2"
            shift 2
            ;;
        --served-model-name)
            [[ $# -ge 2 ]] || fail "--served-model-name requires a value"
            served_model_override="$2"
            shift 2
            ;;
        --tensor-parallel-size)
            [[ $# -ge 2 ]] || fail "--tensor-parallel-size requires a value"
            tp_override="$2"
            shift 2
            ;;
        --public-hostname)
            [[ $# -ge 2 ]] || fail "--public-hostname requires a value"
            public_hostname="$2"
            shift 2
            ;;
        --tunnel-name)
            [[ $# -ge 2 ]] || fail "--tunnel-name requires a value"
            tunnel_name="$2"
            shift 2
            ;;
        --encrypted-secrets)
            [[ $# -ge 2 ]] || fail "--encrypted-secrets requires a value"
            encrypted_secrets_file="$2"
            shift 2
            ;;
        --secrets-key-file)
            [[ $# -ge 2 ]] || fail "--secrets-key-file requires a value"
            secrets_key_file="$2"
            shift 2
            ;;
        --no-secrets)
            use_encrypted_secrets=false
            shift
            ;;
        --with-tunnel)
            with_tunnel=true
            shift
            ;;
        --no-tunnel)
            with_tunnel=false
            shift
            ;;
        --no-start)
            start_services=false
            shift
            ;;
        --yes|-y)
            yes=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            fail "unknown option: $1"
            ;;
    esac
done

python_bin="${PYTHON_BIN:-}"

detect_python() {
    if [[ -n "$python_bin" && -x "$python_bin" ]]; then
        printf '%s\n' "$python_bin"
        return 0
    fi
    local candidate
    for candidate in \
        "$HOME/miniforge3/envs/vllm-hust-dev/bin/python" \
        "$HOME/miniconda3/envs/vllm-hust-dev/bin/python" \
        "$HOME/anaconda3/envs/vllm-hust-dev/bin/python" \
        "$(command -v python3 2>/dev/null || true)" \
        "$(command -v python 2>/dev/null || true)"; do
        if [[ -n "$candidate" && -x "$candidate" ]]; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done
    return 1
}

gpu_count() {
    if command -v nvidia-smi >/dev/null 2>&1; then
        nvidia-smi -L 2>/dev/null | wc -l | awk '{print $1+0}'
    else
        echo 0
    fi
}

min_gpu_mem_mib() {
    if command -v nvidia-smi >/dev/null 2>&1; then
        nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | awk '
            NR == 1 { min = $1 }
            $1 < min { min = $1 }
            END { print min+0 }
        '
    else
        echo 0
    fi
}

npu_count() {
    if command -v npu-smi >/dev/null 2>&1 && npu-smi info >/dev/null 2>&1; then
        npu-smi info 2>/dev/null | awk '/^[[:space:]]*[0-9]+[[:space:]]+/ { count++ } END { print count+0 }'
    else
        echo 0
    fi
}

detect_accelerator() {
    case "$accelerator" in
        auto|nvidia|ascend|none) ;;
        *) fail "--accelerator must be one of: auto, nvidia, ascend, none" ;;
    esac
    if [[ "$accelerator" != "auto" ]]; then
        return 0
    fi
    if [[ "$(gpu_count)" -gt 0 ]]; then
        accelerator="nvidia"
    elif [[ "$(npu_count)" -gt 0 ]]; then
        accelerator="ascend"
    else
        accelerator="none"
    fi
}

set_env_kv() {
    local env_file="$1" key="$2" value="$3"
    "$python_bin" - "$env_file" "$key" "$value" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
key = sys.argv[2]
value = sys.argv[3]
prefix = f"{key}="
lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
out = []
updated = False
for line in lines:
    if line.strip().startswith(prefix):
        out.append(f"{key}={value}")
        updated = True
    else:
        out.append(line)
if not updated:
    out.append(f"{key}={value}")
path.write_text("\n".join(out) + "\n", encoding="utf-8")
PY
}

merge_env_file() {
    local source_env="$1" target_env="$2"
    local line key value
    [[ -f "$source_env" ]] || return 0
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        [[ "$line" == *"="* ]] || continue
        key="${line%%=*}"
        value="${line#*=}"
        key="${key// /}"
        [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
        set_env_kv "$target_env" "$key" "$value"
    done < "$source_env"
}

apply_encrypted_release_secrets() {
    local env_file="$1"
    local default_file="$repo_dir/release/secrets.env.enc"
    local enc_file="${encrypted_secrets_file:-$default_file}"
    local tmp_file pass_args=()

    $use_encrypted_secrets || return 0
    [[ -f "$enc_file" ]] || return 0

    command -v openssl >/dev/null 2>&1 || fail "openssl is required to decrypt $enc_file"
    if [[ -n "$secrets_key_file" ]]; then
        [[ -f "$secrets_key_file" ]] || fail "secrets key file not found: $secrets_key_file"
        pass_args=(-pass "file:$secrets_key_file")
    elif [[ -n "${FACULTY_TWIN_SECRETS_PASSPHRASE:-}" ]]; then
        pass_args=(-pass "env:FACULTY_TWIN_SECRETS_PASSPHRASE")
    else
        warn "encrypted secrets file exists but no key was provided; continuing without decrypting it"
        warn "  file: $enc_file"
        warn "  set FACULTY_TWIN_SECRETS_KEY_FILE or pass --secrets-key-file"
        return 0
    fi

    tmp_file=$(mktemp)
    chmod 0600 "$tmp_file"
    if ! openssl enc -d -aes-256-cbc -pbkdf2 -in "$enc_file" -out "$tmp_file" "${pass_args[@]}" 2>/tmp/faculty_twin_secrets_decrypt.err; then
        rm -f "$tmp_file"
        fail "could not decrypt encrypted release secrets"
    fi
    merge_env_file "$tmp_file" "$env_file"
    rm -f "$tmp_file"
    log "applied encrypted release secrets from $(basename "$enc_file")"
}

apply_initial_release_secrets() {
    local default_file="$script_dir/secrets.env.enc"
    local enc_file="${encrypted_secrets_file:-$default_file}"
    local tmp_file pass_args=()

    $use_encrypted_secrets || return 0
    [[ -f "$enc_file" ]] || return 0
    command -v openssl >/dev/null 2>&1 || return 0

    if [[ -n "$secrets_key_file" ]]; then
        [[ -f "$secrets_key_file" ]] || return 0
        pass_args=(-pass "file:$secrets_key_file")
    elif [[ -n "${FACULTY_TWIN_SECRETS_PASSPHRASE:-}" ]]; then
        pass_args=(-pass "env:FACULTY_TWIN_SECRETS_PASSPHRASE")
    else
        return 0
    fi

    tmp_file=$(mktemp)
    chmod 0600 "$tmp_file"
    if ! openssl enc -d -aes-256-cbc -pbkdf2 -in "$enc_file" -out "$tmp_file" "${pass_args[@]}" 2>/tmp/faculty_twin_initial_secrets_decrypt.err; then
        rm -f "$tmp_file"
        return 0
    fi
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        [[ "$line" == *"="* ]] || continue
        local key="${line%%=*}" value="${line#*=}"
        key="${key// /}"
        [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
        case "$key" in
            GITHUB_TOKEN|GH_TOKEN|HF_TOKEN|HUGGING_FACE_HUB_TOKEN|CLOUDFLARE_API_TOKEN|CLOUDFLARE_GLOBAL_API_KEY)
                if [[ -z "${!key:-}" ]]; then
                    export "$key=$value"
                fi
                ;;
        esac
    done < "$tmp_file"
    rm -f "$tmp_file"
    log "loaded encrypted release secrets needed before clone"
}

prepare_qwen3_next_template() {
    local runtime_dir="$1"
    local template_path="$runtime_dir/qwen3-next-chat-template.jinja"
    mkdir -p "$runtime_dir"
    if [[ -s "$template_path" ]]; then
        printf '%s\n' "$template_path"
        return 0
    fi
    "$python_bin" - "$template_path" <<'PY'
from pathlib import Path
from urllib.request import urlopen
import json
import os
import sys

target = Path(sys.argv[1])
endpoint = os.environ.get("HF_ENDPOINT", "https://hf-mirror.com").rstrip("/")
url = f"{endpoint}/Qwen/Qwen3-Next-80B-A3B-Instruct/resolve/main/tokenizer_config.json"
with urlopen(url, timeout=60) as response:
    payload = json.loads(response.read().decode("utf-8"))
template = payload.get("chat_template")
if not template:
    raise SystemExit("official Qwen3-Next chat_template missing")
target.write_text(template, encoding="utf-8")
PY
    chmod 0600 "$template_path"
    printf '%s\n' "$template_path"
}

cloudflared_bin() {
    local candidate
    for candidate in \
        "${CLOUDFLARED_BIN:-}" \
        "$HOME/.local/bin/cloudflared" \
        "/usr/local/bin/cloudflared" \
        "/usr/bin/cloudflared" \
        "$(command -v cloudflared 2>/dev/null || true)"; do
        if [[ -n "$candidate" && -x "$candidate" ]]; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done
    return 1
}

tunnel_id_for_name() {
    local cf_bin="$1" name="$2"
    "$cf_bin" tunnel list 2>/dev/null | awk -v name="$name" '$2 == name { print $1; exit }'
}

configure_cloudflare_tunnel() {
    local runtime_dir="$1"
    [[ -n "$public_hostname" ]] || fail "--with-tunnel requires --public-hostname or FACULTY_TWIN_PUBLIC_HOSTNAME"

    local cf_bin tunnel_id config_path credentials_path
    cf_bin=$(cloudflared_bin) || fail "cloudflared is required for --with-tunnel"
    [[ -f "${TUNNEL_ORIGIN_CERT:-$HOME/.cloudflared/cert.pem}" ]] || {
        fail "Cloudflare origin cert missing. Run cloudflared tunnel login, or use --no-tunnel."
    }

    tunnel_id=$(tunnel_id_for_name "$cf_bin" "$tunnel_name")
    if [[ -z "$tunnel_id" ]]; then
        log "creating Cloudflare tunnel: $tunnel_name"
        "$cf_bin" tunnel create "$tunnel_name" >/tmp/faculty_twin_tunnel_create.log
        tunnel_id=$(tunnel_id_for_name "$cf_bin" "$tunnel_name")
    else
        log "reusing Cloudflare tunnel: $tunnel_name"
    fi
    [[ -n "$tunnel_id" ]] || fail "could not resolve Cloudflare tunnel id for $tunnel_name"

    credentials_path="$HOME/.cloudflared/$tunnel_id.json"
    [[ -f "$credentials_path" ]] || fail "Cloudflare tunnel credentials file missing for $tunnel_name"

    mkdir -p "$runtime_dir/cloudflared"
    config_path="$runtime_dir/cloudflared/config.yml"
    umask 077
    cat >"$config_path" <<EOF
tunnel: $tunnel_id
credentials-file: $credentials_path

ingress:
  - hostname: $public_hostname
    service: http://127.0.0.1:55601
  - service: http_status:404
EOF

    "$cf_bin" tunnel route dns --overwrite-dns "$tunnel_id" "$public_hostname" >/tmp/faculty_twin_tunnel_route.log
    set_env_kv "$env_file" TUNNEL_CONFIG_PATH "$config_path"
    set_env_kv "$env_file" DIGITAL_TWIN_HOMEPAGE_PUBLIC_URL "https://$public_hostname/"
    log "Cloudflare tunnel ready for https://$public_hostname/"
}

predownload_model_if_needed() {
    [[ "$accelerator" == "nvidia" ]] || return 0
    case "$model_preset" in
        qwen3-next-80b-awq|qwen3-32b-awq|qwen3-14b-awq) ;;
        *) return 0 ;;
    esac
    [[ "${FACULTY_TWIN_PREDOWNLOAD_MODEL:-1}" != "0" ]] || return 0
    [[ "$model" != /* ]] || return 0

    log "pre-downloading model into Hugging Face cache: $model"
    local attempts="${FACULTY_TWIN_PREDOWNLOAD_ATTEMPTS:-}"
    if [[ -z "$attempts" ]]; then
        [[ "$model_preset" == "qwen3-next-80b-awq" ]] && attempts=1 || attempts=4
    fi
    local attempt
    for ((attempt = 1; attempt <= attempts; attempt++)); do
        if [[ "$attempts" -gt 1 ]]; then
            log "pre-download attempt ${attempt}/${attempts}: $model"
        fi
        if "$python_bin" - "$model" <<'PY'
import os
import sys
from huggingface_hub import snapshot_download

model_id = sys.argv[1]
token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
path = snapshot_download(
    repo_id=model_id,
    token=token or None,
    resume_download=True,
    max_workers=1,
)
print(f"[hosted-web] model cache ready: {path}", flush=True)
PY
        then
            export HF_HUB_OFFLINE=1
            log "model cache ready; enabling HF_HUB_OFFLINE=1 for vLLM startup"
            return 0
        fi
        [[ "$attempt" -lt "$attempts" ]] || break
        warn "pre-download attempt ${attempt}/${attempts} failed for $model; retrying with resume"
        sleep "${FACULTY_TWIN_PREDOWNLOAD_RETRY_DELAY_SECONDS:-15}"
    done

    if [[ "$model_preset" == "qwen3-32b-awq" && "${FACULTY_TWIN_ALLOW_MODEL_FALLBACK:-1}" != "0" ]]; then
        warn "pre-download failed for $model; falling back to Qwen/Qwen3-14B-AWQ for a reliable first install"
        model_preset="qwen3-14b-awq"
        model="Qwen/Qwen3-14B-AWQ"
        served_model="${served_model_override:-$model}"
        tp="${tp_override:-1}"
        max_model_len="${VLLM_NVIDIA_MAX_MODEL_LEN:-32768}"
        max_num_seqs="${VLLM_NVIDIA_MAX_NUM_SEQS:-8}"
        set_env_kv "$env_file" DIGITAL_TWIN_MODEL_NAME "$served_model"
        set_env_kv "$env_file" VLLM_NVIDIA_MODEL "$model"
        set_env_kv "$env_file" VLLM_NVIDIA_SERVED_MODEL_NAME "$served_model"
        set_env_kv "$env_file" VLLM_NVIDIA_TENSOR_PARALLEL_SIZE "$tp"
        set_env_kv "$env_file" VLLM_NVIDIA_MAX_MODEL_LEN "$max_model_len"
        set_env_kv "$env_file" VLLM_NVIDIA_MAX_NUM_SEQS "$max_num_seqs"
        set_env_kv "$env_file" VLLM_NVIDIA_CHAT_TEMPLATE ""
        predownload_model_if_needed
        return 0
    fi

    if [[ "$model_preset" == "qwen3-32b-awq" || "$model_preset" == "qwen3-14b-awq" ]]; then
        fail "pre-download failed for $model; check network/Hugging Face access or choose --model-preset qwen2.5-14b-awq"
    fi

    if [[ "${FACULTY_TWIN_ALLOW_MODEL_FALLBACK:-1}" == "0" ]]; then
        fail "pre-download failed for $model; set FACULTY_TWIN_ALLOW_MODEL_FALLBACK=1 or choose a smaller preset"
    fi

    warn "pre-download failed for $model; falling back to Qwen/Qwen3-32B-AWQ for a reliable first install"
    model_preset="qwen3-32b-awq"
    model="Qwen/Qwen3-32B-AWQ"
    served_model="${served_model_override:-$model}"
    tp="${tp_override:-1}"
    max_model_len="${VLLM_NVIDIA_MAX_MODEL_LEN:-32768}"
    max_num_seqs="${VLLM_NVIDIA_MAX_NUM_SEQS:-8}"
    if ! $hf_endpoint_explicit; then
        export HF_ENDPOINT="${FACULTY_TWIN_FALLBACK_HF_ENDPOINT:-https://huggingface.co}"
        set_env_kv "$env_file" HF_ENDPOINT "$HF_ENDPOINT"
        log "using Hugging Face endpoint for fallback model: $HF_ENDPOINT"
    fi
    set_env_kv "$env_file" DIGITAL_TWIN_MODEL_NAME "$served_model"
    set_env_kv "$env_file" VLLM_NVIDIA_MODEL "$model"
    set_env_kv "$env_file" VLLM_NVIDIA_SERVED_MODEL_NAME "$served_model"
    set_env_kv "$env_file" VLLM_NVIDIA_TENSOR_PARALLEL_SIZE "$tp"
    set_env_kv "$env_file" VLLM_NVIDIA_MAX_MODEL_LEN "$max_model_len"
    set_env_kv "$env_file" VLLM_NVIDIA_MAX_NUM_SEQS "$max_num_seqs"
    set_env_kv "$env_file" VLLM_NVIDIA_CHAT_TEMPLATE ""
    predownload_model_if_needed
}

model_cache_path_hint() {
    local model_id="$1"
    [[ "$model_id" != /* ]] || return 1
    printf '%s/hub/models--%s\n' "${HF_HOME:-$HOME/.cache/huggingface}" "${model_id//\//--}"
}

progress_monitor() {
    local model_id="$1" engine_port="$2" interval="${FACULTY_TWIN_PROGRESS_INTERVAL_SECONDS:-60}"
    local cache_path=""
    cache_path=$(model_cache_path_hint "$model_id" 2>/dev/null || true)
    while true; do
        sleep "$interval" || true
        local listen_state="not-listening"
        if command -v ss >/dev/null 2>&1 && ss -lnt 2>/dev/null | awk '{print $4}' | grep -Eq "(^|:)${engine_port}$"; then
            listen_state="listening"
        fi
        local cache_size="n/a"
        if [[ -n "$cache_path" && -e "$cache_path" ]]; then
            cache_size=$(du -sh "$cache_path" 2>/dev/null | awk '{print $1}')
            [[ -n "$cache_size" ]] || cache_size="n/a"
        fi
        local gpu_summary="n/a"
        if command -v nvidia-smi >/dev/null 2>&1; then
            gpu_summary=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null \
                | awk -F, '{gsub(/ /,"",$1); gsub(/ /,"",$2); printf "%s%s/%sMiB", (NR == 1 ? "" : " "), $1, $2}' \
                | sed 's/[[:space:]]*$//')
            [[ -n "$gpu_summary" ]] || gpu_summary="n/a"
        fi
        log "progress: vLLM port ${engine_port}=${listen_state}; model cache=${cache_size}; gpu_mem=${gpu_summary}"
    done
}

select_model() {
    local gpus min_mem
    gpus=$(gpu_count)
    min_mem=$(min_gpu_mem_mib)

    if [[ -n "$model_override" ]]; then
        model="$model_override"
        served_model="${served_model_override:-$model_override}"
        if [[ "$accelerator" == "ascend" ]]; then
            tp="${tp_override:-4}"
            max_model_len="${VLLM_ENGINE_MAX_MODEL_LEN:-32768}"
            max_num_seqs="${VLLM_ENGINE_MAX_NUM_SEQS:-16}"
        else
            tp="${tp_override:-$([[ "$gpus" -ge 2 ]] && echo 2 || echo 1)}"
            max_model_len="${VLLM_NVIDIA_MAX_MODEL_LEN:-32768}"
            max_num_seqs="${VLLM_NVIDIA_MAX_NUM_SEQS:-8}"
        fi
        return 0
    fi

    if [[ "$model_preset" == "auto" ]]; then
        if [[ "$accelerator" == "ascend" ]]; then
            model_preset="qwen3-32b"
        elif [[ "$min_mem" -ge 70000 ]]; then
            model_preset="qwen3-32b-awq"
        else
            model_preset="qwen2.5-14b-awq"
        fi
    fi

    case "$model_preset" in
        qwen3-next-80b-awq)
            model="cyankiwi/Qwen3-Next-80B-A3B-Instruct-AWQ-4bit"
            served_model="${served_model_override:-$model}"
            tp="${tp_override:-$([[ "$accelerator" == "ascend" ]] && echo 4 || echo 2)}"
            if [[ "$accelerator" == "ascend" ]]; then
                max_model_len="${VLLM_ENGINE_MAX_MODEL_LEN:-32768}"
                max_num_seqs="${VLLM_ENGINE_MAX_NUM_SEQS:-16}"
            else
                max_model_len="${VLLM_NVIDIA_MAX_MODEL_LEN:-32768}"
                max_num_seqs="${VLLM_NVIDIA_MAX_NUM_SEQS:-8}"
            fi
            ;;
        qwen3-32b-awq)
            model="Qwen/Qwen3-32B-AWQ"
            served_model="${served_model_override:-$model}"
            tp="${tp_override:-1}"
            max_model_len="${VLLM_NVIDIA_MAX_MODEL_LEN:-32768}"
            max_num_seqs="${VLLM_NVIDIA_MAX_NUM_SEQS:-8}"
            ;;
        qwen3-14b-awq)
            model="Qwen/Qwen3-14B-AWQ"
            served_model="${served_model_override:-$model}"
            tp="${tp_override:-1}"
            max_model_len="${VLLM_NVIDIA_MAX_MODEL_LEN:-32768}"
            max_num_seqs="${VLLM_NVIDIA_MAX_NUM_SEQS:-8}"
            ;;
        qwen3-32b)
            if [[ "$accelerator" == "ascend" ]]; then
                model="${FACULTY_TWIN_MODEL:-/data/shared-models/Qwen3-32B}"
                served_model="${served_model_override:-Qwen3-32B}"
                tp="${tp_override:-4}"
                max_model_len="${VLLM_ENGINE_MAX_MODEL_LEN:-32768}"
                max_num_seqs="${VLLM_ENGINE_MAX_NUM_SEQS:-16}"
            else
                model="Qwen/Qwen3-32B"
                served_model="${served_model_override:-$model}"
                tp="${tp_override:-$([[ "$gpus" -ge 2 ]] && echo 2 || echo 1)}"
                max_model_len="${VLLM_NVIDIA_MAX_MODEL_LEN:-32768}"
                max_num_seqs="${VLLM_NVIDIA_MAX_NUM_SEQS:-8}"
            fi
            ;;
        qwen2.5-14b-awq)
            model="Qwen/Qwen2.5-14B-Instruct-AWQ"
            served_model="${served_model_override:-$model}"
            tp="${tp_override:-1}"
            max_model_len="${VLLM_NVIDIA_MAX_MODEL_LEN:-16384}"
            max_num_seqs="${VLLM_NVIDIA_MAX_NUM_SEQS:-8}"
            ;;
        *)
            fail "unknown --model-preset: $model_preset"
            ;;
    esac
}

clone_or_update_repo() {
    mkdir -p "$(dirname "$repo_dir")"
    local askpass=""
    git_auth() {
        if [[ -n "$askpass" ]]; then
            env GIT_ASKPASS="$askpass" GIT_TERMINAL_PROMPT=0 git "$@"
        else
            git "$@"
        fi
    }
    if [[ -n "${GITHUB_TOKEN:-${GH_TOKEN:-}}" ]]; then
        askpass=$(mktemp)
        chmod 0700 "$askpass"
        cat >"$askpass" <<'EOF'
#!/usr/bin/env bash
case "$1" in
    *Username*) printf '%s\n' "${GITHUB_USER:-x-access-token}" ;;
    *Password*) printf '%s\n' "${GITHUB_TOKEN:-${GH_TOKEN:-}}" ;;
    *) printf '\n' ;;
esac
EOF
    fi
    if [[ ! -d "$repo_dir/.git" ]]; then
        log "cloning $repo_url -> $repo_dir"
        git_auth clone "$repo_url" "$repo_dir" || git_auth clone "$https_repo_url" "$repo_dir"
    fi
    cd "$repo_dir"
    if [[ -n "$(git status --short)" ]]; then
        git stash push -u -m "pre-release-install-$(date +%Y%m%d-%H%M%S)"
    fi
    git checkout "$branch"
    git_auth fetch origin
    git_auth pull --ff-only origin "$branch"
    git submodule update --init --recursive
    [[ -z "$askpass" ]] || rm -f "$askpass"
}

main() {
    command -v git >/dev/null 2>&1 || fail "git is required"
    python_bin=$(detect_python) || fail "could not find Python; set PYTHON_BIN"
    export PYTHON_BIN="$python_bin"
    [[ -n "${HF_ENDPOINT:-}" ]] && hf_endpoint_explicit=true
    export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
    export HF_HUB_DISABLE_XET="${HF_HUB_DISABLE_XET:-1}"

    apply_initial_release_secrets
    detect_accelerator
    if [[ "$accelerator" == "nvidia" ]]; then
        command -v nvidia-smi >/dev/null 2>&1 || fail "nvidia-smi is required for --accelerator nvidia"
    elif [[ "$accelerator" == "ascend" ]]; then
        command -v npu-smi >/dev/null 2>&1 || fail "npu-smi is required for --accelerator ascend"
    fi
    select_model
    clone_or_update_repo

    local env_file="$repo_dir/.env"
    if [[ ! -f "$env_file" && -f "$repo_dir/.env.example" ]]; then
        cp "$repo_dir/.env.example" "$env_file"
    fi
    apply_encrypted_release_secrets "$env_file"

    if [[ "$accelerator" == "nvidia" && ( "$model_preset" == "qwen3-32b-awq" || "$model_preset" == "qwen3-14b-awq" ) ]] && ! $hf_endpoint_explicit; then
        export HF_ENDPOINT="${FACULTY_TWIN_FALLBACK_HF_ENDPOINT:-https://huggingface.co}"
        log "using Hugging Face endpoint for Qwen3 AWQ preset: $HF_ENDPOINT"
    fi

    local runtime_dir="${DIGITAL_TWIN_RUNTIME_DIR:-$repo_dir/../sage-faculty-twin-runtime-private}"
    set_env_kv "$env_file" DIGITAL_TWIN_DEPLOYMENT_MODE hosted
    set_env_kv "$env_file" DIGITAL_TWIN_APP_PROFILE faculty_twin
    set_env_kv "$env_file" DIGITAL_TWIN_CODE_WORKBENCH_ENABLED false
    set_env_kv "$env_file" DIGITAL_TWIN_CODE_WORKSPACE_ROOTS ""
    set_env_kv "$env_file" DIGITAL_TWIN_LLM_BASE_URL "http://127.0.0.1:18001/v1"
    set_env_kv "$env_file" DIGITAL_TWIN_MODEL_NAME "$served_model"
    if [[ "$accelerator" == "nvidia" ]]; then
        set_env_kv "$env_file" VLLM_PROXY_UPSTREAM_BASE_URL "http://127.0.0.1:18000/v1"
        set_env_kv "$env_file" VLLM_NVIDIA_MODEL "$model"
        set_env_kv "$env_file" VLLM_NVIDIA_SERVED_MODEL_NAME "$served_model"
        set_env_kv "$env_file" VLLM_NVIDIA_HOST "127.0.0.1"
        set_env_kv "$env_file" VLLM_NVIDIA_PORT "18000"
        set_env_kv "$env_file" VLLM_NVIDIA_TENSOR_PARALLEL_SIZE "$tp"
        set_env_kv "$env_file" VLLM_NVIDIA_GPU_MEMORY_UTILIZATION "${VLLM_NVIDIA_GPU_MEMORY_UTILIZATION:-0.88}"
        set_env_kv "$env_file" VLLM_NVIDIA_MAX_MODEL_LEN "$max_model_len"
        set_env_kv "$env_file" VLLM_NVIDIA_MAX_NUM_SEQS "$max_num_seqs"
    elif [[ "$accelerator" == "ascend" ]]; then
        set_env_kv "$env_file" VLLM_PROXY_UPSTREAM_BASE_URL "http://127.0.0.1:8000/v1"
        set_env_kv "$env_file" VLLM_ENGINE_MODEL_PATH "$model"
        set_env_kv "$env_file" VLLM_ENGINE_SERVED_MODEL_NAME "$served_model"
        set_env_kv "$env_file" VLLM_ENGINE_PORT "8000"
        set_env_kv "$env_file" VLLM_ENGINE_TP_SIZE "$tp"
        set_env_kv "$env_file" VLLM_ENGINE_MAX_MODEL_LEN "$max_model_len"
        set_env_kv "$env_file" VLLM_ENGINE_MAX_NUM_SEQS "$max_num_seqs"
        set_env_kv "$env_file" VLLM_ENGINE_GPU_MEM_UTIL "${VLLM_ENGINE_GPU_MEM_UTIL:-0.85}"
        set_env_kv "$env_file" VLLM_ENGINE_DTYPE "${VLLM_ENGINE_DTYPE:-bfloat16}"
    else
        set_env_kv "$env_file" VLLM_PROXY_UPSTREAM_BASE_URL "${VLLM_PROXY_UPSTREAM_BASE_URL:-http://127.0.0.1:8000/v1}"
    fi
    set_env_kv "$env_file" HF_ENDPOINT "$HF_ENDPOINT"
    set_env_kv "$env_file" HF_HUB_DISABLE_XET "$HF_HUB_DISABLE_XET"

    if [[ "$accelerator" == "nvidia" && "$model_preset" == "qwen3-next-80b-awq" ]]; then
        set_env_kv "$env_file" VLLM_NVIDIA_CHAT_TEMPLATE "$(prepare_qwen3_next_template "$runtime_dir")"
    fi
    if $with_tunnel; then
        configure_cloudflare_tunnel "$runtime_dir"
    fi
    predownload_model_if_needed
    if [[ "${HF_HUB_OFFLINE:-}" == "1" ]]; then
        set_env_kv "$env_file" HF_HUB_OFFLINE "1"
    fi

    local quickstart_args=(
        --target hosted-web
        --with-vllm-proxy
        --with-site-proxy
        --skip-vdb-extras
        --pip-timeout
        "${FACULTY_TWIN_PIP_TIMEOUT_SECONDS:-3600}"
    )
    if [[ "$accelerator" == "nvidia" ]]; then
        quickstart_args+=(--with-nvidia-vllm-engine)
    elif [[ "$accelerator" == "ascend" ]]; then
        quickstart_args+=(--with-vllm-engine)
    fi
    $with_tunnel && quickstart_args+=(--with-tunnel)
    $yes && quickstart_args+=(--yes)

    if [[ "$accelerator" == "nvidia" && -z "${VLLM_NVIDIA_INSTALLER:-}" ]]; then
        export VLLM_NVIDIA_INSTALLER=pip
    fi

    log "installing hosted/web $accelerator stack"
    if [[ "$model_preset" == "qwen3-next-80b-awq" ]]; then
        log "large model selected; first start may download model shards and can take 30-60 minutes on a fresh host"
    elif [[ "$model_preset" == "qwen3-32b" || "$model_preset" == "qwen3-32b-awq" || "$model_preset" == "qwen3-14b-awq" ]]; then
        log "Qwen3 model selected; first start may download model shards and can take several minutes on a fresh host"
    fi
    ./quickstart.sh "${quickstart_args[@]}"

    if $start_services; then
        local manage_services=(
            --with-app
            --with-vllm-proxy
            --with-site-proxy
        )
        if [[ "$accelerator" == "nvidia" ]]; then
            manage_services+=(--with-nvidia-vllm-engine)
        elif [[ "$accelerator" == "ascend" ]]; then
            manage_services+=(--with-vllm-engine)
        fi
        $with_tunnel && manage_services+=(--with-tunnel)
        ./manage.sh restart "${manage_services[@]}"
        local verify_timeout="${FACULTY_TWIN_VERIFY_TIMEOUT_SECONDS:-}"
        if [[ -z "$verify_timeout" ]]; then
            if [[ "$model_preset" == "qwen3-next-80b-awq" ]]; then
                verify_timeout=7200
            elif [[ "$model_preset" == "qwen3-32b" || "$model_preset" == "qwen3-32b-awq" || "$model_preset" == "qwen3-14b-awq" ]]; then
                verify_timeout=7200
            else
                verify_timeout=900
            fi
        fi
        log "waiting for hosted/web verification timeout=${verify_timeout}s"
        local verify_args=(--timeout "$verify_timeout")
        if $with_tunnel; then
            verify_args+=(--public-url "https://$public_hostname")
        fi
        local progress_pid=""
        if [[ "$accelerator" == "nvidia" || "$accelerator" == "ascend" ]]; then
            local engine_port="8000"
            [[ "$accelerator" == "nvidia" ]] && engine_port="18000"
            progress_monitor "$model" "$engine_port" &
            progress_pid="$!"
        fi
        cleanup_progress() {
            [[ -z "${progress_pid:-}" ]] || kill "$progress_pid" >/dev/null 2>&1 || true
        }
        trap cleanup_progress RETURN
        env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u http_proxy -u https_proxy -u all_proxy \
            NO_PROXY="127.0.0.1,localhost" \
            ./manage.sh verify-hosted-web "${verify_args[@]}"
        cleanup_progress
        trap - RETURN
        ./manage.sh status "${manage_services[@]}"
    fi

    log "done"
    if $with_tunnel; then
        log "web: https://$public_hostname/"
    else
        log "web: http://127.0.0.1:55601/ or http://$(hostname -I | awk '{print $1}'):8088/home/"
    fi
    log "accelerator: $accelerator"
    log "model: $served_model"
}

main "$@"
