# Handover Protocol

**Release status: canonical Studionet deployment and funded lifecycle verified.** The canonical contract, deployment receipt, live lifecycle transactions, and remaining release limitations are recorded in [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) and [`docs/RELEASE_CANDIDATE_VERIFICATION.md`](docs/RELEASE_CANDIDATE_VERIFICATION.md).

**Consensus-backed condition and custody certificates for physical
assets.**

A reusable GenLayer Intelligent Contract primitive that freezes an
accepted physical-asset condition baseline at handover, tracks custody and
defect lineage across every subsequent custody interval, distinguishes
normal wear from material change, attributes supported changes to custody
intervals **without claiming legal causation**, verifies repairs, and
exposes a portable, machine-readable condition certificate for downstream
contracts.

## Problem

Every rental, lease, equipment loan, or shared-vehicle dispute reduces to
the same question: *what changed while this was in someone else's
custody, and how confident can we be about when it changed?* Today that
question is answered (if at all) by unverifiable photos, memory, and
goodwill. Handover Protocol answers it with consensus-backed, typed,
append-only state.

## Why GenLayer

Classifying condition change, matching a defect to prior history,
deciding whether a change is normal wear or material damage, judging
evidence sufficiency, and deciding whether a repair receipt resolves a
defect are all **irreducible semantic judgments** over free-form evidence
text — no deterministic rule can safely make these calls. Everything else
(IDs, custody bookkeeping, bounds, state transitions, certificate
assembly) is ordinary deterministic code. See `DECISION.md` → "the
delete-GenLayer test".

## Delete GenLayer: what breaks?

Classifying a component's condition from inspection text, matching an
observation to an existing defect, judging normal-wear-vs-material under a
frozen policy, and judging whether repair evidence resolves a defect — all
of that breaks. ID assignment, ownership/custody bookkeeping, bound
enforcement, and certificate computation keep working (in a
trust-nothing, non-consensus-backed way).

## Why this is not a rejected pattern

This is not a generic "AI oracle" or a rental marketplace. See
`DECISION.md` for the explicit differentiation from Agent Warranty
Protocol, Decision Memory Protocol, Reality Checkpoint Protocol, and
Provenance Engine, and the three-consumer test proving the certificate is
genuinely reusable (`docs/INTEGRATION.md`).

## State machine

```text
Asset + Component Graph
        |
Frozen Baseline + Wear Policy
        |
Receiver Acceptance
        |
Custody Interval
        |
Return Evidence
        |
Independent GenLayer Evaluation
        |
Condition Delta
        |
Defect Identity + Temporal Attribution
        |
Repair / Challenge
        |
Portable Condition Certificate
```

Full handover/defect/repair state machines: `docs/ARCHITECTURE.md`,
`docs/CONDITION_MODEL.md`, `docs/DEFECT_LINEAGE.md`, `docs/REPAIRS.md`.

## Contract surface

Writes: `register_asset, add_component, seal_asset_definition,
propose_handover, add_baseline_evidence, accept_baseline, dispute_baseline,
begin_custody, delegate_custody, mark_custody_gap, submit_return_evidence,
evaluate_return, challenge_finding(defect_id, reason_code, evidence_kind,
source_url, content_hash), submit_repair, verify_repair, close_handover,
cancel_handover`.

Views: `get_asset, get_component, get_handover, get_custody_gap_history,
get_active_custodian, get_custody_chain, get_defect, get_defect_history,
get_open_defect_count, get_condition_certificate, is_handover_clear`.

## Nondeterministic operations

Exactly four call sites touch `gl.nondet.*`: evidence retrieval
(`gl.nondet.web.get`), per-component condition/defect/attribution
classification, repair-receipt classification, and challenge
re-evaluation against fresh evidence (the latter three via
`gl.nondet.exec_prompt`). All are wrapped in a **custom**
`gl.vm.run_nondet_unsafe(leader_fn, validator_fn)` consensus call — not
`strict_eq` over raw prose — where the validator independently re-derives
the same typed finding and compares only decision-critical fields. See
`docs/CONSENSUS.md`.

## Deterministic responsibilities

IDs, ownership/caller checks, custody-overlap and delegation-scope
enforcement, all numeric bounds, defect lifecycle transitions, checkpoint/
digest assembly, and certificate field computation. See
`docs/INVARIANTS.md` (18 named invariants, each covered by a test).

## Authorization

Every write method that mutates handover or defect state requires the
caller to be an actual party to it: the asset owner for a primary
`propose_handover`, the current custodian for `submit_return_evidence`,
a party to the handover for `add_baseline_evidence`/`begin_custody`/
`mark_custody_gap`/`evaluate_return`/`close_handover`, and a party to the
defect's originating custody interval for `challenge_finding`/
`submit_repair`/`verify_repair`. Proven with a stranger/owner/custodian
matrix in `tests/direct/test_handover_authorization.py` and live on
Studionet (see `docs/DEPLOYMENT.md` → "Security review fixes").

## Equivalence / validator design

See `docs/CONSENSUS.md`. Proven directly with eight forged-leader
rejection cases plus one honest-acceptance sanity check in
`tests/direct/test_handover_consensus.py`, using `gltest`'s
`direct_vm.run_validator` cheatcode.

## Safety / failure semantics

Every malformed/adversarial model output and every unreachable evidence
source fails closed (never to a positive, damage-free, or repair-success
outcome). See `docs/SECURITY.md`, `docs/INVARIANTS.md` (HP14, HP18), and
the 15-test adversarial-parsing matrix in
`tests/direct/test_handover_hardening.py`.

## Reuse surface

Three sketched downstream consumers (deposit refund, insurance
eligibility, resale trust score), each reading only
`get_condition_certificate`/`is_handover_clear`/`get_custody_chain` with no
web/LLM/consensus logic of their own: `docs/INTEGRATION.md`.

## Limitations

- No economics (payments/escrow/deposits/slashing) in v1 by design.
- No image/vision verification claimed as load-bearing (HP17).
- `content_hash` is cross-verified against fetched bytes only when
  submitted in strict sha256-digest form; otherwise unverified by design
  — see `docs/SECURITY.md`.
- `trusted_inspectors` cryptographically verifies a signature, not a
  real-world inspector's identity or credentials — that binding is the
  policy owner's off-chain responsibility.

## Verification

The current candidate is deployed, but it is **not release verified**. The deployment receipt and deployed-source parity were checked; the funded write lifecycle against this candidate did not reach a verified final state because Studionet receipt polling timed out. Historical lifecycle records below describe older deployments only. See `docs/DEPLOYMENT.md` and `docs/RELEASE_CANDIDATE_VERIFICATION.md` for exact addresses, hashes, checks, and open gates.

Latest local results before the current final rerun: Direct Mode 77 passed; the full suite and network integrations require rerunning. `scripts/preflight.py` and Python compilation passed. The installed CLI exposed deployment/schema validation but no separate GenVM lint command. High-assurance signatures are checked against frozen trusted inspector keys; strict SHA-256 content hashes are checked against fetched bytes. These properties are not represented as live lifecycle proof for the current deployment.

The funded write test is opt-in because it submits real transactions:

`HANDOVER_RUN_FUNDED_LIFECYCLE=1 pytest tests/integration/test_handover_studionet_write_lifecycle.py -v`

```bash
py -3.12 -m venv .venv-test
.venv-test\Scripts\Activate.ps1   # or: source .venv-test/bin/activate
python -m pip install -r requirements-test.txt
pytest tests/direct/ -v
```

## Reviewer fast path

1. Read `DECISION.md` (why this primitive, why GenLayer, differentiation).
2. Read `docs/INVARIANTS.md` (18 invariants; grep test files for the `HP`
   tag referenced in each test's docstring/comment).
3. Run `pytest tests/direct/ -v` (current count is recorded in release verification).
4. Read `docs/CONSENSUS.md` and `tests/direct/test_handover_consensus.py`
   for the forged-leader proof.
