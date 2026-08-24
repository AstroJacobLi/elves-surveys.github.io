# ELVES-Dwarf summary figures

Survey summary figures built from the complete sample catalogs
(`ELVES-Dwarf_host_cat_260524.fits`, `ELVES-Dwarf_master_cat_260524.fits`).
Hosts are circles with radius ∝ Rvir; satellites sit inside at their true
projected radius (`ang_proj_Rvir`), colored by log M*_sat (Confirmed),
gray × (Unconfirmed), open circle (Not Observed). Blue = ELVES-Dwarf,
gray = literature resolved-star hosts; solid = isolated, dashed = non-isolated.

## Scripts

- `make_elves_dwarf_figure.py` — Cartesian distance vs. host stellar mass
  plane (style of the previous paper's Fig. 1). Circles are anchored at their
  true (D, M*) values and nudged apart by a force relaxation
  (median displacement ~0.3 Mpc-equivalent) → `elves_dwarf_summary.*`
- `make_elves_dwarf_polar.py` — polar layout: Milky Way at center,
  radius = true distance (±0.5 Mpc slack, ±1 Mpc inside 2 Mpc), azimuth free
  (initialized mass-ranked per 2-Mpc shell, then relaxed). Satellites below
  `SAT_LOGM_MIN` (log M* = 5) are hidden. Two variants:
  - `elves_dwarf_polar_full.*` — 360° disk, square; website hero image
  - `elves_dwarf_polar_fan.*`  — 180° half-disk with distance ruler, 16:9;
    talk slides

  Each variant is also written with literature hosts only
  (`*_lit.*`), rendered from the identical layout — use the lit/all pair as
  a before/after build in talks to show the survey's reach.

  `python make_elves_dwarf_polar.py --paper1-only` instead renders just the
  8 hosts from paper 1 (`*_paper1.*`) on that same shared layout, so you can
  build paper 1 → full sample without any circle jumping between slides.

Each script writes PNG (250 dpi), PDF, and SVG. All tuning knobs sit in the
commented parameter block at the top of each script: `FILL_FULL`/`FILL_FAN`
(circle packing density → circle size), `GRAD_COLOR`/`GRAD_ALPHA`/`GRAD_RAMP`
(background gradient softness), `RINGS_MPC` (which distance rings to draw),
`SAT_LOGM_MIN` (satellite mass cut), `LABEL_ANGLE_OVERRIDE` (pin an awkward
label to a given angle per variant), `HIDE_NAMES` (drop all host name labels;
outputs then get a `_nonames` suffix so both versions coexist),
`SAVE_TRANSPARENT` (transparent background for slides), `X_SPLIT`
(resolved/integrated boundary), colors. Label placement is automatic: inside the circle if it fits (avoiding
satellite markers), else straddling the circle edge, else outside in the
least-crowded direction.

Requires: numpy, matplotlib, astropy, Avenir Next (macOS).
