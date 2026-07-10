#!/usr/bin/env bash
# Install curated faculty-twin skills from the sibling skills repository into
# the private runtime repository.

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
skills_root="${DIGITAL_TWIN_SKILLS_REPO_DIR:-$repo_root/../sage-mate-skills}"
runtime_root="${DIGITAL_TWIN_RUNTIME_DIR:-$repo_root/../sage-mate-runtime-private}"

usage() {
    cat >&2 <<'EOF'
Usage: tools/install_curated_skills.sh [--skills-repo PATH] [--runtime-dir PATH]

Copies:
  - manifests/skills/*.json -> runtime/data/skills/
  - manifests/capability_plugins/*.json -> runtime/data/capability_plugins/
  - install/faculty-twin-fixed-prompt-skills.md -> runtime/data/installed_skills/fixed_prompt_skills.md

The fixed prompt file must contain only low-risk, permission-safe guidance.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skills-repo)
            skills_root="${2:-}"
            [[ -n "$skills_root" ]] || { usage; exit 2; }
            shift 2
            ;;
        --runtime-dir)
            runtime_root="${2:-}"
            [[ -n "$runtime_root" ]] || { usage; exit 2; }
            shift 2
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

[[ -d "$skills_root" ]] || {
    echo "Skills repo not found: $skills_root" >&2
    exit 1
}
[[ -d "$skills_root/manifests/skills" ]] || {
    echo "Missing skills manifests: $skills_root/manifests/skills" >&2
    exit 1
}
[[ -d "$skills_root/manifests/capability_plugins" ]] || {
    echo "Missing capability plugin manifests: $skills_root/manifests/capability_plugins" >&2
    exit 1
}
[[ -f "$skills_root/install/faculty-twin-fixed-prompt-skills.md" ]] || {
    echo "Missing fixed prompt prefix: $skills_root/install/faculty-twin-fixed-prompt-skills.md" >&2
    exit 1
}

mkdir -p \
    "$runtime_root/data/skills" \
    "$runtime_root/data/capability_plugins" \
    "$runtime_root/data/installed_skills"

cp "$skills_root"/manifests/skills/*.json "$runtime_root/data/skills/"
cp "$skills_root"/manifests/capability_plugins/*.json "$runtime_root/data/capability_plugins/"
cp "$skills_root/install/faculty-twin-fixed-prompt-skills.md" \
    "$runtime_root/data/installed_skills/fixed_prompt_skills.md"

skills_commit="unknown"
if git -C "$skills_root" rev-parse --short HEAD >/dev/null 2>&1; then
    skills_commit=$(git -C "$skills_root" rev-parse --short HEAD)
fi

cat > "$runtime_root/data/installed_skills/install_manifest.json" <<EOF
{
  "source_repo": "$skills_root",
  "source_commit": "$skills_commit",
  "installed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "skill_manifest_dir": "data/skills",
  "capability_plugin_dir": "data/capability_plugins",
  "fixed_prompt_path": "data/installed_skills/fixed_prompt_skills.md"
}
EOF

echo "[install-skills] skills_root=$skills_root"
echo "[install-skills] runtime_root=$runtime_root"
echo "[install-skills] source_commit=$skills_commit"
echo "[install-skills] installed"
