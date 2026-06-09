#!/usr/bin/env bash
# install_user_services.sh — Install systemd user services for sage-faculty-twin.
# Prerequisites: run bootstrap_venv.sh first to create .venv.

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source_dir="$repo_root/deploy/systemd/user"
target_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
venv_dir="$repo_root/.venv"

enable_vllm_proxy="false"
start_services="false"

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

# --- Validate venv exists ---
if [[ ! -x "$venv_dir/bin/python" ]]; then
    echo "ERROR: Venv not found at $venv_dir" >&2
    echo "  Run:  bash tools/bootstrap_venv.sh" >&2
    exit 1
fi

echo "Venv OK: $venv_dir/bin/python ($("$venv_dir/bin/python" --version 2>&1))"

# --- Render and install service units ---
mkdir -p "$target_dir"

for unit in "$source_dir"/*.service; do
    rendered_unit="$target_dir/$(basename "$unit")"
    sed \
        -e "s|__REPO_ROOT__|$repo_root|g" \
        "$unit" >"$rendered_unit"
    chmod 0644 "$rendered_unit"
    echo "  Installed: $(basename "$unit")"
done

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
