# SUBMISSION.md

## Title

**Handover Protocol — condition and custody evidence for physical assets**

## Portal one-liner

A GenLayer Intelligent Contract that freezes digest-bound baseline evidence, compares it with return evidence, tracks custody and defect lineage, and issues lifecycle-aware condition certificates without asserting legal causation.

## Current release status

**Not submission-ready.** A fresh candidate was deployed to Studionet at [`0xB0F0509f35846481622d6A3dEcA0601618FFfC34`](https://explorer-studio.genlayer.com/address/0xB0F0509f35846481622d6A3dEcA0601618FFfC34). Its deployment transaction finalized with five agreeing validators and local deployed-source parity passed. The required funded lifecycle did not complete: Studionet RPC receipt queries timed out after writes returned transaction hashes. No live condition delta, defect lineage, repair, challenge, gap resolution, or final certificate claim is made for this candidate. See `docs/DEPLOYMENT.md`.

## What has been verified locally

- Baseline acceptance requires SHA-256-bound evidence for every component in scope and freezes the evidence references and digests.
- Return assessment independently retrieves the accepted baseline and return observations; changed or unavailable bytes fail closed.
- Premature certificates do not report `CLEAR`; recorded custody gaps cannot be cleared through a unilateral `NO_GAP` write.
- Frozen policy schema validation and enforcement now cover evidence assurance, attribution evidence minimums, repair receipt requirements, and challenge-round limits.
- Direct Mode: **77 passed**. Repository-wide default suite before the latest integration-test rewrite: **77 passed, 5 skipped**. A fresh full-suite run remains required.
- Static preflight passed; the fresh deployment compiled and successfully executed its constructor; schema and deployed-source parity checks passed.

## Remaining release gates

- Finish and independently read back the funded Studionet write lifecycle, then record only finalized transactions and their validator outcomes.
- Resolve the remaining design gaps in challenge timing, independent custody-gap resolution, repair comparison against original defect evidence, and sustainable append-only defect history.
- Run GenVM lint/type/schema/runtime checks and the repository CI on the final commit.
- Complete the rejection-oriented adversarial review, update all docs to that exact source commit, push it, and re-check parity.

## Explicit limitations

No image/vision verification, legal causation, physical truth, commercial agreement, or repair authenticity is claimed. Accessible HTTPS content is not by itself an attestation. The older lifecycle evidence in `docs/DEPLOYMENT.md` belongs to superseded deployments and is not proof for the current candidate.
