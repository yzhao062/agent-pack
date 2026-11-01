---
name: figure-candidate-gallery
description: Generate a batch of diverse, polished, on-palette candidate small figures for a near-final document, render them all to one contact sheet, and present an honest per-figure assessment so the author can cherry-pick the strongest few. Use with /workflows enabled when the prose is mostly frozen and a section would read better with small, meaningful illustrations or experiment plots (not the hero or overview figure). Fans out one render agent per candidate (matplotlib for data plots, skia-canvas for modern schematics), enforces one shared visual system, and forbids fabricated data. For outside-model prompt packs use figure-prompt-builder, which this pack ships; for HTML system mockups use ci-mockup-figure where it is installed.
---

# Figure Candidate Gallery

## Overview

Starting from a near-final document, this skill generates a deliberately broad
batch of diverse, on-palette candidate small figures, renders them to one
contact sheet, and presents an honest assessment so the author can select a few
and discard the rest. Each candidate is a self-contained render script, a
vector PDF, and a PNG preview; the contact-sheet helper adapts its grid to the
batch size. The quality floor is the shipped composition contracts in
`references/candidate-archetypes.md` and the legibility and encoding gates in
`references/visual-system.md`, both of which a reviewer can check against a
rendered PNG. Those gates catch a broken figure; they do not make one look
designed. Every batch therefore also gets a visual bar, a few PNGs of the
author's own accepted figures (Phase 2), and every data plot gets the design
layer in `references/visual-system.md`.

The engine is `/workflows`. The skill fans out one render agent per candidate
so a dozen figures render in parallel, then collects their metadata and builds
the contact sheet. Running the candidates serially by hand is slow and loses
the breadth that makes cherry-picking work; the workflow fan-out is the point.

This skill is for **small figures** that raise readability and visual quality:
a decision ladder, a martingale alarm crossing a threshold, a paired
distribution test, a posterior bar chart, a small interaction graph, a
feasibility dumbbell built from real preliminary numbers. It is not for the
hero or overview figure. Those carry the project's whole logic and should go to
a human designer (for example, a student working in Photoshop), or to
`ci-mockup-figure` (if installed) for an HTML system mockup, or to
`figure-prompt-builder` for an outside-model prompt pack.

Invoke it **late**, when the prose is mostly frozen. The skill reads the fixed
text and mines it for concrete, citable hooks: the exact quantity a sentence
names, the decision rule a sub-aim defines, the preliminary result already
cited. Because the text is settled, candidates can be specific to what each
section actually claims rather than to a guess about what it might say.

## When To Use

- The document draft is near-final and a few sections read as dense prose that
  a small figure would lighten.
- The author wants to see many options at once and choose, rather than commit
  to one figure up front.
- The figures are column-width illustrations or small experiment plots, not the
  main architecture diagram.
- An existing table reads as a wall of cells, and a graphic would carry the same
  content in less space with fewer counting steps for the reader.
- A shared color and type system already exists (or can be defined once) so the
  batch looks like one family.

## When Not To Use

- The hero, overview, or full-system figure is the target. Route to a human
  designer, `ci-mockup-figure` if installed, or `figure-prompt-builder`.
- The prose is still moving. Wait until the text is settled, or the candidates
  will illustrate claims that later change.
- A single, already-specified figure needs careful hand-construction. This skill
  optimizes for breadth and selection, not for one polished final asset.
- `/workflows` is unavailable. The method still works run by hand, but it loses
  the parallel breadth it is built around; say so and proceed only if the user
  accepts the slower path.

## The Hard Rules

### 1. Never Fabricate Data

This is the non-negotiable rule. A fabricated number in a federal proposal is a
fatal error, not a style slip. Every candidate carries an explicit evidence
class, and the render agent must declare it:

- `conceptual`: a schematic or diagram. Boxes, arrows, exemplar shapes, axis
  labels, and named stages are fine. No numeric value may be presented as a
  measured result.
- `illustrative`: shows a plausible **shape** (for example, a test statistic
  crossing an alarm line) with values that are clearly exemplar. The caption
  must say "illustrative" or "schematic," and the figure must never be read as a
  real result. Use round or obviously synthetic numbers, never precise decimals
  that look measured.
- `real-data`: every plotted number is copied **verbatim** from a source the
  author owns, with the source file path and the BibTeX cite key recorded. Never
  recompute, never round silently, never invent. A named exemplar in
  `references/candidate-archetypes.md` such as `feasibility-dumbbell`
  supplies the composition only. Every value in a
  `real-data` figure comes from the brief, which must name the source file and
  the cite key, and each plotted number must match that source character for
  character.
- `transcribed`: every value is copied verbatim from the document this figure
  illustrates, which means the source is the document's own prose or a table the
  figure replaces. No external cite key exists here, and inventing one is a
  sourcing error. Record the source `.tex` file and the exact sentence or row
  each value came from. This class fails later than the others: a text edit
  moves a threshold, the figure keeps the old number, and nothing catches the
  mismatch. Re-check every transcribed value against its source sentence after
  any edit to that section, and again before the document ships.

When the evidence class is unclear, downgrade to `illustrative` or drop the
candidate. Rather omit a figure than invent its data. One case must never take
that downgrade: a `transcribed` figure whose numbers are commitments the
document makes, such as a stated threshold or a promised deliverable. Captioning
those as illustrative would misdescribe what the document promises. Fix the
transcription or drop the figure. Surface the evidence class
for every candidate in the final assessment, so the author knows which figures
still need a real source before they ship.

### 2. Small And Meaningful, Not Padding

Each figure must earn its space by compressing logic the prose states less
clearly. Target column width (roughly `0.45` to `0.5\textwidth`), legible down
to the run's type floor: 7 pt by default, or the venue's own minimum when the
solicitation names a font size and does not exempt figures (set `minPt` and
`family` in `palette.json`; see `references/visual-system.md`). A figure that
only restates an adjacent sentence is cut, not kept.

Design the candidate at its final insertion width so the PDF is placed at 1:1.
A graphic drawn at 6.5 in and inserted at 3.38 in halves every font, which is
how a design that passed its own 7 pt gate ships at 3.5 pt. When the slot is
fixed, such as a `wrapfigure` filled at `\linewidth`, create the figure at the
slot size and save with `save(..., exact=True)`: the default tight crop makes
the page narrower or wider than the slot, and LaTeX rescales every font to
fit. Crop with `pdfcrop --margins 0` only when the design already carries its
own padding and no exact slot applies. `scripts/measure_pdf.py` reports the
page width and the smallest text size, so measure rather than judge either one
by eye.

A table replacement is the one sanctioned exception to the width target. It
inherits the table's full `\textwidth` and can run tall, which makes height the
binding constraint. `\topfraction` is 0.7 in the standard `article`, `report`,
and `book` classes unless the class or document changes it, so with
`\textheight` at 9 in the top-float area is about 6.3 in, shared by every top
float on the page. A `[t]`-only float that cannot fit has no float-page option
and may stay queued until `\clearpage` or the end of the document. Measure the
rendered PDF height before promoting a tall candidate and carry the number into
Phase 6.

### 3. One Visual System

The whole batch shares a color-to-role map, one type family, and a small set of
motifs (for example, a hazard treatment for failure or leakage). Consistency is
what makes a dozen separate scripts look like one designed set. The helpers are
`scripts/figure_base.py` and `scripts/skia_base.mjs`. Both are copied into the
run directory before fan-out, and both read the run's palette and font from one
`palette.json` written beside them, so a batch that mixes the two tools cannot
go half off-palette. See `references/visual-system.md`.

### 4. Division Of Labor

Small figures render here. Core figures go to a human designer. State this split
when handing back results, and never let an auto-rendered schematic stand in for
the hero figure the proposal actually needs.

### 5. Internal Until Chosen

Candidates render into `figure-src/candidates/<run-id>/`, which is gitignored,
so the batch stays out of version control. Only the figures the author selects
are copied into `figure/` and wired into the document.

## Workflow

### Phase 1: Read The Frozen Sections And List Opportunities

Read the near-final source for the target sections (for a proposal, the aim
files and any overview). For each section, note the concrete, visualizable
hooks: a decision rule, a defined statistic, a named threshold, a stated
quantity, a cited preliminary result. Map each hook to the section it supports.
Do not read the whole repository; read the sections the figures will serve.

Count the values each data hook carries. Three or four numbers, or several
near zero beside one large value, turn a bar chart into a single bar with
labels. Prefer a unit chart (one mark per counted item), a comparison against a
drawn reference, or folding the numbers into a schematic; see the Unit chart
archetype in `references/candidate-archetypes.md`.

When the target is an artifact the document already carries, measure its defect
before designing the replacement. Count words per column or per region, count
repeated tokens per region, and compare each count against the width that
region receives. Report both metrics: word share finds the starved region, and
repeated-token share finds the region that has no business being one. Exact
counts shift with tokenization, so name the rule you used and keep the script.
Record the counts in the brief so the render agent designs against a measured
imbalance rather than a general impression.

A rebuild of one existing slot runs a smaller batch, with a floor of two
candidates rather than the dozen Phase 2 calls for. Give each candidate a named
strategy rather than a free hand, or they converge on one shape. Phase 5 already
requires a one-line reason per candidate, and with only two candidates that
reason carries the whole recommendation.

Include one candidate that keeps the current size regime and only compresses
it, so the narrow variants are compared against a measured current-size
endpoint. Compare candidates using measurements taken from the current document,
and retain each endpoint's source PDF or build log if the numbers are to be
reused as evidence. Do not carry endpoints over from another document.

### Phase 2: Write The Candidate Brief List

Turn the hooks into a brief list. Aim for breadth: cover each section, and vary
the figure archetype so the batch is diverse rather than six versions of one
shape. Make each brief specific enough that a render agent cannot collapse it to
a generic shape. Each candidate is one JSON object with the keys below, all
required unless marked optional; the Phase 3 template stops before fan-out
when a required key is missing, since a missing value would otherwise reach the
agent as the word "undefined".

- `id` in the form `cand-NN`, a bare descriptive `slug` such as
  `aim2-paired-ks`, and an `outputStem` equal to `<id>-<slug>`. Use that exact
  stem for the script, the PDF, the PNG, and the returned metadata. The contact
  sheet collects `cand-*.png`, so a bare slug renders a file it will not find.
- `section`: the target section
- `archetype`, plus `exemplar` (optional), the named reference exemplar when
  one exists (see `references/candidate-archetypes.md`)
- `compositionSpec`: the required panels or regions, the flow direction, the
  required formulas and thresholds, and any leader lines or callouts. Copy the
  archetype's composition contract; do not pass the shape name alone.
- `densityTarget`: `sparse`, `balanced`, or `dense`, with a text budget such as
  "one formula plus one short note per pillar"
- `designLayer` (required for a `matplotlib` brief, optional for a `skia`
  schematic; the template enforces it): for a data plot, the one reference
  element (threshold line, chance band, target region, baseline, or full
  scale) and the one element the message is about, which gets the emphasis. A
  data-plot brief that says "sparse, nothing else" asks for the `bare-chart`
  anti-pattern.
- `slot` (optional): the insertion width in inches and the height budget, when
  the figure fills a fixed slot such as a `wrapfigure`; omit it for an
  ordinary column-width figure, which the template then sizes at `COL_W`
- `mustInclude`: the visual elements that are not optional
- `avoid`: the named anti-patterns to reject (for example `chip-only-pillars`)
- `message`: the one sentence the figure must land
- `tool`: `matplotlib` for data plots, `skia` (skia-canvas) for modern
  schematics; these are the two values the result schema accepts
- `evidenceClass`, and `dataSource`: for `real-data` the source path and cite
  key; for `transcribed` the source `.tex` file plus the sentence or row each
  value came from; for `conceptual` and `illustrative` the string "n/a" or the
  origin of the exemplar values

Over-generate on purpose. The author expects to keep some and drop others, so a
dozen candidates with a few weak ones is the right shape, not a tight set of
three.

Choose the visual bar before fan-out: two to four figures the author has
already accepted, such as plots from a recent paper or an earlier gallery the
author kept, rendered to PNG with absolute paths. Every render agent reads them
first and matches their finish (hierarchy, reference elements, emphasis), while
colors still come from `palette.json`. Without that bar, render agents optimize
for passing the gates, and a batch that passes every gate can still read as
undesigned next to the author's own figures. When the workspace holds no such
figures, say so in Phase 5.

### Phase 3: Prepare The Work Tree, Then Fan Out With /workflows

Do both of these before launching any agent. A dozen agents that fail on a
missing directory or a missing package cost a fan-out to discover what one
check finds in a second.

**Prepare the tree.** Resolve the repository root and `<skill-dir>`, the
directory holding this `SKILL.md`. For every invocation choose a new run
identifier and create a fresh `<candDir>` at `figure-src/candidates/<run-id>/`.
Never reuse a nonempty run directory for a new batch; a retry of failed ids in
the same batch writes into the same directory and replaces only those stems.
The contact sheet collects every
`cand-*.png` it finds, so a later two-candidate rebuild in a shared directory
silently presents ten stale figures beside the two new ones, and a stale
`transcribed` figure may no longer match the sentence it came from. In a git
repository, ensure the root `.gitignore` carries `/figure-src/candidates/` and
confirm with `git check-ignore` rather than assuming it. If any brief renders
with skia, also copy `<skill-dir>/scripts/skia_base.mjs` into `<candDir>`; the
helper's bare `skia-canvas` import still resolves upward to
`figure-src/node_modules`. Pass this exact `<candDir>` to every render agent
and to the contact-sheet command. Create `figure/` only when the author
promotes a candidate.

**Set the palette once, in `palette.json`.** Copy
`<skill-dir>/scripts/figure_base.py` into `<candDir>` as well, then write
`<candDir>/palette.json` beside the two helpers:

```json
{
  "font": "serif",
  "palette": {
    "data": {"accent": "#B26B00", "fill": "#FBEFD8"},
    "bad":  {"accent": "#B23A48", "fill": "#F9E0E4"}
  }
}
```

Both helpers read that file at import and merge it over their defaults, so one
edit covers a batch that mixes matplotlib and skia. Put the document's own
colors in `palette`, add a role whose name matches the document's vocabulary,
and set `font` to `serif` for a `mathpazo` body or `sans` for crisp small
plots. The role map in `references/visual-system.md` is a starting point rather
than any particular document's palette. Writing the run file is what keeps the
batch on-palette without touching the installed skill, which a pack owns and
which every later run would inherit.

When the venue fixes the type, add two keys. A solicitation that requires
"Times New Roman, not smaller than 12 point" for the whole technical volume,
with no exception for figures, takes `"family": ["Times New Roman"]` and
`"minPt": 12`. Both helpers then lead their font stacks with that family,
matplotlib sets its mathtext letters from it, every default text size rises to
the floor, and the skia text helpers clamp smaller requests up to it. At 12 pt
a narrow slot holds far less text than at 7 pt, so plan shorter labels in the
briefs rather than discovering the overflow in fan-out.

Both helpers now sit beside the candidates, so a matplotlib candidate imports
`figure_base` from `<candDir>` and a skia candidate imports `./skia_base.mjs`.

**Preflight the toolchain.** Verify `<python> -c "import matplotlib"`, which is
required even for an all-skia batch because the contact sheet imports it, and
`<python> -c "import fitz"` (PyMuPDF), which `measure_pdf.py` needs. If
any brief uses skia, verify `<node> <candDir>/skia_base.mjs`, which also
proves `figure-src/node_modules/skia-canvas` resolves. When an import fails,
stop before fan-out, name the missing package and the interpreter you used, and
ask before installing anything. If only skia is missing, offer a
matplotlib-only batch and say plainly that the schematic candidates are lost.

Confirm both helpers resolve the same visual system before fan-out, since a
mixed batch goes off-palette silently otherwise:

```text
<python> <skill-dir>/scripts/check_run_config.py --dir <candDir>
```

It compares the complete palette, the font mode, the family, and the type
floor, so a drift in one role is caught as well as a wholesale mismatch, and it
exits nonzero with what differs. A
malformed `palette.json` makes both helpers raise rather than fall back to the
shipped colors, so this check fails there too instead of agreeing on defaults.

Run one render agent per candidate. Each agent writes a self-contained script
into `<candDir>`, runs it with the configured interpreter, and returns
structured metadata. A compact script:

```javascript
export const meta = {
  name: 'figure-candidate-gallery',
  description: 'Render a batch of small proposal figure candidates in parallel',
  phases: [{ title: 'Render' }],
}

// BRIEFS is the Phase 2 list, passed in whole: id, slug, outputStem, section,
// archetype, exemplar, message, compositionSpec, densityTarget, designLayer,
// slot, mustInclude, avoid, tool, evidenceClass, dataSource. The prompt below
// reads every one of them, and compositionSpec, densityTarget, designLayer,
// mustInclude, and avoid are the fields that keep a render agent from
// collapsing a brief to a generic shape.
const BRIEFS = args.briefs
const CAND_DIR = args.candDir     // the run directory prepared above
const SKILL_DIR = args.skillDir   // the resolved absolute <skill-dir>
const PYTHON = args.python        // the configured interpreter
const NODE = args.node || 'node'  // the configured Node, for skia candidates
const MIN_PT = args.minPt || 7    // the minPt written to palette.json, if any
const REFS = args.referenceImages || []   // absolute PNG paths: the visual bar

// Stop before fan-out on a missing required key; a gap would otherwise reach
// the agent as the word "undefined".
const REQUIRED = ['id', 'slug', 'outputStem', 'section', 'archetype', 'message',
  'compositionSpec', 'densityTarget', 'mustInclude', 'avoid', 'tool',
  'evidenceClass', 'dataSource']
for (const b of BRIEFS) {
  const missing = REQUIRED.filter(k => b[k] === undefined || b[k] === '')
  // A matplotlib brief is a data plot, which needs its design layer.
  if (b.tool === 'matplotlib' && !b.designLayer) missing.push('designLayer')
  if (missing.length) throw new Error(`brief ${b.id || '?'} lacks ${missing.join(', ')}`)
}

const SCHEMA = {
  type: 'object',
  // dataSource is unconditionally required: without it the later recheck has no
  // source to check against, and the result still validates. Do NOT express this
  // as a conditional. A top-level oneOf/allOf/anyOf is not portable across tool
  // APIs, and where it is rejected the whole fan-out fails before any agent
  // starts work. Require the field and let 'conceptual' and
  // 'illustrative' candidates carry the literal string "n/a". selfAssessment is
  // required for the same reason: Phase 5 presents an honest call per candidate,
  // and an agent that omits it leaves the author reading a blank column.
  required: ['id', 'title', 'file', 'tool', 'evidenceClass', 'dataSource', 'status', 'whyItHelps', 'selfAssessment'],
  properties: {
    id: { type: 'string' },
    title: { type: 'string' },
    file: { type: 'string' },                 // path to the rendered .pdf
    tool: { type: 'string', enum: ['matplotlib', 'skia'] },
    evidenceClass: { type: 'string', enum: ['conceptual', 'illustrative', 'real-data', 'transcribed'] },
    dataSource: { type: 'string' },           // cite key, or source .tex + anchor sentence, or "n/a"
    status: { type: 'string', enum: ['rendered', 'failed'] },
    whyItHelps: { type: 'string' },
    selfAssessment: { type: 'string', enum: ['strong', 'ok', 'weak'] },
  },
}

const results = await parallel(BRIEFS.map(b => () => agent(
  [
    `Render proposal figure candidate ${b.id} (${b.slug}) into ${CAND_DIR}. Write only inside that directory; do not edit the document source and do not commit.`,
    `Section: ${b.section}. Archetype: ${b.archetype} (exemplar: ${b.exemplar || 'none'}).`,
    `Message it must land: ${b.message}.`,
    REFS.length
      ? `Visual bar: read these accepted figures first and match their finish (hierarchy, reference elements, emphasis); take colors from palette.json, not from them: ${REFS.join(', ')}.`
      : `No reference figures were supplied; the design layer in ${SKILL_DIR}/references/visual-system.md is the bar.`,
    `Composition, build exactly this and do not collapse it to a generic shape: ${b.compositionSpec}.`,
    `Design layer: ${b.designLayer || 'see the Design Layer section of visual-system.md'}. Slot: ${b.slot || 'column width, COL_W in figure_base'}.`,
    `Density ${b.densityTarget}: one meaningful formula or one-liner per region, at most three chips, no paragraph blocks, and at most one hazard cue. Draw a hazard cue only where the composition or must-include list names a genuine failure, leak, defer, below-chance, or alarm locus, and exactly one where it does; a benign comparison carries none. Must include: ${b.mustInclude}. Avoid: ${b.avoid}.`,
    `Tool: ${b.tool}. Evidence class: ${b.evidenceClass}.`,
    b.evidenceClass === 'real-data'
      ? `Real data only: copy every number VERBATIM from ${b.dataSource}. Do not recompute or invent. Record the source path and cite key.`
      : b.evidenceClass === 'transcribed'
      ? `Transcribed only: copy every value VERBATIM from the document itself at ${b.dataSource}. Do not restate, round, or reword a threshold. Return the source .tex file and the exact sentence or row behind each value, so a later text edit can be checked against this figure. Never caption it illustrative; these values are the document's own commitments.`
      : `Do not present any number as a measured result, and keep values exemplar. The LaTeX caption, not the figure, says illustrative or schematic.`,
    `Reuse the shared toolkit and palette. For any warning mark call the shared glyph (hazard() in skia, hazard_triangle() in matplotlib); never draw your own. For an interaction graph use nodeLinkGraph().`,
    `Import recipe: both helpers were copied into ${CAND_DIR} by the tree-prep step and carry this run's palette, font, and type floor, so import them from there and not from the installed skill. A matplotlib candidate inserts ${CAND_DIR} on sys.path, imports figure_base, calls apply_house_style() with no argument so the run font applies, and calls save(fig, stem, ${CAND_DIR}), passing exact=True when the slot gives a fixed width and creating the figure at exactly that size; a skia candidate is written into ${CAND_DIR} and imports ./skia_base.mjs (skia-canvas resolves upward from figure-src/node_modules).`,
    `Write ${b.outputStem}${b.tool === 'skia' ? '.mjs' : '.py'} into ${CAND_DIR}, run it with ${b.tool === 'skia' ? NODE : PYTHON}, and emit ${b.outputStem}.pdf and ${b.outputStem}.png there at the slot size, legible at ${MIN_PT}pt. Use that exact stem; the contact sheet collects cand-*.png.`,
    `Measure, do not estimate: run ${PYTHON} ${SKILL_DIR}/scripts/measure_pdf.py --pdf ${CAND_DIR}/${b.outputStem}.pdf (add --width-in for a fixed slot, and --allow-small for each mathtext super- or subscript you accept) and fix until it prints OK.`,
    `Legibility self-check: read ${SKILL_DIR}/references/visual-system.md, then read your own ${b.outputStem}.png and fix until it passes that file's design layer, legibility gate, and encoding discipline: no overlapping or clipped text; a hard ${MIN_PT}pt floor at the insertion width (move dense formulas and the illustrative tag to the LaTeX caption, not the figure); every key value labeled; no series separated by color alone; mathtext for subscripts; every symbol defined; no raw cite keys; every axis label and stated statistic matches the construction actually drawn (an "empirical CDF" axis needs a step function from samples, not a smooth parametric curve); any heatmap dark = high/bad.`,
    `Self-assess honestly as strong, ok, or weak. A weak verdict on your own figure is useful; an inflated one costs the author a review round.`,
    `Return the metadata object: id is ${b.id} verbatim, file is the absolute path of the PDF, tool is matplotlib or skia, and dataSource repeats the source path and cite key (real-data), the .tex file and sentence (transcribed), or "n/a" (conceptual and illustrative).`,
  ].join(' '),
  { label: b.id, phase: 'Render', schema: SCHEMA }
)))

return results.filter(Boolean)
```

Pass `skillDir` the resolved absolute `<skill-dir>`, never the literal
placeholder. The full `args` object is `{briefs, candDir, skillDir, python,
node, minPt, referenceImages}`; `node` is needed only for skia candidates,
`minPt` only when `palette.json` sets one, and `referenceImages` is the visual
bar. A child agent reads only its own prompt, so a path this workflow does not
interpolate is a path the child cannot find.

Each render agent uses the shared toolkit so the batch stays consistent. The
`real-data` branch of the prompt restates the no-fabrication rule directly to
the agent, because that is the rule most likely to be violated under
generation.

Before building the contact sheet, reconcile the returned results against every
Phase 2 brief, matching on `id`. Each brief needs a result with
`status: rendered`, and both `<candDir>/<outputStem>.pdf` and
`<candDir>/<outputStem>.png` must exist on disk. Retry the failures, or present
the exact missing and failed list as a
partial run. Never describe a partial run as a completed batch.

### Phase 4: Build The Contact Sheet

After the workflow returns, run the contact-sheet script over the candidates
directory. Resolve `<skill-dir>` as the directory holding the `SKILL.md` you
are reading. A consumer receives this skill at `.claude/skills/`, so a
top-level `skills/` checkout is not there to be found:

```text
<python> <skill-dir>/scripts/make_contact_sheet.py --dir <candDir>
```

It tiles every `cand-*.png` into one labeled grid and writes `_contact-sheet.png`
and `_contact-sheet.pdf`. Read the contact sheet to verify the batch rendered
on-palette and nothing broke. Then run `measure_pdf.py` on every candidate PDF
yourself, with `--width-in` from each brief's slot; a render agent's own report
is a claim, and the measurement is the evidence the author gets. Read the spans
it lists under the floor and accept only mathtext super- and subscripts.

### Phase 5: Present For Cherry-Picking

Give the author the contact-sheet path and a per-candidate table. For each
candidate show the title, the message, the evidence class, and an honest call:
strong, ok, or weak, with a one-line reason. Flag any `real-data` or
`transcribed` candidate whose source still needs verification, and flag any
candidate that overlaps the
hero figure (a human designer owns that). The author selects; do not wire
anything in or commit until they choose.

Make the call yourself, against the visual bar as well as the gates. Agents
grade their own work generously: in one round every render agent rated its
figure strong or ok, and the author found the whole batch plain beside the
author's earlier plots. A candidate that passes every gate but has no design
layer is `ok` at best.

A workable table shape:

| # | Figure (section) | Evidence | Call |
|---|---|---|---|
| 05 | Paired equivalence test (Aim 2) | illustrative | strong: the decisive test as two distributions |
| 11 | Graph predicts failure (Aim 3) | real-data | strong: author's verified numbers |
| 02 | Detector triad (Aim 1) | conceptual | weak: busy, overlaps the pipeline figure |

### Phase 6: Promote The Chosen Figures

Once the author names the keepers, copy each chosen `.pdf` from `<candDir>`
into `figure/`, add a `wrapfigure` or small `figure`
with a caption and a `\ref` callout in the prose, and recompile. For any
`real-data` figure, confirm the cite key resolves and the source is current
before it ships. For any `transcribed` figure, re-read every value against the
sentence or row recorded in the brief. For any `illustrative` or `conceptual`
figure, confirm the caption says illustrative or schematic, since the figure
itself carries no such tag. Leave the rest in the gitignored candidates
directory.

When a figure replaces a placeholder already in the document, change only the
placeholder: keep the environment, width, caption, and label. A `wrapfigure`
cannot break across a page, so near a page foot it can drop its caption while
the build still succeeds; move its anchor to a point with a page of text after
it, rebuild, and check the caption, rather than converting it to a float.

**Measure the free space before placing a tall figure.** A column-width figure
lands wherever it lands. A tall one does not, and eyeballing the gap is
unreliable: in one build the space left on the target page looked like roughly
twice what it measured. The number moves whenever the layout changes, so
re-measure rather than reuse a recorded value:

```text
<python> <skill-dir>/scripts/measure_free_space.py \
  --pdf <doc.pdf> --page <target-page> --full-page <a-known-full-page>
```

Then pick the specifier from the measurement:

| Condition | Initial choice |
|---|---|
| The full box and required spacing fit at the insertion point | `[H]`, then build and inspect the page |
| The box fits the current top-area and text-area limits once other floats are counted | `[t]` |
| Top placement is wanted and only count or fraction policy tests block it | `[!t]`, then build and inspect the page |
| A float page is acceptable | include `p`, for example `[tp]` |

Every row ends in a build because `[!t]` overrides the count and fraction
tests, not the physical page height, the allowed placement letters, or the
same-class queue, so it cannot promise a page. `[H]` on an oversized figure
breaks the page and leaves the rest of it empty; `[t]` on a figure taller than
the top-float area can stay queued for pages. When a section holds two tall
figures, give both the same specifier, or a floating figure overtakes a fixed
one and the numbers read out of order.

**Give a replaced table stable item codes.** When a figure replaces a table the
prose cites by row, print a short code inside the graphic for each row (`O1`
through `O7` for seven outcome rows) and replace every "Table 1, row N"
citation with the code. This removes a counting step for the reader and
survives any later reordering of the rows.

## Toolchain

- **matplotlib** for data plots and any figure with axes. Copy
  `<skill-dir>/scripts/figure_base.py` into the run directory, set this run's
  palette and font in `<candDir>/palette.json` beside it, and have every
  matplotlib candidate import that copy for the shared rcParams, palette, and
  helpers.
  Export PDF (with `pdf.fonttype = 42`) and PNG.
- **skia-canvas** (Node) for modern schematics: rounded cards, chips, arrows,
  node-link graphs, loops. This is the path that gives the clean, current look,
  in place of dated TikZ box farms. Copy `<skill-dir>/scripts/skia_base.mjs`
  into the run directory and have each skia candidate import it as
  `./skia_base.mjs`. Node's ESM loader resolves `skia-canvas` by walking up
  from the file, so the run directory must sit under `figure-src/`, where
  `skia-canvas` is installed at `figure-src/node_modules` (`npm i skia-canvas`,
  run once under `figure-src/`). `NODE_PATH` does not work for ESM bare
  imports.
- **run config check** via `<skill-dir>/scripts/check_run_config.py`, which
  compares the palette, font, family, and type floor both run-local helpers
  resolve.
- **contact sheet** via `<skill-dir>/scripts/make_contact_sheet.py`. It imports
  matplotlib, so matplotlib is required even for a batch rendered entirely
  with skia.
- **slot and type-floor check** via `<skill-dir>/scripts/measure_pdf.py`, run on
  every candidate PDF: page width against the slot, the smallest text span,
  spans under the floor, the fonts the text uses, any Type 3 font, and spans
  outside the page. Needs
  PyMuPDF.
- **unused-text-depth estimate** via `<skill-dir>/scripts/measure_free_space.py`,
  run against the compiled document before placing a tall figure. It compares
  text-block bottoms, so it is a screening figure rather than exact page
  geometry; use it to rule `[H]` out, never to rule it in on its own. Needs
  PyMuPDF.

Interpreter and tool paths are machine-local. Use the workspace's configured
Python and Node rather than hardcoding one machine's paths; if the project
records an interpreter (for example in `AGENTS.local.md`), use that.

## Output Layout

```text
<work-dir>/figure-src/node_modules/       # skia-canvas, installed once
<work-dir>/figure-src/candidates/         # gitignored, internal
  <run-id>/                               # one directory per invocation
    palette.json                          # this run's palette and font; both helpers read it
    figure_base.py                        # copied here, reads palette.json
    skia_base.mjs                         # copied here when a brief uses skia, reads palette.json
    cand-01-<slug>.py | .mjs              # one render script per candidate
    cand-01-<slug>.pdf                    # vector output
    cand-01-<slug>.png                    # raster preview
    ...
    _contact-sheet.png | .pdf             # the grid for review
<work-dir>/figure/                        # only the chosen figures land here
```

## References

- `references/candidate-archetypes.md`: the catalog of small-figure shapes that
  work, grouped by what each one shows, with the evidence class each tends to
  carry.
- `references/visual-system.md`: the palette-to-role map, type and venue
  floors, motifs, the design layer, sizing, the gates, and the shared toolkit
  modules.
