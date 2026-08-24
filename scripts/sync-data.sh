#!/usr/bin/env bash
# Regenerates the derived data files from the published catalogs, so the site
# never ships stale copies. Runs automatically before `npm run build`.
set -euo pipefail

python3 scripts/extract-satellites.py
bash scripts/pack-footprints.sh
