"""figure_base.py -- shared house style for figure-candidate-gallery (matplotlib).

Import this from every matplotlib candidate so the whole batch shares one type
family, one palette, and one export path. The shipped visual-system and
archetype contracts are the quality floor.

Per-run setup: copy this file into the run directory and write a palette.json
beside it holding the document's colors and font mode. Both this helper and
skia_base.mjs read that one file, which is what keeps a mixed batch on one
palette. Never edit an installed copy under `.claude/skills/`: a pack owns
that directory, so a change there is drift, and it would follow every later
run. The font mode is "serif" to match a Palatino/mathpazo body, "sans" for
crisp small plots. Two optional keys serve a venue that fixes the type:
"family" names the fonts tried first (for example ["Times New Roman"]) and
"minPt" raises the 7 pt type floor (for example to 12).

Usage in a candidate script:

    from pathlib import Path
    from figure_base import apply_house_style, style_axes, save, PALETTE, COL_W
    apply_house_style()                      # honours the run font and floor
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(COL_W, 2.5))
    ...
    style_axes(ax)
    save(fig, "cand-XX-slug", outdir=Path(__file__).resolve().parent)

Pass exact=True to save() when the figure is placed at a fixed width (for
example a wrapfigure at \\linewidth): the default tight crop changes the page
size, and LaTeX then rescales every font.

This workflow puts the helper and the candidates in the same run directory, so
that `outdir` is the directory both share. It stays explicit anyway, because an
output destination a reader can see is one a reader can audit.
"""
import json
import math
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  (after backend set)
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.offsetbox import AnnotationBbox, DrawingArea  # noqa: E402
from matplotlib.patches import Circle, Polygon  # noqa: E402

# ---- House palette: role -> {accent, fill}. Defaults; palette.json wins. ----
PALETTE = {
    "data":        {"accent": "#B26B00", "fill": "#FBEFD8"},   # amber
    "fm":          {"accent": "#1F5FBF", "fill": "#E0EAFB"},   # blue
    "harness":     {"accent": "#B23A48", "fill": "#F9E0E4"},   # red
    "measurement": {"accent": "#2D6A4F", "fill": "#DDF1E3"},   # green
    "bad":         {"accent": "#B23A48", "fill": "#F9E0E4"},   # hazard / leak
}

# ---- Run configuration -----------------------------------------------------
# Tree prep writes palette.json into the run directory beside this file's copy.
# Both helpers read it, so a batch that mixes matplotlib and skia shares one
# map and one font. Without the file the defaults above apply unchanged.
RUN_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "palette.json")
FONT = "sans"
FAMILY = []     # fonts tried before the mode's stack; palette.json "family"
MIN_PT = 7.0    # type floor at the insertion width; palette.json "minPt"


FONTS = ("sans", "serif")


def _reject_constant(name):
    raise ValueError(f"{name} is not valid JSON")


def load_run_config(path=RUN_CONFIG):
    """Merge palette.json over the defaults. True when a file was read.

    A missing file is the documented default case and returns False. A file
    that exists is validated in full before either export is touched, and any
    problem raises. Falling back to the shipped colors on a malformed config
    would render a whole batch off-palette while every check still agreed,
    since the two helpers would agree on the same wrong defaults.
    """
    global FONT, FAMILY, MIN_PT
    if not os.path.exists(path):
        return False
    try:
        with open(path, encoding="utf-8") as handle:
            # NaN, Infinity and -Infinity are Python extensions that JSON
            # itself does not define. Accepting them here would load a file
            # that JSON.parse rejects in skia_base, which is the split this
            # shared config exists to prevent.
            cfg = json.load(handle, parse_constant=_reject_constant)
    except (OSError, ValueError) as exc:
        raise ValueError(f"{path}: cannot read run config: {exc}") from exc
    if not isinstance(cfg, dict):
        raise ValueError(f"{path}: run config must be a JSON object")
    font = cfg.get("font", FONT)
    if font not in FONTS:
        raise ValueError(f"{path}: font must be one of {FONTS}, got {font!r}")
    family = cfg.get("family", [])
    if not isinstance(family, list) or not all(
            isinstance(name, str) and name.strip() for name in family):
        raise ValueError(f"{path}: family must be a list of font names, got {family!r}")
    min_pt = cfg.get("minPt", MIN_PT)
    # bool is an int subclass in Python and not a number in JavaScript, so it
    # is rejected here as skia_base rejects it.
    # A JSON number too large for a double, such as 1e309, loads as infinity
    # here and is rejected by skia_base, so it is rejected in both.
    if (isinstance(min_pt, bool) or not isinstance(min_pt, (int, float))
            or not math.isfinite(min_pt) or not min_pt > 0):
        raise ValueError(f"{path}: minPt must be a positive number, got {min_pt!r}")
    palette = cfg.get("palette", {})
    if not isinstance(palette, dict):
        raise ValueError(f"{path}: palette must be a JSON object")
    merged = {}
    for role, tones in palette.items():
        # "__proto__" is a plain key here and the prototype setter in
        # JavaScript, so skia_base would drop the role while this helper
        # kept it. Reject it in both rather than let one half go off-palette.
        if role == "__proto__":
            raise ValueError(f"{path}: '__proto__' is not a usable role name")
        if not isinstance(tones, dict):
            raise ValueError(f"{path}: role {role!r} must be an object")
        bad = [k for k, v in tones.items() if not isinstance(v, str)]
        if bad:
            raise ValueError(f"{path}: role {role!r} tones {bad} must be strings")
        tone = dict(PALETTE.get(role, {}))
        tone.update(tones)
        missing = [k for k in ("accent", "fill") if k not in tone]
        if missing:
            raise ValueError(f"{path}: new role {role!r} needs {missing}")
        merged[role] = tone
    PALETTE.update(merged)
    FONT = font
    FAMILY = [name.strip() for name in family]
    MIN_PT = float(min_pt)
    return True


load_run_config()

NEAR_BLACK = "#1A1A1A"
SUBTITLE = "#666666"
GRID = "#ECECEC"
SPINE = "#AAAAAA"
MUTED = "#BFBFBF"

# Single- and double-column widths in inches for a typical two-column layout.
COL_W = 3.45    # about 0.48 of text width
WIDE_W = 7.10   # full text width


def apply_house_style(font=None):
    """Set rcParams shared by every candidate.

    Call it with no argument so the run's font wins. Pass 'sans' or 'serif'
    only to override one candidate deliberately. A run "family" goes in front
    of the mode's stack and also sets the mathtext letters, so symbols match
    the labels; glyphs the family lacks fall back to STIX. A run "minPt" above
    matplotlib's 10 pt default raises every default text size to the floor.
    """
    font = font or FONT
    rc = matplotlib.rcParams
    rc["pdf.fonttype"] = 42   # embed TrueType, never Type 3
    rc["ps.fonttype"] = 42
    rc["svg.fonttype"] = "none"
    rc["axes.unicode_minus"] = False
    rc["axes.linewidth"] = 0.8
    if font == "serif":
        rc["font.family"] = "serif"
        rc["font.serif"] = FAMILY + [
            "Palatino Linotype", "Palatino", "URW Palladio L", "P052",
            "DejaVu Serif",
        ]
        rc["mathtext.fontset"] = "dejavuserif"
    else:
        rc["font.family"] = "sans-serif"
        rc["font.sans-serif"] = FAMILY + [
            "Arial", "Helvetica", "DejaVu Sans",
        ]
        rc["mathtext.fontset"] = "dejavusans"
    if FAMILY:
        rc["mathtext.fontset"] = "custom"
        rc["mathtext.rm"] = FAMILY[0]
        rc["mathtext.it"] = FAMILY[0] + ":italic"
        rc["mathtext.bf"] = FAMILY[0] + ":bold"
        rc["mathtext.fallback"] = "stix" if font == "serif" else "stixsans"
    for key in ("font.size", "axes.labelsize", "axes.titlesize",
                "xtick.labelsize", "ytick.labelsize", "legend.fontsize"):
        size = rc[key]
        if not isinstance(size, (int, float)):   # 'medium', 'large', ...
            size = FontProperties(size=size).get_size_in_points()
        if size < MIN_PT:
            rc[key] = MIN_PT


def style_axes(ax, grid="x"):
    """Drop top/right spines, mute the rest, draw a light grid below the data."""
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(SPINE)
    ax.spines["bottom"].set_color(SPINE)
    ax.tick_params(length=0)
    if grid in ("x", "both"):
        ax.xaxis.grid(True, color=GRID, linewidth=0.7, zorder=0)
    if grid in ("y", "both"):
        ax.yaxis.grid(True, color=GRID, linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)


def panel_label(ax, text, x=-0.02, y=1.06):
    """Bold lower-case panel tag (a, b, c) in axes coords, paper convention."""
    ax.text(x, y, text, transform=ax.transAxes, fontsize=max(9, MIN_PT),
            fontweight="bold", va="bottom", ha="right", color=NEAR_BLACK)


def hazard_triangle(ax, x, y, size=9.0, color=None):
    """Point-sized warning triangle anchored at data (x, y).

    The glyph lives in a DrawingArea, so its size in POINTS stays constant
    regardless of axis scale (log, row-index, AUC). ``size`` is the triangle
    height in points. Pass ``size`` and ``color`` by keyword.
    """
    color = color or PALETTE["bad"]["accent"]
    h = float(size)
    w = h * 1.08
    da = DrawingArea(w, h, 0, 0)
    # apex up; white fill so the mark reads on any background
    da.add_artist(Polygon([(w / 2.0, h), (0, 0), (w, 0)], closed=True,
                          facecolor="white", edgecolor=color, linewidth=1.05,
                          joinstyle="round"))
    bw = max(0.7, h * 0.07)                       # bang: short bar + dot
    da.add_artist(Polygon([(w / 2 - bw, h * 0.34), (w / 2 + bw, h * 0.34),
                           (w / 2 + bw, h * 0.62), (w / 2 - bw, h * 0.62)],
                          closed=True, facecolor=color, edgecolor="none"))
    da.add_artist(Circle((w / 2.0, h * 0.20), bw, facecolor=color, edgecolor="none"))
    ab = AnnotationBbox(da, (x, y), frameon=False, pad=0.0,
                        box_alignment=(0.5, 0.5), xycoords="data", zorder=7)
    ax.add_artist(ab)
    return ab


def save(fig, stem, outdir, dpi=200, exact=False):
    """Write <stem>.pdf (vector) and <stem>.png under `outdir`.

    `outdir` is required and takes no default. This workflow colocates the
    helper and the candidates in the run directory, so `outdir` is that
    directory. It stays explicit so the destination is visible to a reader.

    The default crops to the drawn content. With exact=True the page keeps the
    figure's own size, which is what a figure placed at a fixed width needs:
    a cropped page is narrower or wider than the slot, LaTeX scales it to fit,
    and every font changes size with it.
    """
    outdir = os.fspath(outdir)
    os.makedirs(outdir, exist_ok=True)
    pdf = os.path.join(outdir, stem + ".pdf")
    png = os.path.join(outdir, stem + ".png")
    crop = {} if exact else {"bbox_inches": "tight", "pad_inches": 0.03}
    # An exact save must not inherit savefig.bbox = "tight" from a style sheet
    # or matplotlibrc, or it crops anyway.
    with matplotlib.rc_context({"savefig.bbox": None} if exact else {}):
        fig.savefig(pdf, **crop)
        fig.savefig(png, dpi=dpi, **crop)
    print("wrote", pdf)
    print("wrote", png)
    return pdf, png
