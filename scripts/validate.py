#!/usr/bin/env python3
"""Validate pack.yaml against the anywhere-agents v2 manifest schema.

Run from the repo root or via .github/workflows/validate.yml on push.
Exits non-zero on schema violations so CI fails loudly.

Schema reference: anywhere-agents docs/pack-architecture.md, "The unified
manifest" section.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "pack.yaml"

ALLOWED_UPDATE_POLICY = {"locked", "auto"}
ALLOWED_KIND = {"skill", "hook", "permission", "command"}
ALLOWED_HOSTS = {"claude-code", "codex", "all"}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def check_files_list(pack_name: str, label: str, idx: int, files) -> None:
    if not isinstance(files, list) or not files:
        fail(f"pack {pack_name!r}: {label}[{idx}].files must be a non-empty list")
    for k, mapping in enumerate(files):
        if not isinstance(mapping, dict):
            fail(f"pack {pack_name!r}: {label}[{idx}].files[{k}] must be a mapping")
        src = mapping.get("from")
        dst = mapping.get("to")
        if not isinstance(src, str) or not src:
            fail(
                f"pack {pack_name!r}: {label}[{idx}].files[{k}].from must be a non-empty string"
            )
        if not isinstance(dst, str) or not dst:
            fail(
                f"pack {pack_name!r}: {label}[{idx}].files[{k}].to must be a non-empty string"
            )
        # Local-existence check: verify the source path exists in the repo.
        # Strip trailing slash for directory-style refs.
        src_path = ROOT / src.rstrip("/")
        if not src_path.exists():
            fail(
                f"pack {pack_name!r}: {label}[{idx}].files[{k}].from {src!r} "
                f"does not exist in the repo"
            )


def main() -> int:
    if not MANIFEST.exists():
        fail(f"{MANIFEST} not found")

    try:
        data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        fail(f"pack.yaml is not valid YAML: {exc}")

    if not isinstance(data, dict):
        fail("pack.yaml top level must be a mapping")

    if data.get("version") != 2:
        fail("pack.yaml: 'version' must be 2 (v2 manifest schema)")

    packs = data.get("packs")
    if not isinstance(packs, list) or not packs:
        fail("pack.yaml: 'packs' must be a non-empty list")

    seen_names: set[str] = set()
    for i, p in enumerate(packs):
        if not isinstance(p, dict):
            fail(f"pack[{i}] must be a mapping")

        name = p.get("name")
        if not isinstance(name, str) or not name:
            fail(f"pack[{i}] missing or invalid 'name'")
        if name in seen_names:
            fail(f"pack[{i}] duplicate 'name': {name!r}")
        seen_names.add(name)

        # source.repo + source.ref
        source = p.get("source")
        if not isinstance(source, dict):
            fail(f"pack {name!r}: 'source' must be a mapping")
        repo = source.get("repo")
        if not isinstance(repo, str) or not repo:
            fail(f"pack {name!r}: 'source.repo' is required")
        ref = source.get("ref")
        if not isinstance(ref, str) or not ref:
            fail(f"pack {name!r}: 'source.ref' is required and must be a non-empty string")

        # update_policy
        policy = p.get("update_policy")
        if policy is not None and policy not in ALLOWED_UPDATE_POLICY:
            fail(
                f"pack {name!r}: 'update_policy' must be one of {sorted(ALLOWED_UPDATE_POLICY)}"
            )

        # hosts: pack-level optional, must be a non-empty list of valid hosts when present
        pack_hosts = p.get("hosts")
        if pack_hosts is not None:
            if not isinstance(pack_hosts, list) or not pack_hosts:
                fail(f"pack {name!r}: 'hosts' must be a non-empty list when present")
            for h in pack_hosts:
                if h not in ALLOWED_HOSTS:
                    fail(
                        f"pack {name!r}: hosts entry {h!r} not in {sorted(ALLOWED_HOSTS)}"
                    )

        # passive and active
        passive = p.get("passive")
        active = p.get("active")
        if not passive and not active:
            fail(
                f"pack {name!r}: must declare at least one of 'passive' or 'active'"
            )

        if passive is not None:
            if not isinstance(passive, list):
                fail(f"pack {name!r}: 'passive' must be a list")
            for j, entry in enumerate(passive):
                if not isinstance(entry, dict):
                    fail(f"pack {name!r}: passive[{j}] must be a mapping")
                check_files_list(name, "passive", j, entry.get("files"))

        if active is not None:
            if not isinstance(active, list):
                fail(f"pack {name!r}: 'active' must be a list")
            if policy == "auto":
                fail(f"pack {name!r}: active packs cannot use update_policy: auto")
            for j, entry in enumerate(active):
                if not isinstance(entry, dict):
                    fail(f"pack {name!r}: active[{j}] must be a mapping")
                kind = entry.get("kind")
                if kind not in ALLOWED_KIND:
                    fail(
                        f"pack {name!r}: active[{j}].kind must be one of {sorted(ALLOWED_KIND)}"
                    )
                # active entries may carry their own hosts override
                entry_hosts = entry.get("hosts")
                if entry_hosts is not None:
                    if not isinstance(entry_hosts, list) or not entry_hosts:
                        fail(
                            f"pack {name!r}: active[{j}].hosts must be a non-empty list when present"
                        )
                    for h in entry_hosts:
                        if h not in ALLOWED_HOSTS:
                            fail(
                                f"pack {name!r}: active[{j}].hosts entry {h!r} not in {sorted(ALLOWED_HOSTS)}"
                            )
                check_files_list(name, "active", j, entry.get("files"))

    print(f"OK: pack.yaml valid; {len(packs)} pack(s): {sorted(seen_names)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
