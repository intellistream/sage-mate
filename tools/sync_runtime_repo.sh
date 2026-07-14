#!/usr/bin/env bash
# Clone or fast-forward a private runtime-data repository without exposing tokens.

set -euo pipefail

runtime_dir=""
repo_url=""
branch="main"
required="false"
env_file=""

log() { printf '[runtime-repo] %s\n' "$*"; }
warn() { printf '[runtime-repo] WARNING: %s\n' "$*" >&2; }
fail() { printf '[runtime-repo] ERROR: %s\n' "$*" >&2; exit 1; }

usage() {
    cat <<'EOF'
Usage: tools/sync_runtime_repo.sh --runtime-dir PATH --repo-url URL [options]

Options:
  --branch NAME      Runtime repository branch. Defaults to main.
  --env-file PATH    Read GITHUB_TOKEN or GH_TOKEN from this env file.
  --required         Fail instead of falling back when synchronization fails.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --runtime-dir) runtime_dir="${2:?--runtime-dir requires a value}"; shift 2 ;;
        --repo-url) repo_url="${2:?--repo-url requires a value}"; shift 2 ;;
        --branch) branch="${2:?--branch requires a value}"; shift 2 ;;
        --env-file) env_file="${2:?--env-file requires a value}"; shift 2 ;;
        --required) required="true"; shift ;;
        -h|--help) usage; exit 0 ;;
        *) fail "unknown argument: $1" ;;
    esac
done

[[ -n "$runtime_dir" ]] || fail "--runtime-dir is required"
[[ -n "$repo_url" ]] || exit 0
command -v git >/dev/null 2>&1 || fail "git is required"

read_env_value() {
    local key="$1"
    [[ -f "$env_file" ]] || return 0
    awk -v wanted="$key" '
        index($0, wanted "=") == 1 {
            sub(/^[^=]*=/, "")
            print
            exit
        }
    ' "$env_file"
}

github_token="${GITHUB_TOKEN:-${GH_TOKEN:-}}"
if [[ -z "$github_token" ]]; then
    github_token="$(read_env_value GITHUB_TOKEN)"
fi
if [[ -z "$github_token" ]]; then
    github_token="$(read_env_value GH_TOKEN)"
fi

askpass=""
staging_root=""
cleanup() {
    [[ -z "$askpass" ]] || rm -f "$askpass"
    [[ -z "$staging_root" || ! -d "$staging_root" ]] || rm -rf "$staging_root"
}
trap cleanup EXIT

if [[ -n "$github_token" && "$repo_url" == https://github.com/* ]]; then
    askpass=$(mktemp)
    chmod 0700 "$askpass"
    cat >"$askpass" <<'EOF'
#!/usr/bin/env bash
case "$1" in
    *Username*) printf '%s\n' x-access-token ;;
    *Password*) printf '%s\n' "${RUNTIME_REPO_GITHUB_TOKEN:-}" ;;
    *) printf '\n' ;;
esac
EOF
fi

git_auth() {
    if [[ -n "$askpass" ]]; then
        RUNTIME_REPO_GITHUB_TOKEN="$github_token" GIT_ASKPASS="$askpass" \
            GIT_CONFIG_GLOBAL=/dev/null GIT_TERMINAL_PROMPT=0 git "$@"
    else
        GIT_TERMINAL_PROMPT=0 git "$@"
    fi
}

sync_failed() {
    if [[ "$required" == "true" ]]; then
        fail "$1"
    fi
    warn "$1; continuing with local runtime data"
    exit 0
}

runtime_dir="${runtime_dir/#\~/$HOME}"
mkdir -p "$(dirname "$runtime_dir")"

if [[ -d "$runtime_dir/.git" ]]; then
    if [[ -n "$(git -C "$runtime_dir" status --short --untracked-files=no)" ]]; then
        sync_failed "runtime repository has local tracked changes: $runtime_dir"
    fi
    log "Updating runtime repository"
    git_auth -C "$runtime_dir" fetch origin "$branch" || sync_failed "could not fetch runtime repository"
    git -C "$runtime_dir" merge --ff-only FETCH_HEAD || sync_failed "runtime repository is not fast-forwardable"
    exit 0
fi

staging_root=$(mktemp -d "$(dirname "$runtime_dir")/.runtime-repo-clone.XXXXXX")
staging_repo="$staging_root/repo"
if ! git_auth clone --depth=1 --branch "$branch" "$repo_url" "$staging_repo"; then
    rm -rf "$staging_root"
    sync_failed "could not clone configured runtime repository"
fi

backup_dir=""
if [[ -e "$runtime_dir" ]]; then
    backup_dir="${runtime_dir}.pre-repo-$(date +%Y%m%d-%H%M%S)"
    mv "$runtime_dir" "$backup_dir"
fi
mv "$staging_repo" "$runtime_dir"
rmdir "$staging_root"
staging_root=""
chmod 0700 "$runtime_dir"

if [[ -n "$backup_dir" ]]; then
    cp -a -n "$backup_dir"/. "$runtime_dir"/
    for local_runtime_dir in cloudflared .runtime logs downloads; do
        [[ -d "$backup_dir/$local_runtime_dir" ]] || continue
        mkdir -p "$runtime_dir/$local_runtime_dir"
        cp -a "$backup_dir/$local_runtime_dir"/. "$runtime_dir/$local_runtime_dir"/
    done
    log "Preserved previous runtime files in $backup_dir and merged local-only files"
fi
log "Runtime repository ready: $runtime_dir"
