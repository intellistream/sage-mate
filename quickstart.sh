#!/usr/bin/env bash
# quickstart.sh — single entry point for sage-faculty-twin installation.
#
# Usage:
#   ./quickstart.sh                      # install env, deps, systemd units
#   ./quickstart.sh --check              # preflight only — diagnose, do not change
#   ./quickstart.sh --with-vllm          # also install vllm-hust (editable)
#   ./quickstart.sh --with-vllm-engine   # enable vLLM engine systemd service
#   ./quickstart.sh --with-vllm-proxy    # enable vLLM OpenAI auth proxy service
#   ./quickstart.sh --with-site-proxy    # enable local nginx/python proxy service
#   ./quickstart.sh --with-tunnel        # enable Cloudflare tunnel service
#   ./quickstart.sh --start              # start systemd services after install
#   ./quickstart.sh --no-systemd         # skip systemd unit install
#   ./quickstart.sh --yes                # non-interactive (assume yes)
#
# Environment overrides:
#   PYTHON_BIN        Path to interpreter (default: python3 in PATH)
#   CONDA_ENV_NAME    Conda env to use/create (default: vllm-hust-dev)
#   APP_PORT          App listen port (default: 55601)
#
# This script will NOT:
#   - Download or launch any LLM model — use manage.sh for runtime operations.
#   - Touch git history.
#   - Edit .env if it already contains a value (only fills in missing keys).

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
parent_dir="${FACULTY_TWIN_PARENT_DIR:-$(dirname "$repo_root")}"

# ── CLI flags ────────────────────────────────────────────────────────────────
mode_check=false
mode_with_vllm=false
mode_no_systemd=false
mode_no_siblings=false
mode_start=false
mode_yes=false
svc_engine=false
svc_proxy=false
svc_site=false
svc_tunnel=false

for arg in "$@"; do
	case "$arg" in
	--check)          mode_check=true ;;
	--with-vllm)      mode_with_vllm=true ;;
	--with-vllm-engine) svc_engine=true ;;
	--with-vllm-proxy)  svc_proxy=true ;;
	--with-site-proxy)  svc_site=true ;;
	--with-tunnel)      svc_tunnel=true ;;
	--no-systemd)     mode_no_systemd=true ;;
	--no-siblings)    mode_no_siblings=true ;;
	--start)          mode_start=true ;;
	--yes | -y)       mode_yes=true ;;
	-h | --help)      sed -n '2,32p' "$0"; exit 0 ;;
	*) echo "Unknown argument: $arg" >&2; exit 2 ;;
	esac
done

log()  { printf '\033[1;36m[quickstart]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[quickstart]\033[0m %s\n' "$*" >&2; }
fail() { printf '\033[1;31m[quickstart]\033[0m %s\n' "$*" >&2; exit 1; }
confirm() { $mode_yes && return 0; read -r -p "$1 [y/N] " ans; [[ "$ans" =~ ^[Yy]$ ]]; }

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

if command -v nvidia-smi >/dev/null 2>&1; then
	gpu_count=$(nvidia-smi -L 2>/dev/null | wc -l)
	log "  nvidia-smi: $gpu_count GPU(s)"
else
	warn "  nvidia-smi not found — vllm-hust will need a host with NVIDIA/Ascend drivers"
fi

$mode_check && { log "Preflight only (--check). Done."; exit 0; }

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
log "Installing sage-faculty-twin (editable, with vdb-anns extras)"
"$python_bin" -m pip install --quiet --upgrade pip
if ! "$python_bin" -m pip install --quiet -e "$repo_root[vdb-anns]"; then
	warn "vdb-anns extras failed (C extensions may need CANN/C++ toolchain)"
	warn "Falling back to base install"
	"$python_bin" -m pip install --quiet -e "$repo_root"
fi

if $mode_with_vllm && [[ -d "$parent_dir/vllm-hust" ]]; then
	log "Installing vllm-hust (editable, may take several minutes)"
	"$python_bin" -m pip install --quiet -e "$parent_dir/vllm-hust" \
		|| warn "vllm-hust install failed; build deps (CUDA/ninja, Ascend toolkit) may be missing"
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
	timer_units=(sage-faculty-twin-wiki-sync.timer)
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
