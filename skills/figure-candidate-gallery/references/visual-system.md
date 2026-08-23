# Visual System

The whole batch must look like one designed family. This file fixes the
palette, type, motifs, sizing, and toolkit that hold that consistency.

## Quality Floor

The composition contracts in `candidate-archetypes.md`, the type and sizing
rules below, and the legibility and encoding gates in this file are the quality
floor. Every one of them can be checked against a rendered PNG. Any technique
pulled in from outside, including the figures4papers repo cited at the end, is
adopted only when the result still passes all of them, and an outside default
tuned for a different figure size is adapted to this small column-width regime
rather than copied. A setting tuned for a full-page figure can overwhelm a
0.48-width inset, so adapt it rather than copy it.

## Palette: Role to Color

One map, locked for the length of a run and shared by every candidate. The
roles below are a starting point. Replace the hex values with the document's
own palette in `<candDir>/palette.json` before fan-out, and add a role whose
name matches the document's vocabulary. Both helpers read that one file, so a
batch that mixes matplotlib and skia stays on one map.

| Role | Accent | Fill | Used for |
|---|---|---|---|
| data | `#B26B00` | `#FBEFD8` | Data layer, Aim 1, amber |
| fm | `#1F5FBF` | `#E0EAFB` | Model layer, Aim 2, blue |
| harness | `#B23A48` | `#F9E0E4` | Harness layer, Aim 3, red |
| measurement | `#2D6A4F` | `#DDF1E3` | Measurement, benchmarks, green |
| bad | `#B23A48` | `#F9E0E4` | Failure, leak, defer, below-chance |

Set the map from the document's existing palette so candidates match the
figures already in it. Swapping to an outside repo's colors breaks that
consistency, which is itself a regression. The discipline that matters: one
color means one role across the entire batch, never decoration.

Reserve the warning color. Coloring every shortfall as a hazard turns the
figure into a list of failures and pulls the eye to the problems rather than to
the thresholds. Keep `bad` for the one place that genuinely needs it, and set a
deficit in the neutral gray.

## Type

Default to sans (`Arial`, `Helvetica`, `DejaVu Sans`) for crisp small plots.
Switch to a Palatino-like serif by setting `"font": "serif"` in
`<candDir>/palette.json` when the figure should match a `mathpazo` document
body. A candidate then calls `apply_house_style()` with no argument, and the
skia helper derives its font stack from the same value, so one edit moves the
whole batch. Font sizes stay small because
these are column-width insets: title near 9 pt, axis labels near 8 pt, ticks and
in-figure notes at 7 pt. Nothing goes below 7 pt. The legibility gate below is
the binding rule, and it fails a figure whose smallest text sits under that
floor at the width the figure is placed.

Size-regime warning. The figures4papers repo recommends 16 to 24 pt fonts and
2.5 to 3.0 axis line width. Those values are tuned for large, standalone paper
figures. Our candidates are small column-width insets, so copying the
large-font, thick-line defaults would overwhelm the figure and fall below the
floor. Keep the small-figure sizing and borrow the encoding techniques below
instead.

## Motifs

- Hazard treatment for failure, leak, defer, or below-chance: a red warning
  triangle (white fill, bang, dot) plus, on graph edges, a red dashed line.
  Always call the shared glyph: `hazard_triangle(ax, x, y, size=9)` in
  `figure_base.py` (point-sized, so it stays identical on log, row, and AUC
  axes) and `hazard(ctx, x, y)` in `skia_base.mjs`. No candidate may draw its
  own warning mark; an ad-hoc glyph is the `custom-hazard` anti-pattern.
- Two-series emphasis: a larger dark-edged accent dot for the hero series, a
  smaller muted dot for the baseline, joined by a thin connector. This is the
  `feasibility-dumbbell` exemplar in `candidate-archetypes.md`.
- Composition and density: the look of a schematic is set by its composition
  contract and density target, not just its shape. See the contracts, named
  exemplars, anti-patterns, and the density gate in `candidate-archetypes.md`.

## Encoding Techniques Worth Reusing

These are adopted from figures4papers (Chen Liu), kept only at sizes that hold
the small-figure quality:

- Bar separation: a black edge on bars (`edgecolor="black"`) with a thin line
  width near 0.8 to 1.2 at our size, not the 2 to 3 used for large figures.
- Sweep or ablation: one role color at varying alpha (about 0.25 to 1.0)
  instead of a rainbow of hues.
- Grayscale safety: hatch overlays (`/`, `\\`, `.`) on subtype bars so a
  black-and-white print still separates them. Federal proposals are often read
  in print.
- Direct value labels above bars or points, so a reader takes the number from
  the figure rather than estimating it against an axis.
- Trend with a shaded band for a confidence or spread region: one clean line
  plus a light fill, not error bars on every point.
- Perceptually uniform colormap families (`magma`, `viridis`) for any heatmap,
  oriented per the colormap-direction rule under Encoding Discipline. Never
  `jet`.
- Multi-format export: PDF (the vector asset that ships) plus PNG (the preview).
  Add SVG or EPS only when a venue needs them.

## Sizing and Output

- Column width about 3.45 in (`COL_W`); full text width about 7.1 in
  (`WIDE_W`).
- Legible at 7 pt. Check the contact sheet at 100 percent before presenting.
- PDF with `pdf.fonttype = 42` so fonts embed as TrueType, never Type 3. PNG at
  200 to 300 dpi for the preview. The PDF is the asset that ships.
- Trim stray margins with `pdfcrop --margins 2` if a canvas or browser export
  adds a white border.

## Legibility Gate

A figure fails if a reader cannot read it, however good the idea. Every
candidate must pass these checks, and the render agent verifies them by reading
its own rendered PNG before returning:

- No overlapping text. Value labels, annotations, and legends must not sit on
  top of bars, markers, each other, or the title. Put a legend in clear space (a
  data-free corner or below the axis), and offset a gap annotation into a blank
  region rather than over a bar.
- Readable contrast. Never put faint gray text on a dark fill. Annotation text
  uses dark ink or the role accent at full strength; a value that belongs to a
  filled bar goes above the bar, not inside it.
- Label the key values. A marker or lollipop that stands for a quantity shows
  that quantity. A per-row verdict panel labels each row's value; a bar labels
  its height.
- Modest markers. Dots in a dumbbell or scatter stay small enough not to collide
  with their own value labels or with each other. Offset the value beside or
  above the dot, and shrink the dot before letting it cover a number. Keep marker
  size equal across series unless size encodes a variable, so it does not read as
  a stray third channel.
- Nothing clipped. All text and glyphs sit inside the figure bounds.
- Hard 7pt floor. No text element may render below 7pt at the width the figure is
  placed (about 0.48 text width is roughly 3.3in, so author and check at that
  size, not at a larger native canvas). Reject a 5 to 6pt subtitle, legend,
  axis label, or in-figure formula. Move a dense formula and the
  "illustrative" tag into the LaTeX caption instead of shrinking them into the
  figure: the figure shows the picture, the caption carries the precise notation.

## Encoding Discipline

- No color-only encoding. Never let hue be the only thing separating two key
  series. Add a line style (solid versus dashed) or distinct markers, so the
  figure survives grayscale printing and red-green color-vision deficiency.
- Colormap direction. With a perceptual colormap, map dark or saturated to high
  or bad so the worst cell reads as the most alarming (`magma_r`, not `magma`),
  and give the colorbar a midpoint tick, not only its endpoints.
- Math typesetting. In matplotlib, write symbols in mathtext (`$c_{\mathrm{ask}}$`,
  `$\Delta_{\mathrm{know}}$`) so subscripts render; a raw `c_ask` shows the `_` as
  a literal character. In skia, draw a subscript as smaller offset text, never a
  raw `_`.
- Every symbol defined. A symbol drawn in a figure is defined in the figure or
  dropped; do not show a term the panel cannot decode.
- No raw cite keys. A figure shows a rendered citation such as "(Author et al.,
  2026)" or nothing, never a raw key like `author2026method`.
- Label matches geometry. An axis label, legend entry, or stated statistic names
  the construction actually drawn. An "empirical CDF" axis needs a step function
  built from samples, not a smooth parametric curve; a panel that claims an
  equivalence test draws the corridor and the gap it compares. A figure whose
  label describes a different construction than the one rendered is a correctness
  bug, not a style nit, so check the drawn geometry against every label before
  the figure ships.

## Toolkit Modules

The skill ships four scripts under `scripts/`. Two of them, `figure_base.py`
and, when a brief uses skia, `skia_base.mjs`, are copied into the run
directory before fan-out, and candidates import those copies. The other two
run in place from `<skill-dir>/scripts/`. Tree prep creates `palette.json` in
the run directory; it is not shipped.

- `palette.json`: the run's `palette` and `font`, written by tree prep into
  the run directory and read by both copied helpers at import. A malformed
  file raises rather than falling back to the shipped defaults.
- `figure_base.py`: shared rcParams, the palette, `style_axes`,
  `panel_label`, `hazard_triangle`, and `save` (writes PDF plus PNG).
- `skia_base.mjs`: `makeCanvas`, `card`, `chip`, `arrow`, `roundRect`,
  `hazard`, `label`, `edgeLabel`, `node`, `nodeLinkGraph`, `saveCanvas`, and the
  matching PALETTE for schematics. Use `nodeLinkGraph` for interaction graphs and
  `hazard` for every warning mark rather than rebuilding them per candidate.
- `scripts/check_run_config.py`: run from `<skill-dir>/scripts/`, compares the
  full palette and font that both run-local helpers resolve, and exits
  nonzero when they differ or when the config will not load.
- `scripts/make_contact_sheet.py`: run from `<skill-dir>/scripts/`, tiles
  every `cand-*.png` into one labeled review grid.

## External Reference

- figures4papers (Chen Liu): <https://github.com/ChenLiu-1996/figures4papers>.
  Source for the encoding techniques above. Its palette (blue `#0F4D92`, red
  `#B64342`, a green family, neutral `#CFCECE`) sits in the same
  publication-quality family as ours and is a useful cross-check, but we keep
  the proposal's locked palette for consistency with figures already in the
  document.
