# ARCHITECTURE.md

## Lifecycle

```text
Asset + Component Graph
        |
Frozen Baseline + Wear Policy   (seal_asset_definition)
        |
Receiver Acceptance             (propose_handover -> accept_baseline)
        |
Custody Interval                (begin_custody .. delegate_custody*)
        |
Return Evidence                 (submit_return_evidence)
        |
Independent GenLayer Evaluation (evaluate_return: leader + validator)
        |
Condition Delta                 (typed per-component findings)
        |
Defect Identity + Temporal Attribution
        |
Repair / Challenge               (submit_repair/verify_repair, challenge_finding)
        |
Portable Condition Certificate   (get_condition_certificate / is_handover_clear)
```

## Storage model

Six top-level `TreeMap[str, <dataclass>]` tables, keyed by contract-assigned
monotonic IDs (`A1`, `C1`, `H1`, `D1`, `E1`, `CP1`):

- `assets` — one row per physical asset.
- `components` — nodes of the bounded, cycle-free component tree.
- `handovers` — one row per custody interval (including delegated ones).
- `defects` — one row per contract-assigned defect identity.
- `evidence` — one row per submitted evidence pointer.
- `checkpoints` — one row per immutable condition-passport checkpoint.

Per section 27 ("storage rules"), bounded histories that would otherwise
need nested dynamic collections inside a stored dataclass (defect lifecycle
events, ID lists) are instead kept as canonical JSON strings
(`history_json`, `component_ids_json`, etc.) on otherwise-primitive-field
dataclasses. This avoids depending on nested storage-container behavior
that is harder to reason about under GenVM's storage serialization, at the
cost of `json.loads`/`json.dumps` on read/write — acceptable given every
such field is bounded (HP15).

## Deterministic vs. nondeterministic boundary

Every call into `gl.nondet.*` lives in exactly four places: `_fetch_text`
(web retrieval), `_classify_component` (condition/defect/attribution
classification), `_classify_repair` (repair verification), and
`_classify_challenge` (fresh-evidence reconsideration of a recorded
finding). All four nondeterministic entry points are wrapped through
`gl.vm.run_nondet_unsafe(leader_fn, validator_fn)` with a validator that
independently re-derives the same typed finding and compares only the
*critical fields* (never free-text rationale) — see `docs/CONSENSUS.md`.

Everything else — ID assignment, ownership/caller checks, custody overlap
and delegation-scope checks, bound enforcement, defect lifecycle
transitions, checkpoint/digest assembly, certificate field computation — is
ordinary deterministic Python with no model or web call anywhere in the
call graph.

## Public surface

Writes: `register_asset`, `add_component`, `seal_asset_definition`,
`propose_handover`, `add_baseline_evidence`, `accept_baseline`,
`dispute_baseline`, `begin_custody`, `delegate_custody`, `mark_custody_gap`,
`submit_return_evidence`, `evaluate_return`, `challenge_finding`,
`submit_repair`, `verify_repair`, `close_handover`, `cancel_handover`.

Views: `get_asset`, `get_component`, `get_handover`, `get_active_custodian`,
`get_custody_chain`, `get_defect`, `get_defect_history`,
`get_open_defect_count`, `get_condition_certificate`, `is_handover_clear`.

See `docs/INTEGRATION.md` for how a downstream contract would consume these
without reimplementing any web/LLM/consensus logic of its own.
