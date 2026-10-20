import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import external_ai_review as review
from prepare_relay_reviews import MODEL_SENTENCE, convert_members


class RelayPackageConversionTests(unittest.TestCase):
    def test_conversion_preserves_instructions_and_substantive_members(self):
        readme = b'# Review\n\nRead manifest.json. Name it PACKAGE-ID-result.zip.\n'
        manifest = {'package_id': 'test', 'files': {'README.md': review.sha(readme), 'scan.jpg': review.sha(b'image')}}
        original = {'README.md': readme, 'scan.jpg': b'image', 'manifest.json': review.encoded(manifest),
                    'result-template/result.json': review.encoded({'input_manifest_sha256': 'old'})}
        converted = convert_members(original)
        self.assertEqual(converted['README.md'].decode().replace(MODEL_SENTENCE + '\n\n', ''), readme.decode())
        self.assertEqual(converted['scan.jpg'], original['scan.jpg'])
        self.assertEqual(original['README.md'], readme)
        self.assertEqual(json.loads(converted['manifest.json'])['files']['README.md'], review.sha(converted['README.md']))
        self.assertEqual(json.loads(converted['result-template/result.json'])['input_manifest_sha256'], review.sha(converted['manifest.json']))
        self.assertEqual(convert_members(converted), converted)

    def test_corrupted_substantive_member_is_rejected(self):
        readme = b'# Review\n\nInstructions.\n'
        files = {'README.md': readme, 'scan.jpg': b'changed',
                 'manifest.json': review.encoded({'files': {'scan.jpg': review.sha(b'original')}}),
                 'result-template/result.json': review.encoded({})}
        with self.assertRaisesRegex(ValueError, 'scan.jpg'):
            convert_members(files)
