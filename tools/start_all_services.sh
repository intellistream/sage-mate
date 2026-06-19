#!/usr/bin/env bash
# start_all_services.sh — One-command startup for the twin stack.
#
# Brings up:
#   1. vLLM model service (via vllm-hust-dev-hub launch script)
#   2. sage-faculty-twin app + site proxy
#   3. Cloudflare tunnel (sage-faculty-twin-tunnel)
#
# Usage:
#   bash tools/start_all_services.sh [--preset coder|w8a8] [--docker CONTAINER]
#                                     [--skip-model] [--skip-twin] [--skip-tunnel]
#                                     [--health-timeout SECS]
#
# Prerequisites:
#   - Docker container running with NPU devices (for model service)
#   - sagevdb C extension built for the correct Python version
#     (cd ~/sageVDB && bash build.sh with Python3_EXECUTABLE set)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEV_HUB_DIR="$HOME/vllm-hust-dev-hub"

# ── defaults ────────────────────────────────────────────────────────────────
PRESET="${PRESET:-coder}"
DOCKER_CONTAINER="${DOCKER_CONTAINER:-vllm_hust_ws_21rc}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-600}"
SKIP_MODEL=0
SKIP_TWIN=0
SKIP_TUNNEL=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --preset)         PRESET="$2"; shift 2 ;;
    --docker)         DOCKER_CONTAINER="$2"; shift 2 ;;
    --health-timeout) HEALTH_TIMEOUT="$2"; shift 2 ;;
    --skip-model)     SKIP_MODEL=1; shift ;;
    --skip-twin)      SKIP_TWIN=1; shift ;;
    --skip-tunnel)    SKIP_TUNNEL=1; shift ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

ok()   { echo -e "\033[32m[OK]\033[0m   $*"; }
warn() { echo -e "\033[33m[WARN]\033[0m $*"; }
fail() { echo -e "\033[31m[FAIL]\033[0m $*"; }
step() { echo -e "\n\033[1;34m━━━ $* ━━━\033[0m"; }

ERRORS=0

# ═══════════════════════════════════════════════════════════════════════════
# Step 1: Model service
# ═══════════════════════════════════════════════════════════════════════════
if (( SKIP_MODEL == 0 )); then
  step "1/3  Model service (preset=$PRESET, docker=$DOCKER_CONTAINER)"

  LAUNCH_SCRIPT="$DEV_HUB_DIR/scripts/launch_ascend_model_service.sh"
  if [[ ! -f "$LAUNCH_SCRIPT" ]]; then
    fail "Launch script not found at $LAUNCH_SCRIPT"
    ERRORS=$((ERRORS + 1))
  elif curl -fsS -m 5 http://127.0.0.1:8000/health >/dev/null 2>&1; then
    ok "Model service already healthy on :8000"
  else
    echo "Launching model service..."
    bash "$LAUNCH_SCRIPT" \
      --preset "$PRESET" \
      --docker "$DOCKER_CONTAINER" \
      --health-timeout "$HEALTH_TIMEOUT" \
      --no-health-check &
    LAUNCH_PID=$!

    echo "Waiting for health check (timeout=${HEALTH_TIMEOUT}s)..."
    DEADLINE=$((SECONDS + HEALTH_TIMEOUT))
    until curl -fsS -m 5 http://127.0.0.1:8000/health >/dev/null 2>&1; do
      if (( SECONDS >= DEADLINE )); then
        fail "Model service did not become healthy within ${HEALTH_TIMEOUT}s"
        ERRORS=$((ERRORS + 1))
        break
      fi
      sleep 5
    done
    if curl -fsS -m 5 http://127.0.0.1:8000/health >/dev/null 2>&1; then
      ok "Model service healthy on :8000"
    fi
    wait "$LAUNCH_PID" 2>/dev/null || true
  fi
else
  warn "Skipping model service (--skip-model)"
fi

# ═══════════════════════════════════════════════════════════════════════════
# Step 2: Twin services (app + site proxy)
# ═══════════════════════════════════════════════════════════════════════════
if (( SKIP_TWIN == 0 )); then
  step "2/3  Twin services (app + site-proxy)"

  cd "$REPO_ROOT"

  # Install + start app and site proxy (tunnel handled separately in Step 3)
  bash tools/install_user_services.sh \
    --start \
    --with-site-proxy 2>&1 | tail -5

  sleep 3

  # Check app
  if systemctl --user is-active --quiet sage-faculty-twin-app.service; then
    ok "sage-faculty-twin-app: running"
  else
    fail "sage-faculty-twin-app: not running"
    journalctl --user -u sage-faculty-twin-app.service --no-pager -n 5 2>&1
    ERRORS=$((ERRORS + 1))
  fi

  # Check site proxy
  if systemctl --user is-active --quiet sage-faculty-twin-site.service; then
    ok "sage-faculty-twin-site: running"
  else
    fail "sage-faculty-twin-site: not running"
    ERRORS=$((ERRORS + 1))
  fi
else
  warn "Skipping twin services (--skip-twin)"
fi

# ═══════════════════════════════════════════════════════════════════════════
# Step 3: Tunnel
# ═══════════════════════════════════════════════════════════════════════════
if (( SKIP_TUNNEL == 0 )); then
  step "3/3  Tunnel (sage-faculty-twin-tunnel)"

  if systemctl --user is-active --quiet sage-faculty-twin-tunnel.service; then
    ok "sage-faculty-twin-tunnel: already running"
  else
    systemctl --user start sage-faculty-twin-tunnel.service 2>&1 || true
    sleep 2
    if systemctl --user is-active --quiet sage-faculty-twin-tunnel.service; then
      ok "sage-faculty-twin-tunnel: started"
    else
      fail "sage-faculty-twin-tunnel: failed to start"
      journalctl --user -u sage-faculty-twin-tunnel.service --no-pager -n 3 2>&1
      ERRORS=$((ERRORS + 1))
    fi
  fi
else
  warn "Skipping tunnel (--skip-tunnel)"
fi

# ═══════════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════════
step "Summary"

echo "  Model service:  http://127.0.0.1:8000"
echo "  Twin app:       http://127.0.0.1:55601"
echo "  External:       https://shuhao.sage.org.ai"

if (( ERRORS > 0 )); then
  fail "$ERRORS service(s) failed to start"
  exit 1
else
  ok "All services started successfully"
fi
