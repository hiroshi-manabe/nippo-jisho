"""Mechanism tests for the glyph experiment, not frozen transcription opinions."""

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/train_cedilla_typeface.py"
spec = importlib.util.spec_from_file_location("cedilla_typeface", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CedillaTypefaceTests(unittest.TestCase):
    def test_import_does_not_start_collection_or_training(self):
        program = (
            "import importlib.util; "
            f"s=importlib.util.spec_from_file_location('cedilla', {str(SCRIPT)!r}); "
            "m=importlib.util.module_from_spec(s); s.loader.exec_module(m)"
        )
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, "-c", program], cwd=directory, capture_output=True,
                text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, check=True,
            )
            self.assertEqual(result.stdout, "")
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_native_patch_projects_twice_resolution_without_enlarging_ocr_crop(self):
        y, x = np.indices((220, 240))
        scan = Image.fromarray(((x + 3 * y) % 256).astype("uint8"))
        row = {
            "alignment": [{"left": 10, "width": 20, "kind": "matched"}],
            "image_width": 100,
            "scan_mapping": {"origin": [50, 60], "dx": [2, 0], "dy": [0, 2]},
        }
        patch = module.native_patch(scan, row, 0)
        self.assertEqual(patch.size, (144, 96))
        # This mapping gives native origin (34,60), one source pixel/output pixel.
        self.assertEqual(patch.getpixel((20, 10)), scan.getpixel((54, 70)))

    def test_blank_crop_has_finite_fixed_length_features(self):
        ink = module.normalize(Image.new("L", (144, 96), 255))
        glyph, info = module.extract_glyph(ink, diagnostics=True)
        features = module.hog(glyph)
        self.assertEqual(info["method"], "fixed_field_fallback")
        self.assertEqual(glyph.shape, (48, 48))
        self.assertEqual(features.shape, (1152,))
        self.assertTrue(np.isfinite(features).all())
        self.assertTrue((features == 0).all())

    def test_descender_glyph_is_not_replaced_by_following_u(self):
        ink = np.zeros((96, 144))
        # Connected open body and cedilla, to the left of the alignment centre.
        ink[34:67, 24:30] = 1
        ink[34:40, 24:43] = 1
        ink[61:67, 24:43] = 1
        ink[65:84, 31:37] = 1
        # Following u is closer to the old presumed centre (56).
        ink[35:66, 49:55] = 1
        ink[35:66, 64:70] = 1
        ink[60:66, 49:70] = 1
        _, info = module.extract_glyph(ink, diagnostics=True)
        self.assertEqual(info["method"], "component")
        self.assertLess(info["box"][2], 49)
        self.assertGreater(info["box"][3], 84)


if __name__ == "__main__":
    unittest.main()
