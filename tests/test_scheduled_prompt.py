import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('builder', ROOT / 'scripts/build_scheduled_prompt.py')
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


class ScheduledPromptTests(unittest.TestCase):
    def profile(self):
        return dict(first_name="ALEX", last_name="O'EXAMPLE", mi=None,
                    exam_no='04034', title_code='13621', list_no='123.500')

    def test_identity_text_and_embedded_marker_are_preserved(self):
        profile = self.profile()
        profile['note'] = '{{OUTPUT_LANGUAGE}}'
        result = BUILDER.build(profile, 'private:item')
        self.assertIn('"exam_no": "04034"', result)
        self.assertIn('"list_no": "123.500"', result)
        self.assertIn('"note": "{{OUTPUT_LANGUAGE}}"', result)
        self.assertIn('OUTPUT LANGUAGE: "English"', result)
        self.assertIn('a9md-ynri.json', result)
        self.assertNotIn('{{PRIVATE_PROFILE_JSON}}', result)

    def test_lossy_numeric_input_rejected(self):
        for field in ('exam_no', 'list_no'):
            profile = self.profile()
            profile[field] = 123
            with self.assertRaises(ValueError):
                BUILDER.build(profile, 'none')

    def test_cli_private_file_and_config_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / 'config.json'
            output = Path(directory) / 'prompt.txt'
            original = json.dumps(self.profile())
            config.write_text(original)
            process = subprocess.run([sys.executable, str(ROOT / 'scripts/build_scheduled_prompt.py'),
                                      '--config', str(config), '--checkpoint-ref', 'private:item',
                                      '--output', str(output)], capture_output=True)
            self.assertEqual(process.returncode, 0)
            self.assertEqual(process.stdout, b'')
            self.assertEqual(config.read_text(), original)
            self.assertEqual(stat.S_IMODE(os.stat(output).st_mode), 0o600)


if __name__ == '__main__':
    unittest.main()
