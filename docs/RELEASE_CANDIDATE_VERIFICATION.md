# RELEASE_CANDIDATE_VERIFICATION.md

## Current candidate

Current candidate address: [0xB0F0509f35846481622d6A3dEcA0601618FFfC34](https://explorer-studio.genlayer.com/address/0xB0F0509f35846481622d6A3dEcA0601618FFfC34)

Deployment transaction: [0xb6fb9266ed849ae415eccca365d1e1725f5cc8eca5791166e4e2fe14c943ce3c](https://explorer-studio.genlayer.com/tx/0xb6fb9266ed849ae415eccca365d1e1725f5cc8eca5791166e4e2fe14c943ce3c)

The deployment receipt was `FINALIZED`, `MAJORITY_AGREE`, with five AGREE votes. The GenLayer CLI returned the 28-method schema. `python scripts/source_parity.py 0xB0F0509f35846481622d6A3dEcA0601618FFfC34` returned PASS against the local contract source; normalized source SHA-256: `7ac07ae241c43ae8685f053e2f261f312e1994637010b588a4bcebe58883b0bf`.

## Local checks

- Baseline Direct Mode before the final integration-file edits: **77 passed**.
- Full default suite before the latest integration-file edits: **77 passed, 5 skipped**. The final repository-wide run after the latest integration-file edits completed: **77 passed, 3 skipped**. The three skipped tests require Studionet RPC access unavailable in the current environment.
- `python scripts/preflight.py`: PASS (static check only).
- `python -m py_compile contracts/handover_protocol.py tests/direct/*.py`: PASS.
- Deployment compiled and the constructor executed successfully. No separate GenVM lint/typecheck command was located in the installed GenLayer CLI.
- No repository CI workflow was found in the cloned checkout; hosted CI status has not been verified.

## Live write lifecycle: not verified

The funded integration test was attempted. It submitted writes, but later receipt calls failed or timed out before `FINALIZED` could be verified. One observed transaction hash was `0x272efa848bf84b51948038f7de5dec3c0fe435a2d76679af922fd8734481e9d0`; its final status was not verified. Do not treat it or any unfinalized write as proof of state transition. The integration harness now waits for `FINALIZED` and does not resubmit when a hash is known, but Studionet RPC availability prevented completion.

No current-candidate evidence is claimed for condition-delta classification, defect lineage, normal-wear/inconclusive outcomes, custody-gap resolution, delegation, repair, challenge, or final clearance. Prior deployment tables in `docs/DEPLOYMENT.md` are historical.

## Release gates still open

1. Complete a funded lifecycle and independently read back all required states using finalized transaction receipts.
2. Finish fixes for repair evidence comparison with the original defect, a verifiable custody-gap resolution path, challenge timing semantics, and sustainable append-only defect history.
3. Complete adversarial tests for these exact paths; rerun the full suite.
4. Run GenVM lint/type/schema/runtime validation and any repository CI available for the final commit.
5. Complete the rejection-oriented review, commit and push the corrected source/docs, then verify deployed-source parity against that committed source.

Historical verification performed against `0x54953F416c4Dc8B80559bb877870Cf636431c658` is not evidence for this candidate's changes.
