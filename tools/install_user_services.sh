#!/usr/bin/env bash

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source_dir="$repo_root/deploy/systemd/user"
target_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
python_bin_state_file="$target_dir/.sage-faculty-twin-python-bin"
enable_vllm_proxy="false"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --start)
            start_services="true"
            ;;
        --with-vllm-proxy)
            enable_vllm_proxy="true"
            ;;
        *)
            echo "Unsupported option: $1" >&2
            exit 1
            ;;
    esac
    shift
done

python_has_uvicorn() {
    local candidate="$1"
    [[ -n "$candidate" && -x "$candidate" ]] || return 1
    "$candidate" - <<'PY' >/dev/null 2>&1
import importlib.util
raise SystemExit(0 if importlib.util.find_spec("uvicorn") else 1)
PY
}

resolve_python_bin() {
    local candidate=""
    local current_user
    current_user=$(id -un)

    if [[ -n "${PYTHON_BIN:-}" ]]; then
        if python_has_uvicorn "$PYTHON_BIN"; then
            printf '%s\n' "$PYTHON_BIN"
            return 0
        fi
    fi

    if [[ -r "$target_dir/sage-faculty-twin-app.service" ]]; then
        candidate=$(sed -n 's/^Environment=PYTHON_BIN=//p' "$target_dir/sage-faculty-twin-app.service" | head -n 1)
        if python_has_uvicorn "$candidate"; then
            printf '%s\n' "$candidate"
            return 0
        fi
    fi

    candidate=$(pgrep -u "$current_user" -f 'sage_faculty_twin.api:app --host 127.0.0.1 --port 55601' | head -n 1 || true)
    if [[ -n "$candidate" && -x "/proc/$candidate/exe" ]]; then
        candidate=$(readlink -f "/proc/$candidate/exe")
        if python_has_uvicorn "$candidate"; then
            printf '%s\n' "$candidate"
            return 0
        fi
    fi

    if [[ -r "$python_bin_state_file" ]]; then
        candidate=$(<"$python_bin_state_file")
        if python_has_uvicorn "$candidate"; then
            printf '%s\n' "$candidate"
            return 0
        fi
    fi

    if command -v python3 >/dev/null 2>&1; then
        candidate=$(command -v python3)
        if python_has_uvicorn "$candidate"; then
            printf '%s\n' "$candidate"
            return 0
        fi
    fi

    if command -v python >/dev/null 2>&1; then
        candidate=$(command -v python)
        if python_has_uvicorn "$candidate"; then
            printf '%s\n' "$candidate"
            return 0
        fi
    fi

    return 1
}

if python_bin=$(resolve_python_bin); then
    :
else
    echo "Unable to locate a usable Python interpreter. Set PYTHON_BIN explicitly." >&2
    exit 1
fi

mkdir -p "$target_dir"
printf '%s\n' "$python_bin" >"$python_bin_state_file"
chmod 0644 "$python_bin_state_file"

for unit in "$source_dir"/*.service; do
    rendered_unit="$target_dir/$(basename "$unit")"
    sed \
        -e "s|__REPO_ROOT__|$repo_root|g" \
        -e "s|__PYTHON_BIN__|$python_bin|g" \
        "$unit" >"$rendered_unit"
    chmod 0644 "$rendered_unit"
done

systemctl --user daemon-reload

service_units=(
    sage-faculty-twin-app.service
    sage-faculty-twin-site.service
    sage-faculty-twin-tunnel.service
)

if [[ "$enable_vllm_proxy" == "true" ]]; then
    service_units+=(sage-faculty-twin-vllm-openai-proxy.service)
fi

systemctl --user enable "${service_units[@]}"

if [[ "${start_services:-false}" == "true" ]]; then
    systemctl --user restart "${service_units[@]}"
    systemctl --user --no-pager --full status \
        "${service_units[@]}"
fi
