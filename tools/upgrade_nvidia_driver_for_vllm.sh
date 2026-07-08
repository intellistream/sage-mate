#!/usr/bin/env bash
# Upgrade NVIDIA driver to the minimum supported line for vllm-hust CUDA wheels.

set -euo pipefail

driver_package="${VLLM_NVIDIA_DRIVER_PACKAGE:-nvidia-driver-575}"
min_driver="${VLLM_NVIDIA_MIN_DRIVER_VERSION:-575.51.03}"
busy_threshold_mib="${VLLM_NVIDIA_REFUSE_IF_USED_MIB:-1024}"
assume_yes=false
dry_run=false

usage() {
    cat <<'EOF'
Usage: tools/upgrade_nvidia_driver_for_vllm.sh [--yes] [--dry-run]

Installs the NVIDIA driver package needed by pinned vllm-hust CUDA wheels.
Defaults:
  VLLM_NVIDIA_DRIVER_PACKAGE=nvidia-driver-575
  VLLM_NVIDIA_MIN_DRIVER_VERSION=575.51.03
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --yes|-y) assume_yes=true; shift ;;
        --dry-run) dry_run=true; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown argument: $1" >&2; exit 2 ;;
    esac
done

version_ge() {
    local actual="$1" required="$2"
    if command -v dpkg >/dev/null 2>&1; then
        dpkg --compare-versions "$actual" ge "$required"
    else
        [[ "$(printf '%s\n%s\n' "$required" "$actual" | sort -V | head -n1)" == "$required" ]]
    fi
}

run_root() {
    if [[ "$(id -u)" -eq 0 ]]; then
        "$@"
    else
        sudo "$@"
    fi
}

if ! command -v apt-get >/dev/null 2>&1; then
    echo "ERROR: apt-get not found; this helper supports Ubuntu/Debian hosts." >&2
    exit 1
fi
if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "ERROR: nvidia-smi not found; install a baseline NVIDIA driver first." >&2
    exit 1
fi

current_driver=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null | head -n1 | tr -d '[:space:]' || true)
gpu_used_mib=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | awk '{ total += $1 } END { print total+0 }')
echo "[driver-upgrade] current NVIDIA driver: ${current_driver:-unknown}"
echo "[driver-upgrade] required minimum driver: $min_driver"
echo "[driver-upgrade] requested package: $driver_package"
echo "[driver-upgrade] current GPU memory use: ${gpu_used_mib} MiB"

if [[ -n "$current_driver" ]] && version_ge "$current_driver" "$min_driver"; then
    echo "[driver-upgrade] driver already satisfies the minimum; no upgrade needed."
    exit 0
fi
if [[ "$busy_threshold_mib" =~ ^[0-9]+$ ]] && (( gpu_used_mib > busy_threshold_mib )); then
    echo "ERROR: GPU memory is already in use (${gpu_used_mib} MiB > ${busy_threshold_mib} MiB); refusing to upgrade while workloads may be running." >&2
    exit 1
fi

echo "[driver-upgrade] apt simulation:"
apt-get -s install "$driver_package" | sed -n '1,180p'
if $dry_run; then
    echo "[driver-upgrade] dry run complete."
    exit 0
fi

if ! $assume_yes; then
    read -r -p "Install $driver_package now? This requires sudo and a reboot. [y/N] " answer
    [[ "$answer" =~ ^[Yy]$ ]] || exit 1
fi

run_root apt-get update
run_root env DEBIAN_FRONTEND=noninteractive apt-get install -y "$driver_package"

echo "[driver-upgrade] install complete. Reboot is required before nvidia-smi reports the new driver:"
echo "[driver-upgrade]   sudo reboot"
