#!/usr/bin/env python3
"""Measure a draft against the author's own ranges, measured on five first-author papers.

Usage: python voice_check.py FILE [--section abstract|introduction|conclusion|other]

Reads .md, .tex, or .txt. Prints each measure, the author's range, and whether the draft sits
inside it. Advisory only: always exits 0. A value outside the range is a prompt to reread that
part of the draft, not an error; the author departs from each habit now and then. Pointers to the
paper's own sections, appendices, figures, and tables (an abstract or conclusion holds none), cited
works (rare in either), and the contribution heads of an introduction are read from the raw text,
before LaTeX is reduced.
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
# A pointer to the paper's own sections, appendices, figures, or tables: a named part before a LaTeX reference command
# ("Section~\ref{...}", "\S\ref{...}"), a bare reference command whose label names such a part ("\ref{sec:exp}"), a
# named part with its number or letter ("section 3", "Table 2", "Appendix B", "Appendix IV", "§4"), or a Markdown
# link to an anchor in the same document whose text or anchor names such a part, counted once. A reference to an
# equation or to an unrecognized label is left to reading.
_NAMED = r"\b(?i:sections?|secs?\.?|appendix|appendices|apps?\.|figures?|figs?\.?|tables?|tabs?\.?)"
_SYMBOL = r"(?:\\S(?![A-Za-z])|§)"
_PART = r"(?:" + _NAMED + r"|" + _SYMBOL + r")"
# Before a bare number or letter, a named part needs a space, a tie, or its own period ("Fig.2"), so a file name or
# identifier such as fig1.png or table2 is not a pointer; a symbol part needs nothing ("§4").
_PART_SEP = r"(?:" + _NAMED + r"(?:(?<=\.)|(?=[\s~]))|" + _SYMBOL + r")"
_PART_WORD = r"(?i:sections?|secs?|appendix|appendices|apps?|figures?|figs?|tables?|tabs?)"
_REF = r"\\(?:[cC]|auto|name|[vV])?ref\*?\s*\{"
# Quarto cross-reference prefixes: "@fig-", "@tbl-", and "@sec-" point at the document's own parts, and these and the
# other reserved prefixes ("@eq-", "@thm-", ...) are never bibliography keys.
_QUARTO_PART = r"(?<![\w.@])@(?i:fig|tbl|sec)-\w"
QUARTO_XREF = re.compile(r"(?:fig|tbl|sec|eq|lst|thm|lem|cor|prp|cnj|def|exm|exr)-", re.I)
POINTER = re.compile(r"\[[^\]]*\b" + _PART_WORD + r"\b[^\]]*\]\(#[^)\s]+\)"
                     r"|\[[^\]]*\]\(#" + _PART_WORD + r"(?=[-_:.\d)])[^)\s]*\)"
                     r"|" + _QUARTO_PART + r"[\w-]*"
                     r"|" + _PART + r"\s*~?\s*" + _REF + r"[^{}]*\}"
                     r"|" + _REF + r"(?i:sections?|ssec|subsec|sec|appendix|appx?|figures?|fig|tables?|tab|tbl)"
                     r"[:._-][^{}]*\}"
                     r"|" + _PART_SEP + r"\s*~?\s*(?:[A-Z]?\d+(?:\.\d+)*[a-z]?|[IVX]+|[A-Z])\b")
# A LaTeX citation command other than \nocite and \citetext, whatever its case or package (\citep, \Citet,
# \parencite), with any spaces LaTeX allows before its options and keys, and a
# Pandoc key, bracketed or narrative ("[@smith2020; @lee2021]", "@smith2020 shows"); an email address is not a key.
CITE = re.compile(r"\\(?!(?:nocite|citetext)\b)[A-Za-z]*[Cc]ite[A-Za-z]*\*?\s*(?:\[[^\]]*\]\s*){0,2}\{([^{}]*)\}")
PANDOC_KEY = re.compile(r"(?<![\w.@])-?@\w(?:[\w:.#$%&+?<>~/-]*\w)?")
TEX_COMMENT = re.compile(r"(?<!\\)((?:\\\\)*)%.*$", re.M)  # an even run of backslashes before % still opens a comment
LIST_ENV = re.compile(r"\\begin\{(itemize|enumerate|list|description)\}")
# A Markdown list marker: a bullet, or an ordered number closed by "." or ")" (both are CommonMark).
MARKER = r"(?:[-*+]|\d{1,9}[.)])"
MD_ITEM = re.compile(r"^[ \t]*" + MARKER + r"[ \t]+")
ITEM_START = re.compile(r"\\item\b|^[ \t]*" + MARKER + r"[ \t]+", re.M)
HEAD_WORDS = 4  # the author's contribution heads after the first run two or three words, never more than four
AFTER_LIST_WORDS = 60  # room for the template's one-sentence Reproducibility line after the contribution list


def uncommented(raw: str, suffix: str) -> str:
    return TEX_COMMENT.sub(r"\1", raw) if suffix == ".tex" else raw


def braced(text: str, i: int) -> tuple[str | None, int]:
    """Return (content, end) of the balanced {...} group that opens at text[i], else (None, i).
    A brace after an odd run of backslashes is escaped."""
    depth = 0
    for j in range(i, len(text)):
        if text[j] not in "{}":
            continue
        k = j
        while k > 0 and text[k - 1] == "\\":
            k -= 1
        if (j - k) % 2:
            continue
        depth += 1 if text[j] == "{" else -1
        if depth == 0:
            return text[i + 1:j], j + 1
    return None, i


def citations(raw: str, suffix: str) -> int:
    """Count distinct cited works: the keys of LaTeX citation commands outside comments, and Pandoc keys outside
    LaTeX. A work cited twice counts once."""
    raw = uncommented(raw, suffix)
    keys = {k.strip() for m in CITE.finditer(raw) for k in m.group(1).split(",") if k.strip() not in ("", "*")}
    if suffix != ".tex":
        keys |= {k.lstrip("-@") for k in PANDOC_KEY.findall(raw) if not QUARTO_XREF.match(k.lstrip("-@"))}
    return len(keys)


def pointers(raw: str, suffix: str) -> int:
    """Count pointers to the paper's own sections, appendices, figures, and tables, outside comments and headings."""
    raw = uncommented(raw, suffix)
    if suffix == ".tex":
        raw = re.sub(r"\\(?:sub)*section\*?(?:\[[^\]]*\])?\{[^{}]*\}", " ", raw)
    else:
        raw = re.sub(r"(?m)^[ \t]{0,3}#{1,6}[ \t].*$", " ", raw)
    return len(POINTER.findall(raw))


def closing_list(raw: str, suffix: str) -> tuple[str, int, str] | None:
    """(text, item count, text after it) of the draft's last list when the text just before it names
    contributions, else None.

    LaTeX: the last itemize, enumerate, list, or description environment, with up to 400 characters before it as
    the lead-in. Markdown: the last run of paragraphs that open with a list marker, with the paragraph before it as
    the lead-in; a lead-in line directly above the first item counts as its own paragraph.
    """
    raw = uncommented(raw, suffix)
    envs = list(LIST_ENV.finditer(raw))
    if envs:
        m = envs[-1]
        close = "\\end{%s}" % m.group(1)
        end = raw.find(close, m.end())
        body = raw[m.end():end if end >= 0 else len(raw)]
        rest = raw[end + len(close):] if end >= 0 else ""
        lead, items = raw[max(0, m.start() - 400):m.start()], len(re.findall(r"\\item\b", body))
    else:
        paras: list[str] = []
        for p in re.split(r"\n[ \t]*\n", raw):
            lines = p.strip("\n").split("\n")
            k = next((i for i, line in enumerate(lines) if MD_ITEM.match(line)), None)
            paras += ["\n".join(lines)] if not k else ["\n".join(lines[:k]), "\n".join(lines[k:])]
        listed = [i for i, p in enumerate(paras) if MD_ITEM.match(p)]
        if not listed:
            return None
        # An indented paragraph belongs to the item above it, so it neither ends the list nor serves as a lead-in.
        inside = set(listed) | {i for i, p in enumerate(paras) if re.match(r"[ \t]{2,}\S", p)}
        first = last = listed[-1]
        while last + 1 in inside:
            last += 1
        while first - 1 in inside:
            first -= 1
        body = "\n\n".join(paras[first:last + 1])
        rest = "\n\n".join(paras[last + 1:])
        lead = paras[first - 1] if first > 0 else ""
        items = len([line for line in body.split("\n") if MD_ITEM.match(line)])
    return (body, items, rest) if re.search(r"\bcontributions?\b", lead, re.I) else None


def contribution_heads(raw: str, suffix: str) -> list[tuple[int, int, bool]]:
    """(item position, words, carries a pointer) for each bold head that opens an item of the closing
    contribution list. The position counts every item, so a later head never inherits the first item's place."""
    found_list = closing_list(raw, suffix)
    if found_list is None:
        return []
    body = found_list[0]
    starts = [m.start() for m in ITEM_START.finditer(body)]
    found: list[tuple[int, str, str]] = []
    # \item \textbf{Head}, \item[\textbf{Head}] (the head as the item label), or \item[1.] \textbf{Head}.
    for m in re.finditer(r"\\item\s*(?:\[\s*|\[[^\[\]{}]*\]\s*)?\\textbf\{", body):
        head, end = braced(body, m.end() - 1)
        if head is not None and m.start() in starts:
            found.append((starts.index(m.start()), head, body[end:end + 80]))
    # A bold head may wrap onto continuation lines, but never past a blank line or the next item.
    for m in re.finditer(r"(?m)^[ \t]*" + MARKER + r"[ \t]+(\*\*|__)"
                         r"((?:(?!\1|\n[ \t]*\n|\n[ \t]*" + MARKER + r"[ \t])[\s\S])+?)\1", body):
        if m.start() in starts:
            found.append((starts.index(m.start()), re.sub(r"\s+", " ", m.group(2)), body[m.end():m.end() + 80]))
    out = []
    for pos, head, after in sorted(found):
        # A pointer in parentheses right after the head, past any closing bracket or colon, belongs to the head; the
        # parentheses may hold a Markdown link, which brings one more pair of its own.
        trailing = re.match(r"[\s\].:;]*\(((?:[^()]|\([^()]*\))*)\)", after)
        has_ptr = bool(POINTER.search(head) or (trailing and POINTER.search(trailing.group(1))))
        label = re.sub(r"\([^()]*\)", lambda p: " " if POINTER.search(p.group(0)) else p.group(0), head)
        label = POINTER.sub(" ", label)
        label = plain(label, ".tex") if suffix == ".tex" else label
        out.append((pos, len([w for w in re.split(r"\s+", label) if re.search(r"[A-Za-z]", w)]), has_ptr))
    return out


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
        text = re.sub(r"(?m)^[ \t]*" + MARKER + r"[ \t]+", "\n\n", text)
        text = text.replace("**", "").replace("__", "").replace("`", "")
    return text


def sentences(par: str) -> list[str]:
    masked = ABBREV.sub(lambda m: m.group(0).replace(".", "\0"), par)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(\"'])", masked)
    return [p.replace("\0", ".").strip() for p in parts if len(p.split()) >= 3]


def contribution_list(raw: str, suffix: str = "") -> tuple[bool, str]:
    """Whether the text ends on a contribution list. A closing list with a contribution lead-in counts its items;
    otherwise the last "contribution(s)" must sit in the second half with at least two items after it, counted
    as list lines, paragraphs, or sentences that open with "We"."""
    found_list = closing_list(raw, suffix)
    if found_list is not None:
        _, items, rest = found_list
        after = len(plain(rest, suffix or ".md").split())
        if items < 2:
            return False, "no list"
        if after > AFTER_LIST_WORDS:
            return False, f"{after} words after it"
        return True, f"{items} items"
    hits = list(re.finditer(r"\bcontributions?\b", raw, re.I))
    if not hits or hits[-1].start() < len(raw) / 2:
        return False, "no" if not hits else "too early"
    tail = raw[hits[-1].end():]
    items = max(len(re.findall(r"(?m)^[ \t]*(?:[-*+]|\d+\.|\\item\b)", tail)),
                len([p for p in re.split(r"\n\s*\n", tail) if len(p.split()) >= 5]),
                len(re.findall(r"(?:^|[.:]\s+|\*\*\s*)We\s", tail)))
    return items >= 2, f"{items} items" if items >= 2 else "no list"


def measure(text: str, section: str, raw: str | None = None, suffix: str = "") -> list[tuple[str, str, str, bool]]:
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
    if section in ("abstract", "conclusion"):
        n = pointers(raw, suffix)
        row("pointers to sections, appendices, figures, or tables", str(n), "0", n == 0)
        c = citations(raw, suffix)
        row("cited works", str(c), "0 to 1", c <= 1)
    if section == "introduction":
        road = bool(ROADMAP.search(text))
        row("roadmap paragraph", "yes" if road else "no", "no", not road)
        ok, how = contribution_list(raw, suffix)
        row("ends on a contribution list", how, "yes", ok)
        heads = contribution_heads(raw, suffix)
        if heads:
            long = [n for pos, n, _ in heads if pos > 0 and n > HEAD_WORDS]
            row(f"contribution heads after the first over {HEAD_WORDS} words",
                ", ".join(f"{n} words" for n in long) or "none", "none", not long)
            ptr = sum(p for _, _, p in heads)
            row("section pointers in contribution heads", str(ptr), "0", ptr == 0)
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
    rows = measure(plain(raw, path.suffix.lower()), a.section, raw, path.suffix.lower())
    width = max(len(r[0]) for r in rows)
    for name, value, rng, ok in rows:
        print(f"{'ok   ' if ok else 'CHECK'}  {name:<{width}}  {value:>10}   author: {rng}")
    off = sum(not r[3] for r in rows)
    print(f"\n{off} of {len(rows)} measures outside the author's range.")


if __name__ == "__main__":
    main()
    sys.exit(0)
