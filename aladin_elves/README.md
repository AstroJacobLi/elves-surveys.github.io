# ELVES satellite explorer (Aladin Lite)

A read-only page for the survey website: pick one of the survey's hosts, the view
jumps to it framed on its virial radius, every satellite candidate is drawn as a
circle coloured by status, and clicking one flies in and shows its measurements.

One explorer is built per survey: `./install.sh <slug>` installs it at
`public/explorer/<slug>/`, served as `/explorer/<slug>/`. Only **elves-dwarf** has
published catalogues today; ELVES and ELVES-Field are already registered and build
as soon as their FITS files land (see *Adding a survey*).

## Files

| file | what it does |
| --- | --- |
| `build_catalog.py` | host cat + master cat → `<slug>.json`; also holds the survey registry |
| `viewer_template.html` | the whole viewer; `{{SURVEY_NAME}}` / `{{CATALOG_JSON}}` filled in, installed as `index.html` |
| `install.sh` | rebuild the json + copy both into the website |

## Data

Two inputs are joined per survey — the newest `<Prefix>_host_cat_*.fits` and
`<Prefix>_master_cat_*.fits` under `public/data/<slug>/`, i.e. the catalogues this
site already publishes, so the viewer shows exactly what visitors can download.
For ELVES-Dwarf those are:

* `ELVES-Dwarf_host_cat_v1.fits` — 39 hosts, their positions, distances, masses, `rvir_kpc`
* `ELVES-Dwarf_master_cat_v1.fits` — 207 satellite candidates with `host`, positions,
  Sérsic photometry, SBF/TRGB distances and `status`

Host positions come from the host catalogue's own `ra`/`dec`. Earlier catalogues had
no position columns and `hosts_config.py` was the only source; `--hosts-config` still
accepts it and fills in any host the catalogue cannot place, but it is skipped when
not readable — so the build runs anywhere the two FITS files are. `EXTRA_POSITIONS`
at the top of `build_catalog.py` is the last-resort escape hatch. Either way the
build warns and drops any host it cannot place, rather than emitting a bad position.

Built from the v1 release the output is byte-identical to the cluster build from the
`260812` catalogues, apart from one host RA differing in the sixth decimal.

Satellites are nested inside their host and sorted by projected separation. Blank
FITS values (including the master catalogue's LaTeX `\nodata`) become JSON `null`
and their panel rows are simply not drawn.

Status counts as built: **Confirmed 39, Unconfirmed 20, Not Observed 17, Rejected 131**.

## Deploy

    ./install.sh --list                       # which surveys can be built now
    ./install.sh elves-dwarf                  # -> public/explorer/elves-dwarf
    ./install.sh elves-dwarf /some/other/dir  # e.g. a public_html tree

With no argument it builds `elves-dwarf`. The install directory, the json filename
(`<slug>` with dashes as underscores) and the name shown in the page's title bar,
help card and loader are all derived from the slug, so nothing about a survey is
spelled out twice.

## Adding a survey

1. Publish `<Prefix>_host_cat_vN.fits` and `<Prefix>_master_cat_vN.fits` under
   `public/data/<slug>/`. The build picks the highest `vN` of each.
2. Check the slug is in `SURVEYS` at the top of `build_catalog.py` (all three ELVES
   surveys already are) and that `prefix` matches the filenames.
3. `./install.sh <slug>`, then link the new `/explorer/<slug>/` from the site.

Step 1 is the whole job **only if the new catalogues use the ELVES-Dwarf v1 column
names** — `build_catalog.py` reads those directly (`dist_mpc`, `rvir_kpc`,
`reff_sersic`, `status`, …). A differently named schema needs those reads mapped per
survey; the paths are parameterised, the columns are not. A survey with no hosts at
all, like ELVES-Field, does not fit this viewer's host → satellites shape and would
need more than a registry entry.

The two installed files are committed to the repo. Astro copies `public/` into
`dist/` verbatim, so building the site needs neither python nor astropy — only this
script does. Re-run it whenever the catalogues change; nothing is cached
client-side, so a redeploy is live immediately.

`--list` reports each registered survey as *ready* or *no catalogues yet*, and a
build for a survey with no catalogues stops before creating anything.

Note that Aladin Lite v3 requires WebGL2. That is fine in every current browser but
does mean the page cannot be screenshotted by a plain headless renderer.

## Using it

Pick a host from the dropdown or the left list. Arrows step through that host's
candidates, `h` backs out to the whole host, `[` / `]` change host, `s` cycles the
imaging survey, `v` toggles the virial-radius circle, `+` / `-` zoom, `?` shows help.
Clicking a circle in the image selects that candidate — the hit test converts the
click through `world2pix` and takes the nearest candidate within ~22 px, so it
behaves the same however the marks were drawn.

The four status chips in the top bar double as filters. **Rejected candidates start
hidden** — 131 of the 207 are rejected background objects, and showing them by
default buries the real satellites. Click the chip to bring them in.

Framing adapts to each object: hosts are framed at 2.4 × their virial diameter
(clamped to 0.05°–14°, because the LMC's virial radius is ~170° across and NGC 4625's
is ~43′), satellites at 24 × their effective radius or 3′, whichever is larger. The
bottom dock reports the field of view in arcmin and in kpc at the host's distance.

`?host=NGC5068&sat=dw1320m2036` in the URL deep-links to a specific object, which is
what the per-host pages on the rest of the site should link to.

### Imaging layers

Defaults are Legacy Surveys DR10, GALEX GR6/7 colour and DSS colored, as requested.

Every layer except DR10 is pinned to a HiPS service URL that was checked to exist, so
it loads without a registry lookup. **DR10 is the exception** — it is not served from
`alasky.cds.unistra.fr`, so it resolves through the CDS registry by id
(`CDS/P/DESI-Legacy-Surveys/DR10/color`) and that id could not be verified from
Princeton, where the CDS MOCServer is unreachable. If DR10 ever comes up blank,
**DECaLS DR5** in the same dropdown is the checked Legacy-family fallback, and
Aladin's own layer control (bottom right) reaches every other HiPS at CDS.

Legacy Surveys also thins out below dec ≈ −30°, which is a real part of this sample
(NGC 1313, IC 5052, ESO 154-023 …) — GALEX and DSS are all-sky and cover those.
