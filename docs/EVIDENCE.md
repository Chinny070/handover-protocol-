# EVIDENCE.md

## Evidence record

Each `Evidence` row binds: `evidence_id` (contract-assigned), `asset_id`,
`handover_id` (empty for repair-only evidence), `evidence_kind`,
`source_url`, `content_hash`, `submitted_by`, `assurance_tier`, and
`component_ids_json` (which components this evidence is relevant to).

`content_hash` is caller-asserted and bounded in length. When submitted
in strict 64-hex-lowercase sha256-digest form, `_fetch_text` verifies it
against the actually-fetched bytes and treats a mismatch as a fetch
failure (HP14) — proven live on Studionet: a correct digest let a real
fetch succeed, and a deliberately wrong digest produced a deterministic
`EVIDENCE_UNAVAILABLE` (see `docs/DEPLOYMENT.md`). A `content_hash` in
any other form (the short placeholder values used throughout the Direct
Mode test fixtures) remains unverified by design — this is an opt-in
check by format, not a retroactive requirement on every piece of evidence
ever submitted. See the field's own docstring in
`contracts/handover_protocol.py` and `docs/SECURITY.md` → Limitations.

## Supported evidence kinds

`WEB_RENDERED_INSPECTION`, `PUBLIC_DOCUMENT`, `SIGNED_INSPECTION_RECORD`,
`API_RESPONSE`, `SENSOR_OR_TELEMETRY_RECORD`, `STRUCTURED_CHECKLIST`,
`REPAIR_RECEIPT`, `SERVICE_RECORD`, `HASH_COMMITMENT`. Only these are
accepted by `add_baseline_evidence`/`submit_return_evidence`/
`submit_repair`; anything else is rejected at the contract boundary.

## Assurance tiers

Evidence carries a caller-asserted `assurance_tier`, one of
`SIGNED_INSPECTION`, `MULTI_SOURCE_CORROBORATED`,
`INDEPENDENT_PUBLIC_SOURCE`, `SINGLE_PUBLIC_SOURCE`, `SELF_REPORTED`,
`HASH_COMMITMENT_ONLY`, `UNVERIFIED` — an unknown tier is rejected at
submission. A tier can only be claimed for an `evidence_kind` that could
plausibly carry it (`_tier_allowed_for_kind`): `SIGNED_INSPECTION`
requires `evidence_kind=SIGNED_INSPECTION_RECORD`, `HASH_COMMITMENT_ONLY`
requires `evidence_kind=HASH_COMMITMENT`, the "public source" tiers
require a plausibly-public kind, and `SELF_REPORTED`/`UNVERIFIED` are
always claimable as the weakest fallback.

For `SIGNED_INSPECTION` specifically, the kind/tier check is not the only
gate: `add_baseline_evidence`/`submit_return_evidence` take optional
`inspector_pubkey`/`sig_r`/`sig_s` parameters, and `_verify_inspector_signature`
requires a valid secp256k1 ECDSA signature from a public key in the
asset's frozen policy's `trusted_inspectors` list, over the exact
`evidence_kind|source_url|content_hash` triple being submitted (so a
signature cannot be replayed onto different evidence). This is pure
deterministic verification — the model is never involved, consistent
with the GenLayer boundary — implemented from scratch in plain Python
since no crypto library exists in the GenVM runtime. It cryptographically
proves the claimed signer produced that exact signature; it cannot (and
does not claim to) prove that public key belongs to a real, licensed
inspector — binding a key to a real-world identity is the policy owner's
responsibility when populating `trusted_inspectors`. An asset whose
policy never sets `trusted_inspectors` can never have evidence clear
`SIGNED_INSPECTION` — there is no default "everyone is trusted" state.

The frozen policy's `evidence_minimums` maps a severity bucket
(`minor`/`major`/`critical`) to the tiers that may support a finding of
that severity. This is enforced deterministically in
`_evidence_meets_minimum`, called from `_apply_findings` *after*
consensus already agreed on a typed finding: if the evidence item that
was actually classified (the first evidence item for that component —
the same one `_classify_component` fetches as `urls[0]`) doesn't meet the
bar, the finding is downgraded to `INCONCLUSIVE` rather than recording a
defect — it is never silently accepted, and never silently dropped as if
nothing changed. Only that classified item's tier counts, not "any
evidence item submitted for the component": a caller cannot attach a weak
item that's actually read alongside an unrelated strong-tier item nobody
fetched and have the strong tier alone satisfy the check. A severity
bucket with no entry in the policy fails closed the same way (see
`tests/direct/test_handover_evidence_assurance.py`). A self-reported note
is never silently relabeled as independently verified anywhere in this
contract: the tier field is passed through unchanged, it is never
upgraded — it is only ever checked for sufficiency.

`component_ids` on every evidence submission is validated against both
the asset's known components and the specific handover's scope
(`_add_evidence`) — evidence cannot be tagged with an unrelated or
non-existent component.

## Physical-World Limitations

GenLayer adjudicates **evidence about** physical reality — rendered web
pages, structured inspection text, repair receipts — it does not directly
sense the physical world. Every finding this contract stores is therefore
a claim of the form "the retrieved evidence, as classified by consensus,
shows X", never a direct physical measurement. Two consequences follow:

1. If nobody submits evidence, or the only evidence submitted is
   unreachable/unparseable, the contract will not and cannot assert
   anything about the asset's real condition — it fails closed to
   `UNAVAILABLE`/`EVIDENCE_UNAVAILABLE`/`EXTERNAL_FAILURE`.
2. The quality of every downstream finding is bounded by the quality and
   honesty of the submitted evidence source. This contract's job is to
   make that evaluation consensus-backed and typed, not to guarantee the
   evidence itself is true.

## Visual/image evidence

This release does **not** claim native image/vision verification as
load-bearing (HP17). Evidence is text/structured only (rendered web text,
structured checklists, receipts). See section 15 ("IMAGE / VISION GATE")
of the master spec and `docs/RELEASE_CANDIDATE_VERIFICATION.md` for what
was and wasn't verified against the current runtime.

## Digest requirements

Baseline evidence must include a strict lowercase 64-character SHA-256 digest at acceptance. Return classification re-fetches and compares the raw fetched body bytes to both the frozen baseline digest and the submitted return digest. A mismatch is an unavailable observation and cannot create a finding or clearance. Repair evidence also requires a SHA-256 digest and is checked when fetched. HTTPS accessibility alone is not an attestation of authenticity; `SIGNED_INSPECTION` requires a signature from a frozen trusted inspector key over the domain-separated evidence kind, URL, and digest.
