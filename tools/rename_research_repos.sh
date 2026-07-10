#!/usr/bin/env bash
# rename_research_repos.sh — Unify research/paper repos under research- prefix.
#
# All repos that produce papers, benchmarks, or research artifacts
# are renamed to use the "research-" prefix.
#
# Usage:  bash /home/shuhao/sage-mate/tools/rename_research_repos.sh
# Requires write access to /home/shuhao/

set -euo pipefail
cd /home/shuhao

# ── Research repos (produce papers/benchmarks) ──────────────────────────────
RENAMES=(
    "wiki-link-retrieval:research-wiki-link-retrieval"
    "agent-kv-system:research-agent-kv-system"
    "bidkv:research-bidkv"
    "CANDOR-Bench:research-candor-bench"
    "kv-materialization-plugin:research-kv-materialization-plugin"
    "llm-serving-motto-lab:research-llm-serving-motto-lab"
    "quality-bounded-inference-plugin:research-quality-bounded-inference-plugin"
    "sage-temporal-memory:research-sage-temporal-memory"
    "sglang-request-placement:research-sglang-request-placement"
    "vllm-kvdelta-plugin:research-vllm-kvdelta-plugin"
    "vllm-segment-reuse:research-vllm-segment-reuse"
    "StreamFP:research-streamfp"
    "FlowRAG:research-flowrag"
    "neuromem-bench:research-neuromem-bench"
)

echo "=== Research Repo Rename ==="
echo "Will rename ${#RENAMES[@]} repos under /home/shuhao/"
echo ""

renamed=0
skipped=0

for entry in "${RENAMES[@]}"; do
    old="${entry%%:*}"
    new="${entry##*:}"

    if [[ ! -d "$old" ]]; then
        echo "SKIP: $old (not found)"
        ((skipped++)) || true
        continue
    fi
    if [[ -d "$new" ]]; then
        echo "SKIP: $new already exists"
        ((skipped++)) || true
        continue
    fi

    echo "  $old → $new"
    mv "$old" "$new"
    ((renamed++)) || true
done

echo ""
echo "Done: $renamed renamed, $skipped skipped"
echo ""
echo "NOTE: You may need to:"
echo "  1. Re-open Qoder workspace to pick up new paths"
echo "  2. Update any git remotes that reference local paths"
echo "  3. Update systemd service files that reference old paths"
