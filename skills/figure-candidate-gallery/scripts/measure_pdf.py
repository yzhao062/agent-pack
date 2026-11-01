"""measure_pdf.py -- check a rendered candidate PDF against its slot and type floor.

Run it on every candidate before the batch is presented, and have each render
agent run it on its own output:

    <python> <skill-dir>/scripts/measure_pdf.py --pdf <candDir>/cand-01-x.pdf \
        --width-in 3.38 [--min-pt 12] [--allow-small "+"]

It reports the page size in inches, the smallest text size, every text span
under the floor with its text, the font names the text uses, any Type 3 font
(a bitmap-like font that `pdf.fonttype = 42` exists to avoid), and any span
that falls outside the page. Reading a size off a PNG is unreliable, and a figure that is
cropped or padded to the wrong width is rescaled by LaTeX, which changes every
font with it; both failures are cheap to measure and easy to miss by eye.

The floor defaults to "minPt" in the palette.json beside the PDF, else 7 pt.
Mathtext super- and subscripts render smaller than their base symbol, as they
do in body math, so name each one you accept with --allow-small (repeatable).

Exit status 1 means: the page width differs from --width-in by more than
0.01 in, a span lies outside the page, the page uses a Type 3 font, or a span
under the floor is not listed in --allow-small. Text converted to outlines is invisible here, so a
figure with labels that reports no spans at all still needs a look by eye.

Requires PyMuPDF (`pip install pymupdf`).
"""
import argparse
import json
import math
import os
import sys

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover - depends on the environment
    fitz = None

DEFAULT_MIN_PT = 7.0
TOLERANCE_PT = 0.05     # PDF sizes carry float noise
WIDTH_TOLERANCE_IN = 0.01


def _reject_constant(name):
    raise ValueError(f"{name} is not valid JSON")


def floor_from_config(pdf_path):
    """minPt from palette.json beside the PDF, or the shipped default."""
    cfg = os.path.join(os.path.dirname(os.path.abspath(pdf_path)), "palette.json")
    if not os.path.exists(cfg):
        return DEFAULT_MIN_PT
    with open(cfg, encoding="utf-8") as handle:
        value = json.load(handle, parse_constant=_reject_constant).get("minPt", DEFAULT_MIN_PT)
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or not value > 0):
        raise ValueError(f"{cfg}: minPt must be a positive number, got {value!r}")
    return float(value)


def measure(pdf_path, min_pt, allow_small=(), width_in=None):
    """Return a report dict for page 1 of pdf_path."""
    doc = fitz.open(pdf_path)
    page = doc[0]
    rect = page.rect
    # Extraction clips to the page by default, which would hide the very spans
    # the outside-the-page check exists to find. Read the whole content stream.
    unclipped = {
        "clip": fitz.INFINITE_RECT(),
        "flags": fitz.TEXTFLAGS_DICT & ~fitz.TEXT_MEDIABOX_CLIP,
    }
    spans = [
        span
        for block in page.get_text("dict", **unclipped)["blocks"]
        for line in block.get("lines", [])
        for span in line["spans"]
        if span["text"].strip()
    ]
    under = [(round(s["size"], 2), s["text"]) for s in spans
             if s["size"] < min_pt - TOLERANCE_PT]
    outside = [s["text"] for s in spans
               if s["bbox"][0] < rect.x0 - 0.5 or s["bbox"][1] < rect.y0 - 0.5
               or s["bbox"][2] > rect.x1 + 0.5 or s["bbox"][3] > rect.y1 + 0.5]
    report = {
        "pdf": os.path.abspath(pdf_path),
        "width_in": round(rect.width / 72, 3),
        "height_in": round(rect.height / 72, 3),
        "min_pt": min_pt,
        "smallest_span_pt": round(min(s["size"] for s in spans), 2) if spans else None,
        "spans_under_floor": under,
        "fonts": sorted({s["font"] for s in spans}),
        "type3_fonts": sorted({f[3] for f in page.get_fonts() if f[2] == "Type3"}),
        "spans_outside_page": outside,
    }
    problems = []
    if width_in is not None and abs(rect.width / 72 - width_in) > WIDTH_TOLERANCE_IN:
        problems.append(f"page width {rect.width / 72:.3f} in, slot {width_in:.3f} in")
    if outside:
        problems.append(f"{len(outside)} span(s) outside the page")
    if report["type3_fonts"]:
        problems.append(f"Type 3 fonts: {report['type3_fonts']}")
    unexplained = [text for _, text in under if text.strip() not in allow_small]
    if unexplained:
        problems.append(f"{len(unexplained)} span(s) under {min_pt:g} pt: {unexplained}")
    if not spans:
        report["note"] = "no text spans found; check labels by eye"
    report["problems"] = problems
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--width-in", type=float, default=None,
                    help="slot width in inches; the page must match it")
    ap.add_argument("--min-pt", type=float, default=None,
                    help="type floor; default: minPt in palette.json beside the PDF, else 7")
    ap.add_argument("--allow-small", action="append", default=[],
                    help="text of an accepted super- or subscript span (repeatable)")
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    a = ap.parse_args()
    if fitz is None:
        print("measure_pdf.py needs PyMuPDF: pip install pymupdf", file=sys.stderr)
        return 2
    min_pt = a.min_pt if a.min_pt is not None else floor_from_config(a.pdf)
    report = measure(a.pdf, min_pt, tuple(s.strip() for s in a.allow_small), a.width_in)
    if a.json:
        print(json.dumps(report, indent=2))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")
    if report["problems"]:
        print("FAIL: " + "; ".join(report["problems"]), file=sys.stderr)
        return 1
    # stdout carries only the JSON report in --json mode, so callers can parse it.
    print("OK", file=sys.stderr if a.json else sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
