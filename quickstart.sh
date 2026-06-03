#!/usr/bin/env bash
# quickstart.sh — one-touch deployment for sage-faculty-twin (+ vllm-hust dep)
#
# Goals:
#   - Bring a fresh Linux machine from "git clone" to "running app on :55601"
#   - Idempotent: safe to re-run; existing config / deps are preserved.
#   - Captures lessons learned from the chat-latency/streaming rollout:
#       * .env must be exported into the process env BEFORE uvicorn launches,
#         otherwise module-level os.environ.get(...) calls (streaming flag,
#         timeouts, SSE keepalive) silently fall back to defaults.
#       * If an OpenAI-compatible *router* sits between faculty-twin and vllm,
#         it MUST emit Transfer-Encoding: chunked or token streaming will be
#         buffered into a single end-of-generation flush. Point
#         DIGITAL_TWIN_LLM_BASE_URL directly at vllm-hust unless your router
#         is known to forward chunked SSE.
#
# Usage:
#   ./quickstart.sh                  # default: install env, deps, .env, systemd
#   ./quickstart.sh --check          # preflight only — diagnose, do not change
#   ./quickstart.sh --with-vllm      # also install vllm-hust (editable) + clone
#   ./quickstart.sh --no-systemd     # skip systemd unit install (foreground use)
#   ./quickstart.sh --start          # start systemd services after install
#   ./quickstart.sh --yes            # non-interactive (assume yes for prompts)
#
# Environment overrides (read at script start):
#   PYTHON_BIN                       Path to interpreter; defaults to python3 in PATH
#   CONDA_ENV_NAME                   Conda env to use/create (default: vllm-hust-dev)
#   FACULTY_TWIN_PARENT_DIR          Where SAGE/sageVDB/neuromem/vllm-hust live
#                                    (default: parent of this repo)
#   APP_PORT                         App listen port (default: 55601)
#
# This script will NOT:
#   - Download or launch any LLM model — vllm-hust serving is GPU/disk-heavy
#     and machine-specific. It prints the recommended `vllm serve ...` command
#     and leaves model lifecycle to the operator.
#   - Touch git history.
#   - Edit .env if it already contains a value (only fills in missing keys).

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
parent_dir="${FACULTY_TWIN_PARENT_DIR:-$(dirname "$repo_root")}"

mode_check=false
mode_with_vllm=false
mode_no_systemd=false
mode_start=false
mode_yes=false

for arg in "$@"; do
	case "$arg" in
	--check) mode_check=true ;;
	--with-vllm) mode_with_vllm=true ;;
	--no-systemd) mode_no_systemd=true ;;
	--start) mode_start=true ;;
	--yes | -y) mode_yes=true ;;
	-h | --help)
		sed -n '1,40p' "$0"
		exit 0
		;;
	*)
		echo "Unknown argument: $arg" >&2
		exit 2
		;;
	esac
done

log() { printf '\033[1;36m[quickstart]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[quickstart]\033[0m %s\n' "$*" >&2; }
fail() {
	printf '\033[1;31m[quickstart]\033[0m %s\n' "$*" >&2
	exit 1
}
confirm() {
	$mode_yes && return 0
	read -r -p "$1 [y/N] " ans
	[[ "$ans" =~ ^[Yy]$ ]]
}

############################################################
# 1. Preflight — must-haves
############################################################
log "Preflight: $repo_root"
command -v git >/dev/null 2>&1 || fail "git not found"

if [[ -n "${PYTHON_BIN:-}" ]]; then
	python_bin="$PYTHON_BIN"
elif command -v python3 >/dev/null 2>&1; then
	python_bin=$(command -v python3)
else
	fail "python3 not found; set PYTHON_BIN or install Python 3.10+"
fi

py_ver=$("$python_bin" -c 'import sys; print("%d.%d"%sys.version_info[:2])')
log "  python: $python_bin ($py_ver)"
case "$py_ver" in 3.1[0-9] | 3.[2-9][0-9]) ;;
*) warn "  expected Python >=3.10, got $py_ver" ;;
esac

if command -v nvidia-smi >/dev/null 2>&1; then
	gpu_count=$(nvidia-smi -L 2>/dev/null | wc -l)
	log "  nvidia-smi: $gpu_count GPU(s)"
else
	warn "  nvidia-smi not found — vllm-hust will need a host with NVIDIA drivers"
fi

if [[ ! -f "$repo_root/pyproject.toml" ]]; then
	fail "pyproject.toml missing — run quickstart from the repo root"
fi

if $mode_check; then
	log "Preflight only (--check). Done."
	exit 0
fi

############################################################
# 2. Sibling repositories (SAGE, neuromem, sageVDB; optional vllm-hust)
############################################################
mkdir -p "$parent_dir"
clone_if_missing() {
	local name="$1" url="$2"
	if [[ ! -d "$parent_dir/$name" ]]; then
		log "Cloning $name into $parent_dir"
		git clone --depth=1 "$url" "$parent_dir/$name"
	else
		log "  sibling repo present: $parent_dir/$name"
	fi
}

clone_if_missing SAGE https://github.com/intellistream/SAGE.git
clone_if_missing neuromem https://github.com/intellistream/neuromem.git
clone_if_missing sageVDB https://github.com/intellistream/sageVDB.git
$mode_with_vllm && clone_if_missing vllm-hust https://github.com/intellistream/vllm-hust.git

############################################################
# 3. Python deps
############################################################
log "Installing faculty-twin in editable mode"
"$python_bin" -m pip install --quiet --upgrade pip
"$python_bin" -m pip install --quiet -e "$repo_root"

# vllm-hust (only on request — heavy build)
if $mode_with_vllm; then
	if [[ -d "$parent_dir/vllm-hust" ]]; then
		log "Installing vllm-hust (editable, may take several minutes)"
		"$python_bin" -m pip install --quiet -e "$parent_dir/vllm-hust" \
			|| warn "vllm-hust install failed; build deps (CUDA, ninja) may be missing"
	fi
fi

############################################################
# 4. .env bootstrap
############################################################
env_file="$repo_root/.env"
template="$repo_root/.env.example"
if [[ ! -f "$env_file" ]]; then
	log "Creating .env from .env.example"
	cp "$template" "$env_file"
	warn "  Edit $env_file before serving real users:"
	warn "    DIGITAL_TWIN_OWNER_NAME / OWNER_ROLE — public identity"
	warn "    DIGITAL_TWIN_LLM_BASE_URL / API_KEY  — point at vllm-hust DIRECTLY"
	warn "                                           (avoid HTTP/1.0 routers)"
	warn "    DIGITAL_TWIN_ADMIN_PASSWORD          — admin login"
fi

# Ensure the latency-related flags exist; only append if absent (never overwrite).
ensure_env_kv() {
	local key="$1" default="$2"
	grep -qE "^[[:space:]]*${key}=" "$env_file" 2>/dev/null && return
	printf '%s=%s\n' "$key" "$default" >>"$env_file"
	log "  appended $key=$default"
}
ensure_env_kv DIGITAL_TWIN_STREAM_CHAT_ANSWER false
ensure_env_kv DIGITAL_TWIN_CHAT_REQUEST_TIMEOUT_SECONDS 80
ensure_env_kv DIGITAL_TWIN_LLM_TIMEOUT_SECONDS 60
ensure_env_kv DIGITAL_TWIN_CHAT_SSE_KEEPALIVE_SECONDS 15
ensure_env_kv DIGITAL_TWIN_CHAT_PROMPT_SOFT_CAP_CHARS 12000

############################################################
# 5. systemd user units
############################################################
if $mode_no_systemd; then
	log "Skipping systemd install (--no-systemd)"
else
	log "Installing systemd --user units (app/site/tunnel)"
	if $mode_start; then
		PYTHON_BIN="$python_bin" "$repo_root/tools/install_user_services.sh" --start
	else
		PYTHON_BIN="$python_bin" "$repo_root/tools/install_user_services.sh"
	fi
fi

############################################################
# 6. Smoke test (only if app is running)
############################################################
app_port="${APP_PORT:-55601}"
if curl -sS --max-time 3 -o /dev/null -w '%{http_code}' "http://127.0.0.1:$app_port/" 2>/dev/null | grep -q '^200$'; then
	log "Smoke test: GET http://127.0.0.1:$app_port/ -> 200 OK"
else
	warn "App not yet listening on :$app_port — run: ./manage.sh restart, or ./quickstart.sh --start"
fi

############################################################
# 7. Next steps
############################################################
cat <<EOM

────────────────────────────────────────────────────────────
Next steps
────────────────────────────────────────────────────────────

1. Edit $env_file and set at minimum:
     DIGITAL_TWIN_OWNER_NAME, DIGITAL_TWIN_OWNER_ROLE
     DIGITAL_TWIN_LLM_BASE_URL  e.g. http://<vllm-host>:8080/v1
     DIGITAL_TWIN_API_KEY       e.g. change-me-please
     DIGITAL_TWIN_MODEL_NAME    e.g. qwen32b
     DIGITAL_TWIN_ADMIN_PASSWORD

2. (Optional) launch vllm-hust on the same host. Recommended baseline for a
   24 GB GPU running an Int8 quantized 32B Qwen:

     vllm serve Qwen/Qwen2.5-32B-Instruct-GPTQ-Int8 \\
         --served-model-name qwen32b --host 0.0.0.0 --port 8080 \\
         --quantization gptq --dtype float16 --tensor-parallel-size 1 \\
         --max-model-len 4096 --gpu-memory-utilization 0.90 \\
         --max-num-seqs 2 --max-num-batched-tokens 4096 \\
         --enforce-eager --api-key change-me-please

   Confirm streaming works END-TO-END before wiring DIGITAL_TWIN_STREAM_CHAT_ANSWER=true:
     curl -N -H 'Authorization: Bearer change-me-please' \\
          -H 'Content-Type: application/json' \\
          --data '{"model":"qwen32b","stream":true,"max_tokens":50,
                   "messages":[{"role":"user","content":"hi"}]}' \\
          http://<vllm-host>:8080/v1/chat/completions
   The response MUST include "Transfer-Encoding: chunked".

3. Manage the service:
     ./manage.sh status            # show all three services
     ./manage.sh start | stop | restart
     journalctl --user -u sage-faculty-twin-app.service -f

4. Open http://127.0.0.1:$app_port/ in a browser to verify.

EOM

log "Done."
