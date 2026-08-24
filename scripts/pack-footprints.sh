#!/usr/bin/env bash
# Bundles the per-host survey footprint files into a single zip for download.
# Runs automatically before `npm run build` (see the "prebuild" script).
set -euo pipefail

dir="public/data/elves-dwarf/survey_footprint"
zip_path="public/data/elves-dwarf/ELVES-Dwarf_survey_footprint_v1.zip"

if ! command -v zip >/dev/null 2>&1; then
  echo "pack-footprints: 'zip' not found; cannot build $zip_path" >&2
  exit 1
fi

rm -f "$zip_path"
zip -q -X -j "$zip_path" "$dir"/*.geojson "$dir"/*.reg
echo "pack-footprints: wrote $zip_path ($(ls -lh "$zip_path" | awk '{print $5}'))"
