import unittest
from datetime import datetime, timezone

from robot_release_check.checks import run_checks, overall_status
from robot_release_check.models import ChangeRecord, ClosureRecord, Release, TestRecord, VerificationRecord, parse_time
from robot_release_check.report import build_json_report


def dt(day, hour=0):
    return datetime(2026, 10, day, hour, tzinfo=timezone.utc)


class CheckTests(unittest.TestCase):
    def test_late_change_demo_flags_r001_r002_r004(self):
        release = Release("v1.4.1", dt(10, 16))
        tests = [TestRecord("T1", "v1.4", "PASS", dt(8, 11), "acceptance")]
        changes = [ChangeRecord("C1", "v1.4.1", dt(9, 9), "config")]
        closures = [ClosureRecord("I1", "CLOSED", dt(9, 18), ("V1",))]
        verifications = [VerificationRecord("V1", "v1.4")]
        findings = run_checks(release, tests, changes, closures, verifications)
        by_id = {f.rule_id: f.status for f in findings}
        self.assertEqual(by_id["R001"], "EVIDENCE_MISMATCH")
        self.assertEqual(by_id["R002"], "EVIDENCE_GAP")
        self.assertEqual(by_id["R003"], "PASS")
        self.assertEqual(by_id["R004"], "EVIDENCE_GAP")
        self.assertEqual(overall_status(findings), "REVIEW REQUIRED")

    def test_all_pass(self):
        release = Release("v2", dt(10, 16))
        tests = [TestRecord("T2", "v2", "PASS", dt(10, 10), "acceptance")]
        changes = [ChangeRecord("C0", "v2", dt(9, 9), "before test")]
        closures = [ClosureRecord("I2", "CLOSED", dt(10, 12), ("VERIFY-2",))]
        verifications = [VerificationRecord("VERIFY-2", "v2")]
        findings = run_checks(release, tests, changes, closures, verifications)
        self.assertTrue(all(f.status == "PASS" for f in findings))
        self.assertEqual(overall_status(findings), "PASS")

    def test_closed_without_evidence_flags_r003(self):
        release = Release("v2", dt(10, 16))
        tests = [TestRecord("T2", "v2", "PASS", dt(10, 10), "acceptance")]
        findings = run_checks(release, tests, [], [ClosureRecord("I2", "CLOSED", dt(10, 12), ())], [])
        by_id = {f.rule_id: f.status for f in findings}
        self.assertEqual(by_id["R003"], "EVIDENCE_GAP")
        self.assertEqual(by_id["R004"], "EVIDENCE_GAP")

    def test_pass_after_delivery_does_not_qualify(self):
        release = Release("v2", dt(10, 16))
        tests = [TestRecord("T3", "v2", "PASS", dt(11, 10), "acceptance")]
        findings = run_checks(release, tests, [], [], [])
        by_id = {f.rule_id: f.status for f in findings}
        self.assertEqual(by_id["R001"], "EVIDENCE_GAP")
        self.assertEqual(by_id["R002"], "EVIDENCE_GAP")

    def test_change_for_unrelated_release_does_not_trigger_r002(self):
        release = Release("v2", dt(10, 16))
        tests = [TestRecord("T2", "v2", "PASS", dt(10, 10), "acceptance")]
        changes = [ChangeRecord("C-other", "v3", dt(10, 12), "unrelated release")]
        findings = run_checks(release, tests, changes, [], [])
        by_id = {f.rule_id: f.status for f in findings}
        self.assertEqual(by_id["R002"], "PASS")

    def test_r002_uses_delivered_release_pass_not_global_latest_pass(self):
        release = Release("v2", dt(10, 16))
        tests = [
            TestRecord("T-v2", "v2", "PASS", dt(10, 10), "acceptance"),
            TestRecord("T-v3", "v3", "PASS", dt(10, 12), "acceptance"),
        ]
        changes = [ChangeRecord("C-v2", "v2", dt(10, 11), "post-v2-test change")]
        findings = run_checks(release, tests, changes, [], [])
        by_id = {f.rule_id: f.status for f in findings}
        self.assertEqual(by_id["R001"], "EVIDENCE_MISMATCH")
        self.assertEqual(by_id["R002"], "EVIDENCE_GAP")

    def test_r004_flags_stale_but_nonempty_reference(self):
        release = Release("v1.4.1", dt(10, 16))
        tests = [TestRecord("T2", "v1.4.1", "PASS", dt(10, 10), "acceptance")]
        closures = [ClosureRecord("I2", "CLOSED", dt(10, 12), ("VERIFY-OLD",))]
        verifications = [VerificationRecord("VERIFY-OLD", "v1.4")]
        findings = run_checks(release, tests, [], closures, verifications)
        by_id = {f.rule_id: f.status for f in findings}
        self.assertEqual(by_id["R003"], "PASS")
        self.assertEqual(by_id["R004"], "EVIDENCE_GAP")

    def test_r004_flags_unresolved_reference(self):
        release = Release("v2", dt(10, 16))
        tests = [TestRecord("T2", "v2", "PASS", dt(10, 10), "acceptance")]
        closures = [ClosureRecord("I2", "CLOSED", dt(10, 12), ("VERIFY-MISSING",))]
        findings = run_checks(release, tests, [], closures, [])
        by_id = {f.rule_id: f.status for f in findings}
        self.assertEqual(by_id["R003"], "PASS")
        self.assertEqual(by_id["R004"], "EVIDENCE_GAP")

    def test_naive_timestamp_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone offset"):
            parse_time("2026-10-10T16:30:00")

    def test_json_report_contains_boundary_and_overall(self):
        release = Release("v2", dt(10, 16))
        tests = [TestRecord("T2", "v2", "PASS", dt(10, 10), "acceptance")]
        findings = run_checks(release, tests, [], [], [])
        report = build_json_report(release, tests, findings)
        self.assertEqual(report["overall"], "PASS")
        self.assertEqual(report["schema_version"], "2")
        self.assertIn("modeled V0.2 relationships", report["interpretation_boundary"])
        self.assertIn("R003 PASS", report["interpretation_boundary"])
        self.assertIn("sufficient test coverage", report["interpretation_boundary"])


if __name__ == "__main__":
    unittest.main()
