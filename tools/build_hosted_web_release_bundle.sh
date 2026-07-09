#!/usr/bin/env bash
# Build the product-style hosted/web release bundle.

set -euo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
tag="${1:-${FACULTY_TWIN_RELEASE_TAG:-v4.4.0}}"
bundle_name="sage-faculty-twin-hosted-web-${tag}"
dist_dir="$repo_root/dist"
stage_parent=$(mktemp -d)
stage_dir="$stage_parent/$bundle_name"

cleanup() {
    rm -rf "$stage_parent"
}
trap cleanup EXIT

mkdir -p "$stage_dir" "$dist_dir"

copy_file() {
    local source="$1" target="$2"
    [[ -f "$source" ]] || {
        echo "missing required release file: $source" >&2
        exit 1
    }
    install -m "$3" "$source" "$target"
}

copy_file "$repo_root/release/install.sh" "$stage_dir/install.sh" 0755
copy_file "$repo_root/release/hosted-web-installer.sh" "$stage_dir/hosted-web-installer.sh" 0755
copy_file "$repo_root/release/hosted-web.sh" "$stage_dir/hosted-web.sh" 0755
copy_file "$repo_root/release/hosted-web-nvidia.sh" "$stage_dir/hosted-web-nvidia.sh" 0755
copy_file "$repo_root/release/hosted-web-ascend.sh" "$stage_dir/hosted-web-ascend.sh" 0755
copy_file "$repo_root/release/README.md" "$stage_dir/README.md" 0644
copy_file "$repo_root/release/secrets.env.example" "$stage_dir/secrets.env.example" 0600

if [[ -f "$repo_root/release/secrets.env.enc" ]]; then
    install -m 0600 "$repo_root/release/secrets.env.enc" "$stage_dir/secrets.env.enc"
fi

cat > "$stage_dir/VERSION" <<EOF
tag=$tag
commit=$(git -C "$repo_root" rev-parse HEAD)
built_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF
chmod 0644 "$stage_dir/VERSION"

tarball="$dist_dir/$bundle_name.tar.gz"
tar -C "$stage_parent" -czf "$tarball" "$bundle_name"
sha256sum "$tarball" > "$tarball.sha256"

echo "$tarball"
echo "$tarball.sha256"
