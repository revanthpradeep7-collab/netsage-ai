"""
NetSage AI - Automated Test Suite (unittest compatible)
Unit and Integration tests for Dataset, Rule Checker, Diagnostic Engine, and Human Review persistence.
"""

import os
import sys
import json
import csv
import shutil
import tempfile
import unittest

from src.cases_data import CASES
from src.rule_checker import NetworkRuleChecker
from src.ai_engine import DiagnosticEngine
from src.case_manager import CaseManager

class TestNetSageAI(unittest.TestCase):

    def test_dataset_coverage(self):
        """Verify that dataset contains at least 30 cases across required concepts."""
        self.assertGreaterEqual(len(CASES), 30, f"Expected >= 30 cases, found {len(CASES)}")
        concepts = set(c["concept_tag"] for c in CASES)
        expected_concepts = {"VLAN", "Gateway", "DHCP", "DNS", "Routing", "ACL", "NAT", "Wireless"}
        for exp in expected_concepts:
            self.assertIn(exp, concepts, f"Missing required concept category: {exp}")

    def test_case_schema_integrity(self):
        """Verify all required fields exist and are non-empty for every case."""
        required_fields = [
            "case_id", "title", "symptom", "topology_note", "show_outputs",
            "expected_fault", "osi_layer", "concept_tag", "severity",
            "recommended_fix_steps", "verification_command"
        ]
        for c in CASES:
            for field in required_fields:
                self.assertIn(field, c, f"Case {c.get('case_id')} missing field: {field}")
                self.assertTrue(len(str(c[field]).strip()) > 0, f"Case {c.get('case_id')} has empty field: {field}")

    def test_deterministic_rule_checker_coverage(self):
        """Verify that the rule checker identifies deterministic misconfigurations across cases."""
        checker = NetworkRuleChecker()
        findings_count = 0
        for c in CASES:
            f = checker.analyze(c["symptom"], c["topology_note"], c["show_outputs"])
            if len(f) > 0:
                findings_count += 1
        coverage_ratio = findings_count / len(CASES)
        self.assertGreaterEqual(coverage_ratio, 0.95, f"Rule checker coverage is {coverage_ratio*100}%, expected >= 95%")

    def test_ai_diagnosis_schema_and_evidence(self):
        """Verify that AI diagnostic engine returns valid schema with quoted evidence."""
        engine = DiagnosticEngine()
        test_case = CASES[0]
        diag = engine.diagnose(test_case["case_id"], test_case["symptom"], test_case["topology_note"], test_case["show_outputs"])
        
        self.assertTrue("root_cause" in diag and len(diag["root_cause"]) > 0)
        self.assertIn(diag["osi_layer"], ["Layer 1", "Layer 2", "Layer 3", "Layer 4", "Layer 7"])
        self.assertIn(diag["confidence"], ["High", "Medium", "Low"])
        self.assertTrue(isinstance(diag["evidence"], list) and len(diag["evidence"]) > 0)
        self.assertTrue(len(diag["next_command"]) > 0)
        self.assertTrue(isinstance(diag["fix_steps"], list) and len(diag["fix_steps"]) > 0)
        self.assertTrue(diag.get("human_review_required") is True)

    def test_human_review_persistence(self):
        """Verify that human reviews are saved and retrieved correctly.

        Uses an isolated temp copy of data/ so this test never mutates the
        project's real review_log.csv / responsible_ai_log.csv on disk.
        """
        real_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        real_cases_json = os.path.join(real_base_dir, "data", "cases.json")

        with tempfile.TemporaryDirectory() as tmp_base_dir:
            tmp_data_dir = os.path.join(tmp_base_dir, "data")
            os.makedirs(tmp_data_dir, exist_ok=True)
            shutil.copy(real_cases_json, os.path.join(tmp_data_dir, "cases.json"))

            mgr = CaseManager(base_dir=tmp_base_dir)

            mgr.submit_review(
                case_id="NET-001",
                verdict="Accepted",
                reviewer="Test TAC Engineer",
                comments="Verified against topology."
            )

            # Reload from disk (still inside the temp dir)
            mgr2 = CaseManager(base_dir=tmp_base_dir)
            self.assertIn("NET-001", mgr2.reviews)
            self.assertEqual(mgr2.reviews["NET-001"]["verdict"], "Accepted")

    def test_responsible_ai_log_minimum_count(self):
        """Verify that at least 5 corrected AI failure scenarios are documented."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        resp_csv = os.path.join(base_dir, "data", "responsible_ai_log.csv")
        self.assertTrue(os.path.exists(resp_csv), "responsible_ai_log.csv does not exist")
        
        with open(resp_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        self.assertGreaterEqual(len(rows), 5, f"Expected >= 5 responsible AI log entries, found {len(rows)}")

if __name__ == "__main__":
    unittest.main(verbosity=2)