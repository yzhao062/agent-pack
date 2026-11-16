---
name: polish
description: Review and polish a draft in place in one command. Runs the deterministic style audit and, for a paper or proposal, the author-voice check; judges claims and length against the review lenses; edits only what the review flags; reruns the checks; and reports what changed. Papers and proposals get the full pass, and any other technical writing gets the readability pass.
---

# Polish

This skill holds an order of steps, the limits on an edit, and a report. The style rules live where every agent already reads them: `AGENTS.md` (Writing Defaults, Formatting Defaults, and the composed `agent-style` pack with its House Style), the `author-voice` skill, and the `/vet` review lenses in `implement-review/references/review-lenses.md`. Follow them there and do not copy them here. Resolve `implement-review` and `author-voice` through the skill lookup order in `AGENTS.md`.

## Scope

- **Target.** The files the user names, and a section when named. Edits go in place, so the git diff is the review surface. Run `git status` first and tell the user when the target already has uncommitted edits, since the diff will mix them with this pass.
- **Kind.** A paper or proposal gets every step. Other technical writing (README, docs, report, email draft) gets the steps not marked *paper or proposal*.
- **Mode.** `review` (or "just review") stops after step 2. Otherwise run all steps.
- **Writer.** The profile pack has Claude draft prose a person will read. Under Codex or Agy this overrides Kind and Mode: run only steps 1 and 2, skip steps 3 and 4, and report the findings with locations and the baseline check results in place of step 5's change report. The edits go to Claude or the user.
- **Lead author.** `author-voice` reproduces the user's own voice. When a paper's lead author appears to be someone else, ask before applying it.
- **Local rules.** Read the repository's `AGENTS.local.md` and any style source it names. Where they set a genre's conventions (a federal proposal's opening, a peer review's register, an email template's punctuation), they govern that draft: report a departure from the shared defaults, and do not edit toward the default.

## Steps

1. **Baseline.** Record each target's word count, and for a revision the count in the last commit (`git show HEAD:<file>`).
2. **Review, read-only.** Collect findings, each with its location, in three groups: *must fix* (a banned word, a claim the evidence does not support in either direction, a fact to verify), *should fix* (a passage that reads badly), and *consider* (a rule departure that may read well).
   - Run `<python> <implement-review>/scripts/style-audit.py --repo <repo> --all-lines <file>`. It always exits 0; read `Style status:` and the rules it reports as partly or not covered, and audit those by reading the rule pack.
   - *Paper or proposal:* run author-voice step 4's `voice_check.py` on each section with its `--section` value. A section that shares a file with other text is copied alone into the session scratchpad first.
   - Read for what no script sees, using the review lenses: for any prose, General items 7 and 8; for a paper, the Paper preamble (undersell and overclaim, accretion) and items 1, 4, 7, and 8; for a proposal, the common proposal dimensions. Compare growth against the baseline.
3. **Polish in place.** For an abstract, introduction, or conclusion, read the `author-voice` template and exemplars for that section first. Then edit only the passages step 2 flagged, with the smallest change that clears each finding:
   - Never add a fact, number, citation, link, example, or claim, and never add a connective that asserts a cause, contrast, or sequence the text does not state. Removing such a connective is allowed.
   - Cut only words that carry no meaning. A hedge or guarantee ("never", "may", "once"), a stated cause, an interval, a tie, a loss, and a marker of exploratory, post-hoc, or review status all stay; removing one is the author's call, so list it.
   - Keep each stated relation at its strength and in its place. Change a `, so` join only where that sentence reads badly, into a split that keeps the cause word; "Since X, Y" fits only when X is already known, not a result being reported. Outside the joins and moves author-voice step 4 names for a `CHECK`, which must also keep every relation, qualifier, and attachment, do not merge or reorder sentences or move a parenthetical, citation, or list to another attachment point. Do not shorten a clause such as "which X it is measured against" to "the X used", end a sentence on a participle ("..., making X"), or open with a transition the text lacked.
   - Keep the sentence's subject, voice, and mood, and the format (LaTeX macros, labels, citations, comments, Markdown structure), unless a finding names them.
   - Treat a `voice_check` `CHECK` or an audit count as a prompt to reread, not a number to move. Handle a `CHECK` as author-voice step 4 says, within the rules above, and keep the departure when the revision would read worse.
   - The word count stays or falls, and no word is added to offset a cut. Replace every banned word. A departure that reads well may stay.
   - Do not apply a change that narrows or reframes a headline claim; list it for the author. Do not move content between sections; flag it.
4. **Recheck.** Rerun the style audit and, for a paper or proposal, `voice_check.py`. Revise once more only for a new *must fix*. Fix a remaining finding you judge real, or keep it with a specific reason.
5. **Report in the reply, never in the file.**
   - Files and sections changed, and word count before and after.
   - One line per changed phrase: the specific finding it answers (for example `RULE-C line 12` or `voice_check ", so"`), or "taste" when none did, with the wording before and after.
   - Style-audit findings before and after, and the last `voice_check` summary line with any `CHECK` kept and why.
   - Items left for the author: claim changes not applied, facts to verify, structural moves.
   - Next steps: `git diff` to accept or discard hunks, and `/vet` for an independent read before a submission.

Keep the run to one agent. An independent second read is `/vet`'s job, and this skill never dispatches it.
