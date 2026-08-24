#!/usr/bin/env python
"""
Build the host + satellite data an ELVES Aladin viewer reads.

Two catalogues are joined into one small json per survey:

  * `<Survey>_host_cat_*.fits`   — the hosts and their properties
  * `<Survey>_master_cat_*.fits` — the satellite candidates

Which survey to build is `--survey`; everything else follows from its slug. The
catalogues are found under `public/data/<slug>/`, i.e. the files this website
already publishes, so the viewer shows exactly what visitors can download, and
the output lands in `public/explorer/<slug>/`.

A third input, `data/hosts_config.py`, is optional and only consulted for hosts
the catalogue cannot place itself. Earlier host catalogues had no RA/Dec column
and the config was the only source of positions; the v1 release carries both.

    python build_catalog.py --survey elves-dwarf --install
    python build_catalog.py --survey elves-dwarf --out /tmp/elves_dwarf.json
    python build_catalog.py --list
    python build_catalog.py --host-cat ... --master-cat ... --hosts-config ...
"""

import argparse
import glob
import importlib.util
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)

# One entry per survey that can have an explorer page. `prefix` is how the
# release names its FITS files; the newest matching pair under
# public/data/<slug>/ is what gets built, so a new release only needs dropping
# in. A survey listed here but with no catalogues yet simply reports as such.
#
# The column names read below are the ELVES-Dwarf v1 schema. A survey whose
# catalogues name things differently will need those reads mapped per survey —
# the paths are parameterised here, the schema is not.
SURVEYS = {
    "elves":       {"name": "ELVES",       "prefix": "ELVES"},
    "elves-dwarf": {"name": "ELVES-Dwarf", "prefix": "ELVES-Dwarf"},
    "elves-field": {"name": "ELVES-Field", "prefix": "ELVES-Field"},
}
DEFAULT_SURVEY = "elves-dwarf"

# Only read if it exists; see the module docstring.
HOSTS_CONFIG = "/home/jiaxuanl/Research/SALAD/data/hosts_config.py"

RAD_TO_ARCMIN = np.degrees(1.0) * 60.0

# The v1 host catalogue places all 39 hosts itself; this is the last-resort
# escape hatch for a host that reaches neither the catalogue nor hosts_config.py.
EXTRA_POSITIONS = {
    "M33": (23.46208, 30.66017),
}


def version_key(path):
    """Sort catalogue filenames so v10 lands after v2, not before it."""
    return [int(t) if t.isdigit() else t
            for t in re.split(r"(\d+)", os.path.basename(path))]


def newest_catalog(data_dir, prefix, kind):
    hits = glob.glob(os.path.join(data_dir, f"{prefix}_{kind}_cat_*.fits"))
    return max(hits, key=version_key) if hits else None


def survey_config(slug):
    """Everything about a survey that is derived from its slug."""
    if slug not in SURVEYS:
        sys.exit(f"unknown survey {slug!r} — known: {', '.join(sorted(SURVEYS))}")
    entry = SURVEYS[slug]
    data_dir = os.path.join(SITE, "public", "data", slug)
    return {
        "slug": slug,
        "name": entry["name"],
        "data_dir": data_dir,
        "host_cat": newest_catalog(data_dir, entry["prefix"], "host"),
        "master_cat": newest_catalog(data_dir, entry["prefix"], "master"),
        # The viewer fetches this next to its own index.html.
        "json": slug.replace("-", "_") + ".json",
        "install_dir": os.path.join(SITE, "public", "explorer", slug),
    }


def clean(v, nd=6):
    """FITS blanks / NaN -> JSON null (JSON.parse rejects NaN)."""
    if v is None or v is np.ma.masked:
        return None
    if isinstance(v, (bytes, np.bytes_)):
        v = v.decode("utf-8", "replace")
    if isinstance(v, (str, np.str_)):
        v = str(v).strip()
        # the master catalogue uses LaTeX \nodata as a blank
        return None if (not v or v in {"--", "\\nodata", "nan", "None"}) else v
    if isinstance(v, (bool, np.bool_)):
        return bool(v)
    v = float(v)
    return None if not np.isfinite(v) else round(v, nd)


def resolve_positions(ht, config_path):
    """Where each host sits on the sky.

    The v1 host catalogue carries ra/dec, so it answers for itself. Older ones
    did not, which is why hosts_config.py is still accepted — it fills in any
    host the catalogue cannot place, and is skipped when it is not readable.
    """
    pos = {}
    if "ra" in ht.colnames and "dec" in ht.colnames:
        for row in ht:
            name, ra, dec = clean(row["name"]), clean(row["ra"]), clean(row["dec"])
            if name and ra is not None and dec is not None:
                pos[name] = (ra, dec)

    if config_path and os.path.exists(config_path):
        for name, radec in load_positions(config_path).items():
            pos.setdefault(name, radec)
    elif not pos:
        sys.exit(f"host catalogue has no ra/dec column and {config_path} is not readable")

    for name, radec in EXTRA_POSITIONS.items():
        pos.setdefault(name, radec)
    return pos


def load_positions(path):
    spec = importlib.util.spec_from_file_location("hosts_config", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out = {}
    for name, cfg in mod.all_hosts.items():
        if isinstance(cfg, dict) and cfg.get("ra") is not None and cfg.get("dec") is not None:
            try:
                out[str(name)] = (float(cfg["ra"]), float(cfg["dec"]))
            except (TypeError, ValueError):
                pass
    return out


def report_surveys():
    """What install.sh prints when asked which surveys it can build."""
    for slug in sorted(SURVEYS):
        cfg = survey_config(slug)
        ready = "ready" if cfg["host_cat"] and cfg["master_cat"] else "no catalogues yet"
        print(f"{slug}\t{cfg['name']}\t{ready}")


def print_config(cfg):
    """KEY=value lines for install.sh to read; order is not significant."""
    for key in ("slug", "name", "json", "install_dir", "host_cat", "master_cat"):
        print(f"{key.upper()}={cfg[key] or ''}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--survey", default=DEFAULT_SURVEY, choices=sorted(SURVEYS))
    ap.add_argument("--host-cat", default=None)
    ap.add_argument("--master-cat", default=None)
    ap.add_argument("--hosts-config", default=HOSTS_CONFIG)
    ap.add_argument("--out", default=None)
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--install-dir", default=None)
    ap.add_argument("--list", action="store_true",
                    help="list the surveys and whether their catalogues are present")
    ap.add_argument("--print-config", action="store_true",
                    help="print this survey's resolved paths and exit (used by install.sh)")
    args = ap.parse_args()

    if args.list:
        report_surveys()
        return

    cfg = survey_config(args.survey)
    host_cat = args.host_cat or cfg["host_cat"]
    master_cat = args.master_cat or cfg["master_cat"]
    install_dir = args.install_dir or cfg["install_dir"]

    if args.print_config:
        print_config(cfg)
        return

    for label, path in (("host", host_cat), ("master", master_cat)):
        if not path:
            sys.exit(f"no {label} catalogue for {args.survey}: nothing matches "
                     f"{SURVEYS[args.survey]['prefix']}_{label}_cat_*.fits in {cfg['data_dir']}")

    # Deferred so --list and --print-config stay instant; astropy is slow to import.
    from astropy.table import Table

    print(f"{cfg['name']}: {os.path.basename(host_cat)} + {os.path.basename(master_cat)}",
          file=sys.stderr)
    ht = Table.read(host_cat)
    mt = Table.read(master_cat)
    pos = resolve_positions(ht, args.hosts_config)

    # ── satellites, grouped by host ─────────────────────────────────
    sats_by_host = {}
    for row in mt:
        host = clean(row["host"])
        ra, dec = clean(row["ra"]), clean(row["dec"])
        if host is None or ra is None or dec is None:
            continue
        sats_by_host.setdefault(host, []).append({
            "name": clean(row["name"]),
            "ra": ra, "dec": dec,
            "status": clean(row["status"]) or "Unknown",
            "Psat": clean(row["Psat"], 3),
            "dist": clean(row["distance"], 3),
            "dist_method": clean(row["dist_method"]),
            "followup": clean(row["followup"]),
            "reff": clean(row["reff_sersic"], 2),          # arcsec
            "m_V": clean(row["m_V_sersic"], 2),
            "m_g": clean(row["m_g_sersic"], 2),
            "gr": clean(row["gr_sersic"], 3),
            "mu0_V": clean(row["mu_0_V"], 2),
            "n_sersic": clean(row["n_sersic"], 2),
            "ell": clean(row["ell_sersic"], 3),
            "logM": clean(row["log_m_star"], 2),
            "d_proj_kpc": clean(row["ang_proj_kpc"], 1),
            "d_proj_rvir": clean(row["ang_proj_Rvir"], 3),
            "velocity": clean(row["velocity"], 1),
            "ms_outlier": clean(row["ms_outlier"]),
            "reference": clean(row["reference"]),
        })

    # ── hosts ───────────────────────────────────────────────────────
    hosts, missing = [], []
    for row in ht:
        name = clean(row["name"])
        if name not in pos:
            missing.append(name)
            continue
        ra, dec = pos[name]
        dist = clean(row["dist_mpc"], 3)
        rvir = clean(row["rvir_kpc"], 1)
        # Angular virial radius, so the viewer can frame each host by its own
        # halo rather than by a fixed angle: theta = R / D.
        rvir_arcmin = None
        if rvir and dist:
            rvir_arcmin = round(rvir / (dist * 1000.0) * RAD_TO_ARCMIN, 4)

        sats = sats_by_host.get(name, [])
        sats.sort(key=lambda s: (s["d_proj_kpc"] is None, s["d_proj_kpc"] or 0))
        hosts.append({
            "name": name,
            "ra": round(ra, 6), "dec": round(dec, 6),
            "dist": dist,
            "dist_err": clean(row["dist_err_mpc"], 3),
            "dist_method": clean(row["dist_method"]),
            "vh": clean(row["v_h_km_s"], 1),
            "logMstar": clean(row["log_mstar_msun"], 3),
            "logMstar_err": clean(row["log_mstar_err"], 3),
            "M_V": clean(row["M_V"], 2),
            "gr": clean(row["g_r_0"], 3),
            "logLK": clean(row["log_l_ks_lsun"], 3),
            "rvir": rvir,
            "rvir_arcmin": rvir_arcmin,
            "theta1": clean(row["theta1"], 2),
            "theta5": clean(row["theta5"], 2),
            "isolated": clean(row["isolated"]),
            "area": clean(row["area_deg2"], 3),
            "frac_unmasked": clean(row["frac_unmasked"], 3),
            "data_source": clean(row["data_source"]),
            "reference": clean(row["reference"]),
            "sats": sats,
            "n_sats": len(sats),
        })

    if missing:
        print(f"WARNING: no position for {missing} — dropped", file=sys.stderr)

    # By name, which is the order the viewer's dropdown and host list show.
    # The catalogue numbers are zero-padded, so this matches numeric order
    # within each of DDO / ESO / IC / NGC / UGC.
    hosts.sort(key=lambda h: h["name"])
    orphans = sorted(set(sats_by_host) - {h["name"] for h in hosts})
    if orphans:
        print(f"WARNING: satellites whose host was dropped: {orphans}", file=sys.stderr)

    n_sats = sum(h["n_sats"] for h in hosts)
    by_status = {}
    for h in hosts:
        for s in h["sats"]:
            by_status[s["status"]] = by_status.get(s["status"], 0) + 1
    print(f"{len(hosts)} hosts, {n_sats} satellites {by_status}", file=sys.stderr)

    payload = {
        "format": "elves-viewer/1",
        "survey": cfg["slug"],
        "survey_name": cfg["name"],
        "host_catalog": os.path.basename(host_cat),
        "master_catalog": os.path.basename(master_cat),
        "n_hosts": len(hosts), "n_sats": n_sats,
        "status_counts": by_status,
        "hosts": hosts,
    }

    out = args.out or os.path.join(HERE, cfg["json"])
    with open(out, "w") as f:
        json.dump(payload, f, separators=(",", ":"))
    print(f"wrote {out}", file=sys.stderr)

    if args.install:
        os.makedirs(install_dir, exist_ok=True)
        dest = os.path.join(install_dir, cfg["json"])
        with open(dest, "w") as f:
            json.dump(payload, f, separators=(",", ":"))
        print(f"installed {dest}", file=sys.stderr)


if __name__ == "__main__":
    main()
