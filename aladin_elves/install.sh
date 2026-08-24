#!/bin/bash
# Publish an ELVES satellite explorer as a page of this website.
#
#   ./install.sh                        -> the default survey, elves-dwarf
#   ./install.sh elves-dwarf            -> public/explorer/elves-dwarf, i.e. /explorer/elves-dwarf/
#   ./install.sh elves-dwarf /some/dir  -> anywhere else (a public_html tree, a scratch copy)
#   ./install.sh --list                 -> which surveys can be built right now
#
# Rebuilds the survey's json from its released host + master catalogues, then fills
# the survey's name and json filename into viewer_template.html and copies it in as
# index.html. The page is one self-contained HTML file and the imaging is streamed
# from CDS at view time, so those two files are the whole deployment.
#
# Everything survey-specific lives in the SURVEYS registry in build_catalog.py;
# adding ELVES or ELVES-Field is a matter of publishing their catalogues under
# public/data/<slug>/ and running this with that slug.
#
# The result is committed to the repo: Astro copies public/ into dist/ verbatim,
# so building the site needs neither python nor astropy. Re-run this whenever the
# catalogues change.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"
BUILD="$HERE/build_catalog.py"

if [[ "${1:-}" == "--list" || "${1:-}" == "-l" ]]; then
  printf '%-14s %-14s %s\n' slug survey catalogues
  "$PYTHON" "$BUILD" --list | while IFS=$'\t' read -r slug name state; do
    printf '%-14s %-14s %s\n' "$slug" "$name" "$state"
  done
  exit 0
fi

SURVEY="${1:-elves-dwarf}"

# One call: the registry in build_catalog.py is the single source of truth for
# where a survey's catalogues, json and page live.
CFG="$("$PYTHON" "$BUILD" --survey "$SURVEY" --print-config)"
SURVEY_NAME=""; CATALOG_JSON=""; DEFAULT_DEST=""; HOST_CAT=""; MASTER_CAT=""
while IFS='=' read -r key value; do
  case "$key" in
    NAME)        SURVEY_NAME="$value" ;;
    JSON)        CATALOG_JSON="$value" ;;
    INSTALL_DIR) DEFAULT_DEST="$value" ;;
    HOST_CAT)    HOST_CAT="$value" ;;
    MASTER_CAT)  MASTER_CAT="$value" ;;
  esac
done <<< "$CFG"

# Checked before anything is created, so a survey that has no release yet does
# not leave an empty directory behind.
if [[ -z "$HOST_CAT" || -z "$MASTER_CAT" ]]; then
  echo "$SURVEY has no published catalogues under public/data/$SURVEY yet" >&2
  echo "(see './install.sh --list')" >&2
  exit 1
fi

DEST="${2:-$DEFAULT_DEST}"
mkdir -p "$DEST"
DEST="$(cd "$DEST" && pwd)"

"$PYTHON" "$BUILD" --survey "$SURVEY" --install --install-dir "$DEST"

sed -e "s/{{SURVEY_NAME}}/$SURVEY_NAME/g" \
    -e "s/{{CATALOG_JSON}}/$CATALOG_JSON/g" \
    "$HERE/viewer_template.html" > "$DEST/index.html"
# A placeholder left standing would ship a page that fetches "{{CATALOG_JSON}}".
if grep -q '{{' "$DEST/index.html"; then
  echo "unsubstituted placeholder left in $DEST/index.html:" >&2
  grep -n '{{' "$DEST/index.html" >&2
  exit 1
fi

chmod 755 "$DEST"
chmod 644 "$DEST/index.html" "$DEST/$CATALOG_JSON"

echo "installed $SURVEY_NAME -> $DEST"
ls -l "$DEST"

# The default destination is inside the site, so say where it will show up.
case "$DEST" in
  "$(cd "$HERE/.." && pwd)"/public/*)
    echo "serve with 'npm run dev' -> http://localhost:4321${DEST#*/public}/index.html"
    ;;
esac
