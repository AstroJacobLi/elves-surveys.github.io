#!/usr/bin/env python
"""
ELVES-Dwarf survey summary figure, polar version.

The Milky Way sits at the center; radius = distance, so every host sits at
(nearly) its true distance and only the azimuth is free. Hosts are drawn as
circles with radius proportional to Rvir. Azimuths are initialized ranked by
host stellar mass within each 2-Mpc shell, then relaxed to remove overlaps;
a small radial slack (+-0.5 Mpc, +-1 Mpc inside 2 Mpc) absorbs crowded shells.
Satellites are placed inside each circle at their true projected radius.

Two variants are produced:
  full  - 360 deg disk  (square; website hero image)
  fan   - 180 deg half-disk with a distance ruler (16:9; talk slides)

Each variant is also rendered with literature hosts only (suffix "_lit"),
using the identical layout, so the pair works as a before/after build in
talks: the ELVES-Dwarf circles simply appear on top of the literature ones.

Pass `--paper1-only` to instead render only the 8 hosts from paper 1
(suffix "_paper1"), still on the same shared layout — useful for a "paper 1
sample -> full sample" build in talks.

Outputs: elves_dwarf_polar_{full,fan}.[png,pdf,svg]
         elves_dwarf_polar_{full,fan}_lit.[png,pdf,svg]
         elves_dwarf_polar_{full,fan}_paper1.[png,pdf,svg]  (--paper1-only)
"""

import argparse
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import Ellipse, Arc, FancyArrowPatch
from matplotlib.lines import Line2D
from matplotlib.colors import Normalize, to_rgba
from astropy.table import Table
from pathlib import Path

HERE = Path(__file__).parent

_parser = argparse.ArgumentParser(
    description="Render ELVES-Dwarf polar summary figures.")
_parser.add_argument("--paper1-only", action="store_true",
                     help="render only the 8 hosts from paper 1 (keeps the "
                          "full-sample layout); outputs get a '_paper1' "
                          "suffix instead of the usual and '_lit' pair.")
PAPER1_ONLY = _parser.parse_args().paper1_only

# hosts included in ELVES-Dwarf paper 1
PAPER1_HOSTS = {"NGC5238", "UGC00685", "NGC4605", "NGC4707",
                "UGC05427", "UGC05423", "DDO046", "NGC4625"}

# ----------------------------------------------------------------- style ----
mpl.rcParams.update({
    "font.family": "Avenir Next",
    "font.weight": "medium",
    "font.size": 16,           # base font size (notebook: rcParams 16)
    "mathtext.fontset": "stixsans",
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
})

# ---- colors (matched to 04_sat_distribution_plot.ipynb) --------------------
C_THIS_EDGE = "royalblue"      # circle edge, ELVES-Dwarf hosts
C_THIS_FACE = to_rgba("royalblue", 0.10)  # fill = edge color at 10% alpha
C_LIT_EDGE = "gray"            # circle edge, isolated literature hosts
C_LIT_EDGE_NONISO = to_rgba("darkgray", 0.8)  # edge, non-isolated lit hosts
C_LIT_FACE = "none"            # literature circles are unfilled
C_SAT_EDGE = "gray"            # rim color of confirmed-satellite dots
C_TEXT = "#333333"             # host label ink
C_RING = "#c3cad4"             # distance-ring gridlines
SAT_CMAP = plt.cm.rainbow_r    # colormap for confirmed-satellite stellar mass
SAT_NORM = Normalize(vmin=5.0, vmax=9.0)  # colorbar span: log M*_sat = 5..9

# ---- background gradient (tints the integrated-light zone) ----------------
GRAD_COLOR = (0.90, 0.96, 0.92)  # RGB of the tint at full strength; soft
                                 # mint, distinct from the royalblue hosts;
                                 # closer to (1,1,1) = softer
GRAD_ALPHA = 0.40                # peak opacity of the tint; 0 disables it
GRAD_RAMP = 4.5                  # Mpc past X_SPLIT over which the tint
                                 # reaches full strength; larger = gentler

# ---- geometry & sample selection -------------------------------------------
X_SPLIT = 3.0          # Mpc; resolved-star <-> integrated-light boundary
D_MAX = 12.0           # Mpc; outer edge of the disk
RINGS_MPC = (0, 4, 8, 12)  # draw a gridline ring at each of these distances
SAT_LOGM_MIN = 5.0     # hide satellites with log M* below this (unknown
                       # masses, e.g. unconfirmed candidates, are kept)
FILL_FULL = 0.20       # fraction of disk area covered by host circles
FILL_FAN = 0.22        # (full / fan variant); smaller = smaller circles

# ---- line widths (notebook: this-work lw=2, literature lw=1.5) -------------
LW_THIS = 2.0          # ELVES-Dwarf circle edge width
LW_LIT = 1.5           # literature circle edge width

# ---- markers & labels ------------------------------------------------------
SAT_MS = 40            # confirmed-satellite marker area, pt^2 (notebook: 45)
SAT_EDGE_LW = 1.2      # rim width of confirmed-satellite dots
X_MS = 20              # unconfirmed-satellite cross area, pt^2 (notebook: 20)
OPEN_MS = 26           # awaiting-follow-up open-circle area, pt^2
SAT_MIN_SEP = 0.115    # min separation between satellite markers, inches
LABEL_FS = 8.6         # host label font size, pt
LABEL_HALO = [pe.withStroke(linewidth=2.6, foreground="white", alpha=0.85)]
SAVE_TRANSPARENT = True  # True = transparent background like the notebook's
                          # savefig(transparent=True); halos stay white
HIDE_NAMES = True        # True = omit host name labels; outputs then get a
                          # "_nonames" suffix so the named versions are kept

# force an outside label at this angle (deg), keyed by (variant, host name)
LABEL_ANGLE_OVERRIDE = {
    ("full", "DDO161"): 225,
    ("full", "ESO245-005"): 270,
    ("fan", "NGC4700"): 0,
    ("fan", "NGC1705"): 90,
    ("fan", "NGC1311"): 45,
}

# ---------------------------------------------------------------- data ------
def pretty(name):
    name = str(name)
    if name.startswith("NGC"):
        return f"NGC {int(name[3:])}"
    if name.startswith("IC"):
        return f"IC {int(name[2:])}"
    return name

host = Table.read("../public/data/elves-dwarf/ELVES-Dwarf_host_cat_v1.fits")
sats = Table.read("../public/data/elves-dwarf/ELVES-Dwarf_master_cat_v1.fits")
sats = sats[np.isin(sats["status"].astype(str),
                    ["Confirmed", "Unconfirmed", "Not Observed"])]
# mass cut: drop satellites below SAT_LOGM_MIN, keep unknown masses
_lm = sats["log_m_star"]
_lm = np.asarray(_lm.filled(np.nan) if hasattr(_lm, "filled") else _lm, float)
n_cut = np.sum(np.isfinite(_lm) & (_lm <= SAT_LOGM_MIN))
sats = sats[~np.isfinite(_lm) | (_lm > SAT_LOGM_MIN)]
print(f"mass cut log M* > {SAT_LOGM_MIN}: dropped {n_cut} satellites, "
      f"{len(sats)} shown")

is_lit = np.array([str(s).startswith(r"\citetalias") for s in host["data_source"]])
is_iso = np.array(host["isolated"], dtype=bool)
dist = np.asarray(host["dist_mpc"], float)
logm = np.asarray(host["log_mstar_msun"], float)
rvir = np.asarray(host["rvir_kpc"], float)
names = [pretty(nm) for nm in host["name"]]
n = len(host)

# ------------------------------------------------------------ relaxation ----
def init_azimuth(span, rng):
    """Mass-ranked azimuths within each 2-Mpc shell, shells staggered."""
    theta = np.zeros(n)
    shell = np.digitize(dist, np.arange(2, 14, 2))
    lo, hi = np.deg2rad(8), np.deg2rad(span - 8)
    for s in np.unique(shell):
        idx = np.where(shell == s)[0]
        idx = idx[np.argsort(-logm[idx])]          # rank by host mass
        offs = (0.382 * s) % 1.0                   # stagger shells
        for k, i in enumerate(idx):
            f = ((k + 0.5) / len(idx) + offs) % 1.0
            theta[i] = lo + f * (hi - lo)
    return theta

def relax_polar(rad, rpi, span, r_out, n_iter=2500, pad=0.085, seed=42):
    rng = np.random.default_rng(seed)
    r_true = dist * rpi
    slack = np.where(dist < 2.0, 1.0, 0.5) * rpi
    theta = init_azimuth(span, rng)
    p = np.column_stack([r_true * np.cos(theta), r_true * np.sin(theta)])
    full = span >= 355
    rlo = np.maximum(r_true - slack, 0.0)
    if not full:
        # fan: a circle can only clear the baseline if its center sits at
        # least one radius above it (matters for the LMC at D ~ 0)
        rlo = np.maximum(rlo, rad + 0.02)
    rhi = np.minimum(r_true + slack, r_out - rad + 0.10)
    for it in range(n_iter):
        for i in range(n):
            for j in range(i + 1, n):
                d = p[i] - p[j]
                dd = np.hypot(*d)
                minsep = rad[i] + rad[j] + pad
                if dd < minsep:
                    if dd < 1e-9:
                        d = rng.normal(size=2); dd = np.hypot(*d)
                    push = 0.5 * (minsep - dd) * d / dd
                    p[i] += push
                    p[j] -= push
        # project back into the allowed radial band (soft)
        r = np.hypot(p[:, 0], p[:, 1])
        r = np.maximum(r, 1e-6)
        rt = np.clip(r, rlo, rhi)
        f = 1.0 + 0.85 * (rt / r - 1.0)
        p *= f[:, None]
        if not full:
            # keep circles above the baseline (fan variant)
            r = np.hypot(p[:, 0], p[:, 1])
            a = np.arctan2(p[:, 1], p[:, 0])
            amin = np.arcsin(np.clip((rad + 0.02) / np.maximum(r, rad + 0.02),
                                     0, 1))
            a = np.clip(a, amin, np.pi - amin)
            p = np.column_stack([r * np.cos(a), r * np.sin(a)])
    worst = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            worst = min(worst, np.hypot(*(p[i] - p[j])) - (rad[i] + rad[j]))
    return p, worst, np.abs(np.hypot(p[:, 0], p[:, 1]) - r_true) / rpi

# ------------------------------------------- satellite / label machinery ----
def place_sats(sub, R, rng):
    rfrac = np.clip(np.asarray(sub["ang_proj_Rvir"], float), 0.10, 1.0)
    r_in = rfrac * max(R - 0.085, 0.35 * R)
    order = np.argsort(-r_in)
    theta = np.full(len(sub), np.nan)
    offset = rng.uniform(0, 2 * np.pi)
    for k, idx in enumerate(order):
        t = offset + np.deg2rad(137.508) * k
        for _ in range(60):
            x, y = r_in[idx] * np.cos(t), r_in[idx] * np.sin(t)
            ok = True
            for jdx in order[:k]:
                xo = r_in[jdx] * np.cos(theta[jdx])
                yo = r_in[jdx] * np.sin(theta[jdx])
                if np.hypot(x - xo, y - yo) < SAT_MIN_SEP:
                    ok = False
                    break
            if ok:
                break
            t += np.deg2rad(23.0)
        theta[idx] = t
    return r_in * np.cos(theta), r_in * np.sin(theta)

def label_size(text, fs=LABEL_FS):
    return 0.0605 * len(text) * fs / 8.6, 0.145 * fs / 8.6

def rect_overlap(a, b):
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])

def rect_circle_overlap(rect, c, r):
    qx = np.clip(c[0], rect[0], rect[2])
    qy = np.clip(c[1], rect[1], rect[3])
    return np.hypot(qx - c[0], qy - c[1]) < r

def place_labels(pos, rad, sat_data, bounds, variant):
    """bounds = (xmin, ymin, xmax, ymax) in layout inches."""
    placed, results = [], {}
    cand_angles = [270, 90, 315, 225, 45, 135, 0, 180, 300, 240, 60, 120]
    inside_fracs = [0.52, -0.52, 0.0, 0.66, -0.66, 0.36, -0.36]

    def sat_clear(i, rect, padd=0.075):
        if i not in sat_data:
            return True
        _, dx, dy = sat_data[i]
        r = (rect[0] - padd, rect[1] - padd, rect[2] + padd, rect[3] + padd)
        for x, y in zip(pos[i, 0] + dx, pos[i, 1] + dy):
            if r[0] <= x <= r[2] and r[1] <= y <= r[3]:
                return False
        return True

    def penalty(i, rect, base):
        score = base
        if rect[0] < bounds[0] or rect[2] > bounds[2]: score += 40
        if rect[1] < bounds[1] or rect[3] > bounds[3]: score += 40
        for j in range(n):
            if j == i:
                continue
            if rect_circle_overlap(rect, pos[j], rad[j] + 0.01):
                score += 12
            elif rect_circle_overlap(rect, pos[j], rad[j] + 0.06):
                score += 5
        for prect in placed:
            if rect_overlap(rect, prect):
                score += 25
        return score

    for i in np.argsort(-rad):
        w, h = label_size(names[i])
        best, best_score = None, np.inf
        forced = LABEL_ANGLE_OVERRIDE.get((variant, str(host["name"][i])))
        if forced is not None:
            t = np.deg2rad(forced)
            w2 = rad[i] + 0.04 + w / 2 * abs(np.cos(t))
            h2 = rad[i] + 0.04 + h / 2 * abs(np.sin(t))
            cx = pos[i, 0] + w2 * np.cos(t)
            cy = pos[i, 1] + h2 * np.sin(t)
            results[i] = (cx, cy)
            placed.append((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))
            continue
        for kf, f in enumerate(inside_fracs):
            cx, cy = pos[i, 0], pos[i, 1] + f * rad[i]
            rect = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
            if np.hypot(w / 2, h / 2 + abs(f) * rad[i]) > rad[i] - 0.028:
                continue
            if not sat_clear(i, rect):
                continue
            score = penalty(i, rect, kf * 0.1)
            if score < best_score:
                best_score, best = score, (cx, cy)
        for ke, a in enumerate((270, 90, 315, 225, 45, 135, 0, 180)):
            t = np.deg2rad(a)
            cx = pos[i, 0] + rad[i] * np.cos(t)
            cy = pos[i, 1] + rad[i] * np.sin(t)
            rect = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
            if not sat_clear(i, rect, padd=0.05):
                continue
            score = penalty(i, rect, 0.9 + ke * 0.05)
            if score < best_score:
                best_score, best = score, (cx, cy)
        for a in cand_angles:
            t = np.deg2rad(a)
            w2 = rad[i] + 0.04 + w / 2 * abs(np.cos(t))
            h2 = rad[i] + 0.04 + h / 2 * abs(np.sin(t))
            cx = pos[i, 0] + w2 * np.cos(t)
            cy = pos[i, 1] + h2 * np.sin(t)
            rect = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
            score = penalty(i, rect, 2.0) + cand_angles.index(a) * 0.15
            if score < best_score:
                best_score, best = score, (cx, cy)
        results[i] = best
        placed.append((best[0] - w / 2, best[1] - h / 2,
                       best[0] + w / 2, best[1] + h / 2))
    return results, placed

def open_spot(pos, rad, label_rects, r_lo, r_hi, rpi, span, half_wh):
    """(x, y) inside the r_lo..r_hi Mpc annulus with most clearance."""
    w2, h2 = half_wh
    best, best_c = None, -np.inf
    for rm in np.arange(r_lo, r_hi + 0.01, 0.35):
        for a in np.arange(6, span - 6, 2.0):
            t = np.deg2rad(a)
            q = np.array([rm * rpi * np.cos(t), rm * rpi * np.sin(t)])
            c = min(np.hypot(*(q - pos[j])) - rad[j] for j in range(n))
            rect = (q[0] - w2, q[1] - h2, q[0] + w2, q[1] + h2)
            for lr in label_rects:
                if rect_overlap(rect, lr):
                    c -= 2.0
            if c > best_c:
                best_c, best = c, q
    return best

# ---------------------------------------------------------------- figure ----
def build(variant):
    full = variant == "full"
    span = 360 if full else 180
    if full:
        fig_w = fig_h = 10.2
        cx_in, cy_in = 5.1, 4.72
        r_out = 4.05
    else:
        fig_w, fig_h = 13.33, 7.5
        cx_in, cy_in = 6.665, 1.28
        r_out = 5.30
    rpi = r_out / D_MAX
    fill = FILL_FULL if full else FILL_FAN

    disk_area = np.pi * r_out ** 2 * (1.0 if full else 0.5)
    scale = np.sqrt(fill * disk_area / (np.pi * np.sum(rvir ** 2)))
    for attempt in range(8):
        rad = rvir * scale
        pos, worst, rdev = relax_polar(rad, rpi, span, r_out)
        if worst > -0.02:
            break
        scale *= 0.95
    print(f"[{variant}] worst gap {worst:+.3f} in | radial deviation "
          f"median {np.median(rdev):.2f} Mpc, max {rdev.max():.2f} "
          f"(scale shrunk {attempt}x)")

    rng = np.random.default_rng(7)
    sat_data = {}
    for i in range(n):
        sub = sats[sats["host"].astype(str) == str(host["name"][i])]
        if len(sub):
            dx, dy = place_sats(sub, rad[i], rng)
            sat_data[i] = (sub, dx, dy)

    if full:
        bounds = (-r_out - 0.65, -r_out - 0.65, r_out + 0.65, r_out + 0.65)
    else:
        bounds = (-r_out - 0.65, 0.02, r_out + 0.65, r_out + 0.62)
    labels, label_rects = place_labels(pos, rad, sat_data, bounds, variant)

    # regime annotations share one spot across the lit-only/all renders
    # (with names hidden there are no label boxes to avoid)
    avoid_rects = [] if HIDE_NAMES else label_rects
    q1 = open_spot(pos, rad, avoid_rects, 1.2, X_SPLIT - 0.5, rpi, span,
                   (0.52, 0.20))
    q2 = open_spot(pos, rad, avoid_rects, 9.8, D_MAX - 0.8, rpi, span,
                   (0.58, 0.20))

    def render(mask, tag):
        """Draw one figure; hosts with mask[i]=False are hidden but their
        layout slot is preserved, so overlays between renders (paper1 vs.
        all, lit vs. all) stay pixel-aligned. `tag` becomes the filename
        suffix (e.g. "" for the full sample, "_lit", "_paper1")."""
        fig = plt.figure(figsize=(fig_w, fig_h))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(-cx_in, fig_w - cx_in)
        ax.set_ylim(-cy_in, fig_h - cy_in)
        ax.set_aspect("equal")
        ax.axis("off")

        # radial background gradient in the integrated-light zone
        ngrid = 720
        gx = np.linspace(-r_out, r_out, ngrid)
        gy = np.linspace(-r_out if full else 0.0, r_out, ngrid)
        GX, GY = np.meshgrid(gx, gy)
        RR = np.hypot(GX, GY) / rpi
        alpha = np.clip((RR - X_SPLIT) / GRAD_RAMP, 0, 1) ** 1.5 * GRAD_ALPHA
        alpha[RR > D_MAX] = 0
        img = np.zeros((ngrid, ngrid, 4))
        img[:, :, :3] = GRAD_COLOR
        img[:, :, 3] = alpha
        ax.imshow(img, extent=(gx[0], gx[-1], gy[0], gy[-1]), origin="lower",
                  zorder=-5, interpolation="bilinear")

        # distance rings
        t1, t2 = (0, 360) if full else (0, 180)
        for dmpc in RINGS_MPC:
            ax.add_patch(Arc((0, 0), 2 * dmpc * rpi, 2 * dmpc * rpi,
                             theta1=t1, theta2=t2, color=C_RING, lw=0.9,
                             zorder=-2))
        ax.add_patch(Arc((0, 0), 2 * D_MAX * rpi, 2 * D_MAX * rpi,
                         theta1=t1, theta2=t2, color="#9aa2ad", lw=1.5,
                         zorder=-2))

        # ring distance labels, dodging host circles near the top
        if full:
            for dmpc in RINGS_MPC:
                txt = f"{dmpc} Mpc" if dmpc == RINGS_MPC[-1] else f"{dmpc}"
                best_a, best_c = 90.0, -np.inf
                for a in np.arange(55, 126, 2.0):
                    t = np.deg2rad(a)
                    q = np.array([dmpc * rpi * np.cos(t),
                                  dmpc * rpi * np.sin(t)])
                    c = min(np.hypot(*(q - pos[j])) - rad[j]
                            for j in range(n))
                    c -= abs(a - 90) * 0.004
                    if c > best_c:
                        best_c, best_a = c, a
                t = np.deg2rad(best_a)
                ax.text(dmpc * rpi * np.cos(t), dmpc * rpi * np.sin(t), txt,
                        fontsize=8.5, color="#8a8f98", ha="center",
                        va="center", zorder=5, path_effects=LABEL_HALO)
        else:
            ax.plot([-r_out - 0.15, r_out + 0.15], [0, 0], color="#555555",
                    lw=1.5, zorder=1, solid_capstyle="round")
            for dmpc in RINGS_MPC:
                for sgn in (-1, 1):
                    x = sgn * dmpc * rpi
                    ax.plot([x, x], [0, -0.09], color="#555555", lw=1.5,
                            zorder=1)
                    ax.text(x, -0.17, f"{dmpc}", fontsize=13,
                            color="#555555", ha="center", va="top")
            ax.plot([0, 0], [0, -0.09], color="#555555", lw=1.5, zorder=1)
            ax.text(0, -0.17, "0", fontsize=13, color="#555555",
                    ha="center", va="top")
            ax.text(0, -0.62, "Distance [Mpc]", fontsize=18, color="#333333",
                    ha="center", va="top")

        # host circles + satellites
        for i in range(n):
            if not mask[i]:
                continue
            if is_lit[i]:
                ec = C_LIT_EDGE if is_iso[i] else C_LIT_EDGE_NONISO
                fc = C_LIT_FACE
                lw, ls = LW_LIT, ("-" if is_iso[i] else "--")
            else:
                ec, fc = C_THIS_EDGE, C_THIS_FACE
                lw, ls = LW_THIS, ("-" if is_iso[i] else "--")
            ax.add_patch(Ellipse(pos[i], 2 * rad[i], 2 * rad[i], facecolor=fc,
                                 edgecolor=ec, lw=lw, ls=ls, zorder=2))
            if i in sat_data:
                sub, dx, dy = sat_data[i]
                for k, row in enumerate(sub):
                    sx, sy = pos[i, 0] + dx[k], pos[i, 1] + dy[k]
                    st = str(row["status"])
                    if st == "Confirmed":
                        ax.scatter(sx, sy, s=SAT_MS,
                                   fc=[SAT_CMAP(SAT_NORM(row["log_m_star"]))],
                                   ec=C_SAT_EDGE, linewidths=SAT_EDGE_LW,
                                   zorder=4)
                    elif st == "Unconfirmed":
                        ax.scatter(sx, sy, marker="x", s=X_MS, c="gray",
                                   linewidths=1.5, zorder=4)
                    else:
                        ax.scatter(sx, sy, s=OPEN_MS, facecolors="none",
                                   edgecolors="darkgray", linewidths=1.2,
                                   zorder=4)

        # Milky Way at the origin
        # ax.scatter(0, 0, marker="*", s=230, c="#F5C242",
        #            edgecolors="#8a6d1f", linewidths=0.8, zorder=5)
        # ax.text(0.10, -0.04, "MW", fontsize=8, color="#8a6d1f", ha="left",
        #         va="top", zorder=5, path_effects=LABEL_HALO,
        #         fontweight="bold")

        # host labels
        if not HIDE_NAMES:
            for i in range(n):
                if not mask[i]:
                    continue
                cx, cy = labels[i]
                ax.text(cx, cy, names[i], fontsize=LABEL_FS, ha="center",
                        va="center", color=C_TEXT, zorder=6,
                        path_effects=LABEL_HALO)

        # regime annotations
        # ax.text(*q1, "Resolved\nStars", fontsize=11.5, fontweight="bold",
        #         color="#777777", ha="center", va="center", zorder=6,
        #         path_effects=LABEL_HALO, linespacing=1.05)
        # ax.text(*q2, "Integrated\nLight", fontsize=11.5, fontweight="bold",
        #         color="#4a90d9", ha="center", va="center", zorder=6,
        #         path_effects=LABEL_HALO, linespacing=1.05)

        # legend + colorbar (identical in both renders for clean overlays)
        handles = [
            Line2D([], [], marker="o", ls="none", ms=13, mfc="none",
                   mec=C_LIT_EDGE, mew=LW_LIT, label="Literature"),
            Line2D([], [], marker="o", ls="none", ms=13, mfc=C_THIS_FACE,
                   mec=C_THIS_EDGE, mew=LW_THIS,
                   label="ELVES-Dwarf (this work)"),
            Line2D([], [], color="gray", lw=2.0, label="Isolated Host"),
            Line2D([], [], color="darkgray", lw=2.0, ls="--",
                   label="Non-Isolated Host"),
            Line2D([], [], marker="o", ls="none", ms=8, mfc="#f0a830",
                   mec=C_SAT_EDGE, mew=1.0, label="Confirmed Sat."),
            Line2D([], [], marker="x", ls="none", ms=6.5, mec="gray",
                   mew=1.5, label="Unconfirmed Sat."),
            Line2D([], [], marker="o", ls="none", ms=6.5, mfc="none",
                   mec="darkgray", mew=1.2, label="Awaiting Follow-up"),
        ]
        if full:
            fig.legend(handles=handles, loc="upper center",
                       bbox_to_anchor=(0.5, 1.002), ncol=4, frameon=False,
                       fontsize=10.5, handletextpad=0.45, columnspacing=1.0)
            cax = fig.add_axes([0.905, 0.055, 0.014, 0.24])
        else:
            fig.legend(handles=handles, loc="upper center",
                       bbox_to_anchor=(0.5, 0.95), ncol=7, frameon=False,
                       fontsize=11.5, handletextpad=0.45, columnspacing=1.15)
            cax = fig.add_axes([0.951, 0.16, 0.012, 0.40])
        cb = mpl.colorbar.ColorbarBase(cax, cmap=SAT_CMAP, norm=SAT_NORM)
        cb.set_ticks([5, 6, 7, 8, 9])
        cb.set_ticklabels([r"$10^{5}$", r"$10^{6}$", r"$10^{7}$",
                           r"$10^{8}$", r"$10^{9}$"])
        cb.ax.tick_params(labelsize=12, length=3.5)
        cb.outline.set_linewidth(1.2)
        cax.set_title(r"$M^{\rm sat}_{\star}$", fontsize=16, pad=10)

        suffix = tag + ("_nonames" if HIDE_NAMES else "")
        for ext in ("png", "pdf", "svg"):
            fig.savefig(HERE / f"elves_dwarf_polar_{variant}{suffix}.{ext}",
                        dpi=250 if ext == "png" else None,
                        transparent=SAVE_TRANSPARENT)
        plt.close(fig)
        print(f"saved elves_dwarf_polar_{variant}{suffix}.[png,pdf,svg]")

    if PAPER1_ONLY:
        # paper-1 hosts + literature hosts (the prior state of the field)
        is_paper1 = np.array([str(nm) in PAPER1_HOSTS
                              for nm in host["name"]])
        render(is_lit | is_paper1, "_paper1")
    else:
        render(np.ones(n, bool), "")
        render(is_lit, "_lit")

# for variant in ("full", "fan"):
    # build(variant)

for variant in ("fan",):
    build(variant)
