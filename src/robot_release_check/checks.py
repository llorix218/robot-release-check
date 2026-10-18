from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import (
    ChangeRecord,
    ClosureRecord,
    Release,
    TestRecord,
    VerificationRecord,
    latest_qualifying_pass,
)


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
    "R004": "Verification/Release Binding",
}


def run_checks(
    release: Release,
    tests: Iterable[TestRecord],
    changes: Iterable[ChangeRecord],
    closures: Iterable[ClosureRecord],
    verifications: Iterable[VerificationRecord] = (),
) -> list[Finding]:
    tests = list(tests)
    changes = list(changes)
    closures = list(closures)
    verifications = list(verifications)
    latest_pass = latest_qualifying_pass(tests, not_after=release.delivered_at)
    delivered_release_pass = latest_qualifying_pass(
        tests,
        not_after=release.delivered_at,
        release_id=release.release_id,
    )

    findings: list[Finding] = []

    # R001: compare the declared delivered release_id with the release_id named
    # by the latest supplied qualifying PASS on/before delivery.
    if latest_pass is None:
        findings.append(Finding(
            "R001", RULES["R001"], "HIGH", "EVIDENCE_GAP",
            "No qualifying PASS test evidence on or before delivery was supplied for comparison.",
        ))
    elif latest_pass.release_id != release.release_id:
        findings.append(Finding(
            "R001", RULES["R001"], "CRITICAL", "EVIDENCE_MISMATCH",
            "The declared delivered release_id does not match the release_id in the latest supplied qualifying PASS evidence on or before delivery.",
            (
                f"Declared delivered release_id: {release.release_id}",
                f"Latest supplied PASS release_id: {latest_pass.release_id} ({latest_pass.test_id})",
            ),
        ))
    else:
        findings.append(Finding(
            "R001", RULES["R001"], "INFO", "PASS",
            "The declared delivered release_id matches the release_id in the latest supplied qualifying PASS evidence on or before delivery.",
            (f"Declared release_id: {release.release_id}", f"Test: {latest_pass.test_id}"),
        ))

    # R002: use the latest qualifying PASS for the declared delivered release
    # itself as the change-analysis baseline. This avoids an unrelated release's
    # later PASS shortening the delivered-release observation window.
    if delivered_release_pass is None:
        findings.append(Finding(
            "R002", RULES["R002"], "HIGH", "EVIDENCE_GAP",
            "Change-after-test analysis cannot be established because no qualifying PASS for the declared delivered release was supplied on or before delivery.",
        ))
    else:
        post_test_changes = sorted(
            [
                c for c in changes
                if c.release_id == release.release_id
                and delivered_release_pass.completed_at < c.changed_at <= release.delivered_at
            ],
            key=lambda c: c.changed_at,
        )
        if post_test_changes:
            findings.append(Finding(
                "R002", RULES["R002"], "CRITICAL", "EVIDENCE_GAP",
                "Changes to the declared delivered release were supplied after its latest qualifying PASS, with no later supplied qualifying PASS for that release before delivery.",
                tuple(
                    [f"Delivered-release PASS: {delivered_release_pass.test_id} at {delivered_release_pass.completed_at.isoformat()}"]
                    + [f"Change: {c.change_id} at {c.changed_at.isoformat()} — {c.description}" for c in post_test_changes]
                ),
            ))
        else:
            findings.append(Finding(
                "R002", RULES["R002"], "INFO", "PASS",
                "No supplied change to the declared delivered release was found after its latest qualifying PASS and before delivery.",
                (f"Baseline test: {delivered_release_pass.test_id}",),
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
            "Every supplied CLOSED item includes at least one non-empty verification evidence reference.",
        ))

    # R004: resolve supplied closure references against local verification records
    # and check whether each CLOSED item has at least one referenced record naming
    # the declared delivered release. This is local declarative ID consistency;
    # it does not validate artifact contents, signatures, sufficiency, or truth.
    verification_by_id = {v.verification_id: v for v in verifications}
    binding_gaps: list[str] = []
    for closure in closures:
        if closure.status != "CLOSED":
            continue
        if not closure.verification_evidence:
            binding_gaps.append(
                f"Closure {closure.item_id}: no verification reference was supplied, so release binding is not established"
            )
            continue
        resolved = [verification_by_id[x] for x in closure.verification_evidence if x in verification_by_id]
        if not resolved:
            binding_gaps.append(
                f"Closure {closure.item_id}: none of the supplied references resolve in verifications.json"
            )
            continue
        if not any(v.release_id == release.release_id for v in resolved):
            named = ", ".join(sorted({v.release_id for v in resolved}))
            binding_gaps.append(
                f"Closure {closure.item_id}: resolved verification release_id(s) [{named}] do not include {release.release_id}"
            )

    if binding_gaps:
        findings.append(Finding(
            "R004", RULES["R004"], "HIGH", "EVIDENCE_GAP",
            "One or more CLOSED items lack a supplied verification record that resolves to the declared delivered release_id.",
            tuple(binding_gaps),
        ))
    else:
        findings.append(Finding(
            "R004", RULES["R004"], "INFO", "PASS",
            "Every supplied CLOSED item with verification references resolves to at least one local verification record naming the declared delivered release_id.",
        ))

    return findings


def overall_status(findings: Iterable[Finding]) -> str:
    statuses = {f.status for f in findings}
    if "EVIDENCE_MISMATCH" in statuses or "EVIDENCE_GAP" in statuses:
        return "REVIEW REQUIRED"
    return "PASS"
