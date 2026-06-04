#!/usr/bin/env bash

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source_dir="$repo_root/deploy/systemd/user"
target_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"

if [[ -n "${PYTHON_BIN:-}" ]]; then
    python_bin="$PYTHON_BIN"
elif command -v python3 >/dev/null 2>&1; then
    python_bin=$(command -v python3)
elif command -v python >/dev/null 2>&1; then
    python_bin=$(command -v python)
else
    echo "Unable to locate a usable Python interpreter. Set PYTHON_BIN explicitly." >&2
    exit 1
fi

mkdir -p "$target_dir"

for unit in "$source_dir"/*.service; do
    rendered_unit="$target_dir/$(basename "$unit")"
    sed \
        -e "s|__REPO_ROOT__|$repo_root|g" \
        -e "s|__PYTHON_BIN__|$python_bin|g" \
        "$unit" >"$rendered_unit"
    chmod 0644 "$rendered_unit"
done

systemctl --user daemon-reload
systemctl --user enable sage-faculty-twin-app.service sage-faculty-twin-site.service sage-faculty-twin-vllm-openai-proxy.service sage-faculty-twin-tunnel.service

if [[ "${1:-}" == "--start" ]]; then
    systemctl --user restart sage-faculty-twin-vllm-openai-proxy.service sage-faculty-twin-app.service sage-faculty-twin-site.service sage-faculty-twin-tunnel.service
    systemctl --user --no-pager --full status \
        sage-faculty-twin-vllm-openai-proxy.service \
        sage-faculty-twin-app.service \
        sage-faculty-twin-site.service \
        sage-faculty-twin-tunnel.service
fi
