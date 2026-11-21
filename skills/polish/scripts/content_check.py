#!/usr/bin/env python3
"""Count the content tokens a polish pass changed.

`snapshot` saves each target before the pass. `compare` reads each target again
and prints every number, citation, link, label, cross-reference, and math
expression whose count changed in that file, and names the other searched files
that hold the same token as leads. The report marks a removed token "(in no
searched file)" when the search finds no remaining occurrence.
`compare` exits 0 after printing its report, also when counts changed; a missing
baseline stops it with an error.
"""
import argparse
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

UNITS = {
    "zero": 0, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
}
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
        "eighty": 80, "ninety": 90}
SCALES = {"hundred": 100, "thousand": 1000, "million": 1000000, "billion": 1000000000,
          "half": 0.5, "twice": 2}
ONES = "one|" + "|".join(list(UNITS)[1:9])
PERCENT = r"(?:(?:\s|~)*(?:\\?%|percent\b))?"
# Measurement units written against the value; a layout size such as 2pt is left out.
UNIT = r"(?:[n\u00b5u]?s|ms|sec|min|hr?s?|[KMGTP]i?B|[KMGT]b|[kMG]?Hz|[nmck]m|[km]g|[kM]?W|m?V|mA|dB|fps|k?bp|Mbp)"
NUMBER_WORD = re.compile(
    r"\b(?:(?P<tens>" + "|".join(TENS) + r")(?:-(?P<ones>" + ONES + r"))?|(?P<word>"
    + "|".join(list(UNITS) + list(SCALES)) + r"))\b(?!-[A-Za-z])" + "(?P<pct>" + PERCENT + ")", re.I)
NUMBER = re.compile(
    r"(?:(?<![\w.\-\u2212+])(?P<sign>[+\-\u2212]))?(?:(?<![\w.])|(?<=\d[xX]))"
    r"(?P<num>(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)(?:[eE][-+\u2212]?\d+)?)"
    r"(?:(?P<sfx>[kKmMbB](?!\w)|[xX](?!\d))|(?!\w)|(?=[xX]\d)|(?=" + UNIT + r"(?!\w)))"
    r"(?!\.\d)(?P<pct>" + PERCENT + r")(?P<times>(?:\s|~)*\u00d7(?!\s*\d))?")
CITE = re.compile(r"\\[A-Za-z]*[Cc]ite[A-Za-z]*\*?\s*(?:\[[^\]]*\]\s*){0,2}\{([^}]*)\}")
PANDOC_CITE = re.compile(r"(?<![\w.\\])@([A-Za-z][\w:.#$%&+?<>~/-]*\w)")
LABEL = re.compile(r"\\label\{([^}]*)\}")
REF = re.compile(r"\\(?:ref|eqref|autoref|cref|cpageref|labelcref|pageref|nameref|subref|vref)\*?\{([^}]*)\}",
                 re.I)
HYPERREF = re.compile(r"\\hyperref\s*\[([^\[\]\n]+)\]")
TEX_LINK = re.compile(r"\\(?:url|href)\{([^}]*)\}")
MD_LINK = re.compile(
    r"\[([^\[\]]*)\]\(\s*(?:<([^<>\n]*)>|((?:[^()\s<>]|\([^()\s]*\))+))(?:\s+\"[^\"]*\")?\s*\)")
MD_CODE = re.compile(r"^ {0,3}(`{3,}|~{3,})[^\n]*$.*?(?:^ {0,3}\1[`~]*[ \t]*$|\Z)"
                     r"|(?<!`)(`+)(?!`)(?:(?!\n[ \t]*\n).)*?(?<!`)\2(?!`)", re.M | re.S)
MD_REF_DEF = re.compile(r"^ {0,3}\[(?!\^)([^\[\]\n]+)\]:[ \t]*(?:<([^<>\n]*)>|(\S+))(?:[ \t]+[\"'(].*)?[ \t]*$", re.M)
MD_REF_FULL = re.compile(r"\[([^\[\]]*)\]\[([^\[\]]*)\]")
MD_REF_SHORT = re.compile(r"(?<![\]\\])\[([^\[\]]+)\](?![\[(:])")
MARKDOWN = (".md", ".markdown")
URL = re.compile(r"https?://(?:[^\s()}\]>\"']|\([^\s()}\]>\"']*\))+")
DISPLAY = re.compile(
    r"(?<!\\)\$\$(.+?)\$\$|(?<!\\)\\\[((?:(?!\\\[).)+?)\\\]|\\begin\{((?:equation|alignat|align|flalign|gather|multline|eqnarray)\*?)\}(.+?)\\end\{\3\}",
    re.S)
TEX_INLINE_MATH = re.compile(r"(?<!\\)\$((?:(?!\n\s*\n)[^$])+?)(?<!\\)\$|(?<!\\)\\\(((?:(?!\\\().)+?)\\\)", re.S)
# Pandoc's rule for Markdown: an opening $ has a non-space on its right, a closing $ a non-space on
# its left and no digit after it, so "$50 and $75" is two prices and "$2 + x$" is math.
MD_INLINE_MATH = re.compile(r"(?<!\\)\$(?=\S)((?:(?!\n\s*\n)[^$])+?)(?<![\s(\[{\"])(?<!\\)\$(?!\d)|(?<!\\)\\\(((?:(?!\\\().)+?)\\\)", re.S)
NUMERIC_MATH = re.compile(r"[+\-−]?(?:[\d.,]|\\,)+(?:\\%|%|\\times)?")
TEX_COMMENT = re.compile(r"(?<!\\)((?:\\\\)*)%.*$", re.M)
TEX_URL_ARG = re.compile(r"(\\(?:url|href)\{)([^}]*)(\})")
HTML_COMMENT = re.compile(r"<!--(?:(?!<!--).)*?-->", re.S)
CODE_OR_COMMENT = re.compile(MD_CODE.pattern + r"|(?P<comment>" + HTML_COMMENT.pattern + ")", re.M | re.S)
ALIGNAT_ARG = re.compile(r"(\\begin\{alignat\*?\})\s*\{\d+\}")
FOOTNOTE = re.compile(r"\[\^[^\[\]\s]+\]")
OPTIONAL = re.compile(r"\[([^\]]*)\]")
SUBSCRIPTED = re.compile(r"\b[A-Za-z]+_(?:\{[^{}]*\}|\d+)")
KINDS = ("numbers", "citations", "links", "labels", "cross-references", "math")


def number_key(match):
    value = ((match.group("sign") or "") + match.group("num")).replace("\u2212", "-").replace(",", "").lower()
    if value.startswith((".", "-.", "+.")):
        value = value.replace(".", "0.", 1)
    sfx = (match.group("sfx") or "").lower()
    scale = sfx if sfx in ("k", "m", "b") else ""
    mult = "x" if sfx == "x" or match.group("times") else ""
    return value + scale + ("%" if match.group("pct").strip() else "") + mult


def link_uses(text, markdown):
    """Links a reader can follow, and the text with each link reduced to its visible caption.
    Markdown counts inline links and each use of a reference-style link, resolved to its
    destination; a definition with no use counts for nothing, so removing the last use shows up.
    Ignore link syntax in code spans and fences."""
    live = MD_CODE.sub(lambda m: " " * len(m.group(0)), text) if markdown else text
    links = [m.group(1) for m in TEX_LINK.finditer(live)]
    body = TEX_LINK.sub(" ", text)
    live = TEX_LINK.sub(" ", live)
    if markdown:
        links += [m.group(2) if m.group(2) is not None else m.group(3) for m in MD_LINK.finditer(live)]
        defs = {m.group(1).strip().lower(): m.group(2) if m.group(2) is not None else m.group(3)
                for m in MD_REF_DEF.finditer(live)}

        def caption(match):
            return match.group(1)

        def resolve(match, record=True):
            label = (match.group(2) or match.group(1)).strip().lower()
            if label not in defs:
                return match.group(0)
            if record:
                links.append(defs[label])
            return match.group(1)

        live = MD_REF_FULL.sub(resolve, MD_REF_DEF.sub(" ", MD_LINK.sub(caption, live)))
        links += [defs[m.group(1).strip().lower()] for m in MD_REF_SHORT.finditer(live)
                  if m.group(1).strip().lower() in defs]
        body = MD_REF_DEF.sub(" ", MD_LINK.sub(caption, body))
        body = MD_REF_FULL.sub(lambda m: resolve(m, record=False), body)
        body = MD_REF_SHORT.sub(lambda m: " " if m.group(1).strip().isdigit()
                                and m.group(1).strip().lower() in defs else m.group(0), body)
    links += [m.group(0).rstrip(".,;:") for m in URL.finditer(live)]
    return links, body


def word_key(match):
    if match.group("tens"):
        value = TENS[match.group("tens").lower()]
        ones = (match.group("ones") or "").lower()
        value += 1 if ones == "one" else UNITS.get(ones, 0)
    else:
        word = match.group("word").lower()
        value = UNITS.get(word, SCALES.get(word))
    text = str(value) if value != int(value) else str(int(value))
    return text + ("%" if match.group("pct").strip() else "")


def items(text, markdown=False, tex=True):
    """Return a Counter of content tokens per kind for one text, comments already removed."""
    found = {kind: Counter() for kind in KINDS}
    if markdown:
        text = FOOTNOTE.sub(" ", MD_CODE.sub(lambda m: " " * len(m.group(0)), text))
    text = ALIGNAT_ARG.sub(r"\1", text)
    prose = text
    for match in CITE.finditer(prose):
        for key in match.group(1).split(","):
            if key.strip():
                found["citations"][key.strip()] += 1
    for match in LABEL.finditer(prose):
        found["labels"][match.group(1).strip()] += 1
    for match in REF.finditer(prose):
        for key in match.group(1).split(","):
            if key.strip():
                found["cross-references"][key.strip()] += 1
    for match in HYPERREF.finditer(prose):
        found["cross-references"][match.group(1).strip()] += 1
    links, scrubbed = link_uses(text, markdown)
    for link in links:
        found["links"][link] += 1
    for match in DISPLAY.finditer(text):
        body = match.group(1) or match.group(2) or match.group(4)
        found["math"][re.sub(r"\s+", "", body)] += 1
    for match in (TEX_INLINE_MATH if tex else MD_INLINE_MATH).finditer(DISPLAY.sub(" ", text)):
        body = re.sub(r"\s+", "", match.group(1) or match.group(2))
        if not NUMERIC_MATH.fullmatch(body):
            found["math"][body] += 1
    # A citation's optional arguments (a page in "p.~3") stay in the text; its keys do not.
    rest = CITE.sub(lambda m: " " + " ".join(OPTIONAL.findall(m.group(0).split("{", 1)[0])) + " ", scrubbed)
    rest = URL.sub(" ", HYPERREF.sub(" ", REF.sub(" ", LABEL.sub(" ", rest))))
    cite_text = MD_CODE.sub(lambda m: " " * len(m.group(0)), rest) if markdown else rest
    for match in PANDOC_CITE.finditer(cite_text):
        found["citations"][match.group(1)] += 1
    rest = PANDOC_CITE.sub(" ", rest)
    outside = (TEX_INLINE_MATH if tex else MD_INLINE_MATH).sub(" ", DISPLAY.sub(" ", rest))
    for match in SUBSCRIPTED.finditer(outside):
        found["math"][match.group(0)] += 1
    rest = re.sub(r"(?<=\d)(?:_|\\,)(?=\d)", "", rest)
    rest = re.sub(r"(?<=[A-Za-z}\])])_+(?:\{[^{}]*\}|\d+)", " ", rest).replace("_", " ")
    rest = re.sub(r"\\[A-Za-z]+", " ", rest.replace("\\times", "×"))
    for match in NUMBER.finditer(rest):
        found["numbers"][number_key(match)] += 1
    for match in NUMBER_WORD.finditer(rest):
        found["numbers"][word_key(match)] += 1
    return found


def read(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    suffix = path.suffix.lower()
    if suffix == ".tex":
        guarded = TEX_URL_ARG.sub(lambda m: m.group(1) + m.group(2).replace("%", "\0") + m.group(3), text)
        return TEX_COMMENT.sub(r"\1", guarded).replace("\0", "%")
    if suffix in MARKDOWN + (".html",):
        return CODE_OR_COMMENT.sub(lambda m: " " if m.group("comment") is not None
                                   else m.group(0).replace("$", "\\$"), text)
    return text


def extract(path):
    suffix = path.suffix.lower()
    return items(read(path), suffix in MARKDOWN, suffix == ".tex")


def relpath(path, repo):
    try:
        return path.resolve().relative_to(repo.resolve())
    except ValueError:
        sys.exit(f"content_check: {path} is outside --repo {repo}")


def shown(path, repo):
    """A path relative to the repository when it lies inside it, else as given."""
    try:
        return str(path.resolve().relative_to(repo.resolve()))
    except ValueError:
        return str(path)


def default_rest(targets, repo):
    """Files with a target's extension in its directory, the directory above it inside the
    repository, and one level below each: where a paper's other sections and tables live."""
    seen = {t.resolve() for t in targets}
    rest = []
    for target in (t.resolve() for t in targets):
        roots = [target.parent]
        if target.parent != repo.resolve():
            roots.append(target.parent.parent)
        nearby = [p for root in roots for pattern in ("*", "*/*") for p in root.glob(pattern + target.suffix)]
        for sibling in sorted(nearby):
            if sibling.resolve() not in seen:
                seen.add(sibling.resolve())
                rest.append(sibling)
    return rest


def snapshot(args):
    repo, out = Path(args.repo), Path(args.out)
    for target in map(Path, args.files):
        if not target.is_file():
            sys.exit(f"content_check: {target} does not exist; for a new draft, create it empty first")
        dest = out / relpath(target, repo)
        if dest.exists():
            sys.exit(f"content_check: {dest} already holds a baseline; choose a fresh --out")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, dest)
    print(f"content_check: saved {len(args.files)} file(s) under {out}")


def compare(args):
    repo, base = Path(args.repo), Path(args.baseline)
    targets = [Path(f) for f in args.files]
    missing = [str(t) for t in targets if not (base / relpath(t, repo)).is_file()]
    if missing:
        sys.exit("content_check: no baseline for " + ", ".join(missing) + "; run snapshot before the pass")
    rest = [Path(f) for f in args.also] if args.also else default_rest(targets, repo)
    current = {t: extract(t) for t in targets}
    current.update({r: extract(r) for r in rest if r.is_file()})
    searched = len(current) - len(targets)
    print(f"content_check: {len(targets)} target file(s); {searched} nearby file(s) searched for leads")
    changes = changed_files = 0
    for target in targets:
        before, after = extract(base / relpath(target, repo)), current[target]
        lines = []
        for kind in KINDS:
            entries = []
            for token in sorted(set(before[kind]) | set(after[kind])):
                old, new = before[kind][token], after[kind][token]
                if old == new:
                    continue
                entry = f"{token} {old} -> {new}"
                leads = [shown(p, repo) for p, found in current.items()
                         if p.resolve() != target.resolve() and found[kind][token]]
                if leads:
                    entry += " (also in " + ", ".join(leads) + ")"
                elif new == 0:
                    entry += " (in no searched file)"
                entries.append(entry)
            if entries:
                lines.append(f"  {kind}: " + "; ".join(entries))
                changes += len(entries)
        if lines:
            changed_files += 1
            print(relpath(target, repo))
            print("\n".join(lines))
    print(f"Summary: content_check: {changes} count change(s) in {changed_files} file(s); check each in context")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    snap = sub.add_parser("snapshot", help="save each target before the pass")
    snap.add_argument("--repo", default=".", help="root that the saved paths are relative to")
    snap.add_argument("--out", required=True, help="a fresh baseline directory in the session scratchpad")
    snap.add_argument("files", nargs="+")
    comp = sub.add_parser("compare", help="print the content tokens whose count changed in each target")
    comp.add_argument("--repo", default=".")
    comp.add_argument("--baseline", required=True, help="the directory that snapshot wrote")
    comp.add_argument("--also", action="append", metavar="FILE",
                      help="another file of the document to search for leads (repeatable); default: files "
                           "with the target's extension beside it, one directory up, and one level below each")
    comp.add_argument("files", nargs="+")
    args = parser.parse_args(argv)
    if args.command == "snapshot":
        snapshot(args)
    else:
        compare(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
