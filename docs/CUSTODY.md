# CUSTODY.md

## Handover record fields

`handover_id, asset_id, from_party, to_party, parent_handover_id,
delegation_depth, scope (component ids), status, baseline/return evidence
id lists, acceptance_status, start_time, end_time, custody_gap,
checkpoint_id`.

## Baseline lock + acceptance handshake

```text
DRAFT -> BASELINE_PROPOSED -> ACCEPTED -> ACTIVE
                           -> BASELINE_DISPUTED
                           -> CANCELLED
```

`accept_baseline`/`dispute_baseline` may only be called by `to_party`,
only while `status == BASELINE_PROPOSED` — any later call (HP1) is
rejected with "baseline already resolved". `tests/direct/
test_handover_protocol.py::test_baseline_propose_accept_and_immutability`
proves double-acceptance and post-acceptance disputes are both rejected.

## Custody continuity (HP2)

`propose_handover` rejects a new *primary* (non-delegated) handover whose
scope overlaps the asset's current `active_handover_id` scope. Once that
active handover reaches a terminal evaluated state
(`RETURN_CLEAR`/`DEFECTS_RECORDED`/`INCONCLUSIVE`/`EVIDENCE_UNAVAILABLE`),
`asset.active_handover_id` is cleared and the scope becomes available
again — proven by `test_custody_begin_end_and_overlap_rejection`.

## Delegated custody (HP11)

`propose_handover(..., parent_handover_id=X)`:

- requires the parent handover to be `ACTIVE` and the caller to be its
  current `to_party`;
- requires the delegated scope to be a subset of the parent's scope
  (`set(scope).issubset(parent_scope)`);
- increments `delegation_depth` from the parent and rejects once it would
  exceed `MAX_DELEGATION_DEPTH` (4).

Both checks are proven directly in `tests/direct/test_handover_custody.py`
(`test_delegated_custody_scope_subset_enforced`,
`test_delegation_depth_bound`).

## Custody gaps (HP3)

`mark_custody_gap(handover_id, gap_state)` deterministically records one
of `NO_GAP | PARTIAL_GAP | CUSTODY_GAP | UNKNOWN` on the handover. There is
no code path that infers or defaults a gap classification onto the
"nearest known holder" — the gap is either explicitly recorded or it
remains `NO_GAP`. A recorded gap propagates into
`get_condition_certificate` as `custody_gap_present` and
`certificate_status = "GAP_PRESENT"`, which takes priority over
severity-based status. Separately, the model's own `attribution_class`
output can independently be `CUSTODY_GAP` for a specific finding, and the
validator's forged-leader test proves a leader cannot claim
`SUPPORTED_AS_NEW_IN_INTERVAL` attribution when the honest classification
is `CUSTODY_GAP` (`docs/CONSENSUS.md`).

## Responsibility propagation

This release implements attribution (which custody interval's evidence
first supports a finding) and leaves contractual *responsibility* mapping
as an explicit integration point: `origin_class`/`attribution_class` on
each `Defect` is the frozen, typed fact a downstream contract or a future
policy layer maps to responsibility, rather than this contract making that
judgment call itself (see `DECISION.md` and section 13 of the master
spec — "the semantic consensus outputs attribution, deterministic policy
outputs responsibility state").
