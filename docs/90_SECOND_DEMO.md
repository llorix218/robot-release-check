# 90-second demo script

## Goal

Show one problem, one command, one result. Do not explain a larger platform.

## 0–15 seconds — the scenario

> This project passed acceptance testing as `v1.4`. After that, two configuration changes were made and `v1.4.1` was declared for delivery. The supplied package contains no later qualifying PASS evidence before delivery.

Show the four small JSON files in `examples/late-change/`.

## 15–35 seconds — run the tool

```bash
robot-release-check ./examples/late-change --html ./report.html --json ./findings.json
```

The expected process exit code is `1` because review is required.

## 35–60 seconds — read the result

Point only to:

```text
Delivered Release            v1.4.1
Latest Qualifying PASS       v1.4

R001  EVIDENCE_MISMATCH
R002  EVIDENCE_GAP

OVERALL
REVIEW REQUIRED
```

Say:

> The tool is not saying the robot was unsafe or that testing never happened. It is saying the evidence supplied here does not establish that the delivered release is covered by the latest qualifying PASS evidence.

## 60–80 seconds — open the HTML report

Show the three rule rows and the interpretation boundary. Do not spend time on implementation details.

## 80–90 seconds — CTA

> If a real robot deployment is approaching acceptance, the same question can be reviewed against a small redacted evidence set without source code, production access, or robot access.
