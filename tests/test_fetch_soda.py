"""Offline tests for the optional curl helper. Run: python3 -m unittest discover -s tests -v"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "fetch-soda.sh"

MOCK_CURL = r'''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
params = {}
output = None
for i, arg in enumerate(args):
    if arg == '--data-urlencode':
        k, v = args[i + 1].split('=', 1)
        params[k] = v
    if arg == '--output':
        output = args[i + 1]
if not output or '$where' not in params:
    sys.exit(15)
mode = os.environ.get('MOCK_MODE', 'ok')
state = Path(os.environ['MOCK_STATE'])
if '$select' in params:
    n = int(state.read_text()) if state.exists() else 0
    state.write_text(str(n + 1))
    result = [{'total': str(5 if mode != 'drift' or n == 0 else 6)}]
else:
    offset = int(params.get('$offset', 0))
    limit = int(params.get('$limit', 1000))
    if mode == 'failure' and offset >= 2:
        sys.exit(22)
    result = [{'exam_no': '4034', 'list_no': '16.500', 'cert_seq_no': str(i + 1)} for i in range(5)][offset:offset + limit]
    if mode == 'short' and offset >= 2:
        result = result[:-1]
    if mode == 'object' and offset >= 2:
        result = {'error': 'unexpected'}
Path(output).write_text(json.dumps(result))
'''

class FetchSodaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        binpath = self.root / 'bin'
        binpath.mkdir()
        (binpath / 'curl').write_text(MOCK_CURL)
        (binpath / 'curl').chmod(0o755)
        self.env = os.environ.copy()
        self.env.update(PATH=str(binpath) + os.pathsep + self.env['PATH'],
                        MOCK_STATE=str(self.root / 'counter'))
        self.out = self.root / 'result.json'

    def tearDown(self):
        self.tmp.cleanup()

    def run_fetch(self, mode='ok', *args):
        self.env['MOCK_MODE'] = mode
        return subprocess.run(
            ['bash', str(SCRIPT), '--where', "exam_no='4034' AND last_name='EXAMPLE'",
             '--page-size', '2', '--out', str(self.out), *args],
            env=self.env, capture_output=True, text=True)

    def test_complete_pagination_and_decimal_strings(self):
        run = self.run_fetch()
        self.assertEqual(run.returncode, 0, run.stderr)
        data = json.loads(self.out.read_text())
        self.assertEqual(len(data), 5)
        self.assertEqual(data[-1]['list_no'], '16.500')
        self.assertIn('Verified 5 rows across 3 page(s)', run.stderr)

    def test_partial_response_preserves_output(self):
        self.out.write_text('previous good snapshot')
        self.assertNotEqual(self.run_fetch('short').returncode, 0)
        self.assertEqual(self.out.read_text(), 'previous good snapshot')

    def test_dataset_drift_preserves_output(self):
        self.out.write_text('previous good snapshot')
        run = self.run_fetch('drift')
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('changed during retrieval', run.stderr)
        self.assertEqual(self.out.read_text(), 'previous good snapshot')

    def test_http_failure_preserves_output(self):
        self.out.write_text('previous good snapshot')
        self.assertNotEqual(self.run_fetch('failure').returncode, 0)
        self.assertEqual(self.out.read_text(), 'previous good snapshot')

    def test_invalid_json_rejected(self):
        self.assertNotEqual(self.run_fetch('object').returncode, 0)
        self.assertFalse(self.out.exists())

    def test_unfiltered_query_rejected(self):
        run = subprocess.run(['bash', str(SCRIPT), '--out', str(self.out)],
                             env=self.env, capture_output=True, text=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertFalse(self.out.exists())

    def test_max_rows_limit(self):
        self.assertNotEqual(self.run_fetch('ok', '--max-rows', '4').returncode, 0)
        self.assertFalse(self.out.exists())

if __name__ == '__main__':
    unittest.main()
