#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
notebook="$repo_root/public/tutorials/notebooks/01_quenched_fraction.ipynb"
output_dir="$repo_root/public/tutorials/rendered"
render_cache="${TMPDIR:-/tmp}/elves-notebook-render"

mkdir -p "$output_dir" "$render_cache"

# Warm Matplotlib's font cache before execution so the one-time cache message
# never becomes part of a notebook cell's published output.
MPLBACKEND=Agg MPLCONFIGDIR="$render_cache" python3 -c 'import matplotlib.pyplot'

MPLCONFIGDIR="$render_cache" jupyter nbconvert \
  --to html \
  --execute \
  --template lab \
  --theme light \
  --TagRemovePreprocessor.enabled=True \
  --TagRemovePreprocessor.remove_cell_tags=render-hero \
  --ExecutePreprocessor.timeout=120 \
  --output 01_quenched_fraction.html \
  --output-dir "$output_dir" \
  "$notebook"

test -s "$output_dir/01_quenched_fraction.html"

# Astropy assigns process-specific numeric IDs to rendered tables. They are not
# used by the page, and removing them keeps the committed fragment deterministic
# so CI can detect meaningful notebook drift.
perl -pi -e 's/ id="table[0-9]+"//g' "$output_dir/01_quenched_fraction.html"

# Replace nbconvert's generic Matplotlib alt text in plot order.
perl -0pi -e 's{alt="No description has been provided for this image"}{alt="Color-magnitude diagram of the ELVES-Dwarf satellite sample with the photometric quenching boundary."}' "$output_dir/01_quenched_fraction.html"
perl -0pi -e 's{alt="No description has been provided for this image"}{alt="ELVES-Dwarf quenched fraction versus stellar mass with 68 percent Jeffreys binomial intervals."}' "$output_dir/01_quenched_fraction.html"

# The notebook is sandboxed in an iframe. Let the trusted, generated document
# report its full height so the surrounding ELVES page does not show a nested
# scrollbar as figures and MathJax finish loading.
perl -0pi -e 's{</body>}{<script>const sendNotebookHeight=()=>parent.postMessage({type:"elves-notebook-height",height:document.documentElement.scrollHeight},"*");addEventListener("load",sendNotebookHeight);new ResizeObserver(sendNotebookHeight).observe(document.body);</script>\n</body>}i' "$output_dir/01_quenched_fraction.html"

printf 'render-notebooks: wrote %s\n' "$output_dir/01_quenched_fraction.html"
