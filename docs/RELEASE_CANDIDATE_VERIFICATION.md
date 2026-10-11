# Release Candidate Verification

## Corrected canonical deployment

- Contract: [0xe53a4b3cEd2B20397F9E749c3D445C0116269599](https://explorer-studio.genlayer.com/address/0xe53a4b3cEd2B20397F9E749c3D445C0116269599)
- Deployment transaction: [0x839bca16fabdb14ab4821c72b66b5ea4062ff511ac65f94b24ea7f020a0fc101](https://explorer-studio.genlayer.com/tx/0x839bca16fabdb14ab4821c72b66b5ea4062ff511ac65f94b24ea7f020a0fc101)
- Contract source commit: `20b67dc`; normalized source SHA-256: `b4749cee7d642f13da9daa1863295610ef54268ef681825d839006fc6eb992d9`.
- Deployment receipt: `FINALIZED`, `MAJORITY_AGREE` (3 AGREE, 2 IDLE).
- `genlayer schema` succeeded; deployed-source parity passed byte-for-byte.

## Steward requests and evidence

1. **Reject/fail closed on inconsistent condition, defect relation, severity, normal-wear, failure, or attribution combinations before mutation.** The contract validates the full findings set and each tuple before applying any finding/checkpoint/defect mutation. Invalid model tuples normalize to `INCONCLUSIVE`. Damage findings with `evidence_sufficient=false` cannot create defects. Focused tests include inconsistent combinations, malformed results, and an insufficient-evidence damage claim.
2. **Recorded custody gaps constrain finding attribution deterministically.** The contract consults the current gap field and append-only event history, rewriting interval-specific model attributions to `CUSTODY_GAP` before validator comparison and state application. The regression deliberately returns a stronger interval attribution from the mock model, then asserts stored defect lineage is `CUSTODY_GAP`.
3. **`MODIFIED` challenge semantics.** `MODIFIED` is removed from the accepted result set because the challenge interface has no structured corrected severity/relation/attribution to persist. Such a model response normalizes to `INCONCLUSIVE`; the test confirms finding status and history remain unchanged. A challenge against a repaired defect is also rejected in the funded lifecycle.

## Verification results

- Full local suite: **89 passed, 3 skipped**.
- Funded lifecycle on the corrected deployment: **1 passed in 581.57s**. It exercised asset and policy setup, baseline acceptance, custody start, return evidence adjudication, repair submission and verification, and a rejected post-repair challenge. Independent readback showed `H1`=`DEFECTS_RECORDED`, `D1`=`REPAIRED`, and the asset certificate `CLEAR` with zero open/unresolved defects and no gap.
- Transaction hashes and finalized receipt votes for deployment and lifecycle are in [`LIVE_LIFECYCLE_TRANSACTIONS.jsonl`](LIVE_LIFECYCLE_TRANSACTIONS.jsonl), summarized in [`DEPLOYMENT.md`](DEPLOYMENT.md).
- `python scripts/preflight.py`: PASS (static checks only); Python compilation and `git diff --check`: PASS.
- No standalone GenVM lint command or hosted CI result is claimed. No separate independent third-party audit is claimed.

## Remaining limits

- The challenge window is bounded by rounds, not wall-clock time.
- Custody-gap history has no independent resolution-evidence workflow; a recorded gap remains consequential.
- Strict SHA-256 checking applies to correctly formatted digests; placeholder hashes are not verified commitments.
- No image/vision evidence is load-bearing.
- The live lifecycle proves the corrected success/repair/post-repair rejection path. It does not prove every optional delegation, gap, disagreement, or unavailable-evidence branch on this deployment.

The canonical contract now matches the corrected source used for these tests. See [`SECURITY.md`](SECURITY.md) and [`DEPLOYMENT.md`](DEPLOYMENT.md) for the detailed controls and on-chain evidence.
