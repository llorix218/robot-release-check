# robot-release-check

[![Tests](https://github.com/llorix218/robot-release-check/actions/workflows/test.yml/badge.svg)](https://github.com/llorix218/robot-release-check/actions/workflows/test.yml)

> **Does the declared delivered release line up with the release identifiers in the acceptance evidence you supplied?**

A small, offline checker for a narrow handover problem in robot software delivery: **testing can pass, the declared delivery can change afterward, and the final evidence package may still point to an older release.**

`robot-release-check` checks declarative relationships across a supplied release record, test evidence, post-test changes, closure references, and local verification records. It does **not** independently inspect or identify the actual binary, container, commit, firmware, parameter set, or deployed configuration. It also does not connect to robots, production systems, CI/CD, cloud accounts, or source repositories.

![Synthetic robot release evidence report](docs/assets/demo-report.svg)

## 30-second demo

Requirements: Python 3.10+.

```bash
python -m pip install .
robot-release-check ./examples/late-change \
  --html ./report.html \
  --json ./findings.json
```

The included synthetic example intentionally produces:

```text
ROBOT RELEASE EVIDENCE REVIEW

Declared Delivered Release   v1.4.1
Latest Supplied PASS         v1.4

R001  EVIDENCE_MISMATCH
R002  EVIDENCE_GAP
R003  PASS
R004  EVIDENCE_GAP

OVERALL
REVIEW REQUIRED
```

Why? The example models this supplied evidence:

```text
v1.4
  -> acceptance test PASS
  -> navigation/config changes are recorded against v1.4.1
  -> v1.4.1 is declared for delivery
  -> no qualifying PASS naming v1.4.1 is supplied before delivery
  -> ISSUE-17 is CLOSED with verification-note-17
  -> verification-note-17 resolves locally to release_id v1.4
```

The result does **not** say the robot was unsafe, that testing never happened, or that the actual delivered artifact was independently identified. It says the supplied records do not establish the modeled V0.2 relationships cleanly.

Open `report.html` for the manager-readable report.

## What V0.2 checks

V0.2 intentionally contains exactly four deterministic checks:

| Rule | Check | Finding when supplied evidence does not line up |
| --- | --- | --- |
| R001 | Release/Test Identity Mismatch | `EVIDENCE_MISMATCH` |
| R002 | Change After Last Qualifying Test | `EVIDENCE_GAP` |
| R003 | Closure Without Verification Evidence | `EVIDENCE_GAP` |
| R004 | Verification/Release Binding | `EVIDENCE_GAP` |

### R001

R001 compares the declared `release.json.release_id` with the `release_id` named by the latest supplied qualifying PASS record on or before the declared delivery time.

For V0.2, every `PASS` record placed in `tests.json` is treated as qualifying evidence. Only include PASS records that you intend to use as delivery/acceptance evidence. A PASS completed after the declared delivery time does not qualify for that delivery.

R001 checks **declared identifier consistency**. It does not prove that the real delivered artifact is the artifact named by that identifier.

### R002

R002 uses the latest qualifying PASS **for the declared delivered release itself** as the baseline, then looks for supplied changes for that same release after the baseline and on/before delivery.

If no qualifying PASS for the declared delivered release is supplied, R002 reports an evidence gap rather than borrowing a later PASS from another release.

### R003

R003 checks only whether each supplied CLOSED item contains at least one non-empty `verification_evidence` reference.

R003 does **not** resolve the reference or prove what it verifies.

### R004

R004 resolves each CLOSED item's supplied `verification_evidence` references against `verifications.json` and checks whether at least one referenced local verification record names the declared delivered `release_id`.

R004 is intentionally narrow. It checks local string-ID relationships only. It does **not** validate the referenced artifact's contents, authenticity, signature, completeness, test adequacy, approval authority, or truth.

## Input

A project directory contains five required files.

### `release.json`

```json
{
  "release_id": "v1.4.1",
  "delivered_at": "2026-10-10T16:30:00Z"
}
```

### `tests.json`

```json
[
  {
    "test_id": "SAT-1042",
    "release_id": "v1.4",
    "status": "PASS",
    "completed_at": "2026-10-08T11:00:00Z",
    "test_type": "site_acceptance"
  }
]
```

### `changes.json`

```json
[
  {
    "change_id": "CHG-88",
    "release_id": "v1.4.1",
    "changed_at": "2026-10-09T09:15:00Z",
    "description": "Navigation parameter adjusted after SAT."
  }
]
```

### `closures.json`

```json
[
  {
    "item_id": "ISSUE-17",
    "status": "CLOSED",
    "closed_at": "2026-10-09T18:00:00Z",
    "verification_evidence": ["verification-note-17"]
  }
]
```

### `verifications.json`

```json
[
  {
    "verification_id": "verification-note-17",
    "release_id": "v1.4"
  }
]
```

`verification_id` values must be unique inside `verifications.json`. These records are local relationship data for R004; V0.2 does not fetch or validate external artifacts.

All timestamps must be ISO-8601 and include a timezone, for example `Z` or `+08:00`.

## Reports

```bash
robot-release-check ./examples/late-change \
  --html ./report.html \
  --json ./findings.json
```

The CLI prints a compact text result. The optional HTML output is designed to be readable by project, QA, delivery, and engineering leaders. The JSON output uses report schema version `2` and includes the overall status, the supplied evidence basis, all findings, and the interpretation boundary.

## Exit codes

- `0` — all four modeled checks PASS.
- `1` — at least one `EVIDENCE_GAP` or `EVIDENCE_MISMATCH` was found.
- `2` — the supplied project files could not be parsed or validated.

A `1` is an evidence-review result, not a statement that the physical system failed.

## Interpretation boundary

A finding means the **supplied evidence** does not establish a modeled relationship cleanly. Missing evidence is not proof that an activity never occurred.

Likewise, all four checks passing means only that these modeled V0.2 relationships passed. It does **not** establish:

- the identity of the actual delivered binary, commit, firmware, container, parameter set, or configuration;
- that the acceptance test scope was complete or sufficient;
- that every real-world change was recorded;
- that a verification artifact is authentic, complete, or adequate;
- that every approved deviation was captured;
- that the system is safe, compliant, production-ready, or appropriate to operate.

A stronger handover process may bind release, configuration, test evidence, and approved deviations into one verifiable handover record. V0.2 does **not** define or validate such a manifest, signing scheme, approval model, or authority protocol.

This utility is not a safety certification tool, a compliance opinion, a penetration-testing tool, or a robot-control system.

## Reviewing a real deployment?

I provide fixed-scope, independent, read-only Automation Project Assurance for real robot and automation projects approaching an acceptance, handover, scale-up, or project-closure decision.

The low-friction entry review focuses on **one real decision point** or **one bounded package of redacted evidence** and asks:

> Does the evidence you have support the decision you are about to make?

Typical review areas can include release/configuration identity, supplied test evidence, post-test changes, issue closure, handover evidence, and unresolved assumptions.

**Entry review: USD 499 · 24–48 hours.**

The output is a concise red-flag review covering:
- what the supplied evidence supports;
- which relationships or claims are not established;
- critical ambiguities;
- questions to take back to the supplier or project team;
- prioritized next actions before the decision.

No source code, production-system access, credentials, cloud-account access, or robot access is required.

For independent review inquiries, contact **llorix218@gmail.com**. Do not post confidential project material in a public issue.

## Scope discipline

V0.2 intentionally stops at these four checks. It has no accounts, hosted service, database, robot connector, continuous monitoring, signed-manifest validator, or production integration.

The public checker is deliberately narrow. Broader questions such as test-scope sufficiency, handover completeness, deviation approval, production identity, and authority remain outside the public checker.

## 90-second walkthrough

See [`docs/90_SECOND_DEMO.md`](docs/90_SECOND_DEMO.md).

## License

Licensed under the **Apache License 2.0**. See [`LICENSE`](LICENSE).
