"""Rebuild src/content/elves-dwarf-satellites.json from the released catalog.

The footprint viewer plots satellite candidates client-side, so the positions
have to exist as JSON. Run this after publishing a new master catalog:

    python3 scripts/extract-satellites.py

Requires astropy; it is NOT part of `npm run build` (the JSON is committed).
"""

import collections
import glob
import json
import os

import numpy as np
from astropy.table import Table

CATALOG = "public/data/elves-dwarf/ELVES-Dwarf_master_cat_v1.fits"
FOOTPRINTS = "public/data/elves-dwarf/survey_footprint/*.geojson"
OUT = "src/content/elves-dwarf-satellites.json"


def text(value):
    return value.decode() if isinstance(value, bytes) else str(value)


def main():
    table = Table.read(CATALOG)
    hosts = {
        os.path.basename(path).replace("_survey_footprint.geojson", "")
        for path in glob.glob(FOOTPRINTS)
    }

    rows = []
    for row in table:
        host = text(row["host"])
        ra, dec = float(row["ra"]), float(row["dec"])
        # Hosts without a footprint file have nothing to plot against.
        if host not in hosts or not np.isfinite(ra) or not np.isfinite(dec):
            continue
        rows.append(
            collections.OrderedDict(
                [
                    ("name", text(row["name"])),
                    ("host", host),
                    ("ra", round(ra, 5)),
                    ("dec", round(dec, 5)),
                    ("status", text(row["status"])),
                ]
            )
        )

    with open(OUT, "w") as stream:
        json.dump(rows, stream, indent=1)
        stream.write("\n")
    print(f"wrote {OUT}: {len(rows)} candidates around {len(hosts)} hosts")


if __name__ == "__main__":
    main()
