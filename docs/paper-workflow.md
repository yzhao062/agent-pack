<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!--
Paper-workflow rule pack: conventions for paper / proposal repos that
use Overleaf submodules and co-PI collaboration. Composed as passive
content into the consumer AGENTS.md by anywhere-agents bootstrap
when the consumer references this pack in agent-config.yaml.

Load this pack on paper / proposal repos. Skip on prototype / OSS repos.
-->

# Paper and Proposal Workflow

Conventions for academic-writing repos that use Overleaf submodules and
co-PI collaboration. Apply when the project is a paper or proposal with
a `.gitmodules` file or an Overleaf-synced subdirectory.

## Submodule Workflow

- Some projects use git submodules for directories shared with collaborators (e.g., co-PI proposal repos, shared paper repos linked to Overleaf).
- At session start, if `.gitmodules` exists, run `git submodule status` to check submodule state. If submodules are uninitialized (prefix `-`), warn the user and suggest `git submodule update --init`.
- Submodule directories have their own `.git` and `origin` remote. Commits and pushes inside a submodule go to the submodule's upstream repo, not the parent.
- **Submodules are shared repos.** Pushes land directly in a collaborator's Overleaf project or co-PI repo. A careless force-push or overwrite can destroy someone else's work. Treat every write operation inside a submodule as high-risk.
- When the user asks to push or pull a submodule:
  1. Before writing, run `git -C <submodule-path> fetch` then `git -C <submodule-path> status` to check for uncommitted local changes. Review recent history with `git -C <submodule-path> log --oneline -5` to see local commits and `git -C <submodule-path> log --oneline -5 --remotes` to see recent remote-tracking activity. This is a quick sanity check, not a full divergence analysis; submodules are often in detached-HEAD state where branch comparisons do not apply cleanly.
  2. Use `git -C <submodule-path>` for git operations inside the submodule. Always confirm with the user before any commit, push, pull, or reset.
  3. Back in the parent repo, update the submodule pointer: `git add <submodule-path>` then commit (also requires confirmation).
- Submodules may have a `.gitignore` that excludes internal-only files (e.g., `.agent/`, `guardrail/`, `figure-spec/`, `figure-src/`). These files exist on disk but are not pushed to the collaborator repo. On a fresh clone, they will be missing. Warn the user if expected internal directories are absent.
- `context/` is synced to co-PI repos and will be available after submodule init.
- Project-specific submodule details (which directories, which upstream repos, which files are internal-only) belong in `CLAUDE.md` or `AGENTS.local.md` in each project repo, not here.

## Overleaf Merge Conflict Resolution

Overleaf-synced repos (usually submodules) require special care during merges. Overleaf's git bridge creates branches from its own snapshot, which may lag behind the latest local push. When a collaborator edits on Overleaf while we push structural changes locally, the Overleaf branch is based on the **pre-push** state. In a merge, "theirs" means "older base plus collaborator styling edits," not "collaborator's newer version." Using `git checkout --theirs` on such files silently discards our work.

**Co-PI changes are the priority.** Our own structural work (compaction, renames) can be redone in minutes because we know exactly what we changed. A co-PI's content changes on Overleaf -- new sentences, rewritten arguments, added references, terminology choices -- represent their intellectual contribution. If we silently drop their edits, we may not even know what was lost, and they may not notice until weeks later. Losing their work is an order of magnitude worse than losing ours. The merge must preserve both sides, but when in doubt, err toward preserving the co-PI's content.

### Rules for merging Overleaf branches with conflicts

1. **Never use `git checkout --theirs`** on files where we have local structural changes (compaction, renames, reorganization). This is the single most dangerous command in an Overleaf merge.
2. **Never use `git checkout --ours` and stop there.** Starting from our version is correct, but the merge is not done until the co-PI's content changes are accounted for. Treating `--ours` as the final answer silently drops their work.
3. **Inspect what the collaborator actually changed** before resolving. First find the merge base: `git merge-base HEAD <overleaf-branch>`. Then run `git diff <merge-base>..<overleaf-branch> -- <file>` to isolate the co-PI's edits relative to the common ancestor, without mixing in our structural changes. Classify each change as:
   - **Content** (new sentences, rewritten arguments, added references, deliberate deletions or shortenings, terminology changes) -- must be preserved. Treat co-PI deletions with the same care as additions; if they removed text, that was a deliberate editorial decision, not noise.
   - **Formatting** (spacing, font commands, styling) -- apply if consistent with our version.
   - **Stale reversions** (undoes our rename or compaction because they edited the pre-push snapshot) -- discard, but note that the co-PI has not seen our change yet. Be careful: a change that looks like a stale reversion may actually be a deliberate content choice. When ambiguous, ask the user.
4. **Apply their content changes onto our structural base.** Start from `git checkout --ours <file>`, then manually integrate every content change identified in step 3. Do not skip any co-PI content change without explicit user approval.
5. **Double-verify before committing** -- check both directions:
   - `git diff <pre-merge-commit> -- <file>` -- confirm our structural changes survived.
   - `git diff <overleaf-branch> -- <file>` -- confirm the only differences from the co-PI's version are our intended structural changes, not dropped content.
   - If the co-PI added entirely new paragraphs or sections, verify they appear in the merged file.
6. **Screen for binary artifacts before staging.** Overleaf branches often carry compiled PDFs, review screenshots (`out-review/`), or other build artifacts that should not be tracked. Use the same merge-base diff from pre-merge checklist step 2 to spot unexpected large files. Add them to `.gitignore` before staging the merge.

### Pre-merge checklist (run before `git merge <overleaf-branch>`)

1. `git fetch` to get the latest Overleaf branch.
2. `git diff --stat $(git merge-base HEAD <overleaf-branch>)..<overleaf-branch>` -- check which files the co-PI actually touched, spot binary artifacts.
3. `git log --oneline HEAD..<overleaf-branch>` -- understand what the collaborator did.
4. If any files we modified structurally appear in the diff, plan to resolve those conflicts manually using the rules above.
5. If the co-PI touched files we did not modify, those should auto-merge cleanly. After the merge, still spot-check them for unintended content loss.

### Recovery if `--theirs` was already used

Restore our structural version from the pre-merge commit with `git restore --source=<pre-merge-commit> --worktree -- <file>` (avoids encoding and line-ending issues from shell redirection on Windows). Then reapply the collaborator's content and formatting changes on top. Do not skip the reapply step -- their work matters too.

## Venue Conventions

For NSF / federal proposal work, do not introduce DEI-related terms unless the solicitation explicitly requires them. For non-federal proposals or calls that explicitly request DEI framing or terminology, follow the call requirements instead of applying a blanket ban.

NSF Merit Review framework defaults: intellectual merit + broader impacts. NIH Simplified Peer Review framework on biomedical proposals.

For paper venues, follow the venue's specific guidelines (NeurIPS / ICML / ICLR / KDD / ACL / EMNLP / CVPR). Do not generate venue-specific formatting (camera-ready, anonymous-version, etc.) unless asked.
