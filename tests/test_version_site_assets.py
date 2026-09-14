import tempfile
import unittest
from pathlib import Path
import sys
import json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from version_site_assets import version_assets

class VersionTests(unittest.TestCase):
    def test_content_versioning(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            source='<head></head><script src="app.js"></script><a href="https://example.com/a.css">external</a>'
            (root/'index.html').write_text(source)
            (root/'app.js').write_text('one')
            version_assets(root)
            first=json.loads((root/'ui-version.json').read_text())
            self.assertIn('app.js?v=',(root/'index.html').read_text())
            self.assertIn('https://example.com/a.css',(root/'index.html').read_text())
            (root/'index.html').write_text(source)
            version_assets(root)
            self.assertEqual(first,json.loads((root/'ui-version.json').read_text()))
            (root/'index.html').write_text(source)
            (root/'app.js').write_text('two')
            version_assets(root)
            self.assertNotEqual(first['version'],json.loads((root/'ui-version.json').read_text())['version'])
