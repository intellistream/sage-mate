#!/usr/bin/env bash
# Double-click friendly hosted/web installer.
#
# This wrapper provides GUI confirmations, progress updates, guarded NVIDIA
# driver upgrade, and reboot resume. The actual deployment still delegates to
# release/hosted-web.sh, quickstart.sh, manage.sh, and repo-managed helpers.

set -euo pipefail

script_path=$(readlink -f "${BASH_SOURCE[0]}")
script_dir=$(cd -- "$(dirname -- "$script_path")" && pwd -P)
state_dir="${XDG_STATE_HOME:-$HOME/.local/state}/sage-faculty-twin-installer"
state_file="$state_dir/state.sh"
log_file="$state_dir/install.log"
repo_dir="${FACULTY_TWIN_DIR:-$HOME/sage-faculty-twin}"
repo_url="${FACULTY_TWIN_REPO_URL:-git@github.com:intellistream/sage-faculty-twin.git}"
https_repo_url="${FACULTY_TWIN_HTTPS_REPO_URL:-https://github.com/intellistream/sage-faculty-twin.git}"
branch="${FACULTY_TWIN_BRANCH:-main}"
hosted_web_script="${FACULTY_TWIN_HOSTED_WEB_SCRIPT:-$script_dir/hosted-web.sh}"
release_url="${FACULTY_TWIN_RELEASE_URL:-https://github.com/intellistream/sage-faculty-twin/releases/download/v4.4.0}"
min_driver="${VLLM_NVIDIA_MIN_DRIVER_VERSION:-575.51.03}"
default_key_file="$HOME/.config/sage-faculty-twin/release-secrets.key"
resume=false
assume_yes=false
no_secrets_mode=false

mkdir -p "$state_dir"
touch "$log_file"
chmod 0600 "$log_file" || true

usage() {
    cat <<'EOF'
Usage: hosted-web-installer.sh [--resume] [--yes] [hosted-web.sh options...]

Double-click friendly installer for hosted/web Faculty Twin. It shows GUI
progress when zenity is available, upgrades NVIDIA drivers with confirmation,
sets up reboot resume, then runs hosted-web.sh.
EOF
}

installer_args=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --resume) resume=true; shift ;;
        --yes|-y) assume_yes=true; installer_args+=(--yes); shift ;;
        -h|--help) usage; exit 0 ;;
        *) installer_args+=("$1"); shift ;;
    esac
done

if ! printf '\n%s\n' "${installer_args[@]}" | grep -qx -- '--yes'; then
    installer_args+=(--yes)
fi

gui=false
if [[ -n "${DISPLAY:-}" ]] && command -v zenity >/dev/null 2>&1; then
    gui=true
fi

progress_pid=""
progress_fd=""

log() {
    printf '[installer] %s\n' "$*" | tee -a "$log_file" >&2
}

progress_start() {
    if $gui; then
        coproc PROGRESS_ZENITY {
            zenity --progress \
                --title="Faculty Twin Installer" \
                --text="Starting..." \
                --percentage=0 \
                --auto-close \
                --no-cancel
        }
        progress_fd="${PROGRESS_ZENITY[1]}"
        progress_pid="$PROGRESS_ZENITY_PID"
    fi
}

progress() {
    local pct="$1" message="$2"
    log "$pct% $message"
    if $gui && [[ -n "$progress_fd" ]]; then
        {
            printf '%s\n' "$pct"
            printf '# %s\n' "$message"
        } >&"$progress_fd" || true
    else
        printf '[%3s%%] %s\n' "$pct" "$message"
    fi
}

progress_finish() {
    if $gui && [[ -n "$progress_fd" ]]; then
        {
            printf '%s\n' "100"
            printf '# Installation complete.\n'
        } >&"$progress_fd" || true
        exec {progress_fd}>&- || true
        [[ -z "$progress_pid" ]] || wait "$progress_pid" 2>/dev/null || true
    fi
}

say_info() {
    local message="$1"
    log "$message"
    if $gui; then
        zenity --info --title="Faculty Twin Installer" --text="$message" || true
    else
        printf '%s\n' "$message"
    fi
}

choose() {
    local title="$1" text="$2"
    shift 2
    local choices=("$@")
    if $gui; then
        zenity --list \
            --title="$title" \
            --text="$text" \
            --column="Option" \
            "${choices[@]}"
    else
        local i answer
        printf '%s\n\n%s\n' "$title" "$text"
        for ((i = 0; i < ${#choices[@]}; i++)); do
            printf '  %d) %s\n' "$((i + 1))" "${choices[$i]}"
        done
        read -r -p "Choose [1-${#choices[@]}]: " answer
        [[ "$answer" =~ ^[0-9]+$ ]] || return 1
        (( answer >= 1 && answer <= ${#choices[@]} )) || return 1
        printf '%s\n' "${choices[$((answer - 1))]}"
    fi
}

confirm() {
    local message="$1"
    if $assume_yes; then
        log "auto-confirmed: $message"
        return 0
    fi
    if $gui; then
        zenity --question --title="Faculty Twin Installer" --text="$message"
    else
        read -r -p "$message [y/N] " answer
        [[ "$answer" =~ ^[Yy]$ ]]
    fi
}

fail() {
    local message="$1"
    log "ERROR: $message"
    if $gui; then
        zenity --error --title="Faculty Twin Installer" --text="$message"$'\n\n'"Log: $log_file" || true
    fi
    exit 1
}

version_ge() {
    local actual="$1" required="$2"
    if command -v dpkg >/dev/null 2>&1; then
        dpkg --compare-versions "$actual" ge "$required"
    else
        [[ "$(printf '%s\n%s\n' "$required" "$actual" | sort -V | head -n1)" == "$required" ]]
    fi
}

quote_args() {
    local arg
    for arg in "$@"; do
        printf '%q ' "$arg"
    done
}

save_state() {
    local step="$1"
    {
        printf 'INSTALLER_STEP=%q\n' "$step"
        printf 'INSTALLER_ARGS=( '
        quote_args "${installer_args[@]}"
        printf ')\n'
    } > "$state_file"
    chmod 0600 "$state_file"
}

clear_state() {
    rm -f "$state_file"
    rm -f "${XDG_CONFIG_HOME:-$HOME/.config}/autostart/sage-faculty-twin-installer.desktop"
}

install_autostart_resume() {
    local autostart_dir="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"
    mkdir -p "$autostart_dir"
    cat > "$autostart_dir/sage-faculty-twin-installer.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Faculty Twin Installer Resume
Exec=$script_path --resume
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
}

load_resume_args() {
    if $resume && [[ -f "$state_file" ]]; then
        # shellcheck disable=SC1090
        source "$state_file"
        if declare -p INSTALLER_ARGS >/dev/null 2>&1 && ((${#INSTALLER_ARGS[@]} > 0)); then
            installer_args=("${INSTALLER_ARGS[@]}")
        fi
    fi
}

has_arg() {
    local needle="$1" arg
    for arg in "${installer_args[@]}"; do
        [[ "$arg" == "$needle" ]] && return 0
    done
    return 1
}

append_arg_once() {
    local arg="$1"
    has_arg "$arg" || installer_args+=("$arg")
}

ensure_release_key_or_choose_mode() {
    [[ -n "${FACULTY_TWIN_SECRETS_KEY_FILE:-}" || -n "${FACULTY_TWIN_SECRETS_PASSPHRASE:-}" ]] && return 0
    if [[ -f "$default_key_file" ]]; then
        export FACULTY_TWIN_SECRETS_KEY_FILE="$default_key_file"
        log "using release secrets key file at default path"
        return 0
    fi

    local enc_file="${FACULTY_TWIN_ENCRYPTED_SECRETS_FILE:-$script_dir/secrets.env.enc}"
    [[ -f "$enc_file" ]] || return 0

    if $assume_yes; then
        no_secrets_mode=true
        append_arg_once --no-secrets
        append_arg_once --no-tunnel
        log "release key missing; continuing without encrypted secrets or tunnel because --yes was used"
        return 0
    fi

    local choice
    choice=$(choose \
        "Faculty Twin Release Key" \
        "This package includes encrypted deployment secrets, but no release key was found at:\n\n$default_key_file\n\nInternal one-click deployment needs that key. Without it, the installer can still set up a local hosted/web service, but private GitHub, Hugging Face, Cloudflare tunnel, and app keys must be configured separately." \
        "I placed the key; check again" \
        "Continue local install without encrypted secrets" \
        "Exit") || fail "No release key option was selected."

    case "$choice" in
        "I placed the key; check again")
            if [[ -f "$default_key_file" ]]; then
                export FACULTY_TWIN_SECRETS_KEY_FILE="$default_key_file"
                return 0
            fi
            fail "Release key still not found: $default_key_file"
            ;;
        "Continue local install without encrypted secrets")
            no_secrets_mode=true
            append_arg_once --no-secrets
            append_arg_once --no-tunnel
            say_info "Continuing without encrypted secrets.\n\nThe installer will not configure Cloudflare tunnel or private tokens automatically. Local service install will continue where possible."
            ;;
        *)
            fail "Installation cancelled before secrets were configured."
            ;;
    esac
}

install_summary() {
    local mode="internal deployment with encrypted secrets"
    if $no_secrets_mode || has_arg --no-secrets; then
        mode="local install without encrypted secrets"
    fi
    local tunnel="enabled when credentials are available"
    has_arg --no-tunnel && tunnel="disabled"
    printf 'Mode: %s\nRepo dir: %s\nTunnel: %s\nLog: %s\n' "$mode" "$repo_dir" "$tunnel" "$log_file"
}

confirm_install_summary() {
    local summary
    summary=$(install_summary)
    if $assume_yes; then
        log "install summary: ${summary//$'\n'/; }"
        return 0
    fi
    confirm "Ready to install Faculty Twin hosted/web.\n\n$summary\n\nContinue?" || fail "Installation cancelled."
}

decrypt_initial_secrets() {
    local enc_file="${FACULTY_TWIN_ENCRYPTED_SECRETS_FILE:-$script_dir/secrets.env.enc}"
    local key_file="${FACULTY_TWIN_SECRETS_KEY_FILE:-}"
    local tmp_file pass_args=()
    [[ -f "$enc_file" ]] || return 0
    command -v openssl >/dev/null 2>&1 || return 0
    if [[ -n "$key_file" && -f "$key_file" ]]; then
        pass_args=(-pass "file:$key_file")
    elif [[ -n "${FACULTY_TWIN_SECRETS_PASSPHRASE:-}" ]]; then
        pass_args=(-pass "env:FACULTY_TWIN_SECRETS_PASSPHRASE")
    else
        return 0
    fi
    tmp_file=$(mktemp)
    chmod 0600 "$tmp_file"
    if ! openssl enc -d -aes-256-cbc -pbkdf2 -in "$enc_file" -out "$tmp_file" "${pass_args[@]}" 2>>"$log_file"; then
        rm -f "$tmp_file"
        return 0
    fi
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# || "$line" != *"="* ]] && continue
        local key="${line%%=*}" value="${line#*=}"
        key="${key// /}"
        [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
        case "$key" in
            GITHUB_TOKEN|GH_TOKEN|HF_TOKEN|HUGGING_FACE_HUB_TOKEN|CLOUDFLARE_API_TOKEN|CLOUDFLARE_GLOBAL_API_KEY)
                [[ -n "${!key:-}" ]] || export "$key=$value"
                ;;
        esac
    done < "$tmp_file"
    rm -f "$tmp_file"
}

git_auth() {
    local askpass=""
    if [[ -n "${GITHUB_TOKEN:-${GH_TOKEN:-}}" ]]; then
        askpass=$(mktemp)
        chmod 0700 "$askpass"
        cat > "$askpass" <<'EOF'
#!/usr/bin/env bash
case "$1" in
    *Username*) printf '%s\n' "${GITHUB_USER:-x-access-token}" ;;
    *Password*) printf '%s\n' "${GITHUB_TOKEN:-${GH_TOKEN:-}}" ;;
    *) printf '\n' ;;
esac
EOF
        env GIT_ASKPASS="$askpass" GIT_TERMINAL_PROMPT=0 git "$@"
        local status=$?
        rm -f "$askpass"
        return "$status"
    fi
    git "$@"
}

ensure_repo_for_driver_helper() {
    decrypt_initial_secrets
    command -v git >/dev/null 2>&1 || fail "git is required before driver upgrade."
    if [[ ! -d "$repo_dir/.git" ]]; then
        progress 12 "Downloading installer helpers..."
        git_auth clone "$repo_url" "$repo_dir" >>"$log_file" 2>&1 || \
            git_auth clone "$https_repo_url" "$repo_dir" >>"$log_file" 2>&1
    fi
    (
        cd "$repo_dir"
        git_auth fetch origin >>"$log_file" 2>&1
        git checkout "$branch" >>"$log_file" 2>&1
        git_auth pull --ff-only origin "$branch" >>"$log_file" 2>&1
    )
}

download_hosted_web_script() {
    if [[ -x "$hosted_web_script" || -f "$hosted_web_script" ]]; then
        chmod +x "$hosted_web_script" || true
        return 0
    fi
    command -v curl >/dev/null 2>&1 || fail "curl is required to download hosted-web.sh."
    progress 8 "Downloading hosted-web.sh..."
    curl -fsSL "$release_url/hosted-web.sh" -o "$hosted_web_script"
    chmod +x "$hosted_web_script"
}

accelerator_arg_is_ascend() {
    local i
    for ((i = 0; i < ${#installer_args[@]}; i++)); do
        if [[ "${installer_args[$i]}" == "--accelerator" && "${installer_args[$((i+1))]:-}" == "ascend" ]]; then
            return 0
        fi
    done
    return 1
}

nvidia_driver_needs_upgrade() {
    accelerator_arg_is_ascend && return 1
    command -v nvidia-smi >/dev/null 2>&1 || return 1
    local current
    current=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null | head -n1 | tr -d '[:space:]' || true)
    [[ -n "$current" ]] || return 1
    ! version_ge "$current" "$min_driver"
}

maybe_upgrade_nvidia_driver() {
    nvidia_driver_needs_upgrade || return 0
    local current
    current=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -n1 | tr -d '[:space:]')
    progress 15 "NVIDIA driver upgrade required."
    confirm "NVIDIA driver $current is too old. Faculty Twin needs at least $min_driver for pinned vLLM. Install the driver upgrade now?" || \
        fail "Driver upgrade was declined."
    ensure_repo_for_driver_helper
    [[ -x "$repo_dir/tools/upgrade_nvidia_driver_for_vllm.sh" ]] || fail "Driver upgrade helper was not found in $repo_dir."
    progress 20 "Installing NVIDIA driver upgrade..."
    (cd "$repo_dir" && tools/upgrade_nvidia_driver_for_vllm.sh --yes) >>"$log_file" 2>&1
    save_state "after-driver-upgrade"
    install_autostart_resume
    progress 30 "Driver upgrade installed. Reboot is required."
    confirm "Driver upgrade is installed. Reboot now and continue installation automatically after login?" || \
        fail "Reboot is required before installation can continue."
    sudo reboot
    exit 0
}

run_hosted_web_install() {
    download_hosted_web_script
    save_state "installing"
    progress 35 "Installing Faculty Twin hosted/web. This can take a while..."
    FACULTY_TWIN_ENCRYPTED_SECRETS_FILE="${FACULTY_TWIN_ENCRYPTED_SECRETS_FILE:-$script_dir/secrets.env.enc}" \
        bash "$hosted_web_script" "${installer_args[@]}" >>"$log_file" 2>&1
    progress 92 "Running final hosted/web verification..."
    if [[ -x "$repo_dir/manage.sh" ]]; then
        (cd "$repo_dir" && ./manage.sh verify-hosted-web) >>"$log_file" 2>&1 || fail "Hosted/web verification failed. See $log_file"
    fi
}

main() {
    load_resume_args
    progress_start
    progress 3 "Checking machine..."
    ensure_release_key_or_choose_mode
    confirm_install_summary
    maybe_upgrade_nvidia_driver
    run_hosted_web_install
    clear_state
    progress 100 "Faculty Twin hosted/web installation complete."
    progress_finish
    say_info "Faculty Twin hosted/web is installed.\n\nOpen: http://127.0.0.1:55601/\n\nLog: $log_file"
}

main "$@"
