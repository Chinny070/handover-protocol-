# REPAIRS.md

## Lifecycle

`submit_repair` requires the defect to be `OPEN`/`WORSENED`/
`PARTIALLY_REPAIRED`, bounded by `MAX_REPAIR_ROUNDS` (5), and moves the
defect to `REPAIR_CLAIMED`. `verify_repair` runs a `run_nondet_unsafe`
round (`_classify_repair`) over the latest repair-receipt evidence and
applies the result deterministically:

| `repair_result` | deterministic effect |
|---|---|
| `REPAIRED` | defect status -> `REPAIRED` |
| `PARTIALLY_REPAIRED` | defect status -> `PARTIALLY_REPAIRED` |
| `NOT_REPAIRED` | defect status -> `OPEN` (or stays `WORSENED` if it was) |
| `INCONCLUSIVE` | **no status change** — left `REPAIR_CLAIMED` |
| `EXTERNAL_FAILURE` | **no status change** — left `REPAIR_CLAIMED` |

A receipt stating "repaired" is evidence, not authority (section 23 of the
master spec): `_classify_repair` feeds the receipt text as untrusted data
into the model and the model's *typed* `repair_result` — not the receipt's
own text — is what the contract trusts, subject to the same independent
validator check as every other consensus call.

## HP14 in practice

`test_repair_receipt_unavailable_is_external_failure_not_repaired` proves
an unreachable receipt resolves to `EXTERNAL_FAILURE` and explicitly does
**not** flip the defect to `REPAIRED` or back to `OPEN` — a failed
observation is kept distinct from both a successful repair and a repair
failure.

## Bounded rounds

`MAX_REPAIR_ROUNDS = 5`; a 6th `submit_repair` call on the same defect is
rejected (`test_repair_round_bound_enforced`). `repair_count` is
incremented on every `verify_repair` call regardless of outcome.
