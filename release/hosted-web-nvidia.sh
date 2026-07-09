#!/usr/bin/env bash
# Compatibility wrapper. Prefer release/hosted-web.sh for new installs.

set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
exec "$script_dir/hosted-web.sh" --accelerator nvidia "$@"
