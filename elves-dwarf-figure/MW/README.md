# Milky Way satellite system — 3D figure & rotation movie

Recreation of the Simon & Geha (2021) style graphic of the spatial
distribution of Milky Way satellites, updated with the Local Volume
Database (`../dwarf_mw.csv`, Pace 2024). Balls are colored **and** sized by
stellar mass (sequential blue ramp, log M* = 2–9.6). Only systems with
`confirmed_real == 1` are shown (64 satellites).

Geometry: Galactocentric coordinates computed from (l, b, heliocentric
distance) with R_sun = 8.122 kpc; orthographic projection at 20° elevation.
The outer sphere is 300 kpc; the inner ring on the Galactic plane is
100 kpc. The spiral glyph marks the Milky Way at the center.

## Usage

```bash
python mw_satellites.py             # mw_satellites_3d.png/.pdf
python mw_satellites.py --labels    # labeled version (offsets tuned for azim=125)
python mw_satellites.py --stems     # guide lines from dwarfs to the Galactic plane
python mw_satellites.py --grid      # faint polar grid on the Galactic plane
python mw_satellites.py --dark      # dark background theme (writes *_dark files)
python mw_satellites.py --movie     # mw_satellites_rotation.gif (360° spin, stems+grid on)
python mw_satellites.py --movie --dark   # dark version of the movie
python mw_satellites.py --azim 90   # different static viewing angle
```

Label positions in `LABELS` are absolute data coordinates (kpc) tuned for
the default azimuth, so `--labels` should only be combined with the default
`--azim 125`. The movie renders without labels.
