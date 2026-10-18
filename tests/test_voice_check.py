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
    return {name: (value, ok) for name, value, _, ok in vc.measure(vc.plain(text, suffix), section, text)}


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


if __name__ == "__main__":
    unittest.main()
