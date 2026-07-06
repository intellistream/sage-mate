#!/usr/bin/env bash
# manage.sh — single entry point for sage-faculty-twin runtime management.
#
# Actions:
#   status    Show service states
#   start     Start services
#   stop      Stop services
#   restart   Restart services
#   logs      Follow journal for a service (usage: manage.sh logs <name>)
#   repair-sagevdb  Repair sageVDB native extension wiring
#   check-inference  Run one inference health check
#   reserve-vllm-devices  Pin vllm-hust to specific Ascend device IDs
#   configure-slack-twin  Configure Slack /twin command secret and access
#
# Flags (combine with any action):
#   --all                Include all optional services
#   --with-vllm-engine   vLLM inference engine
#   --with-vllm-proxy    OpenAI-compatible auth proxy
#   --with-site-proxy    Local nginx/python site proxy
#   --with-tunnel        Cloudflare tunnel
#   --with-model         (start/stop only) launch model engine in foreground
#   --json               Output machine-readable JSON (status only)
#   --foreground         Run the action in the foreground (model engine)
#
# Examples:
#   ./manage.sh status --all
#   ./manage.sh start  --all
#   ./manage.sh restart --with-vllm-engine
#   ./manage.sh logs   app
#   ./manage.sh logs   engine
#   ./manage.sh stop   --all

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

usage() {
    cat <<EOF
Usage: $0 <status|start|stop|restart|logs|install|repair-sagevdb|check-inference|reserve-vllm-devices|configure-slack-twin> [flags]
  Flags: --all --with-vllm-engine --with-vllm-proxy --with-site-proxy --with-tunnel --json
  Logs:  $0 logs <app|engine|proxy|site|tunnel|model>
EOF
}

# ── Parse arguments ──────────────────────────────────────────────────────────
if [[ $# -lt 1 ]]; then
    usage >&2
    exit 1
fi

action="$1"
shift

if [[ "$action" == "-h" || "$action" == "--help" || "$action" == "help" ]]; then
    usage
    exit 0
fi

# Delegate install to quickstart.sh
if [[ "$action" == "install" ]]; then
    exec "$repo_root/quickstart.sh" "$@"
fi

if [[ "$action" == "repair-sagevdb" ]]; then
    SAGEVDB_REPAIR_IGNORE_PYTHON_BIN=1 exec "$repo_root/tools/repair_sagevdb.sh" "$@"
fi

if [[ "$action" == "check-inference" ]]; then
    exec "$repo_root/tools/monitor_twin_inference.sh" "$@"
fi

if [[ "$action" == "reserve-vllm-devices" ]]; then
    exec "$repo_root/tools/reserve_vllm_devices.sh" "$@"
fi

if [[ "$action" == "configure-slack-twin" ]]; then
    exec "$repo_root/tools/configure_slack_twin.sh" "$@"
fi

json_output="false"
foreground="false"
include_engine=false
include_proxy=false
include_site=false
include_tunnel=false
include_model=false
include_app=false
explicit_service_selection=false

for arg in "$@"; do
    case "$arg" in
        --json)              json_output="true" ;;
        --foreground)        foreground="true" ;;
        --all)               explicit_service_selection=true; include_app=true; include_engine=true; include_proxy=true; include_site=true; include_tunnel=true ;;
        --with-vllm-engine)  explicit_service_selection=true; include_engine=true ;;
        --with-vllm-proxy)   explicit_service_selection=true; include_proxy=true ;;
        --with-site-proxy)   explicit_service_selection=true; include_site=true ;;
        --with-tunnel)       explicit_service_selection=true; include_tunnel=true ;;
        --with-model)        explicit_service_selection=true; include_model=true ;;
    esac
done

if ! $explicit_service_selection; then
    include_app=true
fi

# ── Service registry ─────────────────────────────────────────────────────────
# Format: "display_name:systemd_unit"
# Order: model/engine → proxy → app → site → tunnel
services=()
$include_engine && services+=("推理引擎:sage-faculty-twin-vllm-engine.service")
$include_proxy  && services+=("模型代理:sage-faculty-twin-vllm-openai-proxy.service")

$include_app    && services+=("应用服务:sage-faculty-twin-app.service")

$include_site   && services+=("本地代理:sage-faculty-twin-site.service")
$include_tunnel && services+=("公网隧道:sage-faculty-twin-tunnel.service")

# ── Action: logs ─────────────────────────────────────────────────────────────
if [[ "$action" == "logs" ]]; then
    target="${1:-app}"
    case "$target" in
        app)     unit="sage-faculty-twin-app.service" ;;
        engine)  unit="sage-faculty-twin-vllm-engine.service" ;;
        proxy)   unit="sage-faculty-twin-vllm-openai-proxy.service" ;;
        site)    unit="sage-faculty-twin-site.service" ;;
        tunnel)  unit="sage-faculty-twin-tunnel.service" ;;
        model)   echo "Model runs outside systemd — use: journalctl or docker logs"; exit 0 ;;
        *)       echo "Unknown service: $target (app|engine|proxy|site|tunnel|model)" >&2; exit 1 ;;
    esac
    exec journalctl --user -u "$unit" -f
fi

# ── Action: start model in foreground ────────────────────────────────────────
if [[ "$action" == "start" ]] && $include_model; then
    if $foreground || true; then
        echo "[manage] Launching vLLM engine in foreground..."
        exec "$repo_root/tools/run_vllm_engine.sh"
    fi
fi

# ── Validate action ──────────────────────────────────────────────────────────
case "$action" in
    status|start|stop|restart) ;;
    *) echo "Unsupported action: $action" >&2; exit 1 ;;
esac

# ── Extract systemd unit names ───────────────────────────────────────────────
service_units=()
for entry in "${services[@]}"; do
    service_units+=("${entry#*:}")
done

cleanup_vllm_engine_residuals() {
    $include_engine || return 0
    [[ -x "$repo_root/tools/cleanup_vllm_engine.sh" ]] || return 0
    "$repo_root/tools/cleanup_vllm_engine.sh" || true
}

# ── Execute action ───────────────────────────────────────────────────────────
if [[ "$action" != "status" ]]; then
    if [[ "$action" == "restart" ]]; then
        cleanup_vllm_engine_residuals
    fi
    systemctl --user "$action" "${service_units[@]}"
    if [[ "$action" == "stop" ]]; then
        cleanup_vllm_engine_residuals
    fi
fi

# ── Collect status for each service ──────────────────────────────────────────
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
import json, os, sys
payload = json.loads(os.environ["SERVICE_PAYLOAD"])
payload.append({
    "name": sys.argv[1],
    "unit": sys.argv[2],
    "active_state": sys.argv[3],
    "sub_state": sys.argv[4],
    "description": sys.argv[5] or None,
})
print(json.dumps(payload, ensure_ascii=False))
PY
    )
done

# ── Output ───────────────────────────────────────────────────────────────────
message="Service action '${action}' completed."

if [[ "$json_output" == "true" ]]; then
    SERVICES_JSON="$service_payload" "$python_bin" - "$action" "$message" <<'PY'
import json, os, sys
print(json.dumps({
    "action": sys.argv[1],
    "success": True,
    "message": sys.argv[2],
    "services": json.loads(os.environ["SERVICES_JSON"]),
}, ensure_ascii=False))
PY
    exit 0
fi

echo "$message"
SERVICES_JSON="$service_payload" "$python_bin" - <<'PY'
import json, os
for item in json.loads(os.environ["SERVICES_JSON"]):
    state = item['active_state']
    icon = "✓" if state == "active" else "✗" if state == "failed" else "·"
    print(f"  {icon} {item['name']}: {state} ({item['sub_state']}) [{item['unit']}]")
PY
