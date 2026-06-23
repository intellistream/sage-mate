#!/usr/bin/env bash
# sync_wiki_kb.sh — Pull latest sage-wiki and re-ingest into KB.
#
# Designed to run from a systemd timer or cron. Idempotent: safe to run
# even if wiki has not changed (ingest_wiki.py upserts).
#
# Usage:
#   bash tools/sync_wiki_kb.sh [--wiki-dir /home/shuhao/sage-wiki]

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WIKI_DIR="${1:-/home/shuhao/sage-wiki}"

load_dotenv() {
    if [[ -f "$REPO_ROOT/.env" ]]; then
        while IFS= read -r line || [[ -n "$line" ]]; do
            [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
            key="${line%%=*}"
            key="${key// /}"
            [[ -z "$key" || -n "${!key:-}" ]] && continue
            export "$line"
        done < "$REPO_ROOT/.env"
    fi
}

load_dotenv

RUNTIME_ROOT="${DIGITAL_TWIN_RUNTIME_DIR:-$REPO_ROOT/../sage-faculty-twin-runtime-private}"
LOG_DIR="${RUNTIME_ROOT}/logs"
LOG_FILE="${LOG_DIR}/wiki_sync_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "=== Wiki KB Sync Start ==="
log "Wiki dir: ${WIKI_DIR}"

# ── Step 1: Pull latest wiki ────────────────────────────────────────────
if [ -d "${WIKI_DIR}/.git" ]; then
    log "Pulling latest sage-wiki..."
    cd "$WIKI_DIR"
    BEFORE=$(git rev-parse HEAD)
    git pull --ff-only origin master 2>&1 | tee -a "$LOG_FILE" || {
        log "WARN: git pull failed, using local copy"
    }
    AFTER=$(git rev-parse HEAD)
    if [ "$BEFORE" = "$AFTER" ]; then
        log "Wiki unchanged (HEAD=${BEFORE:0:8}), skipping ingest"
        log "=== Wiki KB Sync Done (no changes) ==="
        exit 0
    fi
    log "Wiki updated: ${BEFORE:0:8} → ${AFTER:0:8}"
    cd "$REPO_ROOT"
else
    log "WARN: ${WIKI_DIR} is not a git repo, using as-is"
fi

# ── Step 2: Run ingest ──────────────────────────────────────────────────
log "Running ingest_wiki.py..."
cd "$REPO_ROOT"
PYTHONPATH=src python tools/ingest_wiki.py --wiki-dir "$WIKI_DIR" 2>&1 | tee -a "$LOG_FILE"

# ── Step 3: Verify ──────────────────────────────────────────────────────
log "=== Wiki KB Sync Complete ==="

# Clean up old logs (keep last 30)
ls -t "${LOG_DIR}"/wiki_sync_*.log 2>/dev/null | tail -n +31 | xargs -r rm -f

exit 0
