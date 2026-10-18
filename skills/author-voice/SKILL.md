---
name: author-voice
description: Draft or revise the abstract, introduction, or conclusion of a paper or proposal in Yue Zhao's own pre-AI voice. Loads exemplar passages from five first-author papers and a template for each section, then measures the draft against the author's own ranges with a bundled script. Use when writing or rewriting those sections, or when the user asks for text that sounds like their own papers.
---

# Author Voice

The House Style section of `agent-style` is the always-loaded summary of the author's habits. This skill carries what is too long to load in every session: exemplar passages, a template per section, and a script that measures a draft against the author's own ranges. Paths below are relative to this skill's directory.

## Steps

1. Name the section: abstract, introduction, or conclusion. For any other section, the House Style is enough; go to step 4 if a draft already exists.
2. Read the template for that section in `references/templates.md`, then that section's passages in `references/exemplars.md`. Take in each passage whole: the moves, sentence shapes, and connectives carry the voice. Never copy a sentence or a fact from them.
3. Draft from the facts the user gave. Firm rules: never invent a citation, number, dataset, or result, and keep every stated scope and qualifier.
4. Run `python scripts/voice_check.py <draft> --section <abstract|introduction|conclusion|other>`. For each `CHECK` line, reread that part of the draft and revise it where the revision reads better; a departure that reads well can stay. Run the script once more after revising.
5. Report the script's last summary line to the user in your reply, for example `voice_check: 1 of 12 measures outside the author's range (sentences over 30 words, 12%)`. Keep it out of the draft itself and out of any file you write: the draft holds only the section text.

## What Not to Copy

- The unspaced dash (`---`) the author uses for a trailing gloss: RULE-B in `agent-style` bans it.
- Words the passages use that `agent-style` flags as AI tells: "leverage", "facilitate", "novel", and the banned words the guard blocks. Write "use", "help", or "new", or name what is new.
- "Additionally," as a sentence opener, which one passage uses and RULE-D rules out.
- A move the facts you were given do not support. The passages state priority, releases, and future plans that were true of those papers; `references/templates.md` says which moves need the facts behind them.
- One-off idiom slips in the passages, such as "other than" for "rather than".
- More than one rounded figure in an abstract or conclusion.

## Evidence

On twelve sections rewritten from fact sheets by three models, drafts written with the House Style and these exemplars moved closest to the author's originals on word use and on the measures the script reports. In a blind test of drafts written with an earlier form of the habits and these exemplars, the author mistook three of four for their own originals. The script separates the two cases it was built on: the author's own sections average about one measure outside range, and drafts written under the generic rules about three.
