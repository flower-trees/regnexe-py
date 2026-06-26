#!/usr/bin/env bash
# release.sh — bump version, build, and publish regnexe-py to PyPI
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYPROJECT="$PROJECT_ROOT/pyproject.toml"

cd "$PROJECT_ROOT"

# ── 1. current version ───────────────────────────────────────────────────────
current=$(grep '^version' "$PYPROJECT" | head -1 | sed 's/.*"\(.*\)".*/\1/')
echo "Current version: $current"

# ── 2. new version ───────────────────────────────────────────────────────────
if [ $# -ge 1 ]; then
    new_version="$1"
else
    read -rp "New version (current: $current): " new_version
fi

if [ -z "$new_version" ]; then
    echo "Error: version cannot be empty." >&2
    exit 1
fi

# ── 3. confirm ───────────────────────────────────────────────────────────────
echo ""
echo "  $current  →  $new_version"
echo ""
read -rp "Publish regnexe-py $new_version to PyPI? [y/N] " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

# ── 4. update pyproject.toml ─────────────────────────────────────────────────
sed -i '' "s/^version = \"$current\"/version = \"$new_version\"/" "$PYPROJECT"
echo "Updated version in $PYPROJECT"

# ── 5. clean dist/ ───────────────────────────────────────────────────────────
rm -rf "$PROJECT_ROOT/dist/"
echo "Cleaned dist/"

# ── 6. build ─────────────────────────────────────────────────────────────────
echo "Building..."
python -m build "$PROJECT_ROOT"

# ── 7. publish ───────────────────────────────────────────────────────────────
echo "Uploading to PyPI..."
python -m twine upload "$PROJECT_ROOT/dist/*"

# ── 8. git tag ───────────────────────────────────────────────────────────────
git add "$PYPROJECT"
git commit -m "chore: release v$new_version"
git tag "v$new_version"
echo ""
echo "Done. Run 'git push && git push --tags' to push the release commit and tag."
