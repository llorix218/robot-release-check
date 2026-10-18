# robot-release-check

[![Tests](https://github.com/llorix218/robot-release-check/actions/workflows/test.yml/badge.svg)](https://github.com/llorix218/robot-release-check/actions/workflows/test.yml)

> **Did the robot release you are delivering actually match the release your acceptance evidence covers?**

A small, offline checker for one handover problem in robot software delivery: **testing can pass, the system can change afterward, and the final acceptance package may still point to the older release.**

`robot-release-check` compares a supplied release, test evidence, post-test changes, and closure evidence. It does **not** connect to robots, production systems, CI/CD, cloud accounts, or source repositories.

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

Delivered Release            v1.4.1
Latest Qualifying PASS       v1.4

R001  EVIDENCE_MISMATCH
R002  EVIDENCE_GAP
R003  PASS

OVERALL
REVIEW REQUIRED
```

Why? The example models this sequence:

```text
v1.4
  -> acceptance test PASS
  -> navigation/config changes
  -> v1.4.1 declared for delivery
  -> no later qualifying PASS evidence supplied before delivery
```

The result does **not** say the robot was unsafe or that testing never happened. It says the supplied evidence does not establish that the delivered release is covered by the latest qualifying PASS evidence.

Open `report.html` for the manager-readable report.

## What V0.1 checks

V0.1 intentionally contains exactly three deterministic checks:

| Rule | Check | Finding when evidence does not line up |
| --- | --- | --- |
| R001 | Release/Test Identity Mismatch | `EVIDENCE_MISMATCH` |
| R002 | Change After Last Qualifying Test | `EVIDENCE_GAP` |
| R003 | Closure Without Verification Evidence | `EVIDENCE_GAP` |

For V0.1, every `PASS` record placed in `tests.json` is treated as qualifying evidence. Only include PASS records that you intend to use as delivery/acceptance evidence. A PASS completed after the declared delivery time does not qualify for that delivery.

For R002, only changes whose `release_id` matches the declared delivered release are evaluated.

For R003, V0.1 checks only whether a closed item supplies a non-empty `verification_evidence` reference. It does **not** resolve the referenced artifact or prove that the verification record is bound to the delivered release. A stale-but-nonempty reference can therefore still pass R003. That is an explicit V0.1 scope boundary, not a claim that the closure is fully verified.

## Input

A project directory contains four required files.

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

All timestamps must be ISO-8601 and include a timezone, for example `Z` or `+08:00`.

## Reports

```bash
robot-release-check ./examples/late-change \
  --html ./report.html \
  --json ./findings.json
```

The CLI prints a compact text result. The optional HTML output is designed to be readable by project, QA, delivery, and engineering leaders. The JSON output includes the overall status, the evidence basis, all findings, and the interpretation boundary.

## Exit codes

- `0` — all three checks PASS.
- `1` — at least one `EVIDENCE_GAP` or `EVIDENCE_MISMATCH` was found.
- `2` — the supplied project files could not be parsed or validated.

A `1` is an evidence-review result, not a statement that the physical system failed.

## Interpretation boundary

A finding means the **supplied evidence** does not establish a relationship cleanly. Missing evidence is not proof that an activity never occurred.

Likewise, all three checks passing means only that these modeled relationships passed the V0.1 rules. It does **not** establish that the acceptance test scope was complete or sufficient, that every delivered configuration was independently bound to the evidence package, or that every approved deviation was captured.

V0.1 does not validate signed handover manifests, cryptographic configuration manifests, approved-deviation registers, or the adequacy of the underlying test plan.

This utility does not determine whether a physical system is safe, whether testing happened outside the supplied evidence, whether a deployment is compliant, or whether a robot should be operated.

It is not a safety certification tool, a compliance opinion, a penetration-testing tool, or a robot-control system.

## Reviewing a real deployment?

I provide fixed-scope, independent, read-only Automation Project Assurance for real robot and automation projects approaching an acceptance, handover, scale-up, or project-closure decision.

The low-friction entry review focuses on **one real decision point** or **one bounded package of redacted evidence** and asks:

> Does the evidence you have actually support the decision you are about to make?

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

V0.1 intentionally stops at these three checks. It has no accounts, hosted service, database, robot connector, continuous monitoring, or production integration.

The public checker is deliberately narrow. Feedback about broader acceptance and handover evidence problems is useful, but those ideas are not automatically part of V0.1.

## 90-second walkthrough

See [`docs/90_SECOND_DEMO.md`](docs/90_SECOND_DEMO.md).

## License

Licensed under the **Apache License 2.0**. See [`LICENSE`](LICENSE).
