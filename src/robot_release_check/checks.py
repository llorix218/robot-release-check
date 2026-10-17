from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import ChangeRecord, ClosureRecord, Release, TestRecord, latest_qualifying_pass


@dataclass(frozen=True)
class Finding:
    rule_id: str
    title: str
    severity: str
    status: str
    summary: str
    details: tuple[str, ...] = ()


RULES = {
    "R001": "Release/Test Identity Mismatch",
    "R002": "Change After Last Qualifying Test",
    "R003": "Closure Without Verification Evidence",
}


def run_checks(
    release: Release,
    tests: Iterable[TestRecord],
    changes: Iterable[ChangeRecord],
    closures: Iterable[ClosureRecord],
) -> list[Finding]:
    tests = list(tests)
    changes = list(changes)
    closures = list(closures)
    latest_pass = latest_qualifying_pass(tests, not_after=release.delivered_at)

    findings: list[Finding] = []

    # R001: whether the latest supplied qualifying PASS on/before delivery names
    # the same release that is declared as delivered.
    if latest_pass is None:
        findings.append(Finding(
            "R001", RULES["R001"], "HIGH", "EVIDENCE_GAP",
            "No qualifying PASS test evidence on or before delivery was supplied for comparison.",
        ))
    elif latest_pass.release_id != release.release_id:
        findings.append(Finding(
            "R001", RULES["R001"], "CRITICAL", "EVIDENCE_MISMATCH",
            "The delivered release identity does not match the latest supplied qualifying PASS evidence on or before delivery.",
            (
                f"Delivered release: {release.release_id}",
                f"Latest PASS evidence: {latest_pass.release_id} ({latest_pass.test_id})",
            ),
        ))
    else:
        findings.append(Finding(
            "R001", RULES["R001"], "INFO", "PASS",
            "The delivered release identity matches the latest supplied qualifying PASS evidence on or before delivery.",
            (f"Release: {release.release_id}", f"Test: {latest_pass.test_id}"),
        ))

    # R002: only supplied changes associated with the declared delivered release
    # are considered. A later qualifying PASS becomes the new baseline; any
    # delivered-release change after that baseline creates an evidence gap.
    if latest_pass is None:
        findings.append(Finding(
            "R002", RULES["R002"], "HIGH", "EVIDENCE_GAP",
            "Change-after-test analysis cannot be established because no qualifying PASS evidence on or before delivery was supplied.",
        ))
    else:
        post_test_changes = sorted(
            [
                c for c in changes
                if c.release_id == release.release_id
                and latest_pass.completed_at < c.changed_at <= release.delivered_at
            ],
            key=lambda c: c.changed_at,
        )
        if post_test_changes:
            findings.append(Finding(
                "R002", RULES["R002"], "CRITICAL", "EVIDENCE_GAP",
                "Changes to the delivered release were supplied after the latest qualifying PASS, with no later supplied qualifying PASS evidence before delivery.",
                tuple(
                    [f"Latest PASS: {latest_pass.test_id} at {latest_pass.completed_at.isoformat()}"]
                    + [f"Change: {c.change_id} at {c.changed_at.isoformat()} — {c.description}" for c in post_test_changes]
                ),
            ))
        else:
            findings.append(Finding(
                "R002", RULES["R002"], "INFO", "PASS",
                "No delivered-release change after the latest qualifying PASS was established from the supplied evidence.",
            ))

    # R003: any CLOSED item without a non-empty verification evidence reference.
    gaps = [c for c in closures if c.status == "CLOSED" and not c.verification_evidence]
    if gaps:
        findings.append(Finding(
            "R003", RULES["R003"], "HIGH", "EVIDENCE_GAP",
            "One or more CLOSED items have no supplied verification evidence reference.",
            tuple(f"Closure: {c.item_id} at {c.closed_at.isoformat()}" for c in gaps),
        ))
    else:
        findings.append(Finding(
            "R003", RULES["R003"], "INFO", "PASS",
            "Every supplied CLOSED item includes at least one verification evidence reference.",
        ))

    return findings


def overall_status(findings: Iterable[Finding]) -> str:
    statuses = {f.status for f in findings}
    if "EVIDENCE_MISMATCH" in statuses or "EVIDENCE_GAP" in statuses:
        return "REVIEW REQUIRED"
    return "PASS"
