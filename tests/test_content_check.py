"""Regression tests for skills/polish/scripts/content_check.py (stdlib unittest, Python 3.9+)."""
import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "polish" / "scripts" / "content_check.py"
spec = importlib.util.spec_from_file_location("content_check", SCRIPT)
cc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cc)

ABSTRACT = (
    "Our detector cuts the error by 0.052 on average~\\cite{smith2020,lee2021}, and the control errs "
    "1.73 times as much on 2,048-shot runs. Eight predictions were locked before the data "
    "(Sect.~\\ref{sec:results}). Contact a@b.edu for the data.\n"
)
BODY = "The error falls by 0.052 [0.010, 0.094], and the control errs 1.73 times as much.\n"


def tokens(text, kind, suffix=".tex"):
    """Extract one kind of token from text, through the same comment stripping as a file."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / ("x" + suffix)
        path.write_text(text)
        return dict(cc.extract(path)[kind])


class Extraction(unittest.TestCase):
    def test_number_forms(self):
        found = tokens("Rates of .5 and 0.25, gaps of 3e-4 and 2.1E+3, 2,048 shots, $-0.5$, \u22120.3.", "numbers")
        self.assertEqual(found, {"0.5": 1, "0.25": 1, "3e-4": 1, "2.1e+3": 1, "2048": 1, "-0.5": 1, "-0.3": 1})

    def test_currency_scales_are_counted(self):
        self.assertEqual(tokens("A $1.5M award, a \\$50k pilot, a 7B-parameter model, 2M shots, 8K runs, "
                                "a 3D model, 2min.", "numbers"),
                         {"1.5m": 1, "50k": 1, "7b": 1, "2m": 1, "8k": 1, "2": 1})
        self.assertEqual(tokens("Latency fell from 2ms to 9 ms on 4GB and 4 GB of 3 GPUs, a 3D model.", "numbers"),
                         {"2": 1, "9": 1, "4": 2, "3": 1})
        self.assertEqual(tokens("It costs $50 and $50,000.", "numbers", ".md"), {"50": 1, "50000": 1})

    def test_percent_is_part_of_the_number(self):
        found = tokens("It fell 5 percent, then 5\\%, then 5~percent; five percent of runs; 5 points.", "numbers")
        self.assertEqual(found, {"5%": 4, "5": 1})

    def test_number_words_and_compounds(self):
        # "one" is left out on purpose: it is too common in prose to count without noise.
        found = tokens("Twenty-two seeds, eight predictions, twice as many, zero failures, one run, a "
                       "half-life, a two-sample test, ten-fold cross-validation.", "numbers")
        self.assertEqual(found, {"22": 1, "8": 1, "2": 1, "0": 1})

    def test_a_multiplier_is_part_of_the_number(self):
        found = tokens("It errs $1.7\\times$ as much, then 1.9x, then 2.0 × the raw estimate, then "
                       "2.5~\\times; 3x3 grids.", "numbers")
        self.assertEqual(found, {"1.7x": 1, "1.9x": 1, "2.0x": 1, "2.5x": 1, "3": 2})
        self.assertEqual(tokens("a 3x3 kernel and a 5x5 kernel", "numbers"), {"3": 2, "5": 2})
        self.assertEqual(tokens("a 3\u00d73 kernel", "numbers"), {"3": 2})

    def test_prices_in_markdown_are_not_math(self):
        self.assertEqual(tokens("It costs $50 and $75 per run.", "math", ".md"), {})
        self.assertEqual(tokens("The budget is $50,000 and the grant is $75,000.", "math", ".md"), {})
        text = "Budget is $50,000 per year; set `$HOME` first.\n\nWe optimize $x + y = 1$ over $n$ runs."
        self.assertEqual(tokens(text, "math", ".md"), {"x+y=1": 1, "n": 1})
        self.assertEqual(tokens("We fix $5$ seeds and $2x+1$ terms.", "math", ".md"), {"2x+1": 1})
        self.assertEqual(tokens("We use $2 + x$ and then $y$.", "math", ".md"), {"2+x": 1, "y": 1})

    def test_a_long_markdown_link_does_not_stall(self):
        import time
        start = time.time()
        tokens("See [x](" + "a" * 5000 + " b c)\n", "links", ".md")
        self.assertLess(time.time() - start, 1.0)

    def test_ranges_and_signs(self):
        found = tokens("Years 2020--2024, seeds 10-15, a drop of -0.5 and ($-3$).", "numbers")
        self.assertEqual(found, {"2020": 1, "2024": 1, "10": 1, "15": 1, "-0.5": 1, "-3": 1})

    def test_not_numbers(self):
        found = tokens("A 3D model, version 1.2.3, rung R0, $L_1$, $L_{1}$, \\vspace{2pt}, Fig.~3.", "numbers")
        self.assertEqual(found, {"3": 1})

    def test_subscripts_digit_separators_and_thin_spaces(self):
        self.assertEqual(tokens("The L_1 penalty beats L_{2}.", "math"), {"L_1": 1, "L_{2}": 1})
        self.assertEqual(tokens("The L_1 penalty beats L_{2}.", "numbers"), {})
        self.assertEqual(tokens("We ran 10_000 steps.", "numbers", ".md"), {"10000": 1})
        self.assertEqual(tokens("We ran 3\\,000 steps.", "numbers"), {"3000": 1})

    def test_a_citation_page_is_a_number(self):
        self.assertEqual(tokens("As \\citep[p.~12]{smith2020} shows.", "numbers"), {"12": 1})
        self.assertEqual(tokens("As \\citep[p.~12]{smith2020} shows.", "citations"), {"smith2020": 1})

    def test_citations_labels_and_references_are_separate(self):
        text = ("See \\citep[see][p.~3]{a,b} and \\citet{c}. \\label{sec:x} Sect.~\\ref{sec:x}, "
                "\\cref{fig:a,fig:b}. Mail a@b.edu, or [@doe99]. \\Citet{d} and \\Citeauthor{e} open sentences.")
        self.assertEqual(tokens(text, "citations"), {"a": 1, "b": 1, "c": 1, "doe99": 1, "d": 1, "e": 1})
        self.assertEqual(tokens(text, "labels"), {"sec:x": 1})
        self.assertEqual(tokens(text, "cross-references"), {"sec:x": 1, "fig:a": 1, "fig:b": 1})
        self.assertEqual(tokens("\\Autoref{s:a} and \\subref{f:b}.", "cross-references"), {"s:a": 1, "f:b": 1})

    def test_a_link_with_parentheses_stays_whole(self):
        found = tokens("See [the entry](https://en.wikipedia.org/wiki/Bias_(statistics)).", "links", ".md")
        self.assertEqual(found, {"https://en.wikipedia.org/wiki/Bias_(statistics)": 1})
        found = tokens("Bare https://en.wikipedia.org/wiki/Bias_(statistics) and (see https://x.org/a).", "links")
        self.assertEqual(found, {"https://en.wikipedia.org/wiki/Bias_(statistics)": 1, "https://x.org/a": 1})

    def test_links_include_relative_and_latex_forms(self):
        text = ("Read [the guide](docs/guide.md) and [site](https://x.org/a). See https://y.org/b and "
                "[the notes][ref].\n\n[ref]: ../notes.md\n")
        self.assertEqual(tokens(text, "links", ".md"),
                         {"docs/guide.md": 1, "https://x.org/a": 1, "https://y.org/b": 1, "../notes.md": 1})
        self.assertEqual(tokens("\\url{https://a.org} \\href{https://b.org}{B}", "links"),
                         {"https://a.org": 1, "https://b.org": 1})

    def test_reference_links_count_their_uses_not_their_definitions(self):
        defs = "\n\n[p]: https://x.org/protocol\n"
        self.assertEqual(tokens("Follow [the protocol][p], then [p] again." + defs, "links", ".md"),
                         {"https://x.org/protocol": 2})
        self.assertEqual(tokens("Follow the protocol." + defs, "links", ".md"), {})
        self.assertEqual(tokens("See \\citep[see][p.~3]{a}.", "links"), {})

    def test_plain_text_prices_are_not_math(self):
        for suffix in (".txt", ".rst"):
            self.assertEqual(tokens("The budget is $500 in Q1 and $750 in Q2.", "math", suffix), {})

    def test_angle_destinations_and_explicit_periods(self):
        text = "See [the supplement](<supplementary material.pdf>) and [v1](https://x.org/v1.)."
        self.assertEqual(tokens(text, "links", ".md"),
                         {"supplementary material.pdf": 1, "https://x.org/v1.": 1})
        self.assertEqual(tokens("See the supplement.", "links", ".md"), {})

    def test_link_examples_in_code_are_not_links(self):
        text = ("Write `[guide](https://x.org/guide)` for a link.\n\n```\n[guide](https://x.org/guide)\n```\n\n"
                "Read [the guide](https://x.org/guide).")
        self.assertEqual(tokens(text, "links", ".md"), {"https://x.org/guide": 1})

    def test_reference_definitions_with_angle_destinations(self):
        defs = "\n\n[r]: <supporting files.pdf>\n"
        self.assertEqual(tokens("See [the files][r]." + defs, "links", ".md"), {"supporting files.pdf": 1})
        self.assertEqual(tokens("See the files." + defs, "links", ".md"), {})

    def test_double_backtick_spans_and_prices_before_math(self):
        text = "Use ``foo`` for [the guide](https://x.org/guide) and ``bar`` here."
        self.assertEqual(tokens(text, "links", ".md"), {"https://x.org/guide": 1})
        self.assertEqual(tokens("At $10 per 1M tokens ($p = 0.05$), error drops.", "math", ".md"), {"p=0.05": 1})

    def test_tilde_fences_hold_examples(self):
        text = "~~~~\n[x](guide.md)\n~~~\n~~~~\n\nRead [the guide](guide.md)."
        self.assertEqual(tokens(text, "links", ".md"), {"guide.md": 1})
        text = "```\n\\url{https://x.org/example}\n```\n\nSee \\url{https://x.org/real}."
        self.assertEqual(tokens(text, "links", ".md"), {"https://x.org/real": 1})

    def test_unclosed_fences_and_wrapped_spans_hold_examples(self):
        text = "Read [g](guide.md).\n\n```\n[x](example.md)\n"
        self.assertEqual(tokens(text, "links", ".md"), {"guide.md": 1})
        text = "Set `long_flag\n--val` and read [g](guide.md), then run `make`."
        self.assertEqual(tokens(text, "links", ".md"), {"guide.md": 1})

    def test_commands_in_markdown_code_are_examples(self):
        text = ("```\n\\cite{smith2020} \\label{sec:b} \\ref{sec:a}\n```\n\n~~~~\n@smith2020\n~~~~\n\n"
                "See `\\cite{smith2020}` and \\cite{lee2021} in \\ref{sec:c}.\n")
        self.assertEqual(tokens(text, "citations", ".md"), {"lee2021": 1})
        self.assertEqual(tokens(text, "labels", ".md"), {})
        self.assertEqual(tokens(text, "cross-references", ".md"), {"sec:c": 1})

    def test_hyperref_is_a_cross_reference(self):
        text = "See \\hyperref[sec:results]{Section 3}."
        self.assertEqual(tokens(text, "cross-references"), {"sec:results": 1})
        self.assertEqual(tokens(text, "numbers"), {"3": 1})

    def test_reference_shortcuts_and_definitions(self):
        text = "See [2].\n\n[2]: https://x.org/r\n"
        self.assertEqual(tokens(text, "numbers", ".md"), {})
        self.assertEqual(tokens(text, "links", ".md"), {"https://x.org/r": 1})
        text = "See [Section 3].\n\n[Section 3]: https://x.org/s\n"
        self.assertEqual(tokens(text, "numbers", ".md"), {"3": 1})
        text = "See [files][r].\n\n[r]: <supporting files.pdf>  \n"
        self.assertEqual(tokens(text, "links", ".md"), {"supporting files.pdf": 1})

    def test_markdown_code_and_comments_in_source_order(self):
        text = "Use `<!--` to open a comment. We ran 12 trials, see [g](guide.md).\n<!-- real 99 -->\n"
        self.assertEqual(tokens(text, "numbers", ".md"), {"12": 1})
        self.assertEqual(tokens(text, "links", ".md"), {"guide.md": 1})
        import time
        start = time.time()
        tokens("<!-- open\n" * 4000, "numbers", ".md")
        self.assertLess(time.time() - start, 1.0)

    def test_markdown_code_is_an_example_for_every_scanner(self):
        text = ("```\n\\begin{equation} E = mc^2 \\end{equation}\n\\[E = mc^2\\]\n\\(E = mc^2\\)\n$E = mc^2$\n30\n```\n\n"
                "Real: \\[E = mc^2\\] and 30 runs.\n")
        self.assertEqual(tokens(text, "math", ".md"), {"E=mc^2": 1})
        self.assertEqual(tokens(text, "numbers", ".md"), {"2": 1, "30": 1})

    def test_a_row_break_with_spacing_is_not_display_math(self):
        text = "Method A & 91.2 \\\\[2pt]\nMethod B & 90.1 \\\\[0.5ex]\nThen \\[ x = 1 \\] holds.\n"
        self.assertEqual(tokens(text, "math"), {"x=1": 1})

    def test_unmatched_math_openers_scan_once(self):
        import time
        for suffix in (".md", ".tex"):
            start = time.time()
            tokens("Index \\[a and \\(b " * 4000, "math", suffix)
            self.assertLess(time.time() - start, 1.0)
        self.assertEqual(tokens("Escaped \\[ here, then \\[ x = 1 \\] holds.", "math"), {"x=1": 1})

    def test_alignat_flalign_and_footnotes(self):
        text = "\\begin{alignat}{2} a &= b \\end{alignat} \\begin{flalign} c &= d \\end{flalign}"
        self.assertEqual(tokens(text, "math"), {"a&=b": 1, "c&=d": 1})
        self.assertEqual(tokens(text, "numbers"), {})
        text = "See note[^1] and 1 trial.\n\n[^1]: Note\n"
        self.assertEqual(tokens(text, "numbers", ".md"), {"1": 1})
        self.assertEqual(tokens(text, "links", ".md"), {})

    def test_emphasis_and_thin_spaces_in_math(self):
        self.assertEqual(tokens("We ran _5_ trials.", "numbers", ".md"), {"5": 1})
        self.assertEqual(tokens("We ran _8_ trials.", "numbers", ".md"), {"8": 1})
        text = "A budget of $3\\,000$ runs."
        self.assertEqual(tokens(text, "math"), {})
        self.assertEqual(tokens(text, "numbers"), {"3000": 1})

    def test_bracket_leading_lines_scan_once(self):
        import time
        start = time.time()
        tokens("[unclosed line\n" * 4000, "links", ".md")
        self.assertLess(time.time() - start, 1.0)

    def test_link_syntax_does_not_leak_into_other_counts(self):
        # The caption of an inline link is not a shortcut use of an unused definition.
        text = "Read [p](https://x.org/a).\n\n[p]: https://x.org/unused\n"
        self.assertEqual(tokens(text, "links", ".md"), {"https://x.org/a": 1})
        # A numeric reference label is not a number in the prose.
        text = "See [the results][2] for 2 runs.\n\n[2]: https://x.org/r\n"
        self.assertEqual(tokens(text, "numbers", ".md"), {"2": 1})

    def test_display_math_is_not_split_into_inline_pieces(self):
        text = ("$$ a + b $$ and $x$ then \\[ c = d \\] and \\begin{equation} e = f \\end{equation} "
                "and $y$ and \\(z\\).")
        self.assertEqual(tokens(text, "math"), {"a+b": 1, "x": 1, "c=d": 1, "e=f": 1, "y": 1, "z": 1})

    def test_numeric_math_and_currency_are_numbers(self):
        text = "Budget \\$50,000 in Year 1 and \\$75,000 in Year 2; accuracy $58.3\\%$, speed $1.7\\times$."
        self.assertEqual(tokens(text, "math"), {})
        found = tokens(text, "numbers")
        self.assertEqual(found, {"50000": 1, "1": 1, "75000": 1, "2": 1, "58.3%": 1, "1.7x": 1})
        self.assertEqual(tokens("A shift of $+3.1\\%$.", "math"), {})
        self.assertEqual(tokens("A shift of $+3.1\\%$ from $3.1\\%$.", "numbers"), {"+3.1%": 1, "3.1%": 1})

    def test_a_percent_inside_a_url_is_not_a_comment(self):
        text = "See \\url{https://e.org/a%20b} for 7 runs."
        self.assertEqual(tokens(text, "links", ".TEX"), {"https://e.org/a%20b": 1})
        self.assertEqual(tokens(text, "numbers", ".TEX"), {"7": 1})

    def test_comments_are_not_content(self):
        self.assertEqual(tokens("Kept 7. % dropped 9\\% and \\cite{draft}\nEscaped \\% sign 8.", "numbers"),
                         {"7": 1, "8": 1})
        self.assertEqual(tokens("Kept 7. <!-- dropped 9 -->", "numbers", ".md"), {"7": 1})


class Compare(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        (self.repo / "paper").mkdir(parents=True)
        self.target = self.repo / "paper" / "abstract.tex"
        self.target.write_text(ABSTRACT)
        (self.repo / "paper" / "results.tex").write_text(BODY)
        self.base = Path(self.tmp.name) / "base"
        self.cli("snapshot", "--repo", str(self.repo), "--out", str(self.base), str(self.target))

    def tearDown(self):
        self.tmp.cleanup()

    def cli(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            cc.main(list(argv))
        return out.getvalue()

    def compare(self, text, *extra):
        self.target.write_text(text)
        return self.cli("compare", "--repo", str(self.repo), "--baseline", str(self.base), *extra, str(self.target))

    def test_unchanged_and_reordered_text_report_nothing(self):
        self.assertIn("0 count change(s) in 0 file(s)", self.compare(ABSTRACT))
        first, second, third = ABSTRACT.strip().split(". ")
        report = self.compare(". ".join([second, third.rstrip("."), first]) + ".\n")
        self.assertIn("0 count change(s) in 0 file(s)", report)

    def test_every_change_is_listed_with_a_lead(self):
        report = self.compare(ABSTRACT.replace("by 0.052 on average", "on average")
                              .replace("1.73 times", "about twice"))
        self.assertIn("0.052 1 -> 0 (also in paper/results.tex)", report)
        self.assertIn("1.73 1 -> 0 (also in paper/results.tex)", report)
        self.assertIn("2 0 -> 1", report)
        self.assertIn("3 count change(s) in 1 file(s)", report)

    def test_a_gained_token_is_listed_with_a_lead(self):
        report = self.compare(ABSTRACT.replace("by 0.052 on average", "by 0.052 [0.010, 0.094] on average"))
        self.assertIn("0.094 0 -> 1 (also in paper/results.tex)", report)

    def test_a_lost_token_found_nowhere_else_has_no_lead(self):
        report = self.compare(ABSTRACT.replace("on 2,048-shot runs", "on long runs"))
        self.assertIn("2048 1 -> 0 (in no searched file)", report)
        self.assertNotIn("2048 1 -> 0 (also", report)

    def test_a_partial_drop_is_not_marked_gone(self):
        self.target.write_text(ABSTRACT + "\nThe runs used 2,048 shots.\n")
        base = Path(self.tmp.name) / "base-partial"
        self.cli("snapshot", "--repo", str(self.repo), "--out", str(base), str(self.target))
        self.target.write_text(ABSTRACT + "\nThe runs were long.\n")
        report = self.cli("compare", "--repo", str(self.repo), "--baseline", str(base), str(self.target))
        self.assertIn("2048 2 -> 1", report)
        self.assertNotIn("in no searched file", report)

    def test_snapshot_of_a_missing_target_stops_with_a_message(self):
        missing = self.repo / "paper" / "new-section.tex"
        with self.assertRaises(SystemExit) as stop:
            self.cli("snapshot", "--repo", str(self.repo), "--out", str(Path(self.tmp.name) / "base-new"), str(missing))
        self.assertIn("create it empty first", str(stop.exception))

    def test_a_token_still_in_the_target_is_not_marked_gone(self):
        report = self.compare(ABSTRACT.replace("on 2,048-shot runs", "on 2,048-shot runs (2,048 shots)"))
        self.assertIn("2048 1 -> 2", report)
        self.assertNotIn("in no searched file", report)

    def test_new_numbers_and_citations_are_listed(self):
        report = self.compare(ABSTRACT.replace("Eight predictions", "Nine predictions")
                              .replace("lee2021}", "lee2021,new2024}"))
        self.assertIn("8 1 -> 0", report)
        self.assertIn("9 0 -> 1", report)
        self.assertIn("new2024 0 -> 1", report)

    def test_dropped_cross_reference_and_citation(self):
        report = self.compare(ABSTRACT.replace("(Sect.~\\ref{sec:results})", "")
                              .replace("\\cite{smith2020,lee2021}", "\\citep[see][p.~3]{smith2020}"))
        self.assertIn("cross-references: sec:results 1 -> 0", report)
        self.assertIn("citations: lee2021 1 -> 0", report)

    def test_swapped_values_keep_their_counts(self):
        # A count check cannot see two values traded between claims; step 4's reading covers it.
        text = "Method A errs 0.21 and method B errs 0.35.\n"
        self.target.write_text(text)
        base = Path(self.tmp.name) / "base2"
        self.cli("snapshot", "--repo", str(self.repo), "--out", str(base), str(self.target))
        self.target.write_text("Method A errs 0.35 and method B errs 0.21.\n")
        report = self.cli("compare", "--repo", str(self.repo), "--baseline", str(base), str(self.target))
        self.assertIn("0 count change(s)", report)

    def test_leads_reach_the_main_file_and_tables_of_a_sectioned_paper(self):
        sections = self.repo / "paper" / "sections"
        (self.repo / "paper" / "tables").mkdir()
        sections.mkdir()
        (self.repo / "paper" / "tables" / "main.tex").write_text("0.052 & 1.73 \\\\\n")
        target = sections / "abstract.tex"
        target.write_text("We cut error by 0.052.\n")
        base = Path(self.tmp.name) / "base3"
        self.cli("snapshot", "--repo", str(self.repo), "--out", str(base), str(target))
        target.write_text("We cut error.\n")
        report = self.cli("compare", "--repo", str(self.repo), "--baseline", str(base), str(target))
        self.assertIn("paper/tables/main.tex", report)

    def test_also_replaces_the_default_neighbours(self):
        other = Path(self.tmp.name) / "elsewhere.md"
        other.write_text("Nothing here.\n")
        report = self.compare(ABSTRACT.replace("by 0.052 on average", "on average"), "--also", str(other))
        self.assertIn("0.052 1 -> 0 (in no searched file)", report)

    def test_a_lead_outside_the_repository_is_named_without_stopping(self):
        other = Path(self.tmp.name) / "elsewhere.md"
        other.write_text("The error falls by 0.052.\n")
        report = self.compare(ABSTRACT.replace("by 0.052 on average", "on average"), "--also", str(other))
        self.assertIn("(also in " + str(other) + ")", report)
        self.assertIn("Summary:", report)

    def test_a_bare_filename_still_reaches_the_directory_above(self):
        import os
        sections = self.repo / "paper" / "sections"
        sections.mkdir()
        (sections / "abstract.tex").write_text("x\n")
        cwd = os.getcwd()
        try:
            os.chdir(sections)
            rest = cc.default_rest([Path("abstract.tex")], Path("../.."))
        finally:
            os.chdir(cwd)
        self.assertIn((self.repo / "paper" / "results.tex").resolve(), [p.resolve() for p in rest])

    def test_snapshot_refuses_to_overwrite_a_baseline(self):
        with self.assertRaises(SystemExit) as caught:
            self.cli("snapshot", "--repo", str(self.repo), "--out", str(self.base), str(self.target))
        self.assertIn("already holds a baseline", str(caught.exception))

    def test_compare_without_a_baseline_stops(self):
        with self.assertRaises(SystemExit) as caught:
            self.cli("compare", "--repo", str(self.repo), "--baseline", str(Path(self.tmp.name) / "none"),
                     str(self.target))
        self.assertIn("run snapshot before the pass", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
