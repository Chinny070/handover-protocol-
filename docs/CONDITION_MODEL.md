# CONDITION_MODEL.md

## Condition classes

`UNCHANGED, IMPROVED, NORMAL_WEAR, PRE_EXISTING_DEFECT, NEW_MINOR_DAMAGE,
NEW_MAJOR_DAMAGE, NEW_CRITICAL_DAMAGE, WORSENED_EXISTING_DEFECT,
INCONCLUSIVE, UNAVAILABLE`.

## Per-component typed finding

```json
{
  "component_id": "C3",
  "condition_class": "NEW_MINOR_DAMAGE",
  "defect_relation": "NEW_DISTINCT_DEFECT",
  "severity": "MINOR",
  "normal_wear": false,
  "evidence_sufficient": true,
  "external_failure": false,
  "attribution_class": "SUPPORTED_AS_NEW_IN_INTERVAL",
  "matched_defect_id": "",
  "rationale_codes": [2, 7]
}
```

Produced identically by `_classify_component` on both the leader and
validator side; see `docs/CONSENSUS.md`.

## Normal-Wear Policy

Frozen at `seal_asset_definition` time as `asset.policy_json`
(hash recorded as `asset.policy_hash`, HP10). Required top-level keys:
`component_rules`, `wear_budget`, `evidence_minimums`,
`attribution_minimums`, `repair_closure_requirements`, `challenge_window`.
The wear budget is passed into the classification prompt as
untrusted-but-authoritative *policy context* (distinct from the evidence
text, which is always treated as untrusted data — see
`docs/SECURITY.md`); the actual `normal_wear` true/false flag is still a
model judgment, validated by the independent validator exactly like every
other critical field.

## Deterministic application of findings (`_apply_findings`)

Given the agreed list of typed findings for a `RETURN_PENDING` handover:

- `UNAVAILABLE` -> handover trends toward `EVIDENCE_UNAVAILABLE` (if no
  other component has a positive finding).
- `INCONCLUSIVE` -> handover trends toward `INCONCLUSIVE`.
- `UNCHANGED` / `IMPROVED` / `NORMAL_WEAR` / `PRE_EXISTING_DEFECT` -> no
  defect created or mutated.
- `WORSENED_EXISTING_DEFECT` with relation `SAME_DEFECT`/
  `LIKELY_SAME_DEFECT` and a valid `matched_defect_id` -> appends a
  `WORSENED` event to that defect's history and updates its severity.
- `NEW_MINOR_DAMAGE` / `NEW_MAJOR_DAMAGE` / `NEW_CRITICAL_DAMAGE`, or a
  `WORSENED_EXISTING_DEFECT` finding without a resolvable
  `matched_defect_id` -> a brand-new contract-assigned `Defect` is created
  (HP7: the model never invents the ID it attaches a finding to; the
  contract always picks it, and an invented/absent match degrades to a
  fresh defect rather than mutating the wrong one or failing silently).

Terminal handover status is picked deterministically from the aggregate
of findings: `RETURN_CLEAR` (nothing positive), `DEFECTS_RECORDED` (at
least one new/worsened defect), `INCONCLUSIVE`, or `EVIDENCE_UNAVAILABLE`
— in that precedence, new/worsened defects always take priority over a
mere `INCONCLUSIVE`/`UNAVAILABLE` elsewhere in scope.

A `Checkpoint` is created on every `evaluate_return` call, recording
`open_defect_count`/`major_defect_count`/`critical_defect_count` plus
`condition_digest`/`evidence_digest`/`consensus_digest` hashes and whether
a custody gap was present — this is the immutable condition-passport
lineage (section 22 of the master spec).
