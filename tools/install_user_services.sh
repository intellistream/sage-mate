#!/usr/bin/env bash
# install_user_services.sh — Install systemd user services for sage-faculty-twin.
# Prerequisites: run bootstrap_venv.sh first to create .venv.

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source_dir="$repo_root/deploy/systemd/user"
target_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
venv_dir="$repo_root/.venv"
user_runtime_dir="/run/user/$(id -u)"
user_bus_path="$user_runtime_dir/bus"

if [[ -z "${XDG_RUNTIME_DIR:-}" && -d "$user_runtime_dir" ]]; then
    export XDG_RUNTIME_DIR="$user_runtime_dir"
fi

if [[ -z "${DBUS_SESSION_BUS_ADDRESS:-}" && -S "$user_bus_path" ]]; then
    export DBUS_SESSION_BUS_ADDRESS="unix:path=$user_bus_path"
fi

enable_vllm_proxy="false"
start_services="false"

resolve_python_bin() {
    if [[ -x "$venv_dir/bin/python" ]]; then
        printf '%s\n' "$venv_dir/bin/python"
        return 0
    fi

    if [[ -n "${PYTHON_BIN:-}" && -x "${PYTHON_BIN}" ]]; then
        printf '%s\n' "${PYTHON_BIN}"
        return 0
    fi

    local candidate
    candidate=$(sed -n 's/^Environment=PYTHON_BIN=//p' "$target_dir/sage-faculty-twin-app.service" 2>/dev/null | tail -n 1)
    if [[ -n "$candidate" && -x "$candidate" ]]; then
        printf '%s\n' "$candidate"
        return 0
    fi

    candidate=$(sed -n 's/^Environment=PYTHON_BIN=//p' "$target_dir/sage-faculty-twin-app.service.d/override.conf" 2>/dev/null | tail -n 1)
    candidate=${candidate%%\[*}
    candidate=${candidate%%[[:space:]]*}
    if [[ -n "$candidate" && -x "$candidate" ]]; then
        printf '%s\n' "$candidate"
        return 0
    fi

    return 1
}

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

python_bin=$(resolve_python_bin) || {
    echo "ERROR: No usable Python runtime found for service install." >&2
    echo "  Either fix: $venv_dir/bin/python" >&2
    echo "  Or run with: PYTHON_BIN=/path/to/python3.11 bash tools/install_user_services.sh [--start]" >&2
    exit 1
}

echo "Python OK: $python_bin ($("$python_bin" --version 2>&1))"

cleanup_legacy_override() {
    local override_dir="$target_dir/sage-faculty-twin-app.service.d"
    local override_file="$override_dir/override.conf"
    if [[ ! -f "$override_file" ]]; then
        return 0
    fi

    if awk '
        /^[[:space:]]*$/ { next }
        /^\[Service\]$/ { next }
        /^Environment=PYTHON_BIN=/ { next }
        { exit 1 }
    ' "$override_file"; then
        rm -f "$override_file"
        rmdir "$override_dir" 2>/dev/null || true
        echo "  Removed legacy PYTHON_BIN override"
    fi
}

# --- Render and install service units ---
mkdir -p "$target_dir"

for unit in "$source_dir"/*.service; do
    rendered_unit="$target_dir/$(basename "$unit")"
    sed \
        -e "s|__REPO_ROOT__|$repo_root|g" \
        -e "s|__PYTHON_BIN__|$python_bin|g" \
        "$unit" >"$rendered_unit"
    chmod 0644 "$rendered_unit"
    echo "  Installed: $(basename "$unit")"
done

cleanup_legacy_override

systemctl --user daemon-reload

# --- Enable services ---
service_units=(
    sage-faculty-twin-app.service
    sage-faculty-twin-site.service
    sage-faculty-twin-tunnel.service
)

if [[ "$enable_vllm_proxy" == "true" ]]; then
    service_units+=(sage-faculty-twin-vllm-openai-proxy.service)
fi

systemctl --user enable "${service_units[@]}"

if [[ "$start_services" == "true" ]]; then
    systemctl --user restart "${service_units[@]}"
    systemctl --user --no-pager --full status "${service_units[@]}"
fi

echo ""
echo "Services installed. Use 'manage.sh start' to start them."
