# v0.1.0

Initial public release of `robot-release-check`.

## Scope

This release intentionally contains exactly three deterministic evidence-consistency checks:

- R001 — Release/Test Identity Mismatch
- R002 — Change After Last Qualifying Test
- R003 — Closure Without Verification Evidence

It includes a local CLI, JSON output, a manager-readable HTML report, and one synthetic late-change example.

## Interpretation boundary

Findings describe gaps or mismatches in the supplied evidence only. They do not establish that a physical system was unsafe, untested, incorrectly deployed, or non-compliant.

## License

Apache License 2.0.
