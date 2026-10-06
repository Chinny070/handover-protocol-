# SUBMISSION.md

## Title

**Handover Protocol — consensus-backed condition and custody certificates
for physical assets**

## Portal one-liner

A reusable GenLayer primitive that freezes physical-asset condition at
handover, tracks custody and defect lineage, distinguishes normal wear
from material change, verifies repairs, and exposes machine-readable
condition certificates for downstream contracts.

## What is proven as of this session

- Differentiation from Agent Warranty Protocol, Decision Memory Protocol,
  Reality Checkpoint Protocol, and Provenance Engine (`DECISION.md`).
- Full contract implementation (`contracts/handover_protocol.py`)
  covering the Condition Delta Graph, Custody Chain Graph (with bounded
  delegation), Defect Identity + Lineage, Custody Causality / Temporal
  Attribution (typed classes only, never legal-causation language),
  frozen Normal-Wear Policy, baseline propose/accept/dispute handshake,
  custody-gap handling, Repair Verification, and the Portable Condition
  Certificate.
- 18 named invariants (`docs/INVARIANTS.md`), each covered by at least one
  Direct Mode test.
- **46/46 Direct Mode tests passing** (`docs/RELEASE_CANDIDATE_VERIFICATION.md`),
  including 6 forged-leader rejection cases and 15 adversarial
  output-hardening cases.
- A substantive custom validator (`gl.vm.run_nondet_unsafe`), not
  `strict_eq` over raw prose (`docs/CONSENSUS.md`).

## What is explicitly NOT claimed

- No live Studionet deployment yet (`docs/DEPLOYMENT.md`).
- No image/vision verification (HP17, `docs/EVIDENCE.md`).
- No guaranteed legal attribution — attribution classes never claim
  causation (HP9).
- No economics layer in v1 (by design, section 25 of the master spec).
- Not claimed as "first ever" or "globally unique."

## Do not claim

Per the master spec: no "guaranteed legal attribution," "tamper-proof
physical truth," "perfect image verification," "globally unique," "first
ever," "guaranteed highlight," or "zero consensus disagreement." This
document and `README.md` were written to avoid every one of these.
