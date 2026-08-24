# Data directory

Public catalogs and machine-readable products served from
`https://elves-surveys.github.io/data/`.

Everything under `public/` is copied verbatim into the built site, so a file
placed at `public/data/<survey>/<file>` is downloadable at
`https://elves-surveys.github.io/data/<survey>/<file>`.

## Layout

| Path | Contents |
| --- | --- |
| `data/elves/` | ELVES (Milky Way-mass hosts) products — not yet posted |
| `data/elves-dwarf/` | ELVES-Dwarf (dwarf hosts) products |
| `data/elves-field/` | ELVES-Field (field dwarfs) products — not yet posted |

## Adding a product

1. Drop the file into `public/data/<survey>/`, with the release version in the
   file name (e.g. `ELVES-Dwarf_host_cat_v1.fits`) so links to an older release
   keep pointing at the exact table they were built against.
2. Describe its columns or fields in `src/content/data-docs.json`. That file
   drives the per-survey documentation page at `/catalogs/<survey>/`, where each
   product gets its own section anchored at its product id. A product may also
   set `"viewer": "footprint"` to mount the interactive sky viewer.
3. Fill in the matching entry in `src/content/data-products.json`:
   `downloadLink` is a site-root-relative path such as
   `/data/elves-dwarf/ELVES-Dwarf_host_cat_v1.fits`, `documentationLink` points
   at `/catalogs/<catalog-id>/`, and `status` becomes `Available`. The survey
   page renders that entry in its "Data products" table.
