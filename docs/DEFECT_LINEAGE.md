# DEFECT_LINEAGE.md

## Identity (HP7)

`defect_id` values are always `DEFECT_count`-derived contract IDs
(`D1`, `D2`, ...), assigned only inside `_apply_findings`. A model finding
may reference a candidate defect via `matched_defect_id`, but:

- the candidate set offered to the model is always a contract-computed
  list of currently-open defects for that specific component
  (`candidates_by_component`);
- `_normalize_component_finding` rejects (fails closed to `INCONCLUSIVE`)
  any `matched_defect_id` that is not `""` or not in that candidate list —
  the model can never invent or redirect to an arbitrary defect id;
- `_validate_finding_shape` re-checks the same constraint independently on
  the validator side.

## Lifecycle

```text
OPEN -> WORSENED -> REPAIR_CLAIMED -> REPAIRED / PARTIALLY_REPAIRED / NOT_REPAIRED
                                    \-> (verify_repair INCONCLUSIVE/EXTERNAL_FAILURE: no transition)
(any open status) --challenge_finding(OVERTURNED)--> UNRESOLVED
```

Every transition appends to `history_json` via `_append_defect_event`
(bounded to `MAX_DEFECT_HISTORY_EVENTS`); no transition ever removes or
overwrites a prior event (HP8) — `test_worsened_defect_links_to_predecessor_history`
proves the original `OPEN` event with its original attribution class is
still present and first after a later `WORSENED` event is appended.

## Worsening vs. new-distinct

A `WORSENED_EXISTING_DEFECT` finding with `defect_relation` in
(`SAME_DEFECT`, `LIKELY_SAME_DEFECT`) and a valid `matched_defect_id`
mutates the existing defect's severity/status in place and records a
`WORSENED` event. Every other positive finding (`NEW_MINOR_DAMAGE`,
`NEW_MAJOR_DAMAGE`, `NEW_CRITICAL_DAMAGE`, or a worsening claim without a
resolvable match) creates a fresh `Defect` — see
`docs/CONDITION_MODEL.md` → "Deterministic application of findings".

## Challenges (bounded, HP12)

`challenge_finding(defect_id, reason_code, evidence_kind, source_url,
content_hash)` takes fresh, independently retrievable evidence as part of
the challenge itself. `_classify_challenge` runs its own
`run_nondet_unsafe` round: it independently fetches that evidence
(`_fetch_text`, same HP14 fail-closed-on-non-2xx behavior as condition
classification) and asks the model to reconsider the recorded finding
against it, returning one of `UPHELD, MODIFIED, OVERTURNED, INCONCLUSIVE,
EXTERNAL_FAILURE`. Without evidence, or when the evidence is unreachable,
the result can only be `EXTERNAL_FAILURE`/`INCONCLUSIVE` — never
`UPHELD`/`MODIFIED`/`OVERTURNED` on reason-code rhetoric alone. The
validator independently re-fetches the same evidence URL and re-derives
its own result; a forged leader claiming `OVERTURNED` when the validator's
own fetch fails is rejected
(`test_forged_leader_claims_overturned_when_evidence_is_unreachable_is_rejected`
in `tests/direct/test_handover_consensus.py`).

`challenge_count` is capped at `MAX_CHALLENGE_ROUNDS` (3); a fourth call
is rejected outright (`test_max_challenge_rounds_bounded`). `OVERTURNED`
moves the defect to `UNRESOLVED` (append-only history, original record
untouched); `UPHELD`/`INCONCLUSIVE`/`EXTERNAL_FAILURE` leave status
unchanged beyond the round counter.
