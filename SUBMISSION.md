# Submission Summary

Handover Protocol is a GenLayer Intelligent Contract for consensus-backed physical condition handovers. It freezes an accepted condition baseline, records custody intervals and defect lineage, classifies evidence-backed changes under a frozen normal-wear policy, verifies repairs, and exposes a portable condition certificate. Custody attribution is temporal and evidence-scoped; it does not assert legal causation.

## Previous deployment and corrected source status

- Studionet contract: [0xEC5EcdCd93DFf54c0752628Eed0B51F51417222C](https://explorer-studio.genlayer.com/address/0xEC5EcdCd93DFf54c0752628Eed0B51F51417222C)
- Deployment transaction: [0xffcd5a8409041b78a12465633636be4c21c2256f818f1503a0415431842a058c](https://explorer-studio.genlayer.com/tx/0xffcd5a8409041b78a12465633636be4c21c2256f818f1503a0415431842a058c)
- The address above and its funded lifecycle correspond to the prior source commit `f48ea0d`; its deployed-source parity and lifecycle were verified.
- Current working source includes the steward-requested tuple consistency checks, deterministic custody-gap attribution, and fail-closed `MODIFIED` challenge handling; full suite: 89 passed, 3 skipped.
- **Corrected source redeployment is pending signer unlock.** The previous contract must not be represented as containing the current corrections. Updated deployment and verification status is in [`docs/RELEASE_CANDIDATE_VERIFICATION.md`](docs/RELEASE_CANDIDATE_VERIFICATION.md).

## Security and verification boundaries

The Direct Mode suite covers adversarial write authorization, evidence integrity, custody-gap lifecycle checks, unresolved-challenge behavior, repair comparison with the originating observation, and rejection of challenges against repaired findings. Trusted inspector signatures and strict-format SHA-256 digest checks are implemented. Consensus disagreements and unavailable external evidence fail closed; no vision/image path is claimed.

This candidate has a live verified lifecycle and source parity. It has not received a separate third-party audit, hosted CI is not claimed, and there is no standalone GenVM lint result. Remaining boundaries include round-based challenge timing, custody-gap history semantics, and incomplete live coverage of every optional branch. Details: [`docs/RELEASE_CANDIDATE_VERIFICATION.md`](docs/RELEASE_CANDIDATE_VERIFICATION.md) and [`SECURITY.md`](SECURITY.md).
