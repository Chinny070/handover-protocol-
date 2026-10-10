# INVARIANTS.md

These invariants are binding on `contracts/handover_protocol.py`. Every
invariant below is covered by at least one test in `tests/direct/`.

**HP1 � Evidence-backed Baseline Immutability.**
Acceptance requires digest-bound evidence covering every scoped component and freezes each evidence ID, URL, kind, and SHA-256 digest in `baseline_snapshot_json`. Return evaluation independently re-fetches baseline and return records and fails closed if either digest does not match. Semantic comparison happens at return time; acceptance alone does not claim a verified physical condition.

**HP2 — Custody Continuity.**
No two `ACTIVE` primary custody intervals may exist for the same asset
scope at the same time. Enforced by: `begin_custody` checks the current
active-custodian slot for the scope before activating a new interval.

**HP3 — Custody Gap Honesty.**
If custody/evidence continuity cannot be established, the contract
records `CUSTODY_GAP` / `PARTIAL_GAP` / `UNKNOWN` rather than assigning
the gap to the nearest known custodian. No deterministic code path may
default a gap to an attribution class other than `CUSTODY_GAP`/`UNKNOWN`.

**HP4 — Evidence Independence.**
Leader and validator both retrieve/evaluate evidence independently from
`evidence_id` pointers. The contract never substitutes the leader's
retrieved content for the validator's retrieval; Direct Mode tests prove
a forged leader result is rejectable by an independent validator run.

**HP5 — Model Boundary.**
GenLayer/validators return only typed semantic findings (condition class,
defect relation, severity, normal-wear flag, evidence-sufficiency flag,
attribution class, repair result, rationale codes). They never return
owner, custodian, legal liability, money amounts, defect IDs, or handover
IDs. Output parsing rejects any response that includes such fields.

**HP6 — Deterministic State Transition.**
Given a set of typed findings, the resulting contract state transition
(defect status, checkpoint creation, certificate fields, responsibility
state) is pure deterministic code over frozen policy — no model call
participates in choosing the transition itself.

**HP7 — Defect Identity Integrity.**
`defect_id` values are always contract-assigned monotonic IDs
(`DEFECT-<n>`). A model-returned "defect id" field is never trusted;
matching to an existing defect is expressed as a *relation classification*
(`SAME_DEFECT` / `LIKELY_SAME_DEFECT` / `NEW_DISTINCT_DEFECT` /
`INSUFFICIENT_EVIDENCE`) over contract-held candidate IDs, and the
contract — not the model — picks the concrete ID to attach the finding to.

**HP8 — Defect History Immutability.**
A defect's lifecycle events are appended and never deleted or overwritten. At the fixed bound, new events are rejected rather than silently truncating prior provenance.

**HP9 — Temporal Attribution Honesty.**
Attribution classes (`PRE_EXISTING`, `FIRST_OBSERVED_IN_INTERVAL`,
`SUPPORTED_AS_NEW_IN_INTERVAL`, `WORSENED_IN_INTERVAL`,
`CONTINUATION_OF_PRIOR_DEFECT`, `UNKNOWN_ORIGIN`, `CUSTODY_GAP`,
`INSUFFICIENT_EVIDENCE`, `EXTERNAL_FAILURE`) are the only attribution
vocabulary the contract stores or exposes. No field, docstring, or
certificate value may claim causation ("X caused the damage").

**HP10 — Normal-Wear Policy Immutability.**
The normal-wear policy (component rules, wear budgets, severity mapping,
evidence minimums, attribution minimums, repair closure requirements,
challenge window) is frozen at `seal_asset_definition`/baseline-propose
time and cannot change for the life of the asset's active baseline.

**HP11 — Delegation Conservation.**
A delegated child custody interval's scope must be a subset of its
parent's scope (`child_scope ⊆ parent_scope`), and `delegation_depth` is
bounded by `MAX_DELEGATION_DEPTH`. Both are checked at `delegate_custody`
time and rejected otherwise.

**HP12 — Challenge Boundedness.**
Each finding may be challenged at most `MAX_CHALLENGE_ROUNDS` times.
Challenge resolution is terminal per round; there is no infinite mutable
reconsideration loop.

**HP13 — Evidence Identity Separation.**
`evidence_id` is a contract-assigned stable identifier. Model rationale
text is stored separately (`rationale_codes`, bounded strings) and is
never used as or folded into an identity field.

**HP14 — External Failure Separation.**
`EXTERNAL_FAILURE` (source unreachable, render failure, parse failure) is
a distinct typed outcome from any damage/breach/repair-failure outcome.
A failed observation can never silently become `NORMAL_WEAR`, a
successful repair, or a new defect.

**HP15 — Resource Bounds.**
All of: component count, evidence items per checkpoint, defects per
asset, handover history length, delegation depth, challenge rounds per
finding, repair rounds per defect, and raw source-text length passed to a
model are bounded by named constants. No write path performs unbounded
iteration over full contract history.

**HP16 — Certificate Integrity.**
`get_condition_certificate` and `is_handover_clear` are computed only from
canonical stored state (current defects, current custodian, baseline/
policy hashes, custody-gap flag) — never from transient/unconfirmed model
output.

**HP17 — Visual Claim Honesty.**
This release does not claim native image/vision verification as
load-bearing. Evidence is text/structured (web-rendered inspection pages,
structured checklists, service/repair records). See
`docs/EVIDENCE.md` → "Physical-World Limitations".

**HP18 — Protocol/Contract Uncertainty Separation.**
A GenVM-level `UNDETERMINED` consensus outcome is not stored as a
finalized contract-level result. The contract-level terminal states for
"could not decide" are explicit (`INCONCLUSIVE`, `EVIDENCE_UNAVAILABLE`,
`UNVERIFIABLE`) and are distinct from a never-executed/undetermined
transaction.
