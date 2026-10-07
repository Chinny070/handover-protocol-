# SUBMISSION.md

## Title

**Handover Protocol — consensus-backed condition and custody certificates
for physical assets**

## Portal one-liner

A reusable GenLayer primitive that freezes physical-asset condition at
handover, tracks custody and defect lineage, distinguishes normal wear
from material change, verifies repairs, and exposes machine-readable
condition certificates for downstream contracts.

## What is proven

- Differentiation from Agent Warranty Protocol, Decision Memory Protocol,
  Reality Checkpoint Protocol, and Provenance Engine (`DECISION.md`).
- Full contract implementation (`contracts/handover_protocol.py`)
  covering the Condition Delta Graph, Custody Chain Graph (with bounded
  delegation), Defect Identity + Lineage, Custody Causality / Temporal
  Attribution (typed classes only, never legal-causation language),
  frozen Normal-Wear Policy, evidence-assurance-tier enforcement bound to
  the actually-classified evidence item, per-method caller authorization,
  baseline propose/accept/dispute handshake, custody-gap handling,
  Repair Verification, real fresh-evidence Challenge re-evaluation, and
  the Portable Condition Certificate.
- 18 named invariants (`docs/INVARIANTS.md`), each covered by at least one
  Direct Mode test.
- **68/68 Direct Mode tests + 4/4 real-network integration tests passing**
  (`docs/RELEASE_CANDIDATE_VERIFICATION.md`), including 8 forged-leader
  rejection cases, 15 adversarial output-hardening cases, 12
  stranger/owner/custodian authorization cases, and a custody-gap
  append-only-history case.
- A substantive custom validator (`gl.vm.run_nondet_unsafe`), not
  `strict_eq` over raw prose (`docs/CONSENSUS.md`).
- **Deployed and live-verified on Studionet** (`docs/DEPLOYMENT.md`):
  canonical address `0xc877275d6B3Ad199f2a9eae97EE9eF25A0783807`, real
  leader/validator consensus over public fixture evidence, a genuine
  condition-delta + defect + repair + challenge-OVERTURNED cycle, a
  genuine case of cross-model validator disagreement (`UNDETERMINED`,
  correctly uncommitted), a genuine negative/fail-closed case (404
  evidence → `EVIDENCE_UNAVAILABLE`), and a genuine stranger-rejected
  authorization attempt (confirmed via the reverted transaction's own
  traceback). Several real bugs were found and fixed across two rounds of
  verification — an internal live-lifecycle pass and an external security
  review — all documented rather than hidden.

## What is explicitly NOT claimed

- No image/vision verification (HP17, `docs/EVIDENCE.md`).
- No guaranteed legal attribution — attribution classes never claim
  causation (HP9).
- No economics layer in v1 (by design, section 25 of the master spec).
- No "zero consensus disagreement" — a genuine `UNDETERMINED` validator
  disagreement is documented in `docs/DEPLOYMENT.md`, not hidden.
- Not claimed as "first ever" or "globally unique."

## Do not claim

Per the master spec: no "guaranteed legal attribution," "tamper-proof
physical truth," "perfect image verification," "globally unique," "first
ever," "guaranteed highlight," or "zero consensus disagreement." This
document and `README.md` were written to avoid every one of these.
