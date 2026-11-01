"""Tests for skills/figure-candidate-gallery/scripts (stdlib unittest, Python 3.9+).

The skia half runs against a stub skia-canvas module, so it needs only node.
The matplotlib and PyMuPDF halves skip when those packages are absent, as they
are in CI.
"""
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "figure-candidate-gallery" / "scripts"
NODE = shutil.which("node")
HAS_MPL = importlib.util.find_spec("matplotlib") is not None
HAS_FITZ = importlib.util.find_spec("fitz") is not None

STUB = """
export class Canvas {
  constructor(w, h) { this.width = w; this.height = h }
  getContext() { return new Proxy({}, { get: () => () => ({ width: 0 }) }) }
}
export const FontLibrary = { use() { throw new Error('no fonts in the stub') } }
"""

PROBE = (
    "import {pathToFileURL} from 'node:url';"
    "const m = await import(pathToFileURL(process.argv[1]).href);"
    "console.log(JSON.stringify({family: m.FAMILY, minPt: m.MIN_PT, stack: m.FONT_STACK}))"
)


def run_dir(cfg, with_skia=True):
    """A run directory holding both helpers, a palette.json, and a stub skia-canvas."""
    tmp = Path(tempfile.mkdtemp(prefix="fcg-test-"))
    shutil.copy(SCRIPTS / "figure_base.py", tmp)
    if with_skia:
        shutil.copy(SCRIPTS / "skia_base.mjs", tmp)
        pkg = tmp / "node_modules" / "skia-canvas"
        pkg.mkdir(parents=True)
        (pkg / "package.json").write_text(json.dumps(
            {"name": "skia-canvas", "type": "module", "main": "index.js"}))
        (pkg / "index.js").write_text(STUB)
    if cfg is not None:
        # A str is written raw, for literals json.dumps cannot produce (1e309).
        (tmp / "palette.json").write_text(cfg if isinstance(cfg, str) else json.dumps(cfg))
    return tmp


@unittest.skipUnless(NODE, "node is not installed")
class SkiaRunConfig(unittest.TestCase):
    def probe(self, cfg):
        tmp = run_dir(cfg)
        try:
            proc = subprocess.run([NODE, "--input-type=module", "-e", PROBE, str(tmp / "skia_base.mjs")],
                                  capture_output=True, text=True)
        finally:
            shutil.rmtree(tmp)
        return proc

    def test_family_and_floor_reach_the_font_stack(self):
        proc = self.probe({"font": "serif", "family": ["Times New Roman"], "minPt": 12})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["family"], ["Times New Roman"])
        self.assertEqual(out["minPt"], 12)
        self.assertTrue(out["stack"].startswith("Times New Roman, "))

    def test_defaults_without_the_new_keys(self):
        proc = self.probe({"font": "sans"})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["family"], [])
        self.assertEqual(out["minPt"], 7)
        self.assertTrue(out["stack"].startswith("Arial"))

    def test_bad_values_throw(self):
        for cfg in ({"family": "Times New Roman"}, {"family": [""]}, {"minPt": 0},
                    {"minPt": True}, {"minPt": "12"}, '{"minPt": 1e309}'):
            with self.subTest(cfg=cfg):
                proc = self.probe(cfg)
                self.assertNotEqual(proc.returncode, 0)


@unittest.skipUnless(HAS_MPL, "matplotlib is not installed")
class MatplotlibRunConfig(unittest.TestCase):
    def load(self, cfg):
        tmp = run_dir(cfg, with_skia=False)
        self.addCleanup(shutil.rmtree, tmp)
        code = ("import sys, json; sys.path.insert(0, sys.argv[1]); import figure_base as f;"
                "f.apply_house_style(); import matplotlib as m;"
                "print(json.dumps({'family': f.FAMILY, 'minPt': f.MIN_PT,"
                " 'size': m.rcParams['font.size'], 'tick': m.rcParams['xtick.labelsize'],"
                " 'serif': m.rcParams['font.serif'][0], 'math': m.rcParams['mathtext.fontset']}))")
        return subprocess.run([sys.executable, "-B", "-c", code, str(tmp)],
                              capture_output=True, text=True)

    def test_floor_raises_default_sizes_and_family_leads(self):
        proc = self.load({"font": "serif", "family": ["Times New Roman"], "minPt": 12})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["minPt"], 12.0)
        self.assertEqual(out["size"], 12.0)
        self.assertEqual(out["serif"], "Times New Roman")
        self.assertEqual(out["math"], "custom")

    def test_default_floor_leaves_sizes_alone(self):
        proc = self.load({"font": "sans"})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["minPt"], 7.0)
        self.assertEqual(out["size"], 10.0)

    def test_bad_values_raise(self):
        for cfg in ({"family": "Times New Roman"}, {"family": [""]}, {"minPt": 0},
                    {"minPt": True}, {"minPt": "12"}, '{"minPt": 1e309}'):
            with self.subTest(cfg=cfg):
                self.assertNotEqual(self.load(cfg).returncode, 0)

    @unittest.skipUnless(NODE, "node is not installed")
    def test_check_run_config_agrees(self):
        tmp = run_dir({"font": "serif", "family": ["Times New Roman"], "minPt": 12})
        self.addCleanup(shutil.rmtree, tmp)
        proc = subprocess.run([sys.executable, str(SCRIPTS / "check_run_config.py"), "--dir", str(tmp)],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


@unittest.skipUnless(HAS_MPL and HAS_FITZ, "matplotlib or PyMuPDF is not installed")
class ExactSaveAndMeasure(unittest.TestCase):
    def test_exact_save_keeps_the_slot_width_and_measure_flags_small_text(self):
        tmp = run_dir({"font": "sans", "minPt": 9}, with_skia=False)
        self.addCleanup(shutil.rmtree, tmp)
        code = ("import sys; sys.path.insert(0, sys.argv[1]); import figure_base as f;"
                "f.apply_house_style(); import matplotlib; matplotlib.rcParams['savefig.bbox'] = 'tight';"
                "import matplotlib.pyplot as plt; fig = plt.figure(figsize=(2.5, 1.5)); fig.text(0.1, 0.5, 'label', fontsize=9);"
                "fig.text(0.1, 0.2, 'tiny', fontsize=6);"
                "f.save(fig, 'cand-01-x', sys.argv[1], exact=True)")
        subprocess.run([sys.executable, "-B", "-c", code, str(tmp)], check=True, capture_output=True)
        measure = [sys.executable, str(SCRIPTS / "measure_pdf.py"), "--pdf", str(tmp / "cand-01-x.pdf"),
                   "--width-in", "2.5", "--json"]
        proc = subprocess.run(measure, capture_output=True, text=True)
        report = json.loads(proc.stdout)
        self.assertEqual(report["width_in"], 2.5)
        self.assertEqual(report["min_pt"], 9.0)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual([text for _, text in report["spans_under_floor"]], ["tiny"])
        allowed = subprocess.run(measure + ["--allow-small", "tiny"], capture_output=True, text=True)
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        self.assertEqual(json.loads(allowed.stdout)["problems"], [])

    def test_type3_fonts_fail(self):
        tmp = run_dir({"font": "sans"}, with_skia=False)
        self.addCleanup(shutil.rmtree, tmp)
        code = ("import sys; sys.path.insert(0, sys.argv[1]); import figure_base as f;"
                "f.apply_house_style(); import matplotlib; matplotlib.rcParams['pdf.fonttype'] = 3;"
                "import matplotlib.pyplot as plt; fig = plt.figure(figsize=(2, 1));"
                "fig.text(0.1, 0.5, 'label', fontsize=9); f.save(fig, 'cand-02-t3', sys.argv[1], exact=True)")
        subprocess.run([sys.executable, "-B", "-c", code, str(tmp)], check=True, capture_output=True)
        proc = subprocess.run([sys.executable, str(SCRIPTS / "measure_pdf.py"),
                               "--pdf", str(tmp / "cand-02-t3.pdf"), "--json"],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertTrue(json.loads(proc.stdout)["type3_fonts"])


@unittest.skipUnless(HAS_FITZ, "PyMuPDF is not installed")
class OutsideThePage(unittest.TestCase):
    def test_text_wholly_outside_the_page_fails(self):
        import fitz
        tmp = Path(tempfile.mkdtemp(prefix="fcg-test-"))
        self.addCleanup(shutil.rmtree, tmp)
        pdf = tmp / "cand-03-out.pdf"
        doc = fitz.open()
        page = doc.new_page(width=180, height=108)
        page.insert_text((20, 50), "visible", fontsize=12)
        page.insert_text((190, 70), "clipped-label", fontsize=12)
        doc.save(str(pdf))
        proc = subprocess.run([sys.executable, str(SCRIPTS / "measure_pdf.py"), "--pdf", str(pdf), "--json"],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("clipped-label", json.loads(proc.stdout)["spans_outside_page"])


if __name__ == "__main__":
    unittest.main()
