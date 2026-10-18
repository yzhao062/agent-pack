#!/usr/bin/env python3
"""Measure a draft against the author's own ranges, measured on five first-author papers.

Usage: python voice_check.py FILE [--section abstract|introduction|conclusion|other]

Reads .md, .tex, or .txt. Prints each measure, the author's range, and whether the draft sits
inside it. Advisory only: always exits 0. A value outside the range is a prompt to reread that
part of the draft, not an error; the author departs from each habit now and then.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SIGNPOSTS = ("Moreover", "Notably")  # the two RULE-D lets open one sentence in a paragraph
NEVER_OPENERS = ("Additionally", "Furthermore", "In addition", "What's more")
IMPORTANCE = re.compile(r"\b(important|crucial|critical|increasingly|ubiquitous|widely (used|adopted)|"
                        r"attracted|gained|growing|rapid(ly)?)\b", re.I)
ROADMAP = re.compile(r"\b(rest|remainder) of (this|the) paper\b|\bis organized as follows\b", re.I)
TELLS = re.compile(r"\b(leverag\w*|facilitat\w*|utiliz\w*|novel|foster\w*|necessitat\w*)\b", re.I)
FILLER = re.compile(r"\bit is (worth noting|important to note|noteworthy) that\b", re.I)
ABBREV = re.compile(r"\b(e\.g|i\.e|et al|etc|vs|cf|Fig|Figs|Eq|Sec|Tab|resp|w\.r\.t|avg|approx)\.", re.I)


def plain(text: str, suffix: str) -> str:
    """Reduce LaTeX or Markdown to prose good enough for counting."""
    if suffix == ".tex":
        text = re.sub(r"(?<!\\)%.*", "", text)
        text = re.sub(r"\\begin\{(figure|table|algorithm|equation|align)\*?\}.*?\\end\{\1\*?\}", " ", text, flags=re.S)
        text = re.sub(r"\\(cite[tp]?|ref|label|url|footnote)\*?(\[[^\]]*\])?\{[^{}]*\}", "", text)
        # A heading or an environment boundary ends a paragraph and is not prose.
        text = re.sub(r"\\(begin|end|(?:sub)*section|paragraph)\*?(\[[^\]]*\])?\{[^{}]*\}", "\n\n", text)
        # Inline math that holds a number stays countable ($58\%$); other math becomes a placeholder.
        text = re.sub(r"\$([^$]*)\$",
                      lambda m: m.group(1) if re.search(r"\d", m.group(1)) and not re.search(r"[_^=]", m.group(1)) else "MATH",
                      text)
        text = text.replace("\\%", "%")
        text = re.sub(r"\\(textbf|textit|emph|texttt|underline|mathrm)\{([^{}]*)\}", r"\2", text)
        text = re.sub(r"\\item\b", "\n\n", text)
        text = re.sub(r"\\[A-Za-z]+\*?(\[[^\]]*\])?", " ", text)
        text = text.replace("{", "").replace("}", "").replace("~", " ").replace("``", '"').replace("''", '"')
    else:
        text = re.sub(r"(?m)^[ \t]{0,3}#{1,6}[ \t].*$", "", text)
        # Each list item stays its own paragraph; [ \t] keeps the blank lines before it.
        text = re.sub(r"(?m)^[ \t]*(?:[-*+]|\d+\.)[ \t]+", "\n\n", text)
        text = text.replace("**", "").replace("__", "").replace("`", "")
    return text


def sentences(par: str) -> list[str]:
    masked = ABBREV.sub(lambda m: m.group(0).replace(".", "\0"), par)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(\"'])", masked)
    return [p.replace("\0", ".").strip() for p in parts if len(p.split()) >= 3]


def contribution_list(raw: str) -> tuple[bool, str]:
    """Whether the text ends on a contribution list: its last "contribution(s)" sits in the second half,
    and at least two items follow, counted as list lines, paragraphs, or sentences that open with "We"."""
    hits = list(re.finditer(r"\bcontributions?\b", raw, re.I))
    if not hits or hits[-1].start() < len(raw) / 2:
        return False, "no" if not hits else "too early"
    tail = raw[hits[-1].end():]
    items = max(len(re.findall(r"(?m)^[ \t]*(?:[-*+]|\d+\.|\\item\b)", tail)),
                len([p for p in re.split(r"\n\s*\n", tail) if len(p.split()) >= 5]),
                len(re.findall(r"(?:^|[.:]\s+|\*\*\s*)We\s", tail)))
    return items >= 2, f"{items} items" if items >= 2 else "no list"


def measure(text: str, section: str, raw: str | None = None) -> list[tuple[str, str, str, bool]]:
    raw = text if raw is None else raw
    paras = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    sents = [s for p in paras for s in sentences(p)]
    words = sum(len(p.split()) for p in paras) or 1
    k = 1000 / words
    lens = [len(s.split()) for s in sents] or [0]
    rows: list[tuple[str, str, str, bool]] = []

    def row(name, value, rng, ok):
        rows.append((name, value, rng, ok))

    long_share = 100 * sum(n > 30 for n in lens) / len(lens)
    if len(sents) >= 5:
        row("sentences over 30 words", f"{long_share:.0f}%", "15% to 40%", 15 <= long_share <= 40)
    gloss = len(re.findall(r"\b(e\.g\.|i\.e\.)|\(say,", text)) * k
    paren = text.count("(") * k
    if words >= 120:
        row("e.g. / i.e. glosses per 1,000 words", f"{gloss:.1f}", "1.5 or more", gloss >= 1.5)
        row("parentheses per 1,000 words", f"{paren:.1f}", "12 to 45", 12 <= paren <= 45)
    openers = [re.match(r"[\"'(]*([A-Za-z' ]+?),", s) for s in sents]
    heads = [m.group(1) for m in openers if m]
    busy = [i + 1 for i, p in enumerate(paras)
            if sum(any(s.startswith(w) for w in SIGNPOSTS + NEVER_OPENERS) for s in sentences(p)) > 1]
    row('paragraphs opening two sentences with "Moreover", "Notably", or kin', ", ".join(map(str, busy)) or "none",
        "none", not busy)
    never = sorted({h for h in heads if h in NEVER_OPENERS})
    row("openers the author does not use", ", ".join(never) or "none", "none", not never)
    so = len(re.findall(r", so (?!that\b)", text))
    row('", so" clause joins', str(so), "0", so == 0)
    semi = text.count(";") * k
    row("semicolons per 1,000 words", f"{semi:.1f}", "4 or fewer", semi <= 4)
    dashes = len(re.findall(r"\u2014|\u2013(?!\d)|---| -- ", text))
    row("dashes as punctuation", str(dashes), "0 (RULE-B)", dashes == 0)
    filler = len(FILLER.findall(text))
    row('"it is worth noting that" and kin', str(filler), "0", filler == 0)
    tells = sorted({m.group(0).lower() for m in TELLS.finditer(text)})
    row("words agent-style flags (leverage, novel, ...)", ", ".join(tells) or "none", "none (kept out on purpose)",
        not tells)

    figures = re.findall(r"(?<![\w.])\d[\d,]*(?:\.\d+)?%?\+?", text)
    if section == "abstract":
        row("numeric figures", str(len(figures)), "0 to 2", len(figures) <= 2)
    if section == "conclusion":
        row("numeric figures", str(len(figures)), "0 to 1", len(figures) <= 1)
    if section == "abstract" and sents:
        first = sents[0]
        row("first sentence opens on the field's importance", "yes" if IMPORTANCE.search(first) else "no",
            "no", not IMPORTANCE.search(first))
        asks = any(s.rstrip().endswith("?") for s in sents)
        row("asks the problem as a question", "yes" if asks else "no", "about half the time", True)
    if section == "conclusion":
        row("words", str(words), "70 to 250", 70 <= words <= 250)
    if section == "introduction":
        road = bool(ROADMAP.search(text))
        row("roadmap paragraph", "yes" if road else "no", "no", not road)
        ok, how = contribution_list(raw)
        row("ends on a contribution list", how, "yes", ok)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file")
    ap.add_argument("--section", default="other", choices=["abstract", "introduction", "conclusion", "other"])
    a = ap.parse_args()
    path = Path(a.file)
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"voice_check: cannot read {path}: {exc}")
        return
    rows = measure(plain(raw, path.suffix.lower()), a.section, raw)
    width = max(len(r[0]) for r in rows)
    for name, value, rng, ok in rows:
        print(f"{'ok   ' if ok else 'CHECK'}  {name:<{width}}  {value:>10}   author: {rng}")
    off = sum(not r[3] for r in rows)
    print(f"\n{off} of {len(rows)} measures outside the author's range.")


if __name__ == "__main__":
    main()
    sys.exit(0)
