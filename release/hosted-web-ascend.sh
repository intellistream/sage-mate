#!/usr/bin/env bash
# Convenience wrapper for Ascend/NPU hosted-web installs.

set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
exec "$script_dir/hosted-web.sh" --accelerator ascend "$@"
