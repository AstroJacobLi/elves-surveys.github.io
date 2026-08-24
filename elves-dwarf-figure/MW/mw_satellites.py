"""
3D spatial distribution of Milky Way satellite galaxies, reproducing the
style of the Simon & Geha (2021) graphic: white background, a thin black
sphere outline with equatorial distance rings, glossy shaded balls for the
satellites, a small spiral glyph for the Milky Way, a scale bar, and a
boxed legend. Here the balls are colored AND sized by stellar mass instead
of discovery dataset.

Data: Local Volume Database (Pace 2024), ../dwarf_mw.csv.

Usage:
    python mw_satellites.py             # static figure (PNG + PDF)
    python mw_satellites.py --labels    # static figure with a few labels
    python mw_satellites.py --movie     # rotating GIF (and MP4 if possible)
"""

import argparse
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize, to_rgb
from matplotlib.patches import Rectangle
import matplotlib.patheffects as pe

# ----------------------------------------------------------------------------
# Style (light theme by default; set_theme(dark=True) flips to dark)
# ----------------------------------------------------------------------------
BG = "white"              # figure background
LINE = "#1a1a1a"          # thin line art
TEXT_DIM = "#666666"
GRID_C = "#cfcfcf"        # faint polar grid on the plane
STEM_C = "#9a9a9a"        # guide stems and leader lines
RING_FAR = "#8a8a8a"      # far half of the plane rings


def set_theme(dark=False):
    global BG, LINE, TEXT_DIM, GRID_C, STEM_C, RING_FAR
    if dark:
        BG = "#0b1020"        # deep night blue
        LINE = "#e6e9f0"
        TEXT_DIM = "#9aa3b5"
        GRID_C = "#39415a"
        STEM_C = "#8391ad"
        RING_FAR = "#6f7890"
    else:
        BG, LINE, TEXT_DIM = "white", "#1a1a1a", "#666666"
        GRID_C, STEM_C, RING_FAR = "#cfcfcf", "#9a9a9a", "#8a8a8a"

# muted short-arc rainbow ("sunset"): gold -> orange -> red -> wine-purple,
# light -> dark with stellar mass
colorlist = ['#d53e4f','#fc8d59','#fee08b','#e6f598','#99d594','#3288bd']
# colorlist = ['#ffffcc','#c7e9b4','#7fcdbb','#41b6c4','#2c7fb8','#253494']
MASS_CMAP = LinearSegmentedColormap.from_list(
    "sunset", colorlist
)
LOGM_MIN, LOGM_MAX = 2.0, 9.6

R_SUN = 8.122       # kpc
R_SPHERE = 300.0    # kpc, outer sphere (as in the original)
ELEV = 15.0         # deg, viewing elevation of the Galactic plane

HERE = os.path.dirname(os.path.abspath(__file__))

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
})


# ----------------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------------
def load_data():
    df = pd.read_csv(os.path.join(HERE, "..", "dwarf_mw.csv"))
    df = df[df["confirmed_real"] == 1].reset_index(drop=True)
    # Galactocentric cartesian coordinates from Galactic (l, b, heliocentric d)
    l = np.radians(df["ll"].values)
    b = np.radians(df["bb"].values)
    d = df["distance"].values  # kpc, heliocentric
    df = df.assign(X=d * np.cos(b) * np.cos(l) - R_SUN,
                   Y=d * np.cos(b) * np.sin(l),
                   Z=d * np.sin(b))
    r = np.sqrt(df["X"] ** 2 + df["Y"] ** 2 + df["Z"] ** 2)
    assert np.median(np.abs(r - df["distance_gc"])) < 2.0
    return df


# ----------------------------------------------------------------------------
# Orthographic projection
# ----------------------------------------------------------------------------
def project(x, y, z, azim_deg, elev_deg=ELEV):
    """Screen (u, v) and depth (larger = closer to camera)."""
    a, e = np.radians(azim_deg), np.radians(elev_deg)
    u = -x * np.sin(a) + y * np.cos(a)
    x1 = x * np.cos(a) + y * np.sin(a)
    v = z * np.cos(e) - x1 * np.sin(e)
    depth = x1 * np.cos(e) + z * np.sin(e)
    return u, v, depth


# ----------------------------------------------------------------------------
# Glossy ball sprite (radial shading + upper-left highlight)
# ----------------------------------------------------------------------------
MATTE = False  # matte shading instead of glossy (no specular highlight)


def ball_sprite(color, n=96):
    base = np.array(to_rgb(color))
    lin = np.linspace(-1, 1, n)
    xx, yy = np.meshgrid(lin, lin)
    r2 = xx ** 2 + yy ** 2
    zz = np.sqrt(np.clip(1 - r2, 0, 1))
    light = np.array([-0.42, 0.50, 0.76])
    light /= np.linalg.norm(light)
    diff = np.clip(xx * light[0] + yy * light[1] + zz * light[2], 0, 1)
    if MATTE:
        inten = 0.62 + 0.38 * diff
        spec = np.zeros_like(diff)
    else:
        inten = 0.30 + 0.72 * diff
        spec = 0.85 * diff ** 24
    img = np.empty((n, n, 4))
    img[..., :3] = np.clip(base[None, None, :] * inten[..., None]
                           + spec[..., None], 0, 1)
    # anti-aliased edge
    img[..., 3] = np.clip((1 - np.sqrt(r2)) * n / 2.5, 0, 1)
    return img


def ball_radius(logm):
    """Ball radius in kpc (data units), scaled with log stellar mass."""
    return 3.0 + 1.5 * (np.asarray(logm, dtype=float) - LOGM_MIN)


def ball_color(logm):
    return MASS_CMAP(Normalize(LOGM_MIN, LOGM_MAX)(np.asarray(logm, float)))


def draw_ball(ax, u, v, r, color, zorder):
    ax.imshow(ball_sprite(color), extent=(u - r, u + r, v - r, v + r),
              origin="lower", zorder=zorder, interpolation="bilinear")


# ----------------------------------------------------------------------------
# Milky Way spiral glyph
# ----------------------------------------------------------------------------
def draw_mw_glyph(ax, azim, size=15.0, zorder=7):
    """Small two-armed spiral lying in the Galactic plane at the center.

    The spiral is fixed in world coordinates and sent through the same
    projection as everything else, so it rotates with the scene in the
    movie. Drawn on top of the satellites (like a map marker) with a white
    stroke under the spiral so it stays visible when a ball sits behind it.
    """
    t = np.linspace(0, 2.4 * np.pi, 120)
    for phase in (0, np.pi):
        rr = size * 0.16 * np.exp(0.30 * t)
        rr = np.clip(rr, 0, size)
        gx, gy = rr * np.cos(t + phase), rr * np.sin(t + phase)
        u, v, _ = project(gx, gy, np.zeros_like(gx), azim)
        ax.plot(u, v, color=LINE, lw=1.2, zorder=zorder,
                solid_capstyle="round",
                path_effects=[pe.withStroke(linewidth=3.2,
                                            foreground=BG)])
    ax.scatter([0], [0], s=16, color=LINE, zorder=zorder + 0.1, lw=0)


# ----------------------------------------------------------------------------
# Scene
# ----------------------------------------------------------------------------
# label text positions in data coords (kpc), tuned for azim=125;
# a thin leader line is drawn when the text sits away from the ball
LABELS = {
    "LMC": (115, -42, "left"),
    "SMC": (85, -90, "left"),
    "Sagittarius": (-150, 28, "right"),
    "Fornax": (61, -148, "center"),
    "Leo I": (172, 214, "center"),
    "Sculptor": (-90, -112, "right"),
    "Draco": (-110, 62, "right"),
    "Ursa Minor": (-48, 88, "right"),
    "Antlia II": (158, 96, "left"),
    "Eridanus II": (195, -255, "center"),
    "Canes Venatici I": (-22, 200, "center"),
    "Leo II": (87, 197, "center"),
}


def draw_plane_ring(ax, R, azim, lw, zorder=2):
    """Ring on the Galactic plane, near half heavier than the far half."""
    theta = np.linspace(0, 2 * np.pi, 361)
    u, v, d = project(R * np.cos(theta), R * np.sin(theta),
                      np.zeros_like(theta), azim)
    near, far = d >= 0, d < 0
    ax.plot(np.where(far, u, np.nan), np.where(far, v, np.nan),
            color=RING_FAR, lw=0.75 * lw, zorder=zorder)
    ax.plot(np.where(near, u, np.nan), np.where(near, v, np.nan),
            color=LINE, lw=lw, zorder=zorder)


def draw_scene(ax, df, azim, show_labels=False, show_stems=False,
               show_grid=False):
    ax.set_aspect("equal")
    ax.axis("off")

    theta = np.linspace(0, 2 * np.pi, 361)

    # outer sphere silhouette (orthographic -> a circle)
    ax.plot(R_SPHERE * np.cos(theta), R_SPHERE * np.sin(theta),
            color=LINE, lw=1.1, zorder=2)

    # faint polar grid on the Galactic plane: it rotates with the scene
    # and gives the plane a surface (depth cue for the movie)
    if show_grid:
        for R in (50, 150, 200, 250):
            u, v, _ = project(R * np.cos(theta), R * np.sin(theta),
                              np.zeros_like(theta), azim)
            ax.plot(u, v, color=GRID_C, lw=0.45, zorder=1.2)
        rline = np.linspace(28, R_SPHERE, 60)
        for ang in np.radians(np.arange(0, 360, 30)):
            u, v, _ = project(rline * np.cos(ang), rline * np.sin(ang),
                              np.zeros_like(rline), azim)
            ax.plot(u, v, color=GRID_C, lw=0.45, zorder=1.2)

    # equatorial rings on the Galactic plane: sphere equator + 100 kpc ring
    for R, lw in [(R_SPHERE, 1.1), (100.0, 1.0)]:
        draw_plane_ring(ax, R, azim, lw)

    draw_mw_glyph(ax, azim)

    # satellites: glossy balls, far ones first
    X, Y, Z = df["X"].values, df["Y"].values, df["Z"].values
    us, vs, ds = project(X, Y, Z, azim)
    logm = df["mass_stellar"].values
    rad = ball_radius(logm)
    cols = ball_color(logm)
    order = np.argsort(ds)

    # guide stems: perpendicular drop from each dwarf to the Galactic plane,
    # with a small dot at the foot (anchors the 3D motion in the movie)
    if show_stems:
        uf, vf, _ = project(X, Y, np.zeros_like(Z), azim)
        for i in range(len(df)):
            ax.plot([uf[i], us[i]], [vf[i], vs[i]], color=STEM_C,
                    lw=0.7, alpha=0.85, zorder=3, solid_capstyle="round")
        ax.scatter(uf, vf, s=4, color=STEM_C, alpha=0.85, lw=0, zorder=3)

    for rank, i in enumerate(order):
        draw_ball(ax, us[i], vs[i], rad[i], cols[i], zorder=4 + 0.01 * rank)

    if show_labels:
        names = df["name"].values
        for i in range(len(df)):
            if names[i] not in LABELS:
                continue
            tx, ty, ha = LABELS[names[i]]
            ax.text(tx, ty, names[i], ha=ha, va="center",
                    fontsize=10.5, color=LINE, zorder=8)
            # leader line if the text is well separated from the ball
            gap = np.hypot(tx - us[i], ty - vs[i])
            if gap > rad[i] + 22:
                dx, dy = us[i] - tx, vs[i] - ty
                dx, dy = dx / gap, dy / gap
                start = 12 if ha == "center" else 6
                ax.plot([tx + dx * start, us[i] - dx * (rad[i] + 2.5)],
                        [ty + dy * start, vs[i] - dy * (rad[i] + 2.5)],
                        color=STEM_C, lw=0.7, zorder=8)

    ax.set_xlim(-R_SPHERE * 1.30, R_SPHERE * 1.42)
    ax.set_ylim(-R_SPHERE * 1.22, R_SPHERE * 1.12)


def add_scalebar(ax):
    x0, x1, y = -105, -5, -R_SPHERE * 1.12
    ax.plot([x0, x1], [y, y], color=LINE, lw=1.0, zorder=6)
    for x in (x0, x1):
        ax.plot([x, x], [y - 5, y + 5], color=LINE, lw=1.0, zorder=6)
    ax.text((x0 + x1) / 2, y + 10, "100 kiloparsecs", ha="center",
            va="bottom", fontsize=12.5, color=LINE, zorder=6)


def add_legend(ax):
    """Boxed legend: ball size/color = stellar mass, plus the MW glyph."""
    bx, by, bw, bh = R_SPHERE * 0.56, -R_SPHERE * 1.12, R_SPHERE * 0.78, R_SPHERE * 0.28
    ax.add_patch(Rectangle((bx, by), bw, bh, facecolor=BG,
                           edgecolor=LINE, lw=1.2, zorder=9))

    ax.text(bx + bw / 2, by + bh - 22, r"Stellar mass ($M_\odot$)",
            ha="center", fontsize=15, color=LINE, zorder=11)
    # example balls: 10^3, 10^5, 10^7, 10^9
    xs = np.linspace(bx + 32, bx + bw - 32, 4)
    yb = by + bh - 46
    y_lab = yb - ball_radius(9.0) - 5
    for x, lm in zip(xs, [3.0, 5.0, 7.0, 9.0]):
        r = ball_radius(lm)
        ax.imshow(ball_sprite(ball_color(lm)),
                  extent=(x - r, x + r, yb - r, yb + r),
                  origin="lower", zorder=11, interpolation="bilinear")
        ax.text(x, y_lab, rf"$10^{int(lm)}$", ha="center", va="top",
                fontsize=13, color=LINE, zorder=11)
    # # Milky Way entry
    # ymw = by + 16
    # fs = np.sin(np.radians(ELEV))
    # t = np.linspace(0, 2.4 * np.pi, 120)
    # for phase in (0, np.pi):
    #     rr = np.clip(10 * 0.16 * np.exp(0.30 * t), 0, 10)
    #     ax.plot(xs[0] + rr * np.cos(t + phase),
    #             ymw + rr * np.sin(t + phase) * fs,
    #             color=LINE, lw=0.9, zorder=11)
    # ax.scatter([xs[0]], [ymw], s=8, color=LINE, zorder=11, lw=0)
    # ax.text(xs[0] + 22, ymw, "Milky Way", va="center", fontsize=12.5,
    #         color=LINE, zorder=11)


def make_figure(df, azim, dpi=200, show_labels=False, show_stems=False,
                show_grid=False):
    fig = plt.figure(figsize=(10.2, 9.2), dpi=dpi, facecolor=BG)
    ax = fig.add_axes([0.01, 0.01, 0.98, 0.98])
    draw_scene(ax, df, azim, show_labels=show_labels, show_stems=show_stems,
               show_grid=show_grid)
    # add_scalebar(ax)
    add_legend(ax)
    # fig.text(0.03, 0.022, "Data: Local Volume Database (Pace 2024)",
    #          fontsize=8.5, color=TEXT_DIM)
    return fig


# ----------------------------------------------------------------------------
# Outputs
# ----------------------------------------------------------------------------
def render_static(df, azim=125, labels=False, stems=False, grid=False,
                  dark=False):
    fig = make_figure(df, azim, show_labels=labels, show_stems=stems,
                      show_grid=grid)
    suffix = (("_labeled" if labels else "") + ("_stems" if stems else "")
              + ("_dark" if dark else ""))
    png = os.path.join(HERE, f"mw_satellites_3d{suffix}.png")
    fig.savefig(png, facecolor=BG)
    fig.savefig(png.replace(".png", ".pdf"), transparent=True)
    plt.close(fig)
    print(f"wrote {png} (+.pdf)")


def render_movie(df, n_frames=90, fps=18, dark=False):
    import imageio.v2 as imageio

    frames = []
    for k in range(n_frames):
        azim = 125 + 360.0 * k / n_frames
        fig = make_figure(df, azim, dpi=110, show_stems=True, show_grid=True)
        fig.canvas.draw()
        frames.append(np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy())
        plt.close(fig)
        if (k + 1) % 10 == 0:
            print(f"  frame {k + 1}/{n_frames}")

    suffix = "_dark" if dark else ""
    gif = os.path.join(HERE, f"mw_satellites_rotation{suffix}.gif")
    imageio.mimsave(gif, frames, fps=fps, loop=0)
    print(f"wrote {gif}")
    mp4 = gif.replace(".gif", ".mp4")
    try:
        imageio.mimsave(mp4, frames, fps=fps, codec="libx264", quality=8)
        print(f"wrote {mp4}")
    except Exception as err:
        if os.path.exists(mp4):
            os.remove(mp4)
        print(f"(mp4 skipped, install imageio-ffmpeg to enable: {err})")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--movie", action="store_true")
    p.add_argument("--labels", action="store_true")
    p.add_argument("--stems", action="store_true",
                   help="guide lines from dwarfs to the Galactic plane "
                        "(always on in the movie)")
    p.add_argument("--grid", action="store_true",
                   help="faint polar grid on the Galactic plane "
                        "(always on in the movie)")
    p.add_argument("--dark", action="store_true",
                   help="dark background theme (writes *_dark files)")
    p.add_argument("--azim", type=float, default=125)
    args = p.parse_args()

    set_theme(dark=args.dark)
    df = load_data()
    if args.movie:
        render_movie(df, dark=args.dark)
    else:
        render_static(df, azim=args.azim, labels=args.labels,
                      stems=args.stems, grid=args.grid, dark=args.dark)
