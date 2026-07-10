#!/usr/bin/env bash
# Copy mutable runtime data out of the code repository into the private
# runtime-data checkout used by DIGITAL_TWIN_RUNTIME_DIR.

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
runtime_root="${DIGITAL_TWIN_RUNTIME_DIR:-$repo_root/../sage-mate-runtime-private}"
mode="copy"
init_git=false

usage() {
    cat >&2 <<'EOF'
Usage: tools/migrate_runtime_data.sh [--runtime-dir PATH] [--move] [--init-git]

Default behavior copies data/, logs/, and .runtime/ into the runtime repo and
leaves the original files in place. Use --move only after the app has been
validated against the runtime repo.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --runtime-dir)
            runtime_root="${2:-}"
            [[ -n "$runtime_root" ]] || { usage; exit 2; }
            shift 2
            ;;
        --move)
            mode="move"
            shift
            ;;
        --init-git)
            init_git=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            usage
            exit 2
            ;;
    esac
done

mkdir -p "$runtime_root"

copy_tree() {
    local source="$1"
    local target="$2"
    [[ -e "$source" ]] || return 0
    mkdir -p "$(dirname "$target")"
    if command -v rsync >/dev/null 2>&1; then
        rsync -a "$source"/ "$target"/
    else
        mkdir -p "$target"
        cp -a "$source"/. "$target"/
    fi
    if [[ "$mode" == "move" ]]; then
        rm -rf "$source"
    fi
}

copy_tree "$repo_root/data" "$runtime_root/data"
copy_tree "$repo_root/logs" "$runtime_root/logs"
copy_tree "$repo_root/.runtime" "$runtime_root/.runtime"

mkdir -p \
    "$runtime_root/data/knowledge_base" \
    "$runtime_root/data/conversation_memory" \
    "$runtime_root/data/user_accounts" \
    "$runtime_root/data/slack_user_links" \
    "$runtime_root/data/alerts" \
    "$runtime_root/logs"

if [[ ! -f "$runtime_root/.gitignore" ]]; then
    cat > "$runtime_root/.gitignore" <<'EOF'
# Keep transient process output out of the runtime-data git history.
logs/
.runtime/
secrets/
*.log
*.tmp
*.bak
*.backup
*.sqlite3-wal
*.sqlite3-shm
*.db-wal
*.db-shm
__pycache__/
.DS_Store

# Conversation memory can contain student/private data. Keep the durable
# private repo as the storage root, but do not commit live sqlite state unless
# explicitly reviewed and force-added.
data/conversation_memory/*.sqlite3
data/conversation_memory/**/*.sqlite3
data/conversation_memory/*.db
data/conversation_memory/**/*.db
EOF
fi

if $init_git && [[ ! -d "$runtime_root/.git" ]]; then
    git -C "$runtime_root" init
fi

echo "[migrate-runtime] repo_root=$repo_root"
echo "[migrate-runtime] runtime_root=$runtime_root"
echo "[migrate-runtime] mode=$mode"
echo "[migrate-runtime] done"
