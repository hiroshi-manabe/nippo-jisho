import tempfile
from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import download_gallica  # noqa: E402


class DownloadGallicaTests(unittest.TestCase):
    def test_identifiers_and_urls(self):
        self.assertEqual(download_gallica.page_id(14), "bnf-f0014")
        self.assertEqual(download_gallica.gallica_view(14), "f14")
        self.assertIn("/f14/full/full/0/native.jpg", download_gallica.image_url(14))
        self.assertTrue(download_gallica.item_url(14).endswith("/f14.item"))

    def test_range_validation(self):
        self.assertEqual(list(download_gallica.requested_numbers(1, 3)), [1, 2, 3])
        with self.assertRaises(ValueError):
            list(download_gallica.requested_numbers(0, 3))
        with self.assertRaises(ValueError):
            list(download_gallica.requested_numbers(3, 2))
        with self.assertRaises(ValueError):
            list(download_gallica.requested_numbers(650, 652))

    def test_jpeg_dimensions(self):
        # Minimal JPEG-like byte stream containing a baseline SOF segment.
        jpeg = (
            b"\xff\xd8"
            b"\xff\xe0\x00\x04\x00\x00"
            b"\xff\xc0\x00\x08\x08\x01\xe0\x02\x80\x01"
            b"\xff\xd9"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.jpg"
            path.write_bytes(jpeg)
            self.assertEqual(download_gallica.jpeg_dimensions(path), (640, 480))


if __name__ == "__main__":
    unittest.main()
