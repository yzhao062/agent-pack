"""Estimate the unused text depth at the foot of a page in a compiled PDF.

Use this before choosing a float specifier for a tall figure. Eyeballing the gap
is unreliable; on the run this script was written for, a gap that looked like
about 5 in measured 2.9 in.

WHAT THIS MEASURES, AND WHAT IT DOES NOT
----------------------------------------
The result is the vertical distance between the bottom of the last text block on
the target page and the bottom of the last text block on a reference page whose
text runs to the bottom margin. That is an estimate of unused *text* depth, not
exact page geometry. It does not account for:

  * drawings, images, or rules below the last text block
  * the vertical spacing LaTeX requires around a float
  * headers, footers, or marginalia that the numeric filter does not catch
  * the two pages having different layouts (a two-column page, a page with a
    bottom float whose caption sits below the text block)

So the number can overstate the room actually available to an `[H]` object.
Treat it as a screening figure: it reliably tells you when a figure clearly will
not fit, and it does not by itself license `[H]`. Subtract the placement spacing
and a safety margin, then compile and look at the page.

Pass `--full-page` a page whose text runs to the bottom margin. Taking the
maximum across all pages instead picks up a running footer and inflates the
result.
"""
import argparse
import sys

import fitz  # pymupdf


def text_bottom(page):
    """Bottom edge, in points, of the lowest non-empty text block on the page.

    Page numbers are skipped: a bare numeral sits below the text block and would
    otherwise stand in for the baseline this measurement depends on.
    """
    ys = [
        b[3]
        for b in page.get_text("blocks")
        if b[4].strip() and not b[4].strip().isdigit()
    ]
    return max(ys) if ys else page.rect.y0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--page", type=int, required=True,
                    help="1-indexed page whose unused text depth you want")
    ap.add_argument("--full-page", type=int, required=True,
                    help="1-indexed page whose text runs to the bottom margin")
    a = ap.parse_args()

    doc = fitz.open(a.pdf)
    n = doc.page_count
    for label, value in (("--page", a.page), ("--full-page", a.full_page)):
        if not 1 <= value <= n:
            ap.error(f"{label}={value} is out of range; {a.pdf} has {n} pages "
                     f"(pages are 1-indexed)")

    gap = (text_bottom(doc[a.full_page - 1]) - text_bottom(doc[a.page - 1])) / 72
    print(f"estimated unused text depth on page {a.page}: {gap:.2f} in")
    print("Screening figure only. Subtract float spacing and a safety margin, "
          "then compile and inspect the page before committing to [H].")
    return 0


if __name__ == "__main__":
    sys.exit(main())
