#!/usr/bin/env bash

# Shared deployment helpers for shell entrypoints.
# Keep this file side-effect light: functions only, no command execution on source.

set -euo pipefail

deploy_log() {
    if declare -F log >/dev/null 2>&1; then
        log "$@"
    else
        printf '[deploy] %s\n' "$*"
    fi
}

deploy_warn() {
    if declare -F warn >/dev/null 2>&1; then
        warn "$@"
    else
        printf '[deploy] %s\n' "$*" >&2
    fi
}

deploy_fail() {
    if declare -F fail >/dev/null 2>&1; then
        fail "$@"
    else
        printf '[deploy] %s\n' "$*" >&2
        exit 1
    fi
}

python_meets_min_version() {
    local candidate="$1"
    local min_major="${2:-3}"
    local min_minor="${3:-11}"
    "$candidate" - "$min_major" "$min_minor" <<'PY'
import sys

major = int(sys.argv[1])
minor = int(sys.argv[2])
raise SystemExit(0 if sys.version_info >= (major, minor) else 1)
PY
}

resolve_uv_bin() {
    local uv_bin=""
    uv_bin=$(command -v uv 2>/dev/null || true)
    if [[ -z "$uv_bin" && -x "$HOME/.local/bin/uv" ]]; then
        uv_bin="$HOME/.local/bin/uv"
    fi
    printf '%s\n' "$uv_bin"
}

version_ge() {
    local actual="$1" required="$2"
    if command -v dpkg >/dev/null 2>&1; then
        dpkg --compare-versions "$actual" ge "$required"
    else
        [[ "$(printf '%s\n%s\n' "$required" "$actual" | sort -V | head -n1)" == "$required" ]]
    fi
}

load_dotenv_file() {
    local env_file="$1"
    [[ -f "$env_file" ]] || return 0
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        [[ "$line" == *"="* ]] || continue
        local key="${line%%=*}"
        key="${key// /}"
        [[ -z "$key" || -n "${!key:-}" ]] && continue
        export "$line"
    done < "$env_file"
}

nvidia_driver_version() {
    nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null \
        | head -n1 \
        | tr -d '[:space:]' \
        || true
}

check_nvidia_driver_for_vllm_hust() {
    local min_driver="${VLLM_NVIDIA_MIN_DRIVER_VERSION:-575.51.03}"
    local torch_backend="${VLLM_NVIDIA_TORCH_BACKEND:-cu129}"
    local driver_version=""
    driver_version=$(nvidia_driver_version)
    [[ -n "$driver_version" ]] || deploy_fail "could not detect NVIDIA driver version with nvidia-smi"

    deploy_log "  NVIDIA driver: $driver_version (minimum for vllm-hust $torch_backend: $min_driver)"
    if ! version_ge "$driver_version" "$min_driver"; then
        cat >&2 <<EOF
[deploy] NVIDIA driver $driver_version is too old for pinned vllm-hust $torch_backend wheels.
[deploy] Upgrade the driver first, then reboot and rerun quickstart:
[deploy]   tools/upgrade_nvidia_driver_for_vllm.sh --yes
[deploy]   sudo reboot
[deploy] After reboot, verify:
[deploy]   nvidia-smi
EOF
        exit 1
    fi
}

assert_nvidia_vllm_host() {
    if ! command -v nvidia-smi >/dev/null 2>&1; then
        deploy_fail "nvidia-smi not found; NVIDIA vLLM engine requires a CUDA GPU host."
    fi
    if command -v npu-smi >/dev/null 2>&1 && npu-smi info >/dev/null 2>&1; then
        deploy_fail "npu-smi is present; refusing to use the NVIDIA launcher on a mixed/Ascend host without explicit isolation."
    fi
}

assert_pinned_vllm_hust_checkout() {
    local vllm_hust_root="$1"
    if [[ ! -f "$vllm_hust_root/pyproject.toml" || ! -d "$vllm_hust_root/vllm" ]]; then
        deploy_fail "pinned vllm-hust checkout not found at $vllm_hust_root. Run: git submodule update --init --recursive deps/vllm-hust"
    fi
}

assert_python_imports_pinned_vllm_hust() {
    local python_bin="$1"
    local vllm_hust_root="$2"
    if ! "$python_bin" - "$vllm_hust_root" <<'PY' >/dev/null 2>&1
import importlib.util
import pathlib
import sys

expected = pathlib.Path(sys.argv[1]).resolve()
spec = importlib.util.find_spec("vllm")
if spec is None or spec.origin is None:
    raise SystemExit(1)
origin = pathlib.Path(spec.origin).resolve()
raise SystemExit(0 if expected in origin.parents else 1)
PY
    then
        deploy_fail "Python cannot import pinned vllm-hust from $vllm_hust_root. Run: ./quickstart.sh --target hosted-web --with-nvidia-vllm-engine --with-vllm-proxy"
    fi
}
