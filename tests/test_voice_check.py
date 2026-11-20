"""Regression tests for skills/author-voice/scripts/voice_check.py (stdlib unittest, Python 3.9+)."""
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "author-voice" / "scripts" / "voice_check.py"
spec = importlib.util.spec_from_file_location("voice_check", SCRIPT)
vc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vc)

LONG = ("Our method selects a detector and its hyperparameters for a new dataset without any labels by reusing the "
        "performance of many models on historical benchmark datasets and by matching tasks through meta-features.")
MEDIUM = "The selection runs in under a second at test time on every dataset we tried."


def rows(text, section, suffix=".md"):
    return {name: (value, ok) for name, value, _, ok in vc.measure(vc.plain(text, suffix), section, text, suffix)}


class ShortParagraphsCount(unittest.TestCase):
    def test_short_standalone_sentences_stay_in_the_counts(self):
        text = "\n\n".join([" ".join([LONG] * 3), " ".join([MEDIUM] * 2),
                            "Consider iForest as an example.", "It has few knobs.", "Labels are scarce here."])
        value, ok = rows(text, "other")["sentences over 30 words"]
        self.assertEqual(value, "38%")
        self.assertTrue(ok)


class MarkdownLists(unittest.TestCase):
    INTRO = ("Outlier detection lacks labels, so model selection cannot use evaluation. " * 12 + "\n\n"
             "In summary, the key contributions of this work include:\n\n"
             "- **First approach.** We propose a method. Notably, it needs no labels.\n"
             "- **Meta-features.** We design features that capture outlying characteristics.\n"
             "- **Effectiveness.** We show gains on two testbeds. Moreover, selection is fast.\n")

    def test_list_items_stay_separate_paragraphs(self):
        value, ok = rows(self.INTRO, "introduction")['paragraphs opening two sentences with "Moreover", "Notably", or kin']
        self.assertEqual(value, "none")
        self.assertTrue(ok)

    def test_contribution_list_is_found_at_the_end(self):
        value, ok = rows(self.INTRO, "introduction")["ends on a contribution list"]
        self.assertTrue(ok, value)

    def test_an_early_keyword_is_not_a_list(self):
        text = "Our contributions build on earlier work. " + "We study selection without labels in detail. " * 20
        self.assertFalse(rows(text, "introduction")["ends on a contribution list"][1])


class LatexInput(unittest.TestCase):
    def test_math_mode_numbers_are_counted(self):
        text = ("\\begin{abstract}\nGiven a new dataset, how can we select a model without labels? "
                "Our method improves over the defaults by $58\\%$ and $66\\%$ on $39$ datasets.\n\\end{abstract}\n")
        value, ok = rows(text, "abstract", ".tex")["numeric figures"]
        self.assertEqual(value, "3")
        self.assertFalse(ok)

    def test_section_heading_does_not_hide_an_opener(self):
        text = "\\section{Introduction}\nAdditionally, we study model selection without labels in this paper.\n"
        value, ok = rows(text, "introduction", ".tex")["openers the author does not use"]
        self.assertEqual(value, "Additionally")
        self.assertFalse(ok)


class SectionFigures(unittest.TestCase):
    def test_two_figures_in_an_abstract_pass_and_three_do_not(self):
        two = "Extensive experiments on more than 20 datasets show that it selects from 300+ models."
        self.assertTrue(rows(two, "abstract")["numeric figures"][1])
        three = "It improves accuracy by 10% and cuts training time by 30% on 20 datasets."
        self.assertFalse(rows(three, "abstract")["numeric figures"][1])

    def test_a_conclusion_allows_one_figure(self):
        self.assertTrue(rows("Experiments on more than 20 datasets show its potential.", "conclusion")["numeric figures"][1])
        self.assertFalse(rows("It is 14% better on 8 datasets.", "conclusion")["numeric figures"][1])


class Pointers(unittest.TestCase):
    KEY = "pointers to sections, appendices, figures, or tables"

    CASES = [
        ("We show gains (Section~\\ref{sec:exp}).", ".tex", 1),
        ("Bounds hold, see \\S\\ref{sec:theory}.", ".tex", 1),
        ("Proofs are deferred (\\cref{app:proofs}).", ".tex", 1),
        ("Appendix~B holds proofs.", ".tex", 1),
        ("Table 2 lists datasets.", ".tex", 1),
        ("The loss in Eq.~\\ref{eq:loss} is convex.", ".tex", 0),
        ("It holds as \\ref{thm:main} states.", ".tex", 0),
        ("We prove it. % see Section 5", ".tex", 0),
        ("Selection beats 58% of fixed choices, as section 4 shows.", ".md", 1),
        ("Appendix IV lists the prompts.", ".md", 1),
        ("The prompts are in [the appendix](#appendix).", ".md", 1),
        ("The bound follows [Section 2](#sec-2).", ".md", 1),
        ("It uses the loss in [Eq. 3](#eq-3).", ".md", 0),
        ("Results hold (\\cref{sec_exp}).", ".tex", 1),
        ("Results hold (\\ref {sec:results}).", ".tex", 1),
        ("We show gains (Section~\\ref {sec:exp}).", ".tex", 1),
        ("Details appear in \\Vref{sec:exp} and \\autoref{fig:main}.", ".tex", 2),
        ("The loss in \\ref {eq:loss} is convex.", ".tex", 0),
        ("We focus on [the application](#application).", ".md", 0),
        ("The trend in @fig-trend is flat, as @sec-results shows.", ".md", 2),
        ("The trend in @Fig-trend is flat.", ".md", 1),
        ("Data are listed in \\ref{table:data}.", ".tex", 1),
        ("See [the project page](https://example.org/a#b).", ".md", 0),
        ("Selection runs in 1 second on 300 models.", ".md", 0),
        ("Secs. 3 and 4 hold the proofs.", ".md", 1),
        ("The trend in Fig 2 is flat.", ".md", 1),
        ("The trend in Fig.2 is flat, as Sec 3 shows.", ".md", 2),
        ("See [the figure](fig1.png) and the table2 file.", ".md", 0),
        ("The gap is 0.4 \\SE{} 0.1 over runs.", ".tex", 0),
        ("We prove it. \\\\% see Section 5", ".tex", 0),
        ("\\section{Section 6: Conclusion}\nWe close the gap.", ".tex", 0),
        ("## Section 6: Conclusion\n\nWe close the gap.", ".md", 0),
    ]

    def test_the_command_line_passes_the_file_suffix(self):
        import contextlib
        import io
        import sys
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "abstract.tex"
            path.write_text("We show gains (Section~\\ref{sec:exp}). % Section 5\n", encoding="utf-8")
            out = io.StringIO()
            with mock.patch.object(sys, "argv", ["voice_check.py", str(path), "--section", "abstract"]), \
                    contextlib.redirect_stdout(out):
                vc.main()
        line = next(x for x in out.getvalue().splitlines() if self.KEY in x)
        self.assertTrue(line.startswith("CHECK"))
        self.assertIn(" 1 ", line)

    def test_each_case_counts_on_its_own(self):
        for text, suffix, want in self.CASES:
            with self.subTest(text=text):
                self.assertEqual(rows(text, "conclusion", suffix)[self.KEY], (str(want), want == 0))

    def test_plain_claims_and_citations_pass(self):
        text = "Extensive experiments show that it outperforms prior selectors \\citep{zhao2021}.\n"
        self.assertEqual(rows(text, "abstract", ".tex")[self.KEY], ("0", True))

    def test_other_sections_skip_the_measure(self):
        self.assertNotIn(self.KEY, rows("As Section 3 shows, it works.", "other"))


class Citations(unittest.TestCase):
    KEY = "cited works"

    def test_each_latex_key_counts_and_comments_do_not(self):
        text = "It beats selectors \\citep{zhao2021,park2022} and LOF \\citet[p.~3]{breunig2000}. % \\cite{x}\n"
        self.assertEqual(rows(text, "abstract", ".tex")[self.KEY], ("3", False))

    def test_one_citation_passes_and_pandoc_keys_count(self):
        self.assertEqual(rows("It extends MetaOD \\cite{zhao2021}.\n", "conclusion", ".tex")[self.KEY], ("1", True))
        self.assertEqual(rows("It extends MetaOD [@zhao2021; @park2022].", "conclusion")[self.KEY], ("2", False))

    def test_an_email_address_is_not_a_citation(self):
        self.assertEqual(rows("Write to lab@example.org for the data.", "abstract")[self.KEY], ("0", True))
        self.assertEqual(rows("Data come on request [contact lab@example.org].", "abstract")[self.KEY], ("0", True))

    def test_narrative_pandoc_keys_count(self):
        self.assertEqual(rows("@smith2020 and @2021_lee show the gap.", "abstract")[self.KEY], ("2", False))
        self.assertEqual(rows("As @smith2020 shows [see also @lee2021].", "abstract")[self.KEY], ("2", False))

    def test_spaces_before_keys_count_and_citetext_does_not(self):
        self.assertEqual(rows("\\citep {zhao2021}.\n", "abstract", ".tex")[self.KEY], ("1", True))
        self.assertEqual(rows("\\citep[see] {zhao2021, park2022}.\n", "abstract", ".tex")[self.KEY], ("2", False))
        self.assertEqual(rows("\\citetext{see Jones, 1990}.\n", "abstract", ".tex")[self.KEY], ("0", True))

    def test_other_sections_skip_cited_works(self):
        self.assertNotIn(self.KEY, rows("\\citep{a} and \\citep{b}.\n", "introduction", ".tex"))
        self.assertNotIn(self.KEY, rows("See @zhao2021 and @park2022.", "other"))

    def test_quarto_cross_references_are_not_citations(self):
        self.assertEqual(rows("See @fig-trend and @eq-loss, after @smith2020.", "abstract")[self.KEY], ("1", True))
        self.assertEqual(rows("See @Fig-trend.", "abstract")[self.KEY], ("0", True))

    def test_one_work_cited_twice_counts_once(self):
        text = "It builds on MetaOD \\cite{zhao2021} and beats it \\citep{zhao2021}.\n"
        self.assertEqual(rows(text, "abstract", ".tex")[self.KEY], ("1", True))

    def test_capitalized_commands_count_and_nocite_does_not(self):
        text = "\\Citet{zhao2021} extends it. \\nocite{*}\\nocite{extra}\n"
        self.assertEqual(rows(text, "conclusion", ".tex")[self.KEY], ("1", True))


class ContributionHeads(unittest.TestCase):
    LEAD = "Outlier detection lacks labels, so model selection cannot use evaluation. " * 12 + "\n\n"
    LONG = "contribution heads after the first over 4 words"
    PTR = "section pointers in contribution heads"

    def test_the_author_heads_pass_with_a_long_first_head(self):
        text = self.LEAD + ("In summary, the key contributions of this work include the following:\n\n"
                            "- **First Approach to Unsupervised Outlier Model Selection**: We propose MetaOD.\n"
                            "- **Problem Formulation:** We connect UOMS to cold-start collaborative filtering.\n"
                            "- **Effectiveness and Efficiency**: We show that selection beats a fixed model.\n")
        r = rows(text, "introduction")
        self.assertEqual(r[self.LONG], ("none", True))
        self.assertEqual(r[self.PTR], ("0", True))

    def test_a_finding_in_a_head_and_a_pointer_are_flagged(self):
        text = self.LEAD + (
            "In summary, the key contributions of this work include:\n"
            "\\begin{itemize}\n"
            "\\item \\textbf{Problem Formulation (Section~\\ref{sec:framework}):} We formalize the risk.\n"
            "\\item \\textbf{Harm in a Standard Benchmark and an Interface Fix}: We add a second customer.\n"
            "\\end{itemize}\n")
        r = rows(text, "introduction", ".tex")
        self.assertEqual(r[self.LONG], ("9 words", False))
        self.assertEqual(r[self.PTR], ("1", False))

    def test_the_word_contribution_inside_an_item_keeps_the_list(self):
        text = self.LEAD + ("In summary, the key contributions of this work include:\n\n"
                            "- **First Approach to Model Selection**: We propose MetaOD.\n"
                            "- **Five Words in This Head**: We isolate the contribution of each term.\n")
        r = rows(text, "introduction")
        self.assertEqual(r["ends on a contribution list"], ("2 items", True))
        self.assertEqual(r[self.LONG], ("5 words", False))

    def test_underscore_bold_and_an_optional_item_label_are_read(self):
        md = self.LEAD + ("Our contributions are:\n\n- __First Approach__: We propose it.\n"
                          "- __Five Words in This Head__: We test it.\n")
        self.assertEqual(rows(md, "introduction")[self.LONG], ("5 words", False))
        tex = self.LEAD + ("Our contributions are:\n\\begin{itemize}\n\\item[\\textbf{First}] We propose it.\n"
                           "\\item[\\textbf{Data \\emph{Quality}}] (Section 3) We test it.\n\\end{itemize}\n")
        r = rows(tex, "introduction", ".tex")
        self.assertEqual(r[self.LONG], ("none", True))
        self.assertEqual(r[self.PTR], ("1", False))

    def test_four_words_pass_and_a_parenthetical_counts_unless_it_points(self):
        text = self.LEAD + ("Our contributions are:\n\n- **First**: We propose it.\n"
                            "- **Four Words in Head**: We test it.\n"
                            "- **New Method (Long Parenthetical Inside Head)**: We explain it.\n"
                            "- **Problem Formulation**: (Section 2) We formalize it.\n")
        r = rows(text, "introduction")
        self.assertEqual(r[self.LONG], ("6 words", False))
        self.assertEqual(r[self.PTR], ("1", False))

    def test_a_numbered_item_label_before_the_bold_head(self):
        text = self.LEAD + ("Our contributions are:\n\\begin{enumerate}\n\\item[1.] \\textbf{First} We propose it.\n"
                            "\\item[2.] \\textbf{Five Words in This Head}: We test it.\n\\end{enumerate}\n")
        self.assertEqual(rows(text, "introduction", ".tex")[self.LONG], ("5 words", False))

    def test_a_bold_head_wrapped_across_lines_is_read_whole(self):
        text = self.LEAD + ("Our contributions are:\n\n- **First**: We propose it.\n"
                            "- **Five Words in\n  This Head (Section 2)**: We test it.\n")
        r = rows(text, "introduction")
        self.assertEqual(r[self.LONG], ("5 words", False))
        self.assertEqual(r[self.PTR], ("1", False))

    def test_an_indented_continuation_paragraph_stays_in_its_item(self):
        text = self.LEAD + ("Our contributions are:\n\n- **First**: We propose it.\n\n"
                            "  It needs no labels at test time.\n\n"
                            "- **Five Words in This Head (Section 2)**: We test it.\n")
        r = rows(text, "introduction")
        self.assertEqual(r[self.LONG], ("5 words", False))
        self.assertEqual(r[self.PTR], ("1", False))

    def test_a_linked_pointer_after_the_head_counts_and_an_external_link_does_not(self):
        text = self.LEAD + ("Our contributions are:\n\n- **First**: We propose it.\n"
                            "- **Analysis** ([Section 2](#analysis)): We test it.\n"
                            "- **Platform** ([the code](https://example.org/x)): We release it.\n")
        self.assertEqual(rows(text, "introduction")[self.PTR], ("1", False))

    def test_an_ordered_list_closed_by_a_parenthesis(self):
        text = self.LEAD + ("Our contributions are:\n\n1) **First**: We propose it.\n"
                            "2) **Five Words in This Head (Section 2)**: We test it.\n")
        r = rows(text, "introduction")
        self.assertEqual(r[self.LONG], ("5 words", False))
        self.assertEqual(r[self.PTR], ("1", False))

    def test_a_plain_first_item_does_not_pass_its_exemption_on(self):
        text = self.LEAD + ("Our contributions are:\n\n- We propose a method.\n"
                            "- **Five Words in This Head**: We test it.\n")
        self.assertEqual(rows(text, "introduction")[self.LONG], ("5 words", False))

    def test_a_list_must_close_the_introduction_save_one_short_line(self):
        items = "Our contributions are:\n\n- **First**: We propose it.\n- **Formulation**: We define it.\n\n"
        short = self.LEAD + items + "**Reproducibility.** We release all code and data.\n"
        self.assertEqual(rows(short, "introduction")["ends on a contribution list"], ("2 items", True))
        long = self.LEAD + items + "A further paragraph keeps going about prior work. " * 10
        self.assertEqual(rows(long, "introduction")["ends on a contribution list"], ("80 words after it", False))

    def test_a_list_without_bold_heads_skips_both_measures(self):
        text = self.LEAD + "In summary, our contributions are:\n\n- We propose a method.\n- We show gains.\n"
        r = rows(text, "introduction")
        self.assertNotIn(self.LONG, r)
        self.assertNotIn(self.PTR, r)


if __name__ == "__main__":
    unittest.main()
