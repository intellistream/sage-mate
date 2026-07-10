#!/usr/bin/env bash
# Build a Linux self-extracting .run installer for hosted/web.

set -euo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
tag="${1:-${FACULTY_TWIN_RELEASE_TAG:-v4.6.0}}"
bundle_name="${FACULTY_TWIN_BUNDLE_NAME:-sage-mate-${tag}}"
dist_dir="$repo_root/dist"
bundle_tar="$dist_dir/$bundle_name.tar.gz"
run_path="$dist_dir/$bundle_name-linux.run"

mkdir -p "$dist_dir"

if [[ ! -f "$bundle_tar" ]]; then
    "$repo_root/tools/build_hosted_web_release_bundle.sh" "$tag" >/dev/null
fi

cat > "$run_path" <<'STUB'
#!/usr/bin/env bash
# Self-extracting installer for Sage Mate hosted/web.

set -euo pipefail

bundle_name="__BUNDLE_NAME__"
install_root="${FACULTY_TWIN_INSTALLER_ROOT:-$HOME/.local/share/sage-mate-installer}"
target_dir="$install_root/$bundle_name"
payload_line=$(awk '/^__FACULTY_TWIN_PAYLOAD_BELOW__$/ { print NR + 1; exit 0 }' "$0")

if [[ -z "$payload_line" ]]; then
    echo "Installer payload marker not found." >&2
    exit 1
fi

mkdir -p "$install_root"
rm -rf "$target_dir.new"
mkdir -p "$target_dir.new"

tail -n +"$payload_line" "$0" | tar -xz -C "$target_dir.new"
extracted_dir="$target_dir.new/$bundle_name"
if [[ ! -x "$extracted_dir/install.sh" ]]; then
    echo "Installer payload is incomplete: install.sh missing." >&2
    exit 1
fi

rm -rf "$target_dir"
mv "$extracted_dir" "$target_dir"
rm -rf "$target_dir.new"

echo "Sage Mate installer extracted to: $target_dir"
echo "Starting installer..."
cd "$target_dir"
exec "$target_dir/install.sh" "$@"

__FACULTY_TWIN_PAYLOAD_BELOW__
STUB

python3 - "$run_path" "$bundle_name" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
bundle_name = sys.argv[2]
data = path.read_text(encoding="utf-8")
path.write_text(data.replace("__BUNDLE_NAME__", bundle_name), encoding="utf-8")
PY

cat "$bundle_tar" >> "$run_path"
chmod 0755 "$run_path"
sha256sum "$run_path" > "$run_path.sha256"

echo "$run_path"
echo "$run_path.sha256"
