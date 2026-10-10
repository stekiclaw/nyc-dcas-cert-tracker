import argparse
import datetime as dt
import tempfile
import json
import subprocess
import sys
import unittest
from pathlib import Path
from scripts.dcas_cert import snapshot, key
ROOT=Path(__file__).resolve().parents[1]
def row(**kwargs):
    return dict({"exam_no":"4034","list_title_code":"13621","list_agency_code":"001",
                 "cert_issue_no":"111","list_no":"16","cert_seq_no":"3",
                 "cert_date":"2026-10-01","sel_cert_description":"A", **kwargs})
class DCASTests(unittest.TestCase):
    def test_same_batch_different_selection(self):
        self.assertEqual(key(row()),key({**row(),"sel_cert_description":"B"}))
        self.assertEqual(len(snapshot([],[row(),{**row(),"sel_cert_description":"B"}])["certificates"]),1)
    def test_null_safe_sort(self):
        snapshot([], [row(no_requested=None),{**row(),"no_requested":"3"}])
    def test_null_active(self):
        snapshot([{"extension_date":None},{"extension_date":"2028-01-01"}],[])
    def test_event_classification(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp)
            base={"active":[],"certifications":[row()]}
            source=tmp/"in.json"; baseline=tmp/"baseline.json"; current=tmp/"current.json"
            source.write_text(json.dumps(base))
            def run(prev=None):
                cmd=[sys.executable,str(ROOT/"scripts/dcas_cert.py"),"monitor",
                     "--exam","4034","--title-code","13621","--as-of","2026-10-10",
                     "--input",str(source),"--output",str(current if prev else baseline)]
                if prev: cmd+=["--previous",str(baseline)]
                subprocess.run(cmd,check=True,capture_output=True,text=True)
                return json.loads((current if prev else baseline).read_text())
            a=run()
            self.assertTrue(a["initial_baseline"])
            base["active"]=[{"exam_no":"4034","list_title_code":"13621","list_no":"18"}]
            source.write_text(json.dumps(base))
            result=run(True)
            self.assertEqual(result["material_change_count"],0)
            base["certifications"].append({**row(),"cert_issue_no":"222"})
            source.write_text(json.dumps(base))
            result=run(True)
            self.assertEqual(result["material_change_count"],1)
            self.assertEqual(result["material_changes"][0]["event_types"],["new_certificate"])
if __name__=="__main__": unittest.main()
