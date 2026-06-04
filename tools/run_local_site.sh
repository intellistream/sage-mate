#!/usr/bin/env bash

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
runtime_dir="$repo_root/.runtime"
nginx_prefix="$runtime_dir/nginx"
nginx_template="$repo_root/tools/nginx-local.conf"
nginx_conf="$nginx_prefix/nginx.conf"
exec "$(dirname "${BASH_SOURCE[0]}")/run_local_proxy.sh" "$@"