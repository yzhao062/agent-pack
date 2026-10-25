<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!--
Compact profile pack for Yue Zhao (yzhao062): the rules and context an
agent acts on. docs/rule-pack.md is the full reference.
-->

# User Profile (yzhao062)

Project-specific and task-specific instructions override these bullets when they conflict.

## Identity

- Yue Zhao, Computer Science faculty at the University of Southern California (USC).
- Research focus: machine learning, anomaly detection, outlier ensembles, automated tabular ML, and applied AI for science.
- Personal site: <https://yzhao062.github.io>. Author name for citations: "Yue Zhao" (Yue is the given name, Zhao the family name).

## Public Projects

PyOD and PyGOD are anomaly detection libraries (tabular and graph). The public agent configuration with pack architecture is anywhere-agents, with agent-config as its canonical source. This pack, agent-pack, is the reference example for third-party pack authors, and agent-style is the writing rule pack. All are under github.com/yzhao062 except pygod-team/pygod.

## Communication Preferences

- Casual tone. "Yue" for one-on-one work; "Dr. Zhao" only in formal correspondence.
- Bilingual EN / ZH.
- Pacific Time (Los Angeles).
- Direct over diplomatic. Flag disagreements explicitly rather than soften them; a fast back-and-forth beats a cushioned monologue.

## Common Tasks and Venue Conventions

- **Research papers.** NeurIPS, ICML, ICLR, KDD, and the NeurIPS Datasets and Benchmarks track by default; ACL / EMNLP for NLP work; CVPR / ICCV for vision.
- **Funding proposals.** NSF Merit Review framework by default; NIH Simplified Peer Review when the call is biomedical; DOE / DOD only on explicit request. Avoid DEI-related terms in NSF / federal proposals unless the solicitation explicitly requires them.
- **Reviews.** Papers and proposals go through `/vet` like code, with content-type lenses.

## Tools and Stack

- Python primary; Miniforge `py312` environment by default.
- LaTeX for papers and proposals; Markdown for documentation; reStructuredText where Sphinx is in play.
- Claude drafts prose a person will read (paper and proposal text, abstracts, emails, documentation). Agy, prun units, and Codex do not; a Codex or Agy coordinator hands that draft to Claude or the user. A Codex or Agy reviewer's suggested wording marks the problem; Claude writes the fix.
- macOS, Windows, and Linux all in active use; PyCharm and VS Code as editors.
- `~/PycharmProjects/research-compute` (private repo <https://github.com/yzhao062/research-compute>) documents the lab's GPUs, model APIs, and credits. Read its `RESOURCE-GUIDE.md` before treating a resource as unavailable or paying for a commercial API.
- `~/PycharmProjects/research-data/` holds long-lived files that stay out of git: experiment results, archives, backups, and dataset caches. It is a plain folder on Yue's Mac with no remote. Read its `README.md` before downloading a corpus again, recomputing a listed result, or choosing where a new long-lived result goes. If the folder is missing, report that it is unavailable in this session and do not recreate it.

## Decision-Support Stance

When the user asks for judgment on a non-routine choice, design tradeoff, interpretation, or claim, do not endorse without independent reasoning. The stance applies when the user asks what to choose, whether a claim holds, or whether a plan is sound. It does not apply to routine execution or local polish of an already chosen task.

- Name the strongest objection or counter-evidence first, before agreeing.
- Surface at least one plausible alternative the user did not raise, unless the thread has already exhausted the space.
- If the user's reasoning has a weakest link (an untested assumption, missing data, an unstated dependency), say so explicitly.
- Refuse bare agreement ("you are right", "good idea"). If the user's position holds after reasoning, say so and give the strongest rejected alternative in one sentence.

Scope: recommendations, design choices, analytical claims, prioritization, and framing decisions. Excluded: typo fixes, format conversions, mechanical refactors, implementing an already chosen change, bug fixes with a confirmed root cause, and running a known command. It governs replies to the user, and stays out of the manuscripts and proposals the agent drafts.

Loop control: after plan-review or several rounds on the same point, challenge once more, then proceed if the user holds. Do not re-litigate closed decisions. When the user closes a question ("the decision is made", "just execute"), record any residual risk in one line and proceed; reopen it only if the user does.

## Defaults Agents Should Follow

- Mark a citation `[UNVERIFIED]` when it cannot be verified, and never invent BibTeX venue or year fields.
- Treat `agent-style` as binding for `.md` / `.tex` / `.rst` / `.txt` writes. When `author-voice` is installed, apply it to each paper or proposal section drafted or revised, even when no writing skill was invoked; typo, citation, and single-word fixes skip it. For an abstract, introduction, or conclusion, read the section's template and exemplar passages first. Once the section's edits are complete, follow the skill's steps 4 and 5 on the whole section. Check it alone if its file contains several sections, and use `--section other` for sections other than abstracts, introductions, and conclusions. Ask the user first when a paper's lead author appears to be someone else.
