<a id="readme-top"></a>

<div align="center">

# agent-pack

**Personal pack and reference example for [`anywhere-agents`](https://github.com/yzhao062/anywhere-agents).**

A public, fork-friendly pack repo: real content the maintainer uses on every project, plus a clean structure anyone can copy to author their own pack.

[![License](https://img.shields.io/badge/License-Apache_2.0-8b2635.svg)](LICENSE)

[What's Here](#whats-here) &nbsp;·&nbsp;
[Consumer Setup](#consumer-setup) &nbsp;·&nbsp;
[Pack Selection by Project Type](#pack-selection-by-project-type) &nbsp;·&nbsp;
[Fork to Make Your Own](#fork-to-make-your-own) &nbsp;·&nbsp;
[Roadmap](#roadmap)

</div>

## What's Here

| Pack | Type | Status | What It Does |
|---|---|---|---|
| `profile` | Passive (rule pack) | ✅ Loadable today | Loads the maintainer's profile (research focus, public projects, communication preferences, tools, conventions) into the consumer `AGENTS.md` so any agent gets the context on session start |
| `paper-workflow` | Passive (rule pack) | ✅ Loadable today | Loads paper / proposal conventions into the consumer `AGENTS.md`: submodule push and pull etiquette, Overleaf merge-conflict resolution rules, NSF / NIH framework defaults. Apply on academic repos, skip on prototype / OSS repos |
| `acad-skills` | Active (skill pack) | ⏳ Queued for `anywhere-agents` v0.5.0 | Will install three academic-writing skills (`bibref-filler`, `dual-pass-workflow`, `figure-prompt-builder`) into `.claude/skills/`. The skill files are present in this repo today; the consumer-side remote-fetch wiring lands in `anywhere-agents` v0.5.0 |

The repo doubles as a clean reference: the structure is what every third-party pack should look like.

## Consumer Setup

### Today: v0.4.0

The passive pack bodies in this repo are usable today, but stock `anywhere-agents` v0.4.0 cannot discover arbitrary third-party pack names from a consumer `agent-config.yaml`. Its legacy `rule_packs:` path only resolves names that are already registered in the bootstrap manifest shipped by `anywhere-agents`.

Use one of these paths for v0.4.0:

1. **Manual copy** (simplest). Copy the relevant passive sections from `docs/rule-pack.md` and `docs/paper-workflow.md` into the consumer repo's `AGENTS.local.md`. The local override is hand-authored and never overwritten by bootstrap, so the content stays put across upstream syncs.
2. **Fork the bootstrap manifest** (reusable). Fork `anywhere-agents`, add entries for `profile` and `paper-workflow` to your fork's `bootstrap/packs.yaml` pointing at this repo's `source.repo`, and have consumer projects bootstrap from your fork (`AGENT_CONFIG_UPSTREAM=<your-fork>`). Then `agent-config.yaml` `rule_packs:` can list the registered names and the composer resolves them via the manifest.

### After `anywhere-agents` v0.5.0

When v0.5.0 adds remote pack discovery and the active-kind auth chain, install directly from this repo with a release tag:

```bash
anywhere-agents pack add https://github.com/yzhao062/agent-pack --ref v0.1.0
```

Re-run bootstrap. The composer reads `pack.yaml`, fetches the requested packs, and composes passive bodies into `AGENTS.md` plus installs active skills under `.claude/skills/`. No fork required.

Pin a tag rather than `main` for production projects. `update_policy: locked` in `pack.yaml` reinforces that consumers should not float `main`.

### Ref strategy

In production, pin `source.ref` to a release tag (`v0.1.0`), not `main`. The manifest in this repo currently uses `main` as a development convenience; once a tag is published, switch consumer projects to the tag for reproducibility.

## Pack Selection by Project Type

A reference matrix for which packs to load on which kinds of project:

| Project type | `profile` | `paper-workflow` | `acad-skills` |
|---|---|---|---|
| General dev / OSS | ✅ | — | — |
| Solo paper, no Overleaf | ✅ | — | ✅ (v0.5.0+) |
| Co-PI paper with Overleaf | ✅ | ✅ | ✅ (v0.5.0+) |
| Submitted paper, revision phase only | ✅ | ✅ | — |
| Funding proposal | ✅ | ✅ | ✅ (v0.5.0+) |

> [!NOTE]
> v0.4.0 can use the passive Markdown bodies in this repo only by copying them into local instructions or by registering the packs in a bootstrap manifest you control. Direct third-party source-URL discovery and active remote skill installation are queued for `anywhere-agents` v0.5.0, when `anywhere-agents pack add` reads this repo's `pack.yaml` directly and the auth chain handles fetches.

## Fork to Make Your Own

This repo is structured to be forked and replaced.

1. **Fork** this repo to your GitHub account.
2. **Replace** `docs/rule-pack.md` with your own profile (research interests, projects, preferences, conventions). Optionally replace or remove `docs/paper-workflow.md` if you do not write papers.
3. **Update** `pack.yaml`: rename packs to disambiguate (e.g. `profile` → `<your-handle>-profile` if you also load this upstream version), point `source.repo` at your fork.
4. **Tag a release** (`v0.1.0`) so consumers can pin.
5. **Use your fork** through the same split described in [Consumer Setup](#consumer-setup): for v0.4.0, copy the passive bodies into the consumer's `AGENTS.local.md` or register your fork's pack names in a bootstrap manifest you control; for v0.5.0+, run `anywhere-agents pack add https://github.com/<you>/<repo> --ref v0.1.0`.

The whole repo is small. Pack authoring is roughly a 30-minute task once you know what you want in the profile.

## Repo Layout

```text
agent-pack/
├── pack.yaml                  # self-describing manifest (v2 schema)
├── docs/
│   ├── rule-pack.md           # `profile` pack body (passive)
│   └── paper-workflow.md      # `paper-workflow` pack body (passive)
├── skills/                    # `acad-skills` pack content (active, v0.5.0)
│   ├── bibref-filler/
│   ├── dual-pass-workflow/
│   └── figure-prompt-builder/
├── scripts/
│   └── validate.py            # validates pack.yaml against the v2 schema
├── .github/workflows/
│   └── validate.yml           # CI runs validate.py on every push
├── .gitattributes             # forces PDFs and images to binary diff
├── .gitignore                 # standard ignores plus Review-*.md scratch
├── README.md                  # this file
└── LICENSE                    # license terms (see License section below)
```

## Roadmap

- **v0.1.0** *(this release)*: `profile` and `paper-workflow` passive bodies are ready for v0.4.0 reuse by copying into `AGENTS.local.md` or by registering them in a bootstrap manifest you control (e.g., a fork of `anywhere-agents`). `acad-skills` is declared in `pack.yaml` with skill files present, awaiting `anywhere-agents` v0.5.0 for consumer-side remote activation.
- **v0.2.0** *(coordinated with `anywhere-agents` v0.5.0)*: same content, new tag. With v0.5.0's active-kind remote fetch wired, `anywhere-agents pack add https://github.com/yzhao062/agent-pack` installs all three packs (consumer chooses which to keep). No content change required in this repo; the existing manifest works as-is.
- **Later**: additional domain packs as the maintainer's workflow expands. Each new pack is a new entry in `pack.yaml`; the structure stays stable.

## License

The repo carries two licenses, one for code and one for the passive pack bodies, so forks can reuse the prose under attribution-preserving terms while the code remains under a permissive software license.

- **Code, configuration, manifests** (`pack.yaml`, `scripts/`, `.github/`, `validate.py`, etc.): Apache License 2.0. See [LICENSE](LICENSE).
- **Passive pack bodies** (`docs/rule-pack.md`, `docs/paper-workflow.md`, and any future `docs/*.md` pack body): CC-BY-4.0. See [LICENSES/CC-BY-4.0.txt](LICENSES/CC-BY-4.0.txt). SPDX header in each file declares the license; full legal text at <https://creativecommons.org/licenses/by/4.0/legalcode>.

If you fork this repo as a starting point for your own pack, you may keep both licenses or replace either with your own choice. The CC-BY-4.0 attribution requirement applies only if you keep the upstream prose; if you fully replace `docs/rule-pack.md` and `docs/paper-workflow.md` with your own writing, that writing is yours to license however you want.

<div align="center">

<a href="#readme-top">↑ Back to Top</a>

</div>
