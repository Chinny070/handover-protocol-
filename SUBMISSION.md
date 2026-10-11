# Submission Summary

Handover Protocol is a GenLayer Intelligent Contract for consensus-backed physical condition handovers. It freezes an accepted condition baseline, records custody intervals and defect lineage, classifies evidence-backed changes under a frozen normal-wear policy, verifies repairs, and exposes a portable condition certificate. Custody attribution is temporal and evidence-scoped; it does not assert legal causation.

## Previous deployment and corrected source status

- Studionet contract: [0xe53a4b3cEd2B20397F9E749c3D445C0116269599](https://explorer-studio.genlayer.com/address/0xe53a4b3cEd2B20397F9E749c3D445C0116269599)
- Deployment transaction: [0x839bca16fabdb14ab4821c72b66b5ea4062ff511ac65f94b24ea7f020a0fc101](https://explorer-studio.genlayer.com/tx/0x839bca16fabdb14ab4821c72b66b5ea4062ff511ac65f94b24ea7f020a0fc101)
- Deployed source commit: `20b67dc`; source parity passed.
- Corrected funded lifecycle passed, including return adjudication, repair verification, rejection of a post-repair challenge, and final condition-certificate readback.
- Full suite: 89 passed, 3 skipped; static preflight passed.

## Security and verification boundaries

The Direct Mode suite covers adversarial write authorization, evidence integrity, custody-gap lifecycle checks, unresolved-challenge behavior, repair comparison with the originating observation, and rejection of challenges against repaired findings. Trusted inspector signatures and strict-format SHA-256 digest checks are implemented. Consensus disagreements and unavailable external evidence fail closed; no vision/image path is claimed.

This candidate has a live verified lifecycle and source parity. It has not received a separate third-party audit, hosted CI is not claimed, and there is no standalone GenVM lint result. Remaining boundaries include round-based challenge timing, custody-gap history semantics, and incomplete live coverage of every optional branch. Details: [`docs/RELEASE_CANDIDATE_VERIFICATION.md`](docs/RELEASE_CANDIDATE_VERIFICATION.md) and [`SECURITY.md`](SECURITY.md).
