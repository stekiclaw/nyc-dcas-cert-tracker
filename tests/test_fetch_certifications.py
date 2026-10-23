"""Tests for Python SODA2 candidate fetcher. Network-free; synthetic identities."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "fetch_certifications.py"
spec = importlib.util.spec_from_file_location("dcas_candidate_fetch", MODULE)
fetcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetcher)


class PythonFetchTests(unittest.TestCase):
    def test_quote_and_exam_forms(self):
        where = fetcher.build_where("Alex", "O'Neil", "04034", "13621")
        self.assertIn("last_name='O''NEIL'", where)
        self.assertIn("exam_no='4034'", where)
        self.assertIn("exam_no='04034'", where)
        self.assertIn("list_title_code='13621'", where)

    def test_complete_paging_and_decimal_list_no(self):
        def fake(params):
            if params["$select"].startswith("count("):
                return [{"total": "3"}]
            all_rows = [
                dict(first_name="ALEX", last_name="EXAMPLE", exam_no="04034",
                     list_title_code="13621", list_no=v, cert_seq_no=str(i + 1))
                for i, v in enumerate(["103", "103.000", "104"])]
            offset = int(params["$offset"])
            return all_rows[offset:offset + int(params["$limit"])]
        result = fetcher.fetch("Alex", "Example", "4034", "13621", "103.000",
                               page_size=2, requester=fake)
        self.assertEqual(result["matched_count"], 2)
        self.assertEqual(result["count_before_list_filter"], 3)

    def test_count_drift(self):
        n = [0]
        def fake(params):
            if params["$select"].startswith("count("):
                n[0] += 1
                return [{"total": str(n[0])}]
            return [dict(first_name="ALEX", last_name="EXAMPLE", exam_no="4034")]
        with self.assertRaisesRegex(ValueError, "drift"):
            fetcher.fetch("Alex", "Example", "4034", page_size=1, requester=fake)

    def test_partial_page(self):
        def fake(params):
            if params["$select"].startswith("count("):
                return [{"total": "2"}]
            return []
        with self.assertRaisesRegex(ValueError, "Incomplete page"):
            fetcher.fetch("Alex", "Example", "4034", requester=fake)

    def test_private_output(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "private.json"
            fetcher.private_write(path, {"rows": [{"list_no": "103.000"}]})
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(json.loads(path.read_text())["rows"][0]["list_no"],
                             "103.000")


if __name__ == "__main__":
    unittest.main()
