import subprocess
import unittest
from pathlib import Path


class PageTimerTests(unittest.TestCase):
    def test_timing_and_persistence(self):
        subprocess.run(['node', '-e', r'''
const assert = require('node:assert/strict');
const {createTimer, format} = require('./site/assets/page-timer.js');
const values = new Map();
const storage = {getItem: k => values.get(k), setItem: (k,v) => values.set(k,v), removeItem: k => values.delete(k)};
let now = 0;
const timer = createTimer(storage, () => now);
timer.select('a'); now = 1000; timer.select('a'); now = 2000;
assert.equal(timer.total(), 2000); // Column change does not reset.
timer.select('b'); now = 5000; timer.select('a');
assert.equal(timer.total(), 2000);
timer.visibility(false); now = 9000; assert.equal(timer.total(), 2000);
timer.visibility(true); now = 10000; timer.save();
const reloaded = createTimer(storage, () => now); reloaded.select('a');
assert.equal(reloaded.total(), 3000);
timer.reset('b'); assert.equal(timer.total(), 3000);
timer.reset('a'); assert.equal(timer.total(), 0);
now = 11000; timer.select(null); now = 12000; timer.select('a');
assert.equal(timer.total(), 1000);
assert.equal(format(65000), '1:05'); assert.equal(format(3661000), '1:01:01');
'''], cwd=Path(__file__).resolve().parents[1], check=True)
