# ELVES-Dwarf public data

Release **v1** (2026-08-12). Full documentation, with every column and field
described, lives at https://elves-surveys.github.io/catalogs/elves-dwarf/

| Product | File(s) |
| --- | --- |
| Host catalog | `ELVES-Dwarf_host_cat_v1.fits` — 39 hosts x 19 columns |
| Satellite candidate catalog | `ELVES-Dwarf_master_cat_v1.fits` — 207 candidates x 36 columns |
| Survey footprints | `survey_footprint/<host>_survey_footprint.{geojson,reg}` — 32 hosts, also bundled as `ELVES-Dwarf_survey_footprint_v1.zip` |

```python
from astropy.table import Table

hosts = Table.read("ELVES-Dwarf_host_cat_v1.fits")
sats = Table.read("ELVES-Dwarf_master_cat_v1.fits")
```

The documentation page also carries an interactive footprint viewer: pick a host
to see its coverage polygon, search radius, and satellite candidates, or link
straight to one with `?host=NGC1313`. It reads the same GeoJSON files published
here, plus `src/content/elves-dwarf-satellites.json`.

Both `src/content/elves-dwarf-satellites.json` (via `scripts/extract-satellites.py`,
which needs astropy) and the footprint zip (via `scripts/pack-footprints.sh`) are
regenerated automatically by `scripts/sync-data.sh`, which runs before every
`npm run build` — locally and in the GitHub Actions deploy — so the satellite
catalog and the master FITS table never drift apart. Update the FITS table or a
footprint file and the JSON, the zip, the file count, and the per-host download
list on the documentation page all follow on the next build.

Column and field documentation lives in `src/content/data-docs.json` in this
repository — that JSON file is the single source of truth and drives the
documentation page.

If you use these products, please cite Li et al. 2026, ApJ, 1002, 75
([ELVES-Dwarf. I.](https://doi.org/10.3847/1538-4357/ae4495)).

## Notes

- Missing values are `NaN` in floating-point columns and `--` or an empty string
  in string columns.
- A few provenance strings in the source/reference columns are still in the
  LaTeX form used by the paper tables (e.g. `\citetalias{Tully2013}`); resolve
  them against the reference list of Li et al. 2026.
