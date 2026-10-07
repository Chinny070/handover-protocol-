# DECISION.md

## Fixed thesis

**Handover Protocol** is a reusable GenLayer primitive that gives physical
assets a consensus-backed chain of condition and custody. It freezes an
accepted condition baseline at handover, tracks condition deltas and
persistent defect lineage across custody intervals, distinguishes normal
wear from material change, attributes supported changes to custody
intervals **without claiming legal causation**, verifies repairs, and
exposes a portable condition certificate for downstream contracts.

This thesis is fixed. This document records *why the primitive is
differentiated from adjacent primitives*, not a replacement search.

## Repeated trust question

> Given a physical asset, a frozen pre-handover condition baseline, a
> defined custody interval, and independently inspectable evidence before
> and after handover, what materially changed — and which custody interval
> first contains enough evidence to support (not prove) that change?

Every downstream dispute about rentals, leases, equipment loans, shared
vehicles, and field equipment is a variant of this question. No single
marketplace or app owns it; it is infrastructure.

## Differentiation (spec section 7)

**vs. Agent Warranty Protocol** — Agent Warranty judges whether an
autonomous software agent fulfilled a promised task (a performance
question about an agent's conduct). Handover Protocol judges physical-asset
condition change across human/organizational custody intervals (a
condition question about an object). Different subject, different
evidence, different state machine.

**vs. Decision Memory Protocol** — Decision Memory preserves and
revalidates prior *decisions* so they can be referenced or re-checked
later. Handover Protocol preserves condition *baselines*, *custody*,
*defects*, *repairs*, and *temporal attribution* — a structural model of
an asset's life, not a decision log.

**vs. Reality Checkpoint Protocol** — Reality Checkpoint produces general
external-state certificates ("is X still true"). Handover Protocol is a
specialization with much more required structure on top: custody-interval
transitions, baseline acceptance handshake, contract-assigned defect
identity with lifecycle, a frozen normal-wear policy, repair closure, and
attribution of a defect to the custody interval that first supports it.
None of that is implied by a generic checkpoint certificate.

**vs. Provenance Engine** — Evidence provenance (where did this evidence
come from, is it tamper-evident) is *supporting infrastructure* inside
Handover Protocol, not the product. The product is the combination of
condition + custody + defect identity + temporal attribution + repair
verification exposed as one certificate.

## The delete-GenLayer test

Delete GenLayer/validators from this contract and ask what breaks:

- Classifying condition change (`UNCHANGED` vs `NEW_MAJOR_DAMAGE`, etc.)
  from free-form evidence text requires semantic judgment — this breaks.
- Matching an after-handover observation to an existing `DEFECT-n` vs.
  calling it a new distinct defect requires semantic judgment — this
  breaks.
- Deciding whether a described change falls inside a frozen normal-wear
  policy's semantic language requires semantic judgment — this breaks.
- Deciding whether repair evidence actually addresses a specific defect
  requires semantic judgment — this breaks.

Everything else — IDs, custody-interval bookkeeping, overlap rejection,
deadline/bound enforcement, certificate field assembly, responsibility
mapping from a frozen policy table — stays deterministic code and would
work (in a degraded, trust-nothing way) without GenLayer. That is the
intended split: GenLayer is used only where it is irreducible.

## Three-consumer test

A downstream contract can rely on `get_condition_certificate` /
`is_handover_clear` without reimplementing any web/LLM/consensus logic,
for example: a deposit-refund contract, an insurance-eligibility gate, and
a resale-trust-score contract (see `docs/INTEGRATION.md` for sketches).

## No economics in v1

No payments, escrow, deposits, insurance pools, slashing, or challenge
bonds are implemented. The primitive's value is condition + custody +
attribution + defect lineage + repair. Downstream contracts can layer
their own economics on top of the certificate this contract exposes.

## Reviewer rejection audit (master spec section 35)

Tried to reject the repo with each listed objection; recorded the actual
answer rather than an assertion.

**"This is just a rental app."** No rental-specific concept (no booking,
pricing, or marketplace logic) exists anywhere in the contract. The three
sketched consumers in `docs/INTEGRATION.md` are a deposit-refund
contract, an insurance-eligibility gate, and a resale-trust-score
contract — none of which is a rental app, and the core contract is
identical for all three.

**"This is just AI comparing photos."** No image/vision input exists in
this release (HP17); evidence is text (rendered pages, structured
checklists, receipts). The model never just "compares" — it classifies
into a closed typed vocabulary, matches against contract-held candidate
defect IDs it cannot invent, and is independently re-derived and cross-
checked by a validator, not accepted as a single call's opinion.

**"This is generic dispute resolution."** A generic dispute resolver has
no baseline-acceptance handshake, no contract-assigned defect identity
with an append-only lifecycle, no custody-interval graph with bounded
delegation, and no frozen normal-wear policy. Handover Protocol has all
four; see `DECISION.md` → differentiation vs. Reality Checkpoint
Protocol above.

**"The model decides liability."** The model never outputs money,
ownership, or a liability verdict (HP5; `_normalize_component_finding`
rejects any response containing fields outside the typed schema). It
outputs `attribution_class` — a fact about which custody interval's
evidence first supports a finding. Mapping that fact to contractual
responsibility is left as an explicit downstream/policy-layer integration
point (see "Responsibility propagation" in `docs/CUSTODY.md`), per
section 13 of the master spec.

**"First observed is falsely treated as caused by."** The attribution
vocabulary never includes a causation word; `FIRST_OBSERVED_IN_INTERVAL`
and `SUPPORTED_AS_NEW_IN_INTERVAL` are the strongest claims made, and
`test_evaluate_return_new_damage_creates_defect` asserts the literal
string `"caused"` never appears in a stored defect event (HP9).

**"Private evidence makes consensus fake."** Every piece of evidence used
in this submission's live Studionet proof is a public
`raw.githubusercontent.com` URL, independently fetched by leader and
validator (confirmed live: a genuine cross-model validator disagreement
occurred on a two-component case — not possible if validators were
trusting the leader's content instead of fetching it themselves). See
`docs/DEPLOYMENT.md`.

**"Visual verification is claimed without runtime support."** Not
claimed anywhere (HP17; `docs/EVIDENCE.md` → "Physical-World
Limitations").

**"The validator only checks JSON."** The validator independently
re-fetches evidence and independently re-runs the same classification
prompt, then compares the resulting typed fields — including
`matched_defect_id`, a decision-critical field not in `CRITICAL_FIELDS`
that a forged leader could otherwise exploit (found and fixed during
review, see `tests/direct/test_handover_consensus.py`).

**"A broken URL becomes damage."** `_fetch_text` checks HTTP status
deterministically (fixed after the live run first exposed the gap — see
`docs/DEPLOYMENT.md`); a 404/5xx never reaches the model as if it were
successful evidence. Proven live: a genuine 404 → `EVIDENCE_UNAVAILABLE`.

**"Normal wear is whatever the model feels like."** Section 4 of the
master spec explicitly assigns "whether change is normal wear under a
frozen policy" to GenLayer/validators, not to deterministic arithmetic —
this is a designed boundary, not a gap. The frozen policy's wear budget
is given to the model as fixed context it cannot alter, and the
classification is cross-validated by an independent validator, not
accepted from a single call.

**"The validator always rejects / only rejects."** Disproven directly:
`test_honest_leader_result_is_accepted` proves an honest, matching leader
result is accepted; the live Studionet proof recorded multiple genuinely
successful consensus rounds (`DEFECTS_RECORDED`, `REPAIRED`,
`OVERTURNED`) alongside the genuine `UNDETERMINED` disagreement.

**"Defects can be rewritten."** `_append_defect_event` only appends
(HP8); `test_worsened_defect_links_to_predecessor_history` and the live
`get_defect_history(D1)` both show the original `OPEN` event preserved
after a later `UNRESOLVED` event is appended.

**"The custody chain is decorative."** `begin_custody` rejects an
overlapping primary custody interval for the same scope (HP2);
`propose_handover`'s delegation path rejects a child scope exceeding its
parent's and a depth beyond `MAX_DELEGATION_DEPTH` (HP11) — both tested
and both real rejections, not advisory warnings.

**"The repo overclaims physical/legal causation."** See "First observed"
above; additionally `docs/EVIDENCE.md` → "Physical-World Limitations"
states explicitly that a content hash proves content identity, not
physical authenticity or capture time/place.

**"Submission claims exceed live proof."** `SUBMISSION.md` → "What is
proven" lists only what `docs/DEPLOYMENT.md` actually records with real
addresses/transaction hashes, and explicitly does not claim "zero
consensus disagreement" — the genuine `UNDETERMINED` case is documented,
not hidden.
