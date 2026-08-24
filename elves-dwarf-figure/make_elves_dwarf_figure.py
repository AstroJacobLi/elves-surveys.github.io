#!/usr/bin/env python
"""
ELVES-Dwarf survey summary figure.

Hosts are drawn as circles with radius proportional to Rvir, anchored at their
true (distance, host stellar mass) position. Because 39 hosts cannot occupy
that plane without overlapping, an anchored force relaxation nudges circles
apart while spring-pulling them back toward their true positions; the circles
therefore sit *near* (not exactly at) their catalog values. Satellites are
placed inside each circle at their true projected radius (ang_proj_Rvir),
with angles chosen to avoid marker overlap.

Outputs: elves_dwarf_summary.png / .pdf / .svg
"""

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import Ellipse, FancyArrowPatch
from matplotlib.lines import Line2D
from matplotlib.colors import Normalize, to_rgba
from astropy.table import Table
from pathlib import Path

HERE = Path(__file__).parent
RNG = np.random.default_rng(42)

# ----------------------------------------------------------------- style ----
mpl.rcParams.update({
    "font.family": "Avenir Next",
    "font.weight": "medium",
    "font.size": 16,
    "mathtext.fontset": "stixsans",
    "axes.linewidth": 1.5,
    "xtick.major.size": 6, "xtick.major.width": 1.5,
    "ytick.major.size": 6, "ytick.major.width": 1.5,
    "xtick.direction": "inout", "ytick.direction": "inout",
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
})

# colors & widths matched to 04_sat_distribution_plot.ipynb
C_THIS_EDGE = "royalblue"    # edge, ELVES-Dwarf hosts
C_THIS_FACE = to_rgba("royalblue", 0.10)   # fill = edge at 10% alpha
C_LIT_EDGE = "gray"          # edge, isolated literature hosts
C_LIT_EDGE_NONISO = to_rgba("darkgray", 0.8)
C_LIT_FACE = "none"          # literature circles are unfilled
C_SAT_EDGE = "gray"          # rim of confirmed-satellite dots
C_TEXT = "#333333"
C_GRAD = (0.90, 0.96, 0.92)  # background gradient color (integrated light);
                             # soft mint, distinct from royalblue hosts
LW_THIS, LW_LIT = 2.0, 1.5   # circle edge widths (this work / literature)
SAT_CMAP = plt.cm.rainbow_r
SAT_NORM = Normalize(vmin=5.0, vmax=9.0)   # log M*_sat colorbar range
X_SPLIT = 3.6                # Mpc; resolved stars <-> integrated light

# ------------------------------------------------------------- geometry -----
FIG_W, FIG_H = 13.33, 7.5
AX_RECT = [0.058, 0.100, 0.855, 0.760]
X0, X1 = -0.7, 12.7          # Mpc
Y0, Y1 = 7.02, 10.28         # log Mstar host
AX_W_IN = FIG_W * AX_RECT[2]
AX_H_IN = FIG_H * AX_RECT[3]
XPI = AX_W_IN / (X1 - X0)    # inches per Mpc
YPI = AX_H_IN / (Y1 - Y0)    # inches per dex

FILL_FRAC = 0.315            # fraction of axes area covered by circles
PAD_IN = 0.085               # min gap between circle edges, inches
SAT_MS = 45                  # confirmed-satellite marker area (notebook: 45)
X_MS = 20                    # unconfirmed cross area (notebook: 20)
OPEN_MS = 26                 # awaiting-follow-up open-circle area
SAT_MIN_SEP = 0.135          # min separation between sat markers, inches
LABEL_FS = 8.6
HIDE_NAMES = False           # True = omit host name labels; outputs then get
                             # a "_nonames" suffix

# Manual label angle overrides (degrees, math convention), tune after preview.
LABEL_ANGLE_OVERRIDE = {}

# ---------------------------------------------------------------- data ------
def pretty(name):
    name = str(name)
    if name.startswith("NGC"):
        return f"NGC {int(name[3:])}"
    if name.startswith("IC"):
        return f"IC {int(name[2:])}"
    return name

host = Table.read(HERE / "ELVES-Dwarf_host_cat_260524.fits")
sats = Table.read(HERE / "ELVES-Dwarf_master_cat_260524.fits")
sats = sats[np.isin(sats["status"].astype(str),
                    ["Confirmed", "Unconfirmed", "Not Observed"])]
# only classical dwarfs: log M* > 5 (unknown masses are kept)
_lm = sats["log_m_star"]
_lm = np.asarray(_lm.filled(np.nan) if hasattr(_lm, "filled") else _lm, float)
sats = sats[~np.isfinite(_lm) | (_lm > 5.0)]

is_lit = np.array([str(s).startswith(r"\citetalias") for s in host["data_source"]])
is_iso = np.array(host["isolated"], dtype=bool)
n = len(host)

# ------------------------------------------------- anchored force layout ----
anch = np.column_stack([(host["dist_mpc"] - X0) * XPI,
                        (host["log_mstar_msun"] - Y0) * YPI])
rvir = np.asarray(host["rvir_kpc"], float)
scale = np.sqrt(FILL_FRAC * AX_W_IN * AX_H_IN / (np.pi * np.sum(rvir ** 2)))
rad = rvir * scale           # circle radii in inches

def relax(pos, rad, anchor, n_iter=2000, k0=0.12, pad=PAD_IN, edge=0.04):
    pos = pos.copy()
    for it in range(n_iter):
        # pairwise overlap resolution
        for i in range(len(pos)):
            for j in range(i + 1, len(pos)):
                d = pos[i] - pos[j]
                dist = np.hypot(*d)
                minsep = rad[i] + rad[j] + pad
                if dist < minsep:
                    if dist < 1e-9:
                        d = RNG.normal(size=2); dist = np.hypot(*d)
                    push = 0.5 * (minsep - dist) * d / dist
                    pos[i] += push
                    pos[j] -= push
        # spring back toward true position, annealed to zero
        k = k0 * max(0.0, 1.0 - it / (0.75 * n_iter))
        pos += k * (anchor - pos)
        # keep circles inside the axes
        pos[:, 0] = np.clip(pos[:, 0], rad + edge, AX_W_IN - rad - edge)
        pos[:, 1] = np.clip(pos[:, 1], rad + edge, AX_H_IN - rad - edge)
    return pos

pos = relax(anch, rad, anch)

# verify no residual overlaps
worst = 0.0
for i in range(n):
    for j in range(i + 1, n):
        gap = np.hypot(*(pos[i] - pos[j])) - (rad[i] + rad[j])
        worst = min(worst, gap)
disp = np.hypot(*(pos - anch).T)
print(f"layout: worst gap {worst:+.3f} in | displacement "
      f"median {np.median(disp / XPI):.2f} Mpc-equiv, max {disp.max() / XPI:.2f}")

# ------------------------------------------- satellite placement in hosts ---
def place_sats(sub, R):
    """Return marker offsets (inches) for satellites of one host."""
    rfrac = np.clip(np.asarray(sub["ang_proj_Rvir"], float), 0.10, 1.0)
    r_in = rfrac * max(R - 0.085, 0.35 * R)
    order = np.argsort(-r_in)          # place outer ones first
    theta = np.full(len(sub), np.nan)
    offset = RNG.uniform(0, 2 * np.pi)
    for k, idx in enumerate(order):
        t = offset + np.deg2rad(137.508) * k
        for _ in range(60):            # rotate until no marker collision
            x, y = r_in[idx] * np.cos(t), r_in[idx] * np.sin(t)
            ok = True
            for jdx in order[:k]:
                if np.isnan(theta[jdx]):
                    continue
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

# precompute satellite marker positions so labels can avoid them
sat_data = {}
for i in range(n):
    sub = sats[sats["host"].astype(str) == str(host["name"][i])]
    if len(sub):
        dx, dy = place_sats(sub, rad[i])
        sat_data[i] = (sub, dx, dy)

# ------------------------------------------------------- label placement ----
def label_size(text, fs=LABEL_FS):
    return 0.0605 * len(text) * fs / 8.6, 0.145 * fs / 8.6

def rect_overlap(a, b):
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])

def rect_circle_overlap(rect, c, r):
    qx = np.clip(c[0], rect[0], rect[2])
    qy = np.clip(c[1], rect[1], rect[3])
    return np.hypot(qx - c[0], qy - c[1]) < r

def sat_clearance_ok(i, rect, pad=0.075):
    """True if no satellite marker of host i lands inside the inflated rect."""
    if i not in sat_data:
        return True
    _, dx, dy = sat_data[i]
    r = (rect[0] - pad, rect[1] - pad, rect[2] + pad, rect[3] + pad)
    for x, y in zip(pos[i, 0] + dx, pos[i, 1] + dy):
        if r[0] <= x <= r[2] and r[1] <= y <= r[3]:
            return False
    return True

def place_labels(names):
    placed = []
    results = {}
    cand_angles = [270, 90, 315, 225, 45, 135, 0, 180, 300, 240, 60, 120]
    inside_fracs = [0.52, -0.52, 0.0, 0.66, -0.66, 0.36, -0.36]
    order = np.argsort(-rad)           # big circles claim spots first

    def shared_penalty(i, rect, base):
        score = base
        if rect[0] < 0.02 or rect[2] > AX_W_IN - 0.02: score += 40
        if rect[1] < 0.02 or rect[3] > AX_H_IN - 0.02: score += 40
        for j in range(n):
            if j == i:
                continue
            if rect_circle_overlap(rect, pos[j], rad[j] + 0.01):
                score += 12            # sits on top of another host
            elif rect_circle_overlap(rect, pos[j], rad[j] + 0.06):
                score += 5             # hugs another host: ambiguous
        for prect in placed:
            if rect_overlap(rect, prect):
                score += 25
        return score

    for i in order:
        w, h = label_size(names[i])
        best, best_score = None, np.inf
        if str(host["name"][i]) not in LABEL_ANGLE_OVERRIDE:
            # 1) inside the circle: unambiguous, so preferred when it fits
            for kf, f in enumerate(inside_fracs):
                cx, cy = pos[i, 0], pos[i, 1] + f * rad[i]
                rect = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
                corner = np.hypot(w / 2, h / 2 + abs(f) * rad[i])
                if corner > rad[i] - 0.028:
                    continue           # label does not fit at this offset
                if not sat_clearance_ok(i, rect):
                    continue
                score = shared_penalty(i, rect, kf * 0.1)
                if score < best_score:
                    best_score, best = score, (cx, cy, rect, f"in{f}")
            # 2) straddling the circle edge: still clearly attached
            for ke, a in enumerate((270, 90, 315, 225, 45, 135, 0, 180)):
                t = np.deg2rad(a)
                cx = pos[i, 0] + rad[i] * np.cos(t)
                cy = pos[i, 1] + rad[i] * np.sin(t)
                rect = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
                if not sat_clearance_ok(i, rect, pad=0.05):
                    continue
                score = shared_penalty(i, rect, 0.9 + ke * 0.05)
                if score < best_score:
                    best_score, best = score, (cx, cy, rect, f"edge{a}")
        # 3) outside the circle
        angles = ([LABEL_ANGLE_OVERRIDE[str(host["name"][i])]]
                  if str(host["name"][i]) in LABEL_ANGLE_OVERRIDE else cand_angles)
        for a in angles:
            t = np.deg2rad(a)
            gap = 0.04
            cx = pos[i, 0] + (rad[i] + gap + w / 2 * abs(np.cos(t))) * np.cos(t)
            cy = pos[i, 1] + (rad[i] + gap + h / 2 * abs(np.sin(t))) * np.sin(t)
            rect = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
            score = shared_penalty(i, rect, 2.0)
            score += cand_angles.index(a) * 0.15 if a in cand_angles else 0
            if score < best_score:
                best_score, best = score, (cx, cy, rect, a)
        results[i] = best
        placed.append(best[2])
    return results

names = [pretty(nm) for nm in host["name"]]
labels = place_labels(names)

# ---------------------------------------------------------------- figure ----
fig = plt.figure(figsize=(FIG_W, FIG_H))
ax = fig.add_axes(AX_RECT)
ax.set_xlim(X0, X1)
ax.set_ylim(Y0, Y1)

def in2x(v):  # inches -> data
    return v / XPI
def in2y(v):
    return v / YPI

# background gradient (integrated-light region)
ngrad = 400
gx = np.linspace(X_SPLIT, X1, ngrad)
alpha = np.clip((gx - X_SPLIT) / 3.2, 0, 1) ** 1.5 * 0.85
grad = np.zeros((2, ngrad, 4))
grad[:, :, :3] = C_GRAD
grad[:, :, 3] = alpha
ax.imshow(grad, extent=(X_SPLIT, X1, Y0, Y1), aspect="auto",
          origin="lower", zorder=-5, interpolation="bilinear")

# host circles + satellites
for i in range(n):
    x, y = X0 + in2x(pos[i, 0]), Y0 + in2y(pos[i, 1])
    w, h = 2 * in2x(rad[i]), 2 * in2y(rad[i])
    if is_lit[i]:
        ec = C_LIT_EDGE if is_iso[i] else C_LIT_EDGE_NONISO
        fc = C_LIT_FACE
        lw, ls = LW_LIT, ("-" if is_iso[i] else "--")
    else:
        ec, fc = C_THIS_EDGE, C_THIS_FACE
        lw, ls = LW_THIS, ("-" if is_iso[i] else "--")
    ax.add_patch(Ellipse((x, y), w, h, facecolor=fc, edgecolor=ec,
                         lw=lw, ls=ls, zorder=2))

    if i in sat_data:
        sub, dx, dy = sat_data[i]
        for k, row in enumerate(sub):
            sx, sy = x + in2x(dx[k]), y + in2y(dy[k])
            st = str(row["status"])
            if st == "Confirmed":
                ax.scatter(sx, sy, s=SAT_MS,
                           fc=[SAT_CMAP(SAT_NORM(row["log_m_star"]))],
                           ec=C_SAT_EDGE, linewidths=1.2, zorder=4)
            elif st == "Unconfirmed":
                ax.scatter(sx, sy, marker="x", s=X_MS, c="gray",
                           linewidths=1.5, zorder=4)
            else:  # Not Observed
                ax.scatter(sx, sy, s=OPEN_MS, facecolors="none",
                           edgecolors="darkgray", linewidths=1.2, zorder=4)

# labels
if not HIDE_NAMES:
    for i in range(n):
        cx, cy, _, _ = labels[i]
        ax.text(X0 + in2x(cx), Y0 + in2y(cy), names[i], fontsize=LABEL_FS,
                ha="center", va="center", color=C_TEXT, zorder=6,
                path_effects=[pe.withStroke(linewidth=2.6, foreground="white",
                                            alpha=0.85)])

# ------------------------------------------------------------ axes decor ----
ax.set_xlabel("Distance [Mpc]", fontsize=17)
ax.set_ylabel(r"Host Stellar Mass [$M_\odot$]", fontsize=17)
ax.set_xticks(np.arange(0, 13, 2))
ax.set_yticks([8, 9, 10])
ax.set_yticklabels([r"$10^{8}$", r"$10^{9}$", r"$10^{10}$"])
ax.tick_params(labelsize=16)   # notebook: no minor ticks, inout majors
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
# arrow tips on the axes
ax.plot(1, Y0, ">", ms=9, color="k", transform=ax.get_yaxis_transform(),
        clip_on=False, zorder=10)
ax.plot(X0, 1, "^", ms=9, color="k", transform=ax.get_xaxis_transform(),
        clip_on=False, zorder=10)

# resolved / integrated annotation above the axes
ytop = 1.030
ax.add_patch(FancyArrowPatch((X0 + 0.15, Y1 + (Y1 - Y0) * (ytop - 1)),
                             (X_SPLIT, Y1 + (Y1 - Y0) * (ytop - 1)),
                             arrowstyle="|-|,widthA=4,widthB=4", lw=2.6,
                             color="#666666", clip_on=False))
ax.add_patch(FancyArrowPatch((X_SPLIT + 0.12, Y1 + (Y1 - Y0) * (ytop - 1)),
                             (X1 - 0.05, Y1 + (Y1 - Y0) * (ytop - 1)),
                             arrowstyle="-|>,head_width=3.5,head_length=7",
                             lw=2.6, color="#4a90d9", clip_on=False,
                             mutation_scale=1.4))
ax.text((X0 + X_SPLIT) / 2, Y1 + (Y1 - Y0) * 0.065, "Resolved Stars",
        fontsize=17, fontweight="bold", color="#555555",
        ha="center", va="bottom", clip_on=False)
ax.text((X_SPLIT + X1) / 2, Y1 + (Y1 - Y0) * 0.065, "Integrated Light",
        fontsize=17, fontweight="bold", color="#4a90d9",
        ha="center", va="bottom", clip_on=False)

# ---------------------------------------------------------------- legend ----
handles = [
    Line2D([], [], marker="o", ls="none", ms=13, mfc="none",
           mec=C_LIT_EDGE, mew=LW_LIT, label="Literature"),
    Line2D([], [], marker="o", ls="none", ms=13, mfc=C_THIS_FACE,
           mec=C_THIS_EDGE, mew=LW_THIS, label="ELVES-Dwarf (this work)"),
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
fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 1.005),
           ncol=7, frameon=False, fontsize=11.5, handletextpad=0.45,
           columnspacing=1.15)

# --------------------------------------------------------------- colorbar ---
cax = fig.add_axes([0.938, 0.13, 0.013, 0.38])
cb = mpl.colorbar.ColorbarBase(cax, cmap=SAT_CMAP, norm=SAT_NORM)
cb.set_ticks([5, 6, 7, 8, 9])
cb.set_ticklabels([r"$10^{5}$", r"$10^{6}$", r"$10^{7}$", r"$10^{8}$",
                   r"$10^{9}$"])
cb.ax.tick_params(labelsize=12, length=3.5)
cb.outline.set_linewidth(1.2)
cax.set_title(r"$M^{\rm sat}_{\star}$", fontsize=16, pad=10)

# ----------------------------------------------------------------- output ---
suffix = "_nonames" if HIDE_NAMES else ""
for ext in ("png", "pdf", "svg"):
    fig.savefig(HERE / f"elves_dwarf_summary{suffix}.{ext}",
                dpi=250 if ext == "png" else None)
print(f"saved elves_dwarf_summary{suffix}.[png,pdf,svg]")
