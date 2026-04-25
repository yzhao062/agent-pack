<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!--
Personal profile rule pack for Yue Zhao (yzhao062).

This file is composed as passive content into a consumer project's
AGENTS.md by the anywhere-agents bootstrap when the consumer references
this pack in agent-config.yaml. Any agent reading AGENTS.md
(Claude Code, Codex, others) gets this profile on session start.

Mirrors RULES.md / a single source of truth for the profile pack.
-->

# User Profile (yzhao062)

The following bullets describe the user the agent is working with. Use
this context to tailor tone, default tooling, terminology, and venue
conventions. Project-specific or task-specific instructions still
override these defaults when they conflict.

## Identity

- Yue Zhao, Computer Science faculty at the University of Southern California (USC).
- Research focus: machine learning, anomaly detection, outlier ensembles, automated tabular ML, and applied AI for science.
- Personal site: <https://yzhao062.github.io>.
- Public author identity for citations: "Yue Zhao" (Yue is the given name, Zhao is the family name).

## Public projects

- [PyOD](https://github.com/yzhao062/pyod): Python anomaly detection library. Around 9.8k GitHub stars, 38M+ total downloads, ~12k research citations.
- [PyGOD](https://github.com/pygod-team/pygod): graph outlier detection library, sister project to PyOD.
- [anywhere-agents](https://github.com/yzhao062/anywhere-agents): public AI agent configuration with pack architecture.
- [agent-style](https://github.com/yzhao062/agent-style): writing rule pack covering AI-tell vocabulary, formatting, and field-observed LLM patterns.
- [agent-config](https://github.com/yzhao062/agent-config): personal working dir and canonical source for anywhere-agents.
- [agent-pack](https://github.com/yzhao062/agent-pack): this repo, personal pack and reference example for third-party pack authors.

## Communication preferences

- Casual tone. "Yue" is preferred over "Dr. Zhao" for one-on-one work; use "Dr. Zhao" only in formal correspondence.
- Bilingual EN / ZH. Switch language by context; do not translate code, paths, or technical identifiers.
- Pacific Time (Los Angeles).
- Direct over diplomatic. Flag disagreements explicitly rather than soften them; the user prefers a fast back-and-forth over a cushioned monologue.

## Common tasks and venue conventions

- **Research papers.** NeurIPS, ICML, ICLR, KDD, NeurIPS-DB tracks default. ACL / EMNLP for NLP work; CVPR / ICCV for vision.
- **Funding proposals.** NSF Merit Review framework default; NIH Simplified Peer Review when the call is biomedical. DOE / DOD only on explicit request. Avoid DEI-related terms in NSF / federal proposals unless the solicitation explicitly requires them.
- **Reviews.** Code reviews use the [`implement-review`](https://github.com/yzhao062/anywhere-agents/blob/main/skills/implement-review/SKILL.md) skill (dual-agent: Claude Code implements, Codex reviews). Paper / proposal reviews follow the same pattern with content-type lenses.
- **Writing discipline.** Follows the [`agent-style`](https://github.com/yzhao062/agent-style) 21-rule pack: 12 classic rules (Strunk / White / Orwell / Pinker tradition) + 9 field-observed LLM patterns (em-dash overuse, summary-tail paragraphs, sentence-opener repetition, transition word overuse, and so on).

## Tools and stack

- Python primary. Miniforge `py312` environment as default; prefer `mamba` over `conda` for installs.
- LaTeX for papers and proposals; Markdown for documentation; reStructuredText where Sphinx is in play.
- Claude Code is the primary workhorse (drafting, implementation, research). Codex is the gatekeeper (review, feedback, quality checks).
- macOS / Windows / Linux all in active use. PyCharm and VS Code as editors.
- GitHub for source control; `gh` CLI for PR / issue work.

## Active focus snapshot

This block goes stale fastest. Treat as a snapshot of what the user is
likely working on at the time of bootstrap; if the date below is older
than a few months, recent context probably differs.

- Snapshot date: 2026-04 (post v0.4.0 release of `anywhere-agents`).
- `pyod` 3 — third major release, expanding modern detector coverage.
- `anywhere-agents` v0.4.x → v0.5.0 — wiring composer-side locks, startup reconciliation, and private-source pack support with auth chain.
- `agent-style` ongoing curation of the 21-rule pack as new LLM patterns surface.
- Active research themes: outlier-detection foundation models, automated detector selection, large-scale benchmark curation.

## Defaults agents should follow

- Confirm before any `git commit` or `git push`. This is non-negotiable across all projects.
- Use `git -C <path>` rather than `cd <path> && git ...` to avoid compound-command approval prompts.
- Verify cited papers actually exist before generating a citation; mark `[UNVERIFIED]` if unable to verify.
- For BibTeX, provide entries that copy cleanly into a `.bib` file; never invent venue / year fields.
- Treat the writing rules in [`agent-style`](https://github.com/yzhao062/agent-style) as binding for all `.md` / `.tex` / `.rst` / `.txt` writes.
