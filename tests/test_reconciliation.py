import tempfile
import unittest
from pathlib import Path
import pandas as pd
from reconciliation import build_reconciliation, save_reconciliation

class ReconciliationTests(unittest.TestCase):
    def make_fixture(self, confirmed=True, conflicting_dob=False):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        scenario = "S1_5pct"
        sd = root / scenario
        (sd / "golden_record").mkdir(parents=True)
        (sd / "standardized").mkdir()
        membership = pd.DataFrame([
            {"scenario": scenario, "golden_record_id":"GR1","source_system":"ADMISSION_SYS","source_patient_id":"A1","member_count":1,"source_count":1},
            {"scenario": scenario, "golden_record_id":"GR2","source_system":"LAB_SYS","source_patient_id":"L1","member_count":1,"source_count":1},
        ])
        membership.to_csv(sd/"golden_record"/"cluster_membership.csv", index=False)
        golden = pd.DataFrame([
            {"scenario":scenario,"golden_record_id":"GR1","source_count":1,"member_count":1,"first_name":"Ada"},
            {"scenario":scenario,"golden_record_id":"GR2","source_count":1,"member_count":1,"first_name":"Ada"},
        ])
        golden.to_csv(sd/"golden_record"/"golden_records.csv", index=False)
        pd.DataFrame([
            {"source_system":"ADMISSION_SYS","source_patient_id":"A1","std__date_of_birth":"1980-01-01"},
            {"source_system":"LAB_SYS","source_patient_id":"L1","std__date_of_birth":"1990-01-01" if conflicting_dob else "1980-01-01"},
        ]).to_csv(sd/"standardized"/"identities.csv", index=False)
        queue = pd.DataFrame([{
            "case_id":"CASE1","scenario":scenario,"source_system_a":"ADMISSION_SYS",
            "source_patient_id_a":"A1","source_system_b":"LAB_SYS","source_patient_id_b":"L1",
            "reviewer_decision":"CONFIRM_MATCH" if confirmed else "",
            "current_status":"REVIEWED_MATCH" if confirmed else "PENDING"
        }])
        queue.to_csv(root/"human_review_queue.csv", index=False)
        return tmp, root, scenario

    def test_confirmed_safe_pair_merges(self):
        tmp, root, scenario = self.make_fixture()
        with tmp:
            result = build_reconciliation(root, scenario)
            self.assertEqual(result["confirmed_decisions_count"], 1)
            self.assertEqual(result["reconciled_golden_count"], 1)
            self.assertIn("MERGED", result["accepted_decisions"]["result"].tolist())

    def test_conflicting_dob_blocks_merge(self):
        tmp, root, scenario = self.make_fixture(conflicting_dob=True)
        with tmp:
            result = build_reconciliation(root, scenario)
            self.assertEqual(result["reconciled_golden_count"], 2)
            self.assertIn("CONFLICTING_DATE_OF_BIRTH", result["rejected_decisions"]["reason"].tolist())

    def test_unconfirmed_pair_does_not_merge(self):
        tmp, root, scenario = self.make_fixture(confirmed=False)
        with tmp:
            result = build_reconciliation(root, scenario)
            self.assertEqual(result["confirmed_decisions_count"], 0)
            self.assertEqual(result["reconciled_golden_count"], 2)

    def test_saves_versioned_outputs_without_overwrite(self):
        tmp, root, scenario = self.make_fixture()
        with tmp:
            result = build_reconciliation(root, scenario)
            out1 = save_reconciliation(result)
            out2 = save_reconciliation(result)
            self.assertEqual(out1.name, "reconciliation_v1")
            self.assertEqual(out2.name, "reconciliation_v2")
            self.assertTrue((out1/"golden_record_lineage.csv").exists())
            self.assertTrue((out2/"reconciliation_summary.csv").exists())

if __name__ == "__main__":
    unittest.main()
