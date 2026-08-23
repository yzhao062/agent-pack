"""check_run_config.py -- prove both helpers in a run directory agree.

Run this after tree prep and before the fan-out:

    <python> <skill-dir>/scripts/check_run_config.py --dir <candDir>

It loads `figure_base.py` and, when a batch uses skia, `skia_base.mjs` from the
run directory, then compares the complete palette and the font. Exit 0 means
both helpers resolved the same visual system; any other exit prints what
differs and names the file to fix.

Comparing the whole map matters. A check that samples one role passes while a
`bad` accent or a custom role silently diverges, and a mixed batch then ships
half on palette. Both helpers raise on a malformed `palette.json` rather than
falling back to their defaults, so a config that fails to load fails here too
instead of agreeing on the wrong colors.

The node half builds a `file://` URL with `pathToFileURL`. A bare Windows path
handed to a dynamic `import()` fails with `ERR_UNSUPPORTED_ESM_URL_SCHEME`,
which is a broken check rather than a real disagreement.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

PY_SNIPPET = (
    "import sys, json;"
    "sys.path.insert(0, sys.argv[1]);"
    "import figure_base as f;"
    "print(json.dumps({'palette': f.PALETTE, 'font': f.FONT}, sort_keys=True))"
)

JS_SNIPPET = (
    "import {pathToFileURL} from 'node:url';"
    "const m = await import(pathToFileURL(process.argv[1]).href);"
    "console.log(JSON.stringify({palette: m.PALETTE, font: m.FONT}))"
)


def _run(cmd, label):
    """Return the parsed JSON a helper printed, or exit with its error."""
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"{label} failed to load:", file=sys.stderr)
        print((proc.stderr or proc.stdout).strip(), file=sys.stderr)
        raise SystemExit(2)
    try:
        return json.loads(proc.stdout.strip())
    except ValueError:
        print(f"{label} printed no readable config:", file=sys.stderr)
        print(proc.stdout.strip()[:400], file=sys.stderr)
        raise SystemExit(2)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", required=True, help="the run directory (candDir)")
    ap.add_argument("--node", default=None, help="node executable (default: from PATH)")
    args = ap.parse_args()

    run_dir = os.path.abspath(args.dir)
    if not os.path.isfile(os.path.join(run_dir, "figure_base.py")):
        print(f"no figure_base.py in {run_dir}; copy the helpers first", file=sys.stderr)
        return 2

    cfg = os.path.join(run_dir, "palette.json")
    print("run config:", cfg if os.path.exists(cfg) else "(absent, shipped defaults apply)")

    py = _run([sys.executable, "-B", "-c", PY_SNIPPET, run_dir], "figure_base.py")
    print("matplotlib: font=" + py["font"], "roles=" + ",".join(sorted(py["palette"])))

    skia = os.path.join(run_dir, "skia_base.mjs")
    if not os.path.isfile(skia):
        print("skia_base.mjs is not in this run directory; matplotlib-only batch")
        return 0

    node = args.node or shutil.which("node")
    if node is None:
        print("node is not on PATH, so the skia half was not checked", file=sys.stderr)
        return 2

    js = _run([node, "--input-type=module", "-e", JS_SNIPPET, skia], "skia_base.mjs")
    print("skia:       font=" + js["font"], "roles=" + ",".join(sorted(js["palette"])))

    problems = []
    if py["font"] != js["font"]:
        problems.append(f"font: matplotlib {py['font']!r} vs skia {js['font']!r}")
    for role in sorted(set(py["palette"]) | set(js["palette"])):
        a, b = py["palette"].get(role), js["palette"].get(role)
        if a != b:
            problems.append(f"role {role}: matplotlib {a} vs skia {b}")

    if problems:
        print("the two helpers disagree:", file=sys.stderr)
        for line in problems:
            print("  " + line, file=sys.stderr)
        print(f"fix {cfg}, or the copies of the helpers beside it", file=sys.stderr)
        return 1

    print("OK: both helpers resolve the same palette and font")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
