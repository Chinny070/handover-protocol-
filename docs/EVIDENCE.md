# EVIDENCE.md

## Evidence record

Each `Evidence` row binds: `evidence_id` (contract-assigned), `asset_id`,
`handover_id` (empty for repair-only evidence), `evidence_kind`,
`source_url`, `content_hash`, `submitted_by`, `assurance_tier`, and
`component_ids_json` (which components this evidence is relevant to).

## Supported evidence kinds

`WEB_RENDERED_INSPECTION`, `PUBLIC_DOCUMENT`, `SIGNED_INSPECTION_RECORD`,
`API_RESPONSE`, `SENSOR_OR_TELEMETRY_RECORD`, `STRUCTURED_CHECKLIST`,
`REPAIR_RECEIPT`, `SERVICE_RECORD`, `HASH_COMMITMENT`. Only these are
accepted by `add_baseline_evidence`/`submit_return_evidence`/
`submit_repair`; anything else is rejected at the contract boundary.

## Assurance tiers

Evidence carries a caller-asserted `assurance_tier` (e.g.
`SELF_REPORTED`). This release does not yet enforce per-severity minimum
assurance tiers in deterministic code (the frozen policy's
`evidence_minimums`/`attribution_minimums` keys are validated as present
at seal time but not yet cross-checked against submitted evidence tier in
`evaluate_return`) — this is a known gap, see "Limitations" below. A
self-reported note is never silently relabeled as independently verified
anywhere in this contract: the tier field is passed through unchanged, it
is never upgraded.

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
