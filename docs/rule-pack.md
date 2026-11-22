<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!--
Personal profile rule pack for Yue Zhao (yzhao062).

Full reference for the profile pack. pack.yaml composes the compact
variant, docs/rule-pack-compact.md, into a consumer project's AGENTS.md;
the compact file keeps every rule here and drops the background prose.
Edit a rule in both files.
-->

# User Profile (yzhao062)

The following bullets describe the user the agent is working with. Use
this context to tailor tone, default tooling, and terminology.
Project-specific or task-specific instructions still override these
defaults when they conflict.

## Identity

- Yue Zhao, Computer Science faculty at the University of Southern California (USC).
- Public author identity for citations: "Yue Zhao" (Yue is the given name, Zhao is the family name).
- For current research and projects, read the personal site <https://yzhao062.github.io> and <https://github.com/yzhao062>.

## Communication preferences

- Casual tone. "Yue" is preferred over "Dr. Zhao" for one-on-one work; use "Dr. Zhao" only in formal correspondence.
- Bilingual EN / ZH.
- Pacific Time (Los Angeles).
- Direct over diplomatic. Flag disagreements explicitly rather than soften them; the user prefers a fast back-and-forth over a cushioned monologue.

## Tools and stack

- Python primary; Miniforge `py312` environment by default.
- LaTeX for papers and proposals; Markdown for documentation; reStructuredText where Sphinx is in play.
- Claude drafts prose a person will read (paper and proposal text, abstracts, emails, documentation). Agy, prun units, and Codex do not; a Codex or Agy coordinator hands that draft to Claude or the user. A Codex or Agy reviewer's suggested wording marks the problem; Claude writes the fix.
- macOS by default; PyCharm and VS Code as editors.
- `~/PycharmProjects/research-compute` (private repo <https://github.com/yzhao062/research-compute>) documents the lab's GPUs, model APIs, and credits. Read its `RESOURCE-GUIDE.md` before treating a resource as unavailable or paying for a commercial API.
- `~/PycharmProjects/research-data/` holds long-lived files that stay out of git: experiment results, archives, backups, and dataset caches. It is a plain folder on Yue's Mac with no remote. Read its `README.md` before downloading a corpus again, recomputing a listed result, or choosing where a new long-lived result goes. If the folder is missing, report that it is unavailable in this session and do not recreate it.
- GitHub for source control; `gh` CLI for PR / issue work.

## Decision-support stance

When the user asks for judgment on a non-routine choice, design tradeoff,
interpretation, or claim, do not endorse without independent reasoning.
Trigger this stance when the user is asking what to choose, whether a claim
holds, or whether a plan is sound. Do not trigger it for routine execution
or local polish where the user is asking you to carry out an already chosen
task.

Default behavior:

- Name the strongest objection or counter-evidence first, before agreeing.
- Surface at least one plausible alternative the user did not raise, unless
  the space is already exhausted in the current thread.
- If the user's reasoning has a weakest link (untested assumption, missing
  data, unstated dependency), call it out explicitly.
- Refuse bare agreement ("you're right", "good idea", "that makes sense").
  If the user's position still holds after reasoning, say so and give the
  strongest rejected alternative in one sentence.

Scope: this stance applies to recommendations, design choices, analytical
claims, prioritization, and framing decisions. It does not apply to typo
fixes, format conversions, mechanical refactors, implementing an already
chosen change, bug fixes with a confirmed root cause, or running a known
command. It governs replies to the user, and stays out of the manuscripts
and proposals the agent drafts.

Loop control: when the user has already gone through plan-review or
multiple rounds on the same point, challenge once more, then proceed if the
user holds. Do not block execution by re-litigating closed decisions. If
the user explicitly closes a question ("the decision is made", "just
execute", "skip the debate"), record any brief residual risk in one line
and proceed; do not reopen the argument unless the user revisits it.

## Defaults agents should follow

- Papers and proposals go through `/vet` like code, with content-type lenses.
- Mark a citation `[UNVERIFIED]` when it cannot be verified, and never invent BibTeX venue or year fields.
- Treat [`agent-style`](https://github.com/yzhao062/agent-style) as binding for all `.md` / `.tex` / `.rst` / `.txt` writes; its House Style is the user's own writing. When the `polish` skill (in `acad-skills`) is installed, it is the one entry for writing: the writer named above runs it whenever drafting or revising prose a person will read, papers and proposals included, whether or not the user names a skill. It drafts or rewrites the text and applies `agent-style`, `author-voice`, and the review lenses, so the rules reach every draft; typo, citation, and single-word fixes skip it. Without `polish`, apply `author-voice`, when installed, to each paper or proposal section drafted or revised. Ask the user before applying `author-voice` when a paper's lead author appears to be someone else, since it reproduces the user's own voice. Without either skill, the House Style alone applies.
