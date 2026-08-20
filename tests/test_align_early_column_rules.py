import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "align_early_column_rules", ROOT / "scripts/align_early_column_rules.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class EarlyColumnRuleAlignmentTests(unittest.TestCase):
    def test_all_early_column_pages_have_four_ordered_rule_trajectories(self):
        self.assertEqual(set(MODULE.RULES), set(range(13, 31)))
        for page, (y0, y1, outer_left, c1_right, c2_left, outer_right) in MODULE.RULES.items():
            self.assertLess(y0, y1, page)
            for at in (y0, y1):
                positions = [
                    MODULE.rule_x(rule, at, y0, y1)
                    for rule in (outer_left, c1_right, c2_left, outer_right)
                ]
                self.assertEqual(positions, sorted(positions), page)

    def test_horizontal_envelope_keeps_padding_outside_both_rules(self):
        x, width = MODULE.horizontal_envelope((100, 120), (900, 940), 200, 100, 0, 1000)
        self.assertLessEqual(x, MODULE.rule_x((100, 120), 200, 0, 1000))
        self.assertGreaterEqual(x + width, MODULE.rule_x((900, 940), 300, 0, 1000))


if __name__ == "__main__":
    unittest.main()
