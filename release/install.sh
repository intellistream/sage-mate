#!/usr/bin/env bash
# Product entrypoint for the hosted/web release bundle.

set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
installer="$script_dir/hosted-web-installer.sh"

if [[ ! -x "$installer" ]]; then
    chmod +x "$installer" 2>/dev/null || true
fi

exec "$installer" "$@"
