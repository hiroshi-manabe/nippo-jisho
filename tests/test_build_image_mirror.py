import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_image_mirror  # noqa: E402


class BuildImageMirrorTests(unittest.TestCase):
    def test_variant_dimensions_preserve_aspect_ratio(self):
        self.assertEqual(build_image_mirror.variant_dimensions(3000, 4200, 1000), (1000, 1400))
        self.assertEqual(build_image_mirror.variant_dimensions(800, 1200, 1000), (800, 1200))

    def test_prepare_variant_writes_requested_width(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.jpg"
            output = root / "variant.jpg"
            Image.new("RGB", (1200, 1800), "white").save(source)
            build_image_mirror.prepare_variant(source, output, 1000, False)
            with Image.open(output) as image:
                self.assertEqual(image.size, (1000, 1500))

    def test_page_record_uses_stable_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "f0017.jpg"
            Image.new("RGB", (2200, 3000), "white").save(source)
            record = build_image_mirror.page_record(source)
            self.assertEqual(record["preview"], "scans/1000/f0017.jpg")
            self.assertEqual(record["reading"], "scans/2200/f0017.jpg")
            self.assertTrue(record["gallica"].endswith("/f17.item"))


if __name__ == "__main__":
    unittest.main()
