#!/usr/bin/env python3
"""Publish figures from elves-dwarf-figure/ into public/figures/.

Raster files are downscaled to MAX_RASTER_WIDTH (the print exports are ~3300px
wide, far more than the page ever shows). SVG exports from matplotlib get three
fixes instead, all safe to re-run:

1. Drop the opaque white page rect so the figure sits on the page background.
2. Add a fallback stack behind the macOS-only fonts matplotlib names.
3. Strip the fixed pt width/height so the viewBox drives responsive sizing.

Usage: python3 scripts/prepare-figures.py <in> <out>
       python3 scripts/prepare-figures.py        # rebuild the defaults below
"""
import re
import shutil
import sys
from pathlib import Path

# (source, destination) pairs rebuilt when the script is run with no arguments.
# To publish a different variant (the labelled fan, the 360-degree full disk,
# or the SVG rather than the PNG), add it here or pass two paths on the CLI.
DEFAULTS = [
    (
        "elves-dwarf-figure/elves_dwarf_polar_fan_nonames.png",
        "public/figures/elves_dwarf_polar_fan_nonames.png",
    ),
]

# The figure renders at most ~760 CSS px wide, so this still covers 2x screens.
MAX_RASTER_WIDTH = 1600

FONT_FALLBACKS = {
    "'Avenir Next'": "'Avenir Next', Inter, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif",
    "'STIXGeneral'": "'STIXGeneral', 'Times New Roman', Georgia, serif",
}

# patch_1 is matplotlib's full-canvas rect. Its path is spelled slightly
# differently between exports, so match the group by its white fill instead.
BACKGROUND_RECT = re.compile(
    r'\s*<g id="patch_1">\s*<path d="M 0 [^"]*?"\s*style="fill: #ffffff"\s*/>\s*</g>'
)
ROOT_SIZE = re.compile(r'(<svg [^>]*?)width="[\d.]+pt" height="[\d.]+pt" ')


def prepare_svg(src: Path, dst: Path) -> str:
    svg = src.read_text(encoding="utf-8")

    svg, dropped = BACKGROUND_RECT.subn("", svg, count=1)
    for name, stack in FONT_FALLBACKS.items():
        # Undo then redo the substitution so re-running on an already
        # processed file does not nest the fallback stack.
        svg = svg.replace(f"font-family: {stack}", f"font-family: {name}")
        svg = svg.replace(f"font-family: {name}", f"font-family: {stack}")
    svg, resized = ROOT_SIZE.subn(r"\1", svg, count=1)

    dst.write_text(svg, encoding="utf-8")
    if not resized:
        print(f"  warning: no pt width/height on the <svg> root of {src}", file=sys.stderr)
    # Some exports are already saved transparent, so a missing rect is fine.
    return "opaque background removed" if dropped else "already transparent"


def publish_raster(src: Path, dst: Path) -> str:
    try:
        from PIL import Image
    except ImportError:
        shutil.copyfile(src, dst)
        return "copied full size (install Pillow to downscale)"

    with Image.open(src) as img:
        if img.width <= MAX_RASTER_WIDTH:
            shutil.copyfile(src, dst)
            return "copied"
        height = round(img.height * MAX_RASTER_WIDTH / img.width)
        resized = img.convert("RGBA").resize((MAX_RASTER_WIDTH, height), Image.LANCZOS)
        resized.save(dst, optimize=True)
        return f"downscaled {img.width}px -> {MAX_RASTER_WIDTH}px"


def publish(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    note = prepare_svg(src, dst) if src.suffix.lower() == ".svg" else publish_raster(src, dst)
    print(f"prepare-figures: {dst} ({dst.stat().st_size / 1024:.0f} KB, {note})")


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    if len(sys.argv) == 3:
        pairs = [(Path(sys.argv[1]), Path(sys.argv[2]))]
    elif len(sys.argv) == 1:
        pairs = [(root / s, root / d) for s, d in DEFAULTS]
    else:
        print(__doc__, file=sys.stderr)
        return 2

    for src, dst in pairs:
        if not src.exists():
            print(f"prepare-figures: missing source {src}", file=sys.stderr)
            return 1
        publish(src, dst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
