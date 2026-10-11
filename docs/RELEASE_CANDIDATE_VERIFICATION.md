# Release Candidate Verification

## Previously verified deployment

- Contract: [0xEC5EcdCd93DFf54c0752628Eed0B51F51417222C](https://explorer-studio.genlayer.com/address/0xEC5EcdCd93DFf54c0752628Eed0B51F51417222C)
- Deployment transaction: [0xffcd5a8409041b78a12465633636be4c21c2256f818f1503a0415431842a058c](https://explorer-studio.genlayer.com/tx/0xffcd5a8409041b78a12465633636be4c21c2256f818f1503a0415431842a058c)
- Source commit: `f48ea0d`; normalized source SHA-256: `3c8637329f0ab0d4c341a5bf266690777fa2d10f8fb4f8de85fdb640c9c12957`.
- Deployment finalized with `MAJORITY_AGREE` (3 AGREE, 2 IDLE); current schema query succeeded and source parity passed.

The contract at this address predates the steward-requested cross-field
finding validation, deterministic custody-gap attribution override, and
removal of the unpersistable `MODIFIED` challenge result. It is not the
source currently in this working tree and must not be presented as
containing those corrections.

## Steward-requested correction candidate

The current source adds complete semantic-tuple validation before any
finding/checkpoint/defect mutation; deterministic rewriting of interval
attribution to `CUSTODY_GAP` whenever the handover gap state or append-only
history records uncertainty; and fail-closed handling of `MODIFIED` as
`INCONCLUSIVE` because no correction payload exists to persist. Focused
regressions cover inconsistent fields, unsubstantiated damage, gap
attribution overriding stronger model claims, and unchanged state/history
for `MODIFIED` output.

**Deployment status: pending.** The existing Studionet account is listed,
but its private key is not currently cached in the OS keychain and the
GenLayer CLI requires the account keystore password to unlock it. No new
deployment, deployed-source parity for these changes, or matching live
transaction evidence is claimed yet. After the signer is unlocked, deploy
this exact source, verify FINALIZED receipt, schema, source parity, and run
the focused live checks before resubmission.

## Test and live verification

- Previously deployed source suite: **80 passed, 3 skipped**. Current corrected source suite: **89 passed, 3 skipped**.
- Funded lifecycle against the previous deployment: **1 passed**. It finalized the asset/handover writes, submitted and adjudicated return evidence, verified a repair, rejected a post-repair challenge, and independently read back the handover, defect/repair, and certificate state. This is evidence for the previous source only. Per-action transaction hashes and receipt votes are in [`LIVE_LIFECYCLE_TRANSACTIONS.jsonl`](LIVE_LIFECYCLE_TRANSACTIONS.jsonl) and summarized in [`DEPLOYMENT.md`](DEPLOYMENT.md).
- `python scripts/preflight.py`: PASS (static checks only).
- Deployed source parity for the previous source: PASS, byte-for-byte after line-ending normalization. Parity for the corrected source is pending deployment.
- No standalone GenVM lint command or hosted CI result is claimed; local preflight explicitly requires a running node for full runtime schema validation.

## Adversarial review performed

The implementation and direct tests were reviewed against authorization, lifecycle, evidence-integrity, and resolution attacks. In the corrected source, complete typed tuples are checked before state application, recorded custody gaps override interval-specific attribution deterministically, and unsupported `MODIFIED` challenges become `INCONCLUSIVE` without state mutation. Existing controls include owner-only primary handover origination; party- and lifecycle-scoped writes; strict digest verification for well-formed SHA-256 commitments; trusted-inspector signatures; evidence-to-policy binding; and repair comparison against the originating observation. External evidence failure fails closed and does not consume a challenge round. A resolved finding cannot be reopened by a post-repair challenge.

Full details are in `tests/direct/test_handover_authorization.py`, `test_handover_custody.py`, `test_handover_defects.py`, `test_handover_repairs.py`, and related Direct Mode tests. A separate outside reviewer/steward was not run; this is an implementation-level adversarial pass, not an independent third-party audit.

## Remaining release limitations

- The challenge window is bounded by rounds, not wall-clock time.
- Custody-gap history remains party-updatable under its authorization/lifecycle rules; independent resolution evidence is not implemented as an append-only adjudication mechanism.
- High-assurance inspector signing is supported for trusted inspectors. Other declared source-quality tiers are not cryptographically attested.
- SHA-256 comparison is enforced only when the submitted digest has the required strict format; other fixture digests are treated as unverified commitments.
- No image/vision evidence is load-bearing. No claim is made that the current GenLayer runtime can fetch and consistently adjudicate image bytes.
- The live lifecycle exercises the canonical success/repair/rejection path. It does not by itself demonstrate every delegation, custody-gap, protocol-disagreement, or unavailable-evidence branch on this deployment.

The corrected source is not ready for resubmission until signer access permits deployment and source parity verification. See [`SECURITY.md`](../SECURITY.md) and [`DEPLOYMENT.md`](DEPLOYMENT.md) for threat assumptions and exact transaction evidence.
