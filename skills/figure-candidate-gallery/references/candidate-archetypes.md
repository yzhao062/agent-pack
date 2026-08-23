# Candidate Archetypes

A catalog of small-figure shapes that work, so the batch stays diverse instead
of becoming six versions of one chart. Each entry names what the figure shows,
when it fits, the render tool, and the evidence class it usually carries. Pick a
spread of archetypes across the document's sections.

Evidence class reminder (the load-bearing rule):

- `conceptual`: a schematic. No number is presented as a measured result.
- `illustrative`: a plausible shape with clearly exemplar values. The caption
  says illustrative. Never read as a real result.
- `real-data`: every value copied verbatim from a cited source the author owns,
  with the source path and cite key recorded.
- `transcribed`: every value is copied verbatim from the host document; record
  the source `.tex` file and exact sentence or row, then recheck it after any
  edit to that source.

## Recommended Shapes

Choose a shape, then copy its **composition contract** into the candidate brief.
A render agent should receive the contract, not just the archetype name. A
shape name alone permits a literal minimum, such as a plain three-band ladder
in place of the dial-gate-ladder composition, so copy the composition contract
into the brief.

| Archetype | Composition contract | Density | Tool | Usual class |
|---|---|---|---|---|
| Risk-gated decision ladder | Two panels: left is a semicircular action-risk dial with a needle from low to high; it feeds `z = rho(a) * (1 - q_max)` through a labeled gate arrow into a full-width ACT / ASK / DEFER ladder on the right. Each band carries its own z-condition (`z <= c_ask`, `c_ask < z <= c_def`, `z > c_def`) and one short action sentence. Draw `c_ask` and `c_def` as threshold leader lines on the axis. | balanced: one dial, one formula gate, one condition and one sentence per band | skia | conceptual |
| Detector triad | Three compact detector cards feed one scored decision. Short detector labels; put the scoring or max/threshold rule in a single bottom card. | balanced: three labels, one rule, one verdict | skia | conceptual |
| Test-martingale alarm | A statistic rises and crosses a `1/alpha` line over time, with an explicit alarm band and one hazard mark at the crossing. | balanced: one label per trace, one alarm label | matplotlib | illustrative |
| Two-pillar fork | A clean-input card and a frozen-FM node feed two pillars. Each pillar gets one meaningful formula or one-line test plus up to three subtype chips. The hazard cue sits on the frozen-FM node, since the risk is latent source ambiguity, not the clean input. | balanced: one formula or note per pillar, at most three chips per pillar, no paragraph blocks | skia | conceptual |
| Paired equivalence test | Two distributions with a delta band and a small verdict strip. | balanced: one margin label, one verdict rule, no boxed legend | matplotlib | illustrative |
| Knowledge-boundary gap | Paired bars for a gap quantity such as `Delta_know`, with direct value labels and a short reading rule. | balanced | matplotlib | illustrative or real-data |
| Interaction graph | A small node-link graph `G_t` (use `nodeLinkGraph`) with typed edge labels, one anomalous dashed hazard edge, and one score formula in a bottom band. | balanced: 4 to 5 nodes, 3 to 5 edges, one formula | skia | conceptual |
| MAPE-K loop | A monitor, analyze, plan, execute, knowledge cycle. Use only when it does not duplicate the hero figure. | sparse | skia | conceptual |
| Latent-cause posterior | Posterior bars over causes with an abstain floor and one verdict callout. | balanced | matplotlib | illustrative |
| Least-agency knee | A utility-versus-agency curve with the knee marked, the feasible band shaded, and `P*` tied to the constraint. | balanced | matplotlib | illustrative |
| Feasibility dumbbell | Two series per row (baseline versus method) with a chance line and direct values. | balanced | matplotlib | real-data |
| Lifecycle ribbon | Layer bands such as Data, Model, Harness. Hero-adjacent; use only when no core overview figure already owns the arc. | sparse | skia | conceptual |

### Named Composition Exemplars

- `act-ask-defer-ladder`: risk dial, then a formula gate arrow, then an
  ACT / ASK / DEFER ladder with per-band z-conditions and `c_ask` / `c_def`
  threshold leaders. Do not replace it with a plain three-band ladder.
- `two-pillar-target`: an uncluttered two-pillar target with one meaningful
  formula or one-liner per pillar and a hazard cue on the frozen-FM node. It
  fails in both directions: packed with prose it reads as a table, stripped to
  labeled chips it reads as a generic flowchart.
- `feasibility-dumbbell`: the real-data transfer figure, with the chance band,
  one hazard cue beside the below-chance region when at least one point falls
  below chance, and direct values.

### Anti-Patterns (reject in review)

- `literal-ladder-only`: a ladder with labels but no dial, formula gate,
  per-band conditions, or threshold leaders.
- `chip-only-pillars`: pillars with subtype chips but no formula, test, or
  claim-level content (a generic flowchart).
- `table-in-card`: too many subtypes, formulas, and prose snippets packed into
  one schematic so it reads like a table.
- `custom-hazard`: any warning glyph drawn outside the shared helper
  (`hazard()` in skia, `hazard_triangle()` in matplotlib).

### The Density Gate

The target is a specific density rather than simply a lighter one, because a
schematic fails when it is packed and again when it is stripped. A schematic
passes the density gate when each region carries one meaningful formula or
one-liner, holds at most three chips, uses no paragraph blocks, and places at
most one hazard cue. Use a hazard cue only where the composition contract or the
brief names a genuine failure, leak, defer, below-chance, or alarm locus; a
contract that names one requires exactly one. A benign comparison carries none.
State the chosen density target in every brief and reject a candidate that
satisfies the shape but fails this gate.

## Additive Shapes (from figures4papers, kept at small-figure size)

| Archetype | What it shows | Fits | Tool | Usual class |
|---|---|---|---|---|
| Grouped bar | A quantitative comparison across two or three conditions, values labeled, black bar edges | A clean before-after or method-versus-baseline | matplotlib | illustrative or real-data |
| Shaded-band trend | One metric over training or time with a light confidence or spread fill | A learning curve or a convergence claim | matplotlib | illustrative or real-data |
| Compact heatmap | A small pairwise grid (transfer, confusion, ablation) in `magma_r`, so the worst cell is darkest | A matrix relationship across classes | matplotlib | usually real-data |

Render these at the same small column-width sizing as the shapes above. Use the
encoding techniques in `visual-system.md` (black bar edges, single-color alpha
for sweeps, hatch for grayscale print safety), but keep the small fonts and thin
lines. The large-figure defaults from the source repo would regress the look at
our size.

## Mapping Sections to Archetypes

When listing candidates in Phase 2 of the skill, give each target section one or
two archetypes whose message matches what that section actually claims. A worked
example:

- Aim 1 (data layer): decision ladder, test-martingale alarm, detector triad.
- Aim 2 (model layer): two-pillar fork, paired equivalence test,
  knowledge-boundary gap.
- Aim 3 (harness layer): interaction graph, MAPE-K loop, latent-cause
  posterior, least-agency knee, feasibility dumbbell.

Cover every section, vary the shape, and over-generate so the author has real
choices to cut.
