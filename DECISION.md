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
