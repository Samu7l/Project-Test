#!/usr/bin/env bash
# Build the deliverable StApp26_20230845_MOLLIERE_DAI.zip: code, README, processed data and DATA_SOURCES.md.
# No raw data (data/raw/), no .git, no caches. Run from the project root:  bash make_zip.sh
set -euo pipefail

NAME="StApp26_20230845_MOLLIERE_DAI"
ROOT="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${PYTHON:-python}"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

cd "$ROOT"
"$PYTHON" -m src.sources.registry > DATA_SOURCES.md          # every dataset link, from src/sources/registry.py

mkdir -p "$STAGE/$NAME"
# rsync applies the first matching rule: caches are excluded before the folders are included.
rsync -a \
  --exclude '__pycache__/' --exclude '*.pyc' --exclude '.DS_Store' \
  --include 'app.py' --include 'requirements.txt' --include 'README.md' --include 'DATA_SOURCES.md' \
  --include 'make_zip.sh' --include '.gitignore' \
  --include 'app_pages/***' --include 'src/***' --include 'tests/***' --include 'docs/***' \
  --include 'data/' --include 'data/processed/***' \
  --exclude '*' \
  ./ "$STAGE/$NAME/"

if [ -e "$STAGE/$NAME/data/raw" ] || [ -e "$STAGE/$NAME/.git" ]; then
  echo "error: raw data or .git found in the staging folder" >&2
  exit 1
fi

rm -f "$ROOT/$NAME.zip"
(cd "$STAGE" && zip -qr -X "$ROOT/$NAME.zip" "$NAME")
echo "$NAME.zip: $(du -h "$ROOT/$NAME.zip" | cut -f1), $(unzip -Z1 "$ROOT/$NAME.zip" | grep -vc '/$') files"
