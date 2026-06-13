#!/usr/bin/env bash

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$repo_root/tools/lib/runtime_env.sh"
user_runtime_dir="/run/user/$(id -u)"
user_bus_path="$user_runtime_dir/bus"

if [[ -z "${XDG_RUNTIME_DIR:-}" && -d "$user_runtime_dir" ]]; then
    export XDG_RUNTIME_DIR="$user_runtime_dir"
fi

if [[ -z "${DBUS_SESSION_BUS_ADDRESS:-}" && -S "$user_bus_path" ]]; then
    export DBUS_SESSION_BUS_ADDRESS="unix:path=$user_bus_path"
fi

export_repo_runtime_env "$repo_root"
python_bin="$PYTHON_BIN"

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <install|status|start|stop|restart> [--json] [--with-vllm-proxy] [--with-tunnel] [--start]" >&2
    exit 1
fi

action="$1"

if [[ "$action" == "install" ]]; then
    shift || true
    exec "$repo_root/tools/install_user_services.sh" "$@"
fi

json_output="false"
include_vllm_proxy="false"
include_tunnel="false"
include_site_proxy="false"

for arg in "$@"; do
    case "$arg" in
        --json)
            json_output="true"
            ;;
        --with-tunnel)
            include_tunnel="true"
            ;;
        --with-site-proxy)
            include_site_proxy="true"
            ;;
        --with-vllm-proxy)
            include_vllm_proxy="true"
            ;;
    esac
done

services=(
    "应用服务:sage-faculty-twin-app.service"
)

if [[ "$include_site_proxy" == "true" ]]; then
    services+=("本地代理:sage-faculty-twin-site.service")
fi

if [[ "$include_tunnel" == "true" ]]; then
    services+=("公网隧道:sage-faculty-twin-tunnel.service")
fi

if [[ "$include_vllm_proxy" == "true" ]]; then
    services=("模型代理:sage-faculty-twin-vllm-openai-proxy.service" "${services[@]}")
fi

case "$action" in
    status|start|stop|restart)
        ;;
    *)
        echo "Unsupported action: $action" >&2
        exit 1
        ;;
esac

service_units=()
for entry in "${services[@]}"; do
    service_units+=("${entry#*:}")
done

if [[ "$action" != "status" ]]; then
    systemctl --user "$action" "${service_units[@]}"
fi

service_payload="[]"
for entry in "${services[@]}"; do
    name="${entry%%:*}"
    unit="${entry#*:}"
    properties=$(systemctl --user show "$unit" \
        --property=Id \
        --property=ActiveState \
        --property=SubState \
        --property=Description)

    id_value=""
    active_state=""
    sub_state=""
    description=""
    while IFS='=' read -r key value; do
        case "$key" in
            Id) id_value="$value" ;;
            ActiveState) active_state="$value" ;;
            SubState) sub_state="$value" ;;
            Description) description="$value" ;;
        esac
    done <<< "$properties"

    service_payload=$(SERVICE_PAYLOAD="$service_payload" "$python_bin" - "$name" "$id_value" "$active_state" "$sub_state" "$description" <<'PY'
import json
import os
import sys

payload = json.loads(os.environ["SERVICE_PAYLOAD"])
payload.append(
    {
        "name": sys.argv[1],
        "unit": sys.argv[2],
        "active_state": sys.argv[3],
        "sub_state": sys.argv[4],
        "description": sys.argv[5] or None,
    }
)
print(json.dumps(payload, ensure_ascii=False))
PY
)
done

message="Service action '${action}' completed."

if [[ "$json_output" == "true" ]]; then
    SERVICES_JSON="$service_payload" "$python_bin" - "$action" "$message" <<'PY'
import json
import os
import sys

print(
    json.dumps(
        {
            "action": sys.argv[1],
            "success": True,
            "message": sys.argv[2],
            "services": json.loads(os.environ["SERVICES_JSON"]),
        },
        ensure_ascii=False,
    )
)
PY
    exit 0
fi

echo "$message"
SERVICES_JSON="$service_payload" "$python_bin" - <<'PY'
import json
import os

for item in json.loads(os.environ["SERVICES_JSON"]):
    print(f"- {item['name']}: {item['active_state']} ({item['sub_state']}) [{item['unit']}]")
PY