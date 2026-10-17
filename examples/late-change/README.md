# Synthetic example: late change after acceptance test

This example is completely synthetic.

Timeline:

1. `v1.4` has supplied acceptance evidence with status `PASS`.
2. Two supplied changes occur afterward and are associated with `v1.4.1`.
3. `v1.4.1` is declared as the delivered release.
4. No later qualifying PASS evidence is supplied before delivery.
5. The supplied CLOSED issue includes a verification-evidence reference.

Expected results:

- R001: `EVIDENCE_MISMATCH`
- R002: `EVIDENCE_GAP`
- R003: `PASS`
- Overall: `REVIEW REQUIRED`

The result is limited to the supplied evidence and does not establish what did or did not happen outside that evidence set.
