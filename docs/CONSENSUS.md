# CONSENSUS.md

## Exact nondeterministic calls

| Call site | API | Purpose |
|---|---|---|
| `_fetch_text` | `gl.nondet.web.get(url)` | retrieve evidence text; typed failure (including non-2xx HTTP status) instead of exception or false success |
| `_classify_component` | `gl.nondet.exec_prompt(prompt, response_format="json")` | classify one component's condition/defect-relation/severity/attribution |
| `_classify_repair` | `gl.nondet.exec_prompt(prompt, response_format="json")` | classify whether a repair receipt resolves a defect |
| `_classify_challenge` | `gl.nondet.exec_prompt(prompt, response_format="json")` | reconsider a recorded finding against fresh challenge evidence |

All four are invoked identically from both the leader closure and the
validator closure passed to `gl.vm.run_nondet_unsafe(leader_fn,
validator_fn)` (verified against the installed `genlayer-py-std` v0.2.16
runtime — see `docs/RELEASE_CANDIDATE_VERIFICATION.md`).

## Leader behavior

1. Load the frozen policy (`asset.policy_json`) and candidate open-defect
   IDs for each in-scope component.
2. For each component, retrieve the submitted evidence URL(s) and classify
   with the model.
3. Return a list of typed findings, one per in-scope component, sorted by
   the scope order.

## Validator behavior

Independently repeats step 1–3 using its own retrieval and its own model
call (the Direct Mode mock layer lets both sides see the same
deterministic mocked response, which is how `test_honest_leader_result_is_accepted`
proves the validator is not simply hostile-by-default). It then:

1. Rejects immediately if the leader's result is not a `Return` (i.e. the
   leader errored).
2. Rejects if the finding list length doesn't match scope length, or if any
   component id is missing/duplicated/invented.
3. Re-validates each leader finding's *shape* independently
   (`_validate_finding_shape`): known enums only, real booleans only,
   `matched_defect_id` must be `""` or a real open-defect candidate for
   that component.
4. Compares the **critical fields** between its own and the leader's
   finding, component by component:
   `component_id, condition_class, defect_relation, severity, normal_wear,
   evidence_sufficient, external_failure, attribution_class`, **plus**
   `matched_defect_id` — not itself in `CRITICAL_FIELDS`, but still
   decision-critical because it selects which stored defect record gets
   mutated to `WORSENED`. A leader that agrees on every typed field but
   points `matched_defect_id` at a different, still-valid candidate defect
   for the same component is rejected (HP4, HP7; see
   `test_forged_leader_matches_wrong_candidate_defect_is_rejected`).
   `rationale_codes` and any other prose/explanatory content are
   explicitly *not* compared — they cannot change contract state, so
   stylistic divergence between leader and validator text must not cause a
   spurious disagreement.

## Equivalence

This is a **substantive custom validator**, not `strict_eq` over raw
prose: both sides produce a structured object and only the fields that
drive contract state are required to match exactly. See section 18 of the
master spec — `NORMAL_WEAR` vs `NEW_MAJOR_DAMAGE`, `PRE_EXISTING` vs
`NEW_DAMAGE`, `SAME_DEFECT` vs `NEW_DISTINCT_DEFECT`, `REPAIRED` vs
`NOT_REPAIRED`, `SUPPORTED_AS_NEW_IN_INTERVAL` vs `CUSTODY_GAP`, and
`evidence_sufficient` true vs false are never treated as equivalent.

## Forged-leader defense

`tests/direct/test_handover_consensus.py` uses the Direct Mode
`direct_vm.run_validator(leader_result=...)` cheatcode to feed a forged
leader payload straight at the captured validator closure and proves
rejection for:

- claiming `NORMAL_WEAR` when the validator's own classification is
  `NEW_MAJOR_DAMAGE`;
- claiming `REPAIRED` when the validator cannot even fetch the receipt
  (`EXTERNAL_FAILURE`);
- omitting a critical field (`condition_class`);
- smuggling an unknown enum value (`"TOTALED"`);
- using a truthy string instead of a real boolean for `normal_wear`;
- claiming `SUPPORTED_AS_NEW_IN_INTERVAL` attribution when a custody gap
  is present (the validator's honest answer is `CUSTODY_GAP`);
- matching every critical field honestly but pointing `matched_defect_id`
  at a different, still-valid candidate defect for the same component
  (`test_forged_leader_matches_wrong_candidate_defect_is_rejected`);
- claiming a challenge is `OVERTURNED` when the validator's own
  independent re-fetch of the same challenge evidence fails
  (`test_forged_leader_claims_overturned_when_evidence_is_unreachable_is_rejected`
  — the challenge consensus path has its own leader/validator round in
  `challenge_finding`, not just the condition-classification path).

A final test (`test_honest_leader_result_is_accepted`) proves the validator
is not merely rejecting everything — an honest, matching leader result is
accepted. This also holds live: the Studionet proof in
`docs/DEPLOYMENT.md` recorded several genuinely successful consensus
rounds (`DEFECTS_RECORDED`, `REPAIRED`, `OVERTURNED`) as well as a
genuine disagreement (`UNDETERMINED`).

## Failure semantics

- `_fetch_text` never raises out of itself; a web failure becomes a typed
  `(False, "")` and propagates to `condition_class = "UNAVAILABLE"` /
  `external_failure = True`, never a damage or repair finding (HP14).
- Any exception from `gl.nondet.exec_prompt` is caught and mapped to
  `INCONCLUSIVE`, not silently retried as a different outcome.
- A GenVM-level `UNDETERMINED`/disagreement outcome (the validator function
  returning `False`) terminates the surrounding transaction — it is never
  stored as a finalized contract-level result (HP18); the contract-level
  "could not decide" states (`INCONCLUSIVE`, `EVIDENCE_UNAVAILABLE`) are
  reached only through an *agreed* typed finding that says so.

## Why consensus is load-bearing

Delete `gl.vm.run_nondet_unsafe`/`gl.nondet.*` from `_classify_component`,
`_classify_repair`, and `_classify_challenge`, and the contract can no
longer determine condition change, defect relation, repair resolution, or
challenge reconsideration from evidence text at all — see `DECISION.md`
→ "The delete-GenLayer test".
