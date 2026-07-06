#!/usr/bin/env bash
# quickstart.sh — single entry point for Faculty Twin / Sage Mate installation.
#
# Usage:
#   ./quickstart.sh                                # hosted web install; code tools off
#   ./quickstart.sh --target hosted-web --start    # server/web install + start systemd
#   ./quickstart.sh --local-mac-app --start        # local Sage Mate app-style install
#   ./quickstart.sh --mac-dmg                      # build dist/sage-mate-macos.dmg
#   ./quickstart.sh --check                        # preflight only — diagnose, do not change
#   ./quickstart.sh --systemd-only                 # refresh systemd units only; no pip, no start
#   ./quickstart.sh --skip-python-install          # skip editable pip install steps
#   ./quickstart.sh --with-vllm                    # also install vllm-hust (editable)
#   ./quickstart.sh --with-vllm-engine             # enable vLLM engine systemd service
#   ./quickstart.sh --with-vllm-proxy              # enable vLLM OpenAI auth proxy service
#   ./quickstart.sh --with-site-proxy              # enable local nginx/python proxy service
#   ./quickstart.sh --with-tunnel                  # enable Cloudflare tunnel service
#   ./quickstart.sh --no-systemd                   # skip systemd unit install
#   ./quickstart.sh --yes                          # non-interactive (assume yes)
#
# Install targets:
#   hosted-web       Linux/server browser deployment. Default. Never enables code tools.
#   local-mac-app    Local Sage Mate install; delegates to tools/install_local_code_mode.sh.
#   mac-dmg          Build the macOS DMG package; delegates to tools/build_macos_local_code_package.sh.
#
# Environment overrides:
#   PYTHON_BIN        Path to interpreter (default: python3 in PATH)
#   CONDA_ENV_NAME    Conda env to use/create (default: vllm-hust-dev)
#   APP_PORT          App listen port (default: 55601)
#
# This script will NOT:
#   - Download or launch any LLM model — use manage.sh for runtime operations.
#   - Touch git history.
#   - Enable local code tools on hosted-web installs.

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
parent_dir="${FACULTY_TWIN_PARENT_DIR:-$(dirname "$repo_root")}"

# ── CLI flags ────────────────────────────────────────────────────────────────
mode_check=false
mode_systemd_only=false
mode_skip_python_install=false
pip_timeout_seconds="${PIP_INSTALL_TIMEOUT_SECONDS:-0}"
mode_with_vllm=false
mode_no_systemd=false
mode_no_siblings=false
mode_start=false
mode_yes=false
svc_engine=false
svc_proxy=false
svc_site=false
svc_tunnel=false
install_target="hosted-web"
local_install_args=()
mac_dmg_args=()
local_target_hint=false
local_claude_hust_dir_explicit=false

usage() {
	cat <<'EOF'
quickstart.sh — single entry point for Faculty Twin / Sage Mate installation.

Usage:
  ./quickstart.sh                                # hosted web install; code tools off
  ./quickstart.sh --target hosted-web --start    # server/web install + start systemd
  ./quickstart.sh --local-mac-app --start        # local Sage Mate app-style install
  ./quickstart.sh --mac-dmg                      # build dist/sage-mate-macos.dmg
  ./quickstart.sh --check                        # static/preflight checks only
  ./quickstart.sh --systemd-only                 # refresh systemd user units only

Install targets:
  hosted-web       Linux/server browser deployment. Default. Never enables code tools.
  local-mac-app    Local Sage Mate install; delegates to tools/install_local_code_mode.sh.
  mac-dmg          Build the macOS DMG package; delegates to tools/build_macos_local_code_package.sh.

Hosted-web options:
  --with-vllm, --with-vllm-engine, --with-vllm-proxy, --with-site-proxy, --with-tunnel
  --no-systemd, --no-siblings, --skip-python-install, --pip-timeout SECONDS, --start, --yes

Local Sage Mate options:
  --app-profile faculty_twin|code_assistant
  --workspace PATH              Repeatable local repository allowlist.
  --workspace-roots CSV         Comma-separated local repository allowlist.
  --runtime-dir PATH
  --llm-base-url URL
  --api-key KEY
  --model-name NAME
  --code-backend auto|internal|claude_hust
  --claude-hust-repo URL
  --claude-hust-dir PATH
  --skip-claude-hust
  --prefill-env PATH
  --port PORT
  --python PATH
  --venv PATH
  --start

DMG options:
  --zip                         Also build a zip fallback.
EOF
}

while [[ $# -gt 0 ]]; do
	case "$1" in
	--target)
		[[ $# -ge 2 ]] || { echo "--target requires a value" >&2; exit 2; }
		install_target="$2"
		shift 2
		;;
	--target=*)
		install_target="${1#*=}"
		shift
		;;
	--hosted-web)
		install_target="hosted-web"
		shift
		;;
	--local-mac-app)
		install_target="local-mac-app"
		shift
		;;
	--mac-dmg | --build-mac-dmg)
		install_target="mac-dmg"
		shift
		;;
	--check)          mode_check=true; shift ;;
	--systemd-only)
		mode_systemd_only=true
		mode_no_siblings=true
		mode_skip_python_install=true
		shift
		;;
	--skip-python-install) mode_skip_python_install=true; shift ;;
	--pip-timeout)
		[[ $# -ge 2 ]] || { echo "--pip-timeout requires a value" >&2; exit 2; }
		pip_timeout_seconds="$2"
		shift 2
		;;
	--pip-timeout=*)
		pip_timeout_seconds="${1#*=}"
		shift
		;;
	--with-vllm)      mode_with_vllm=true; shift ;;
	--with-vllm-engine) svc_engine=true; shift ;;
	--with-vllm-proxy)  svc_proxy=true; shift ;;
	--with-site-proxy)  svc_site=true; shift ;;
	--with-tunnel)      svc_tunnel=true; shift ;;
	--no-systemd)     mode_no_systemd=true; shift ;;
	--no-siblings)    mode_no_siblings=true; shift ;;
	--start)
		mode_start=true
		local_install_args+=(--start)
		shift
		;;
	--yes | -y)       mode_yes=true; shift ;;
	--zip)
		mac_dmg_args+=(--zip)
		shift
		;;
	--workspace | --workspace-roots | --runtime-dir | --llm-base-url | --api-key | --model-name | --prefill-env | --port | --python | --venv | --app-profile | --code-backend | --claude-hust-repo | --claude-hust-dir)
		[[ $# -ge 2 ]] || { echo "$1 requires a value" >&2; exit 2; }
		local_target_hint=true
		[[ "$1" == "--claude-hust-dir" ]] && local_claude_hust_dir_explicit=true
		if [[ "$1" == "--app-profile" ]]; then
			local_install_args+=(--profile "$2")
		else
			local_install_args+=("$1" "$2")
		fi
		shift 2
		;;
	--skip-claude-hust)
		local_target_hint=true
		local_install_args+=(--skip-claude-hust)
		shift
		;;
	--profile)
		[[ $# -ge 2 ]] || { echo "--profile requires a value" >&2; exit 2; }
		case "$2" in
			hosted-web|local-mac-app|mac-dmg) install_target="$2" ;;
			faculty_twin|code_assistant)
				local_target_hint=true
				local_install_args+=(--profile "$2")
				;;
			*) echo "--profile must be a deployment target or app profile" >&2; exit 2 ;;
		esac
		shift 2
		;;
	-h | --help)      usage; exit 0 ;;
	*) echo "Unknown argument: $1" >&2; exit 2 ;;
	esac
done

if $local_target_hint && [[ "$install_target" == "hosted-web" ]]; then
	install_target="local-mac-app"
fi

case "$install_target" in
	hosted-web|local-mac-app|mac-dmg) ;;
	*) echo "--target must be one of: hosted-web, local-mac-app, mac-dmg" >&2; exit 2 ;;
esac

log()  { printf '\033[1;36m[quickstart]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[quickstart]\033[0m %s\n' "$*" >&2; }
fail() { printf '\033[1;31m[quickstart]\033[0m %s\n' "$*" >&2; exit 1; }
confirm() { $mode_yes && return 0; read -r -p "$1 [y/N] " ans; [[ "$ans" =~ ^[Yy]$ ]]; }

run_with_optional_timeout() {
	if [[ "$pip_timeout_seconds" =~ ^[0-9]+$ ]] && (( pip_timeout_seconds > 0 )) && command -v timeout >/dev/null 2>&1; then
		timeout "$pip_timeout_seconds" "$@"
	else
		"$@"
	fi
}

run_static_checks() {
	log "Static checks: shell entrypoints"
	local shell_scripts=(
		manage.sh
		quickstart.sh
		tools/run_app_server.sh
		tools/run_vllm_engine.sh
		tools/run_vllm_openai_proxy.sh
		tools/run_local_proxy.sh
		tools/run_named_tunnel.sh
		tools/monitor_twin_inference.sh
		tools/reserve_vllm_devices.sh
	)
	local script=""
	for script in "${shell_scripts[@]}"; do
		[[ -f "$repo_root/$script" ]] || continue
		bash -n "$repo_root/$script"
		log "  ok: $script"
	done

	log "Static checks: Python entrypoints"
	local py_files=(
		src/sage_faculty_twin/vllm_openai_proxy.py
		tools/openai_key_proxy.py
		tools/repair_sagevdb.py
	)
	local py_file=""
	for py_file in "${py_files[@]}"; do
		[[ -f "$repo_root/$py_file" ]] || continue
		"$python_bin" -m py_compile "$repo_root/$py_file"
		log "  ok: $py_file"
	done

	log "Static checks: vLLM-HUST dev-hub launcher"
	local dev_hub_launcher="$repo_root/deps/vllm-hust-dev-hub/scripts/run_vllm_hust_engine.sh"
	[[ -x "$dev_hub_launcher" ]] || fail "missing executable dev-hub launcher: $dev_hub_launcher"
	bash -n "$dev_hub_launcher"
	log "  ok: deps/vllm-hust-dev-hub/scripts/run_vllm_hust_engine.sh"

	log "Static checks: systemd templates"
	local unit=""
	for unit in "$repo_root"/deploy/systemd/user/*.service "$repo_root"/deploy/systemd/user/*.timer; do
		[[ -f "$unit" ]] || continue
		grep -q "__REPO_ROOT__" "$unit" || [[ "$(basename "$unit")" == *.timer ]] || warn "  $(basename "$unit") has no __REPO_ROOT__ placeholder"
		log "  ok: deploy/systemd/user/$(basename "$unit")"
	done
}

log "Install target: $install_target"

# ── 1. Preflight ─────────────────────────────────────────────────────────────
log "Preflight: $repo_root"
command -v git >/dev/null 2>&1 || fail "git not found"
[[ -f "$repo_root/pyproject.toml" ]] || fail "pyproject.toml missing — run quickstart from the repo root"

if [[ -n "${PYTHON_BIN:-}" ]]; then
	python_bin="$PYTHON_BIN"
elif command -v python3 >/dev/null 2>&1; then
	python_bin=$(command -v python3)
else
	fail "python3 not found; set PYTHON_BIN or install Python 3.10+"
fi

py_ver=$("$python_bin" -c 'import sys; print("%d.%d"%sys.version_info[:2])')
log "  python: $python_bin ($py_ver)"
case "$py_ver" in 3.1[0-9] | 3.[2-9][0-9]) ;; *) warn "  expected Python >=3.10, got $py_ver" ;; esac

if command -v npu-smi >/dev/null 2>&1; then
	npu_count=$(npu-smi info 2>/dev/null | awk '/^[|][[:space:]]*[0-9]+[[:space:]]+910/ { count++ } END { print count+0 }')
	log "  npu-smi: $npu_count Ascend NPU(s)"
elif command -v nvidia-smi >/dev/null 2>&1; then
	gpu_count=$(nvidia-smi -L 2>/dev/null | wc -l)
	log "  nvidia-smi: $gpu_count GPU(s)"
else
	warn "  neither npu-smi nor nvidia-smi found — local vLLM serving needs Ascend/NVIDIA drivers"
fi

if $mode_check; then
	run_static_checks
	log "Preflight/static checks only (--check). Done."
	exit 0
fi

if [[ "$install_target" == "mac-dmg" ]]; then
	log "Building Sage Mate macOS DMG"
	exec "$repo_root/tools/build_macos_local_code_package.sh" "${mac_dmg_args[@]}"
fi

if [[ "$install_target" == "local-mac-app" ]]; then
	if ! $local_claude_hust_dir_explicit; then
		local_install_args+=(--claude-hust-dir "$parent_dir/claude-code-hust")
	fi
	log "Installing local Sage Mate app runtime"
	exec "$repo_root/tools/install_local_code_mode.sh" "${local_install_args[@]}"
fi

# ── 3. Sibling repositories ─────────────────────────────────────────────────
mkdir -p "$parent_dir"
clone_if_missing() {
	local name="$1" url="$2"
	if [[ ! -d "$parent_dir/$name" ]]; then
		log "Cloning $name into $parent_dir"
		if ! git clone --depth=1 "$url" "$parent_dir/$name" 2>/dev/null; then
			warn "  could not clone $name (may need GITHUB_TOKEN for private repos)"
		fi
	else
		log "  sibling repo present: $parent_dir/$name"
	fi
}

if $mode_no_siblings; then
	log "Skipping sibling repo cloning (--no-siblings)"
else
	clone_if_missing SAGE      https://github.com/intellistream/SAGE.git
	clone_if_missing neuromem  https://github.com/intellistream/neuromem.git
	clone_if_missing sageVDB   https://github.com/intellistream/sageVDB.git
	$mode_with_vllm && clone_if_missing vllm-hust https://github.com/intellistream/vllm-hust.git
fi

# ── 4. Python dependencies ───────────────────────────────────────────────────
if $mode_skip_python_install; then
	log "Skipping Python dependency installation (--skip-python-install)"
else
	log "Installing sage-faculty-twin (editable, with vdb-anns extras)"
	run_with_optional_timeout "$python_bin" -m pip install --quiet --upgrade pip
	if ! run_with_optional_timeout "$python_bin" -m pip install --quiet -e "$repo_root[vdb-anns]"; then
		warn "vdb-anns extras failed (C extensions may need CANN/C++ toolchain)"
		warn "Falling back to base install"
		run_with_optional_timeout "$python_bin" -m pip install --quiet -e "$repo_root"
	fi

	if [[ -d "$parent_dir/sageVDB" ]]; then
		log "Repairing sageVDB native extension wiring"
		if ! "$python_bin" "$repo_root/tools/repair_sagevdb.py" --sagevdb-root "$parent_dir/sageVDB"; then
			warn "sageVDB repair failed; sagevdb backend may be unavailable for this Python"
			warn "  Retry with: ./manage.sh repair-sagevdb"
		fi
	fi

	if $mode_with_vllm && [[ -d "$parent_dir/vllm-hust" ]]; then
		log "Installing vllm-hust (editable, may take several minutes)"
		run_with_optional_timeout "$python_bin" -m pip install --quiet -e "$parent_dir/vllm-hust" \
			|| warn "vllm-hust install failed; build deps (CUDA/ninja, Ascend toolkit) may be missing"
	fi
fi

# ── 5. .env bootstrap ────────────────────────────────────────────────────────
env_file="$repo_root/.env"
template="$repo_root/.env.example"
if [[ ! -f "$env_file" ]]; then
	log "Creating .env from .env.example"
	cp "$template" "$env_file"
	warn "  Edit $env_file before serving real users:"
	warn "    DIGITAL_TWIN_OWNER_NAME / OWNER_ROLE"
	warn "    DIGITAL_TWIN_LLM_BASE_URL / API_KEY  (point at vllm-hust DIRECTLY)"
	warn "    DIGITAL_TWIN_ADMIN_PASSWORD"
fi

# Ensure required keys exist (append only if absent — never overwrite).
ensure_env_kv() {
	local key="$1" default="$2"
	grep -qE "^[[:space:]]*${key}=" "$env_file" 2>/dev/null && return
	printf '%s=%s\n' "$key" "$default" >>"$env_file"
	log "  appended $key=$default"
}
ensure_env_kv DIGITAL_TWIN_STREAM_CHAT_ANSWER       true
ensure_env_kv DIGITAL_TWIN_CHAT_REQUEST_TIMEOUT_SECONDS 80
ensure_env_kv DIGITAL_TWIN_LLM_TIMEOUT_SECONDS       60
ensure_env_kv DIGITAL_TWIN_CHAT_SSE_KEEPALIVE_SECONDS 15
ensure_env_kv DIGITAL_TWIN_CHAT_PROMPT_SOFT_CAP_CHARS 12000

set_env_kv() {
	local key="$1" value="$2"
	if grep -qE "^[[:space:]]*${key}=" "$env_file" 2>/dev/null; then
		"$python_bin" - "$env_file" "$key" "$value" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
key = sys.argv[2]
value = sys.argv[3]
lines = path.read_text(encoding="utf-8").splitlines()
prefix = f"{key}="
updated = False
out = []
for line in lines:
    if line.strip().startswith(prefix):
        out.append(f"{key}={value}")
        updated = True
    else:
        out.append(line)
if not updated:
    out.append(f"{key}={value}")
path.write_text("\n".join(out) + "\n", encoding="utf-8")
PY
	else
		printf '%s=%s\n' "$key" "$value" >>"$env_file"
	fi
}

if [[ "$install_target" == "hosted-web" ]]; then
	log "Applying hosted web safety defaults: local code tools disabled"
	set_env_kv DIGITAL_TWIN_DEPLOYMENT_MODE hosted
	set_env_kv DIGITAL_TWIN_APP_PROFILE faculty_twin
	set_env_kv DIGITAL_TWIN_CODE_WORKBENCH_ENABLED false
	set_env_kv DIGITAL_TWIN_CODE_WORKSPACE_ROOTS ""
fi

# ── 6. Systemd service units ─────────────────────────────────────────────────
# Renders templates from deploy/systemd/user/ and installs them.
# This was previously tools/install_user_services.sh — now inlined.

if $mode_no_systemd; then
	log "Skipping systemd install (--no-systemd)"
else
	source_dir="$repo_root/deploy/systemd/user"
	target_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
	user_runtime_dir="/run/user/$(id -u)"
	user_bus_path="$user_runtime_dir/bus"

	if [[ -z "${XDG_RUNTIME_DIR:-}" && -d "$user_runtime_dir" ]]; then
		export XDG_RUNTIME_DIR="$user_runtime_dir"
	fi
	if [[ -z "${DBUS_SESSION_BUS_ADDRESS:-}" && -S "$user_bus_path" ]]; then
		export DBUS_SESSION_BUS_ADDRESS="unix:path=$user_bus_path"
	fi

	# Resolve Python binary (prefer PYTHON_BIN env var, then python3 in PATH)
	resolve_python_bin() {
		if [[ -n "${PYTHON_BIN:-}" && -x "$PYTHON_BIN" ]]; then
			printf '%s\n' "$PYTHON_BIN"; return 0
		fi
		local conda_env_name="${CONDA_ENV_NAME:-vllm-hust-dev}"
		for candidate in \
			"$HOME/miniconda3/envs/$conda_env_name/bin/python3" \
			"$HOME/anaconda3/envs/$conda_env_name/bin/python3"; do
			if [[ -x "$candidate" ]]; then
				printf '%s\n' "$candidate"; return 0
			fi
		done
		printf '%s\n' "$python_bin"
	}
	render_python_bin=$(resolve_python_bin)
	log "Installing systemd --user units (python=$render_python_bin)"

	mkdir -p "$target_dir"

	# Render and install all .service and .timer templates
	for unit in "$source_dir"/*.service "$source_dir"/*.timer; do
		[[ -f "$unit" ]] || continue
		rendered="$target_dir/$(basename "$unit")"
		sed \
			-e "s|__REPO_ROOT__|$repo_root|g" \
			-e "s|__PYTHON_BIN__|$render_python_bin|g" \
			"$unit" >"$rendered"
		chmod 0644 "$rendered"
		log "  installed: $(basename "$unit")"
	done

	# Clean up legacy PYTHON_BIN override
	_override_dir="$target_dir/sage-faculty-twin-app.service.d"
	_override_file="$_override_dir/override.conf"
	if [[ -f "$_override_file" ]] && awk '
		/^[[:space:]]*$/ { next }
		/^\[Service\]$/ { next }
		/^Environment=PYTHON_BIN=/ { next }
		{ exit 1 }
	' "$_override_file"; then
		rm -f "$_override_file"
		rmdir "$_override_dir" 2>/dev/null || true
		log "  removed legacy PYTHON_BIN override"
	fi

	systemctl --user daemon-reload

	# Build service list
	service_units=(sage-faculty-twin-app.service)
	$svc_site   && service_units+=(sage-faculty-twin-site.service)
	$svc_tunnel && service_units+=(sage-faculty-twin-tunnel.service)
	$svc_proxy  && service_units+=(sage-faculty-twin-vllm-openai-proxy.service)
	$svc_engine && service_units+=(sage-faculty-twin-vllm-engine.service)

	systemctl --user enable "${service_units[@]}"
	log "  enabled: ${service_units[*]}"

	# Enable and start timers
	timer_units=(sage-faculty-twin-wiki-sync.timer sage-faculty-twin-inference-monitor.timer)
	systemctl --user enable "${timer_units[@]}"
	log "  enabled: ${timer_units[*]}"

	if $mode_start; then
		systemctl --user restart "${service_units[@]}" "${timer_units[@]}"
		systemctl --user --no-pager --full status "${service_units[@]}"
	fi
fi

# ── 7. Smoke test ────────────────────────────────────────────────────────────
app_port="${APP_PORT:-55601}"
if curl -sS --max-time 3 -o /dev/null -w '%{http_code}' "http://127.0.0.1:$app_port/" 2>/dev/null | grep -q '^200$'; then
	log "Smoke test: GET http://127.0.0.1:$app_port/ -> 200 OK"
else
	warn "App not yet listening on :$app_port — run: ./manage.sh restart, or ./quickstart.sh --start"
fi

# ── 8. Next steps ────────────────────────────────────────────────────────────
cat <<EOM

────────────────────────────────────────────────────────────
Next steps
────────────────────────────────────────────────────────────

1. Edit $env_file and set at minimum:
     DIGITAL_TWIN_OWNER_NAME, DIGITAL_TWIN_OWNER_ROLE
     DIGITAL_TWIN_LLM_BASE_URL  e.g. http://<vllm-host>:8080/v1
     DIGITAL_TWIN_API_KEY       e.g. change-me-please
     DIGITAL_TWIN_MODEL_NAME    e.g. qwen3-32b
     DIGITAL_TWIN_ADMIN_PASSWORD

2. The vLLM engine runs inside a Docker container.
   Make sure VLLM_ENGINE_CONTAINER is set in .env, then:
     ./manage.sh start --with-vllm-engine

3. Manage the stack:
     ./manage.sh status --all
     ./manage.sh start  --all
     ./manage.sh logs   app
     ./manage.sh logs   engine

4. Open http://127.0.0.1:$app_port/ in a browser to verify.

EOM

log "Done."
