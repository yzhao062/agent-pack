"""make_contact_sheet.py -- tile cand-*.png into one labeled review grid.

The contact sheet is how the author scans the whole batch at once and decides
which candidates to keep. Run it after the render workflow finishes.

Usage:
  python make_contact_sheet.py --dir <candidates_dir> [--cols N] [--title "..."]

Writes _contact-sheet.png and _contact-sheet.pdf into the same directory.
"""
import argparse
import glob
import math
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="candidates directory")
    ap.add_argument("--cols", type=int, default=0, help="columns (0 = auto)")
    ap.add_argument("--title", default="Figure candidates")
    args = ap.parse_args()

    pngs = sorted(glob.glob(os.path.join(args.dir, "cand-*.png")))
    if not pngs:
        # An empty batch is a failed render rather than a finished contact
        # sheet, so exit nonzero: a fan-out that produced nothing must not
        # read as success to whatever ran this.
        print("no cand-*.png found in", args.dir, file=sys.stderr)
        return 1

    n = len(pngs)
    cols = args.cols or (3 if n <= 12 else 4)
    rows = math.ceil(n / cols)

    fig, axes = plt.subplots(rows, cols, figsize=(4.5 * cols, 4.4 * rows),
                             squeeze=False)
    for ax in axes.flat:
        ax.axis("off")
    for i, p in enumerate(pngs):
        ax = axes.flat[i]
        ax.imshow(mpimg.imread(p))
        ax.set_title(os.path.basename(p).replace(".png", ""),
                     fontsize=9, color="#333333")

    fig.suptitle("%s (%d)" % (args.title, n), fontsize=14, y=0.997)
    fig.tight_layout(rect=[0, 0, 1, 0.99])

    out_png = os.path.join(args.dir, "_contact-sheet.png")
    out_pdf = os.path.join(args.dir, "_contact-sheet.pdf")
    fig.savefig(out_png, dpi=130, bbox_inches="tight", facecolor="white")
    fig.savefig(out_pdf, bbox_inches="tight", facecolor="white")
    print("contact sheet written:", out_png, "|", n, "figures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
