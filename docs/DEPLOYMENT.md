# DEPLOYMENT.md

## Status: deployed to Studionet, full live lifecycle proven (Gates 1-3)

**Canonical contract address:** `0xD16141830b78A71b6F594d90fa4E1a6eF717DE85`
**Deployment transaction:** `0xdb4bd58b179a6614f3d55b261a1f10355ac52534485cbdf1cc854492c162def4`
**Network:** Genlayer Studio Network (`studionet`, chainId `61999`)
**Explorer:** https://genlayer-explorer.vercel.app (search the tx hash or
address above)
**Deployer account:** `0xaffE15eEc45b68835cc9E5B4Ab85dD5deaE8e70b`
(`my-studionet-wallet`)

Verified independently, not just the CLI's own echo:

- `genlayer receipt <tx>` → `status_name: 'FINALIZED'`, leader result
  `{ status: 'return', payload: null }` (5/5 validators AGREE).
- `genlayer schema <address>` → 27 methods with the full expected ABI.
- `python scripts/source_parity.py` → `PASS`: byte-for-byte identical to
  `contracts/handover_protocol.py` in this working tree.

This is the **second** deployment. The first
(`0x796bfBD33C7fFD8330F8ff6cCD46681B7E938ACe`, tx
`0x491be3b3d45bf875e3c968e6eec273362125652650386c9733cba48f6f14a2b1`) was
superseded after the live lifecycle run below surfaced a real bug in
`_fetch_text` (see "Bugs found during live verification"). That first
deployment itself superseded an even earlier one that failed outright
over a bad dependency pin. Neither earlier address is canonical.

## Live handover lifecycle proof (section 31 of the master spec)

All of the following are real Studionet transactions against the
canonical address above, run via `scripts/gl_write.js` (see below for why
the plain CLI couldn't be used for every call) and verified via
`genlayer receipt`/`genlayer call`, not assumed from a CLI success
message.

### Positive path — asset A3 / handover H2 (single component, for a clean
run; a two-component run on asset A2/H1 hit genuine validator
disagreement, documented below)

| Step | Call | Result |
|---|---|---|
| Register | `register_asset("Fleet Van 7 Single")` | `A3` |
| Component | `add_component(A3, "", "front_bumper")` | `C4` |
| Freeze policy | `seal_asset_definition(A3, {...})` | `policy_hash` recorded |
| Propose | `propose_handover(A3, offset-bob, [C4])` | `H2` |
| Baseline evidence | `add_baseline_evidence` → `fixtures/vehicle_baseline_bumper.txt` | accepted |
| Accept | `accept_baseline(H2)` (signed by offset-bob, the receiving party) | `ACCEPTED` |
| Begin custody | `begin_custody(H2)` | `ACTIVE` |
| Return evidence | `submit_return_evidence` → `fixtures/vehicle_return_bumper_damaged.txt` | `RETURN_PENDING` |
| **Evaluate (real consensus)** | `evaluate_return(H2)` | 3 AGREE / 2 DISAGREE → `MAJORITY_AGREE`, `DEFECTS_RECORDED` |
| Condition delta | `get_defect(D1)` | `severity: MAJOR`, `status: OPEN` |
| Attribution | defect history | `origin_class: SUPPORTED_AS_NEW_IN_INTERVAL` — not "caused by" |
| Certificate | `get_condition_certificate(A3)` | `major_defect_count: 1`, real `condition_digest`/`consensus_digest` hashes |
| Repair claim | `submit_repair(D1, REPAIR_RECEIPT, ...)` → `fixtures/vehicle_repair_receipt_bumper.txt` | `REPAIR_CLAIMED` |
| **Verify repair (real consensus)** | `verify_repair(D1)` | `REPAIRED` |
| Certificate again | `get_condition_certificate(A3)` | `major_defect_count: 0`, `open_defect_count: 0` |
| Challenge | `challenge_finding(D1, WRONG_SEVERITY)` | `UPHELD` (see Limitations — `_classify_challenge` is a placeholder) |
| Close | `close_handover(H2)` | `CLOSED` |
| Clear check | `is_handover_clear(A3)` | `true` |

### Genuine validator disagreement — asset A2 / handover H1 (two
components, `C1` front_bumper + `C3` engine)

`evaluate_return(H1)` was called three times. The first two attempts
produced `status_name: UNDETERMINED` (3 DISAGREE/1 AGREE/1 IDLE, then
3 DISAGREE/1 AGREE/1 IDLE again, 4 rounds, rotations exhausted) — the
five validators' different underlying models (a mix of
`anthropic/claude-sonnet-4.6`, `openai/gpt-5.4`,
`google/gemini-3-flash-preview` behind an internal router/policy) did not
reach exact agreement on every typed critical field across *two*
components simultaneously. Crucially: **no defect was created and no
state changed** on either UNDETERMINED result — `get_handover(H1)`
confirmed it stayed `RETURN_PENDING` both times, confirming HP18
("protocol disagreement != finalized contract-level result") held under
genuine adversarial-by-nature conditions, not a constructed test. A third
attempt after sharpening the return-evidence fixture's wording also came
back `UNDETERMINED` (3 DISAGREE/2 IDLE that time). H1 was left as-is
(`RETURN_PENDING`) as an honest record of this; the positive proof above
used a separate, single-component asset to reduce the joint-agreement
surface.

This is real, useful evidence for `docs/CONSENSUS.md` and
`docs/SECURITY.md`, not a shortcoming to hide: exact-match consensus
across multiple cross-model-graded components is measurably harder to
agree on than a single component, and the contract's fail-closed design
handled every one of those disagreements correctly.

### Negative / fail-closed case — asset A4 / handover H3

`submit_return_evidence` pointed at
`https://raw.githubusercontent.com/Chinny070/handover-protocol-/main/fixtures/does_not_exist.txt`
— confirmed with `curl` to return a genuine `404` before use.
`evaluate_return(H3)` → `EVIDENCE_UNAVAILABLE` (confirmed via
`genlayer call get_handover`). See "Bugs found during live verification"
below for what this run caught.

## Bugs found during live verification (fixed, not hidden)

**1. `_fetch_text` didn't check HTTP status (contract bug, fixed).**
The negative case above passed, but only because the model happened to
recognize GitHub's 404 HTML page as "evidence unavailable" when asked to
classify it — `_fetch_text` decoded and returned the body as successful
(`ok=True`) regardless of `resp.status`. That is not a deterministic
guarantee (HP14 requires render failure to be separated from a damage
finding by code, not by hoping the model notices). Fixed by checking
`resp.status` and treating any non-2xx response as a fetch failure
deterministically, with a new Direct Mode regression test
(`test_evaluate_return_http_404_is_deterministically_unavailable` in
`tests/direct/test_handover_protocol.py`) that registers no LLM mock at
all, so it would fail loudly (not just assert the wrong status) if the
fix regressed. 48/48 Direct Mode tests pass with the fix; the contract
was redeployed (see canonical address above) after this fix landed.

**2. `genlayer write --args` CLI bugs (environment/tooling, not a
contract bug).** `genlayer` CLI 0.39.2's `--args` parser:
- Silently coerces any argument whose text is valid JSON for an
  object/array into a dict/array type, even when the ABI expects a plain
  string (`seal_asset_definition`'s `policy_json` hit this).
- Coerces an empty string argument `""` into the number `0`
  (`Number("") === 0` in JS), breaking `add_component`'s legitimately-empty
  `parent_id` for a root-category component.

Both failures manifest as a clean `contract_error: exit_code 1` with no
state change — safe, but easy to misdiagnose as a contract bug. Worked
around with `scripts/gl_write.js`, which calls `genlayer-js` directly
with exact argument types, reusing the CLI's own keytar-cached signer (no
private key ever printed).

## What's still outstanding

- `_classify_challenge` is a conservative placeholder (documented in
  `docs/DEFECT_LINEAGE.md`/`docs/SECURITY.md`), confirmed live: the
  challenge call above returned `UPHELD` regardless of fresh evidence,
  as expected for the current implementation.
- Evidence-assurance-tier enforcement against submitted evidence is not
  yet wired in (separate tracked follow-up).
- GenVM lint beyond "schema loads against a live deployment" — no deeper
  static-analysis subcommand was discoverable in this CLI version.

## Canonical vs. disposable

Only the address/tx recorded at the top of this file is canonical.
Everything else deployed while iterating (both earlier addresses in this
document) is disposable and must not be referenced from README/SUBMISSION.
