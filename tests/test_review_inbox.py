import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import review_inbox as inbox
import external_ai_review as review


class InboxTests(unittest.TestCase):
    def test_stable_file_and_content_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            path = folder / 'returned.zip'
            path.write_bytes(b'first')
            ledger = {'observed': {}}
            self.assertEqual(inbox.discover_results(folder, ledger, 0), [])
            self.assertEqual(inbox.discover_results(folder, ledger, 59), [])
            first = inbox.discover_results(folder, ledger, 60)[0][0]
            path.write_bytes(b'second')
            self.assertEqual(inbox.discover_results(folder, ledger, 61), [])
            second = inbox.discover_results(folder, ledger, 121)[0][0]
            self.assertNotEqual(first, second)

    def test_nested_human_requests(self):
        self.assertTrue(inbox.needs_human({'pages': [{'changes': [{'second_opinion': True}]}]}))
        self.assertTrue(inbox.needs_human({'changes': [{'message': 'Check crop'}]}))
        self.assertFalse(inbox.needs_human({'changes': [{'after': 'text', 'second_opinion': False}]}))

    def test_ids(self):
        self.assertEqual(review.normalize_page_id(241), 'bnf-f0241')
        self.assertEqual(review.normalize_page_id('bodleian-f0090v'), 'bodleian-f0090v')
        with self.assertRaises(ValueError):
            review.normalize_page_id('../bad')

    def test_dirty_queue_preserves_unattempted_jobs(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            def run(*args):
                if args[0] == 'gh':
                    return json.dumps([[{'number': 1, 'title': 'Correction', 'body': '{}'}]])
                return ' M user-file'
            with patch.object(inbox, 'STATE', folder / 'state'), patch.object(inbox, 'INCOMING', folder / 'incoming'), patch.object(inbox, 'run', side_effect=run):
                inbox.cycle()
            ledger = json.loads((folder / 'state/ledger.json').read_text())
            self.assertEqual(ledger['jobs'], {})
            self.assertIn('Tracked changes', ledger['paused'])

    def test_failure_is_not_retried(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            def run(*args):
                if args[0] == 'gh':
                    return json.dumps([[{'number': 1, 'title': 'Bad JSON', 'body': '{}'}]])
                return '0' if 'rev-list' in args else ''
            with patch.object(inbox, 'STATE', folder / 'state'), patch.object(inbox, 'INCOMING', folder / 'incoming'), patch.object(inbox, 'run', side_effect=run):
                inbox.cycle()
                first = (folder / 'state/ledger.json').read_text()
                inbox.cycle()
                self.assertEqual(first, (folder / 'state/ledger.json').read_text())
