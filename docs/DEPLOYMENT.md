# DEPLOYMENT.md

## Status

**Not deployed in this session.** This session's explicit scope was:
repository scaffolding, design docs, contract implementation, and Direct
Mode testing — no live Studionet deployment, no GitHub push, no PR/issue
creation. See `docs/RELEASE_CANDIDATE_VERIFICATION.md` for exactly what
was and was not verified.

## What deployment would require (next session)

1. `genlayer` CLI is already installed and discoverable (`genlayer
   --version` → `0.39.2`; see verification doc). A GenLayer account/signer
   needs to be created or selected (`genlayer account` subcommands) and
   funded on Studionet.
2. `genlayer deploy` (or the `genlayer-test` Studio Mode helpers in
   `gltest.contracts`) against `contracts/handover_protocol.py`, targeting
   the `studionet` network entry already present in `gltest`'s default
   network list.
3. Post-deployment: `scripts/source_parity.py` (stubbed below) should pull
   the deployed contract's source via `genlayer code <address>` and diff
   it byte-for-byte against the committed `contracts/handover_protocol.py`
   at the commit that was deployed.
4. `scripts/live_verify.py` (stubbed below) should drive the minimum live
   lifecycle from section 31 of the master spec: register asset -> define
   components -> freeze policy -> propose baseline -> attach public
   evidence -> accept baseline -> begin custody -> submit return evidence
   -> real validator consensus -> typed condition delta -> defect lineage
   case -> read the Condition Certificate -> at least one negative/
   fail-closed case.

## Canonical vs. disposable

Only one deployment should ever be treated as canonical (the one recorded
in `docs/RELEASE_CANDIDATE_VERIFICATION.md` once it exists); anything
deployed while iterating is disposable and must not be referenced from
README/SUBMISSION.
