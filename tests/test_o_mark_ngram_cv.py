import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "cross_validate_o_mark_ngram",
    ROOT / "scripts" / "cross_validate_o_mark_ngram.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class OMarkNgramCrossValidationTest(unittest.TestCase):
    def test_make_folds_is_complete_disjoint_and_deterministic(self):
        pages = list(range(13, 32))
        first = MODULE.make_folds(pages, 5, 1603)
        second = MODULE.make_folds(pages, 5, 1603)
        self.assertEqual(first, second)
        self.assertEqual(sorted(page for fold in first for page in fold), pages)
        self.assertEqual(len({page for fold in first for page in fold}), len(pages))
        self.assertLessEqual(max(map(len, first)) - min(map(len, first)), 1)


if __name__ == "__main__":
    unittest.main()
