#!/usr/bin/env bash
# Install the Sage Mate Apple Silicon vLLM Metal runtime from vLLM-HUST/vllm-metal-hust.

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source_dir="${SAGE_MATE_VLLM_METAL_DIR:-$repo_root/deps/vllm-metal-hust}"
vllm_hust_dir="${VLLM_METAL_VLLM_SOURCE_DIR:-$repo_root/deps/vllm-hust}"
install_root="${SAGE_MATE_VLLM_METAL_INSTALL_ROOT:-$HOME/Library/Application Support/Sage Mate/vllm-metal-hust}"
source_target="$install_root/source"
fork_url="${SAGE_MATE_VLLM_METAL_REPO:-https://github.com/vLLM-HUST/vllm-metal-hust.git}"

log()  { printf '\033[1;36m[vllm-metal-install]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[vllm-metal-install]\033[0m %s\n' "$*" >&2; }
fail() { printf '\033[1;31m[vllm-metal-install]\033[0m %s\n' "$*" >&2; exit 1; }

usage() {
    cat <<'EOF'
Usage: tools/install_vllm_metal_runtime.sh [--source-dir PATH] [--vllm-hust-dir PATH] [--install-root PATH]

Installs vLLM Metal from the vLLM-HUST fork on top of the local vllm-hust core.
The runtime is installed under:
  ~/Library/Application Support/Sage Mate/vllm-metal-hust

Options:
  --source-dir PATH    Existing vllm-metal-hust source tree. Defaults to deps/vllm-metal-hust.
  --vllm-hust-dir PATH Existing vllm-hust source tree. Defaults to deps/vllm-hust.
  --install-root PATH  Runtime install root.
  -h, --help           Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --source-dir)
            [[ $# -ge 2 ]] || fail "--source-dir requires a path"
            source_dir="${2/#\~/$HOME}"
            shift 2
            ;;
        --vllm-hust-dir)
            [[ $# -ge 2 ]] || fail "--vllm-hust-dir requires a path"
            vllm_hust_dir="${2/#\~/$HOME}"
            shift 2
            ;;
        --install-root)
            [[ $# -ge 2 ]] || fail "--install-root requires a path"
            install_root="${2/#\~/$HOME}"
            source_target="$install_root/source"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            fail "Unknown argument: $1"
            ;;
    esac
done

[[ "$(uname -s)" == "Darwin" ]] || fail "vllm-metal-hust requires macOS."
[[ "$(uname -m)" == "arm64" ]] || fail "vllm-metal-hust requires Apple Silicon arm64."

if ! /usr/bin/xcode-select -p >/dev/null 2>&1; then
    fail "Xcode Command Line Tools are required. Run: xcode-select --install"
fi

mkdir -p "$install_root"

if [[ -f "$source_dir/install.sh" && -f "$source_dir/pyproject.toml" ]]; then
    log "Syncing bundled vllm-metal-hust source from: $source_dir"
    mkdir -p "$source_target"
    rsync -a \
        --delete \
        --exclude '.git' \
        --exclude '.venv-vllm-metal' \
        --exclude 'target' \
        --exclude '.pytest_cache' \
        --exclude '__pycache__' \
        --exclude '*.pyc' \
        "$source_dir/" "$source_target/"
elif [[ -f "$source_target/install.sh" ]]; then
    log "Using existing vllm-metal-hust source: $source_target"
else
    command -v git >/dev/null 2>&1 || fail "git is required to clone $fork_url"
    log "Cloning vllm-metal-hust into: $source_target"
    git clone --depth=1 "$fork_url" "$source_target"
fi

patch_file="$repo_root/tools/patches/vllm-metal-hust-install-cache.patch"
if [[ -f "$patch_file" ]] && ! grep -q 'curl_with_retries' "$source_target/install.sh"; then
    log "Applying Sage Mate vllm-metal-hust installer patch"
    if command -v git >/dev/null 2>&1; then
        (cd "$source_target" && git apply "$patch_file")
    else
        (cd "$source_target" && patch -p1 < "$patch_file")
    fi
fi

chmod +x "$source_target/install.sh"

if [[ -n "$vllm_hust_dir" ]]; then
    [[ -f "$vllm_hust_dir/pyproject.toml" && -d "$vllm_hust_dir/vllm" ]] \
        || fail "vllm-hust source tree was not found: $vllm_hust_dir"
    vllm_hust_patch="$repo_root/tools/patches/vllm-hust-macos-cpu-build.patch"
    if [[ -f "$vllm_hust_patch" ]] && ! grep -q 'sysctlbyname("hw.l2cachesize"' "$vllm_hust_dir/csrc/cpu/utils.hpp"; then
        log "Applying Sage Mate vllm-hust macOS CPU build patch"
        if command -v git >/dev/null 2>&1; then
            (cd "$vllm_hust_dir" && git apply "$vllm_hust_patch")
        else
            (cd "$vllm_hust_dir" && patch -p1 < "$vllm_hust_patch")
        fi
    fi
    if [[ ! -d "$vllm_hust_dir/.git" && -z "${VLLM_VERSION_OVERRIDE:-}" && -f "$vllm_hust_dir/.sage-mate-vllm-hust-version" ]]; then
        export VLLM_VERSION_OVERRIDE
        VLLM_VERSION_OVERRIDE=$(tr -d '[:space:]' < "$vllm_hust_dir/.sage-mate-vllm-hust-version")
        log "Using packaged vllm-hust version: $VLLM_VERSION_OVERRIDE"
    fi
    export VLLM_METAL_VLLM_SOURCE_DIR="$vllm_hust_dir"
    export VLLM_TARGET_DEVICE="${VLLM_TARGET_DEVICE:-cpu}"
    export VLLM_METAL_BUILD_FROM_SOURCE="${VLLM_METAL_BUILD_FROM_SOURCE:-1}"
    log "Using local vllm-hust core: $vllm_hust_dir"
fi

vllm_tarball="${VLLM_METAL_VLLM_TARBALL:-}"
if [[ -z "$vllm_tarball" && -f "$source_target/.cache/vllm/vllm-0.24.0.tar.gz" ]]; then
    vllm_tarball="$source_target/.cache/vllm/vllm-0.24.0.tar.gz"
fi
if [[ -n "$vllm_tarball" ]]; then
    [[ -f "$vllm_tarball" ]] || fail "VLLM_METAL_VLLM_TARBALL does not exist: $vllm_tarball"
    export VLLM_METAL_VLLM_TARBALL="$vllm_tarball"
    log "Using cached vLLM source tarball: $vllm_tarball"
fi

log "Installing vllm-metal-hust runtime; this compiles vLLM core and may take a while."
(
    cd "$source_target"
    ./install.sh
)

venv_python="$source_target/.venv-vllm-metal/bin/python"
[[ -x "$venv_python" ]] || fail "vllm-metal virtualenv was not created: $venv_python"

"$venv_python" - <<'PY'
import platform
import sys

if platform.machine() != "arm64":
    raise SystemExit("vllm-metal requires an arm64 Python runtime")
import vllm_metal  # noqa: F401
from vllm.platforms import current_platform

print(f"Resolved platform: {type(current_platform).__name__}")
PY

log "Installed vllm-metal-hust runtime: $source_target/.venv-vllm-metal"
