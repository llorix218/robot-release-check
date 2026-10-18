# 90-second demo script

## Goal

Show one narrow evidence-consistency problem, one command, one result. Do not explain or imply a larger platform.

## 0–15 seconds — the scenario

> The supplied project records show an acceptance PASS for `v1.4`. Later changes are recorded against `v1.4.1`, which is then declared for delivery. No qualifying PASS naming `v1.4.1` is supplied before delivery. The closed issue references `verification-note-17`, but the local verification record names `v1.4`, not `v1.4.1`.

Show the five small JSON files in `examples/late-change/`.

## 15–35 seconds — run the tool

```bash
robot-release-check ./examples/late-change --html ./report.html --json ./findings.json
```

The expected process exit code is `1` because review is required.

## 35–60 seconds — read the result

Point only to:

```text
Declared Delivered Release   v1.4.1
Latest Supplied PASS         v1.4

R001  EVIDENCE_MISMATCH
R002  EVIDENCE_GAP
R003  PASS
R004  EVIDENCE_GAP

OVERALL
REVIEW REQUIRED
```

Say:

> The tool is not identifying the actual deployed artifact and it is not saying the robot was unsafe or that testing never happened. It is saying the supplied records do not establish these four modeled evidence relationships cleanly.

## 60–80 seconds — open the HTML report

Show the four rule rows and the interpretation boundary. Point out that R003 only checks reference presence and R004 only checks local reference-to-release-ID binding.

Do not claim that PASS proves sufficient test coverage, artifact identity, safety, compliance, or production readiness.

## 80–90 seconds — CTA

> If a real robot or automation project is approaching acceptance or handover, a bounded independent review can examine one decision point or redacted evidence package without source code, production access, credentials, or robot access.
