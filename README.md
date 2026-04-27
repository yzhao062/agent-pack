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
| `acad-skills` | Active (skill pack) | ✅ Loadable on `anywhere-agents` v0.5.0+ | Installs three academic-writing skills (`bibref-filler`, `dual-pass-workflow`, `figure-prompt-builder`) into `.claude/skills/`. v0.5.0 wired the consumer-side remote-fetch path; one-line `pack add` from this repo |

The repo doubles as a clean reference: the structure is what every third-party pack should look like.

## Consumer Setup

### Today: v0.4.0

The passive pack bodies in this repo are usable today, but stock `anywhere-agents` v0.4.0 cannot discover arbitrary third-party pack names from a consumer `agent-config.yaml`. Its legacy `rule_packs:` path only resolves names that are already registered in the bootstrap manifest shipped by `anywhere-agents`.

Use one of these paths for v0.4.0:

1. **Manual copy** (simplest). Copy the relevant passive sections from `docs/rule-pack.md` and `docs/paper-workflow.md` into the consumer repo's `AGENTS.local.md`. The local override is hand-authored and never overwritten by bootstrap, so the content stays put across upstream syncs.
2. **Fork the bootstrap manifest** (reusable). Fork `anywhere-agents`, add entries for `profile` and `paper-workflow` to your fork's `bootstrap/packs.yaml` pointing at this repo's `source.repo`, and have consumer projects bootstrap from your fork (`AGENT_CONFIG_UPSTREAM=<your-fork>`). Then `agent-config.yaml` `rule_packs:` can list the registered names and the composer resolves them via the manifest.

### After `anywhere-agents` v0.5.0

v0.5.0 added direct-URL pack discovery and the 4-method auth chain (SSH → gh CLI → `GITHUB_TOKEN` → anonymous), so installing directly from this repo is a one-line command:

```bash
anywhere-agents pack add https://github.com/yzhao062/agent-pack --ref v0.1.0
```

Re-run bootstrap. The composer reads `pack.yaml`, fetches the three packs declared there (`profile`, `paper-workflow`, `acad-skills`), composes the passive bodies into `AGENTS.md`, and installs the active skills under `.claude/skills/`. No fork required.

Install a subset by passing `--pack <name>` once per pack to install:

```bash
# profile only (general dev / OSS projects)
anywhere-agents pack add https://github.com/yzhao062/agent-pack --ref v0.1.0 --pack profile

# profile + paper-workflow (revision-phase paper repos that do not need acad-skills yet)
anywhere-agents pack add https://github.com/yzhao062/agent-pack --ref v0.1.0 --pack profile --pack paper-workflow
```

Default `update_policy` is `prompt` in v0.5.0: each bootstrap surfaces upstream drift via a banner and asks before applying. Set `ANYWHERE_AGENTS_UPDATE=apply` for non-interactive refresh, or pin `update_policy: locked` per-entry in `agent-config.yaml` for packs that must never auto-refresh.

### Ref strategy

In production, pin `source.ref` to a release tag (`v0.1.0`), not `main`. The manifest in this repo currently uses `main` as a development convenience; once a tag is published, switch consumer projects to the tag for reproducibility.

## Pack Selection by Project Type

A reference matrix for which packs to load on which kinds of project:

| Project type | `profile` | `paper-workflow` | `acad-skills` |
|---|---|---|---|
| General dev / OSS | ✅ | — | — |
| Solo paper, no Overleaf | ✅ | — | ✅ |
| Co-PI paper with Overleaf | ✅ | ✅ | ✅ |
| Submitted paper, revision phase only | ✅ | ✅ | — |
| Funding proposal | ✅ | ✅ | ✅ |

> [!NOTE]
> Active skill installation requires `anywhere-agents` v0.5.0+, which added direct-URL pack discovery and the 4-method auth chain. Consumers still on v0.4.0 can use the passive bodies (`profile`, `paper-workflow`) by copying them into local instructions or by registering the packs in a bootstrap manifest they control; the active `acad-skills` pack is loadable only on v0.5.0+.

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
├── skills/                    # `acad-skills` pack content (active)
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

- **v0.1.0** *(this release; the `anywhere-agents` v0.5.0 acceptance-test target)*: `profile`, `paper-workflow`, and `acad-skills` are all loadable via `anywhere-agents` v0.5.0's direct-URL `pack add`. Consumers run `anywhere-agents pack add https://github.com/yzhao062/agent-pack --ref v0.1.0` to install all three; `--pack <name>` filters to a subset. v0.4.0 consumers can still reuse the two passive bodies by copying them into `AGENTS.local.md` or by registering the packs in a bootstrap manifest they control.
- **v0.2.0+**: content refresh as the maintainer's profile and paper-workflow conventions evolve. Tag and content change; manifest structure stays stable.
- **Later**: additional domain packs as the maintainer's workflow expands. Each new pack is a new entry in `pack.yaml`; the structure stays stable.

## License

The repo carries two licenses, one for code and one for the passive pack bodies, so forks can reuse the prose under attribution-preserving terms while the code remains under a permissive software license.

- **Code, configuration, manifests** (`pack.yaml`, `scripts/`, `.github/`, `validate.py`, etc.): Apache License 2.0. See [LICENSE](LICENSE).
- **Passive pack bodies** (`docs/rule-pack.md`, `docs/paper-workflow.md`, and any future `docs/*.md` pack body): CC-BY-4.0. See [LICENSES/CC-BY-4.0.txt](LICENSES/CC-BY-4.0.txt). SPDX header in each file declares the license; full legal text at <https://creativecommons.org/licenses/by/4.0/legalcode>.

If you fork this repo as a starting point for your own pack, you may keep both licenses or replace either with your own choice. The CC-BY-4.0 attribution requirement applies only if you keep the upstream prose; if you fully replace `docs/rule-pack.md` and `docs/paper-workflow.md` with your own writing, that writing is yours to license however you want.

<div align="center">

<a href="#readme-top">↑ Back to Top</a>

</div>
