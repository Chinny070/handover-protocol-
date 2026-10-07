# DEPLOYMENT.md

## Status: deployed to Studionet, full live lifecycle proven (Gates 1-3)

**Canonical contract address:** `0xc877275d6B3Ad199f2a9eae97EE9eF25A0783807`
**Deployment transaction:** `0x1f27396a89478861ca3521daaf704c57790128afe75d796227125b2b305c8fa5`
**Network:** Genlayer Studio Network (`studionet`, chainId `61999`)
**Explorer (contract page):**
https://explorer-studio.genlayer.com/address/0xc877275d6B3Ad199f2a9eae97EE9eF25A0783807
**Deployer account:** `0xaffE15eEc45b68835cc9E5B4Ab85dD5deaE8e70b`
(`my-studionet-wallet`)

Verified independently, not just the CLI's own echo:

- `genlayer receipt <tx>` → `status_name: 'FINALIZED'`, leader result
  `{ status: 'return', payload: null }` (5/5 validators AGREE).
- `genlayer schema <address>` → 28 methods with the full expected ABI
  (27 + the new `get_custody_gap_history` view).
- `python scripts/source_parity.py` → `PASS`: byte-for-byte identical to
  `contracts/handover_protocol.py` in this working tree.
- `tests/integration/test_handover_studionet.py` → 4/4 passed, real
  network reads against this exact address (see "Automated integration
  checks" below).

This is the **fifth** deployment, superseding
`0x4b4D04B5268cC7e20ea6970947Cf2f9b29B0aB92` (the authorization/
evidence-integrity fix deployment; predates making custody-gap recording
append-only), which superseded `0x785503f0aB50C458813AdEE36B43937Ebb884077`
(predates the authorization/evidence-integrity fixes), which superseded
`0xD16141830b78A71b6F594d90fa4E1a6eF717DE85` (fixed the `_fetch_text`
HTTP-status bug, predates evidence-assurance and real-challenge wiring),
which superseded `0x796bfBD33C7fFD8330F8ff6cCD46681B7E938ACe` (predates
the HTTP-status fix), which superseded a first attempt that failed
outright over a bad dependency pin. No earlier address is canonical.

## Custody-gap history fix, proven live

A follow-up review suggested making `mark_custody_gap` append-only or
challengeable rather than freely mutable by either party — a party could
otherwise silently erase an earlier gap report by later overwriting it
with `NO_GAP`. Fixed (`custody_gap_history_json`, bounded
`MAX_CUSTODY_GAP_EVENTS`, exposed via the new `get_custody_gap_history`
view; `tests/direct/test_handover_custody.py::test_custody_gap_history_is_append_only_and_not_erasable`)
and proven live:

| Step | Call | Tx hash | Result |
|---|---|---|---|
| Register | `register_asset("Gap History Smoke Test Asset")` | `0x36e36b7fa1c8ec45dd93156f8c9a161cf2759bb0705ab66d32167f4900b7275f` | `A1` |
| Component | `add_component(A1, "", "bumper")` | `0xdd42aa5e4c34de479a1b5a68101bf01699747ea000d495586e9ebf742b0aed73` | `C1` |
| Freeze policy | `seal_asset_definition(A1, {...})` | `0x7987d05f40c9ead8c82dd9b2dd8b222d00f9ff093734b5852171894126a6ebb6` | `policy_hash` recorded |
| Propose | `propose_handover(A1, offset-bob, [C1])` | `0x47a4a066d53d6606c2c65ce8cfe662acb96347bf43c41f5060c1af0e3ef9e7aa` | `H1` |
| Mark gap | `mark_custody_gap(H1, "CUSTODY_GAP")` | `0xfdfe78cf969c3024b3bcc0393e7a6349e846ab53c15127d0cc3113760426e8c6` | `custody_gap: CUSTODY_GAP` |
| Overwrite | `mark_custody_gap(H1, "NO_GAP")` | `0xc0f4477f0f7becdd53b038806f2d40a2acc0c3c6ef82186f6e495e323b961ee2` | `custody_gap: NO_GAP` (live field) |

`get_handover(H1).custody_gap` reads `NO_GAP` (the latest call), but
`get_custody_gap_history(H1)` still shows both entries in order —
`CUSTODY_GAP` (previous: `NO_GAP`) followed by `NO_GAP` (previous:
`CUSTODY_GAP`) — confirming the original report was not erased. This is
the exact state `tests/integration/test_handover_studionet.py` asserts
against.

## Security review fixes, proven live (not just in Direct Mode)

An external review of the previous canonical deployment found that most
public write methods had no caller authorization at all, and two gaps in
how evidence assurance was bound to what was actually classified. Fixed
in `contracts/handover_protocol.py`, covered by
`tests/direct/test_handover_authorization.py` (12 stranger/owner/
custodian/receiver tests), and proven live on
`0x4b4D04B5268cC7e20ea6970947Cf2f9b29B0aB92` (the fourth deployment,
since superseded by the custody-gap-history fix below; the authorization
logic itself is unchanged in the current canonical contract and
re-confirmed by the Direct Mode suite):

| Step | Call | Tx hash | Result |
|---|---|---|---|
| Register | `register_asset("Audit Smoke Test Asset")` | `0x9f83301c4ebd39496c0e6d1dbd7775461374119e04c131f0702b28153f0423be` | `A1` |
| Component | `add_component(A1, "", "bumper")` | `0xbb73646f699da0a33916f09bddd4a0f8e1abed52726de85d54a838a62735f7c8` | `C1` |
| Freeze policy | `seal_asset_definition(A1, {...})` | `0x30562061a86c41fffd3065d7ac1cdaf966b8bcbbf681e068ab4410e5a720e86b` | `policy_hash` recorded |
| **Propose as stranger (offset-bob, not owner)** | `propose_handover(A1, ..., parent_handover_id="")` | `0xf26afc3659d4a2228d8b82f9a7d44e8c54bd2cf014cdc5d0b80bfd2600b42f3c` | reverted: `Exception: only the asset owner may propose primary custody` (confirmed via the transaction's own `stderr` traceback, not just a status code) |
| **Propose as owner** | `propose_handover(A1, offset-bob, [C1])` | `0xc66bc22e876ed459693e57d0fa87f4241b098f31a05669a691ef469b580b605b` | succeeded, `H1` |
| **Baseline evidence with mismatched tier/kind** | `add_baseline_evidence(H1, WEB_RENDERED_INSPECTION, ..., assurance_tier=SIGNED_INSPECTION)` | `0x535090014e1928e445b87a2d07f300659f9715168b92ec388b0f37cd6fb2067e` | reverted: `Exception: assurance tier SIGNED_INSPECTION is not claimable for evidence kind WEB_RENDERED_INSPECTION` |
| Baseline evidence (valid) | `add_baseline_evidence(H1, WEB_RENDERED_INSPECTION, ..., assurance_tier=SELF_REPORTED)` | `0x1ce96be0712f6c7b36b0bcd35ee8c246637e5416f9d5040372f543769fdd1ea9` | accepted |
| Accept | `accept_baseline(H1)` (offset-bob) | `0x91dc0958275017d5a4c36bc6bcfd745df65d0c9150a56f1277e3336df9fab305` | `ACCEPTED` |
| Begin custody | `begin_custody(H1)` | `0x1fd26cad48f9dd01da4b8575099ba85bfc655d188dd50c9bb83c060637239179` | `ACTIVE` |

This state predates the custody-gap-history deployment and is no longer
what `tests/integration/test_handover_studionet.py` asserts against (see
"Custody-gap history fix" above and "Automated integration checks" below
for the current canonical deployment's real state).

- **`submit_return_evidence` now requires the current custodian**;
  **`add_baseline_evidence`/`begin_custody`/`mark_custody_gap`/
  `evaluate_return`/`close_handover` now require a party to the
  handover**; **`challenge_finding`/`submit_repair`/`verify_repair` now
  require a party to the defect's originating custody interval.** All
  proven in Direct Mode (`test_handover_authorization.py`); the primary-
  proposal and tier/kind checks above were additionally proven live since
  they are the two most severe (any address could otherwise originate
  custody of someone else's asset).
- **`_evidence_meets_minimum` now checks only the evidence item actually
  classified** (index 0, what `_classify_component` fetches), not "any
  evidence item submitted for the component" — closing a gap where a weak
  item that's actually read could be paired with an unrelated strong-tier
  item nobody fetched.
- **`_add_evidence` now validates `component_ids` against the asset's
  known components and the handover's scope.**
- **`content_hash` is explicitly documented, in the `Evidence` dataclass
  itself, as caller-asserted and not cryptographically verified** — the
  reviewer's explicitly offered alternative to full verification, chosen
  over mechanically rewriting ~40 Direct Mode test fixtures to carry real
  sha256 digests for marginal additional assurance.

## Automated integration checks (replaces the previous unconditional skip)

`tests/integration/test_handover_studionet.py` now runs real
`genlayer_py.read_contract` calls against the canonical address above,
using a freshly generated, **never-signing, unfunded** keypair purely to
populate the required `from` field — no real private key is used or
needed, so the test runs from any machine with network access and no
secrets configured. It asserts on asset `A1` and handover `H1`'s exact
recorded state from the custody-gap-history smoke test below, including
that `get_custody_gap_history` still shows the original `CUSTODY_GAP`
report even though the live `custody_gap` field was later overwritten
with `NO_GAP`. 4/4 pass.

## Live handover lifecycle proof (section 31 of the master spec)

Every step below is a real Studionet transaction, run via
`scripts/gl_write.js` (see "Bugs found during live verification" for why
the plain CLI couldn't be used for every call) and verified via
`genlayer receipt`/`genlayer call`, not assumed from a CLI success
message. Each table names the exact deployment address it ran against,
since this lifecycle predates the current canonical address (the
authorization/evidence-integrity fixes landed in later deployments; the
underlying condition/custody/defect/repair mechanics they ran against are
unchanged and re-confirmed by the Direct Mode suite against the current
contract).

### Positive path — asset A3 / handover H2 (single component)

Ran on `0x796bfBD33C7fFD8330F8ff6cCD46681B7E938ACe` (the second
deployment — fixed dependency pin, predates the HTTP-status fix below,
which this very run's negative case discovered).

| Step | Call | Tx hash | Result |
|---|---|---|---|
| Register | `register_asset("Fleet Van 7 Single")` | `0x4613721113bb35a568fd96d80dd27c67bd71592ec2871b228284d2c17d5452de` | `A3` |
| Component | `add_component(A3, "", "front_bumper")` | `0xcc0ba62a3906b8ae2e8277947aa20986faa0288bcbb370e4bb0bd251f581da0b` | `C4` |
| Freeze policy | `seal_asset_definition(A3, {...})` | `0xbcc0a92376ea72d13e52e12161c9cab33100e20f36215b489598b9905bcacb44` | `policy_hash` recorded |
| Propose | `propose_handover(A3, offset-bob, [C4])` | `0x0213f492a4614ef28689f7a000a1f18b609aea56d47966bd2adde5a9c61bb5d8` | `H2` |
| Baseline evidence | `add_baseline_evidence` → `fixtures/vehicle_baseline_bumper.txt` | `0x28d8f4ae229c1447c72f73744c3e026c041c461ee786cd183a0b18ad02673e4c` | accepted |
| Accept | `accept_baseline(H2)` (offset-bob) | `0x53052ffaf9cfc6e5c2fce86c7a3e157cf849fcc0002aa2b8c4f481ec79f7c779` | `ACCEPTED` |
| Begin custody | `begin_custody(H2)` | `0xf4898186eae3893b23100327b38c638f150c18e796949bb7eb2b3a91579032bb` | `ACTIVE` |
| Return evidence | `submit_return_evidence` → `fixtures/vehicle_return_bumper_damaged.txt` | `0x258397782b6dd0a1ba9c840e7879ace1f91effff4a23559d700293c17ba1c264` | `RETURN_PENDING` |
| **Evaluate (real consensus)** | `evaluate_return(H2)` | `0x5850f45ed6c874bef4c31030ea41bd801eea38be258bb4dcd57441471071bc18` | 3 AGREE / 2 DISAGREE → `MAJORITY_AGREE`, `DEFECTS_RECORDED` |
| Condition delta | `get_defect(D1)` (view) | — | `severity: MAJOR`, `status: OPEN` |
| Attribution | defect history (view) | — | `origin_class: SUPPORTED_AS_NEW_IN_INTERVAL` — not "caused by" |
| Certificate | `get_condition_certificate(A3)` (view) | — | `major_defect_count: 1`, real `condition_digest`/`consensus_digest` hashes |
| Repair claim | `submit_repair(D1, REPAIR_RECEIPT, ...)` → `fixtures/vehicle_repair_receipt_bumper.txt` | `0xaba248ff960a96f135bc7617941e06784450fb34b6372a76c06ee6ace68f1745` | `REPAIR_CLAIMED` |
| **Verify repair (real consensus)** | `verify_repair(D1)` | `0xe380899ddd66ed92ac948000431f9111eb3167d67c092620152bd17c0e6c121b` | `REPAIRED` |
| Certificate again | `get_condition_certificate(A3)` (view) | — | `major_defect_count: 0`, `open_defect_count: 0` |
| Challenge | `challenge_finding(D1, WRONG_SEVERITY)` | `0xa715a6fc6ff7bf18e299837ae223d17e0fdc55731ba5ce52bbf2d75a15e21dbe` | `UPHELD` — at the time of this run `_classify_challenge` was still the old placeholder; see "Real challenge re-evaluation" below for the later live proof against the real implementation |
| Close | `close_handover(H2)` | `0xe315d42cdfc555da9f522b92d9bead6ae0d960b9511144c2c97484614380a5f7` | `CLOSED` |
| Clear check | `is_handover_clear(A3)` (view) | — | `true` |

### Genuine validator disagreement — asset A2 / handover H1 (two
components, `C1` front_bumper + `C3` engine)

Also on `0x796bfBD33C7fFD8330F8ff6cCD46681B7E938ACe`.

| Step | Call | Tx hash | Result |
|---|---|---|---|
| Register | `register_asset("Fleet Van 7")` | `0x8a8c09981aef23dab56be5283509f70615d7cb2b427ade5a421a8a50521a24ea` | `A2` |
| Component | `add_component(A2, "", "front_bumper")` | `0x5e99eaeb28b6050f6de51fa03bb675954e96393010ee81e0754380f41b504f28` | `C1` |
| Component | `add_component(A2, "", "engine")` | `0xe6ca2b534be4761df906b716b3c4671f6732699209719efe04153ac3d8208143` | `C3` |
| Freeze policy | `seal_asset_definition(A2, {...})` | `0x9e989c66143aacd80290616bbf4ac915d634f97965fb58e830b898b9df275d8b` | `policy_hash` recorded |
| Propose | `propose_handover(A2, offset-bob, [C1,C3])` | `0xf2043e07125ed3ecedc1df5116578a515ceaee9e5ded3a90d91d5d778245c817` | `H1` |
| Baseline evidence x2 | `add_baseline_evidence` (bumper, engine) | `0xfa72dd3f552055fdd2f7b5bea371afe15c83d3f35d0056e6872144fa42f32dac`, `0x2b109708abdb6cdaa0e5b3cc1cdeb7ac098358dd7036e77dcaa884388ee48d18` | accepted |
| Accept | `accept_baseline(H1)` | `0xf0a833d1739c40690af616b4775287f42d5f05508ca6341ee2eb133794e91fed` | `ACCEPTED` |
| Begin custody | `begin_custody(H1)` | `0x27eac7c7bae011fcb376c7f438972965ab167cbadc2f87a804295e3d20894884` | `ACTIVE` |
| Return evidence x2 | `submit_return_evidence` (bumper damaged, engine unchanged) | `0xb0cfedcece7190f2d7643f3be381e9f8802720a8426f807f689b18452efc84e3`, `0xc96cf75129e2a3837b0306f752f60b9d50290350a7a6c1b7bfe5b43655e8123c` | `RETURN_PENDING` |
| **Evaluate attempt 1** | `evaluate_return(H1)` | `0x8a8379c7585012d9c5fefb780e85b4112a9e8038a7d8b9ce5f28f9cf8d3915b5` | `UNDETERMINED` (3 DISAGREE/1 AGREE/1 IDLE) |
| **Evaluate attempt 2** | `evaluate_return(H1)` | `0xfc11d1014cfad9756f9c5026167247865dc47abf72517a31cd7a05e492b2646a` | `UNDETERMINED` (3 DISAGREE/1 AGREE/1 IDLE) |
| **Evaluate attempt 3** (after sharpening fixture wording) | `evaluate_return(H1)` | `0x87c0ec009873c6791222260c2ffbcf82d576340ab61c75a7c533398b586447ff` | `UNDETERMINED` (3 DISAGREE/2 IDLE) |

`evaluate_return(H1)` was called three times across the above
transactions. The five validators' different underlying models (a mix of
`anthropic/claude-sonnet-4.6`, `openai/gpt-5.4`,
`google/gemini-3-flash-preview` behind an internal router/policy) did not
reach exact agreement on every typed critical field across *two*
components simultaneously, every single time. Crucially: **no defect was
created and no state changed** on any of the three UNDETERMINED results —
`get_handover(H1)` confirmed it stayed `RETURN_PENDING` throughout,
confirming HP18 ("protocol disagreement != finalized contract-level
result") held under genuine adversarial-by-nature conditions, not a
constructed test. H1 was left as-is (`RETURN_PENDING`) as an honest
record of this; the positive proof above used a separate,
single-component asset to reduce the joint-agreement surface.

This is real, useful evidence for `docs/CONSENSUS.md` and
`docs/SECURITY.md`, not a shortcoming to hide: exact-match consensus
across multiple cross-model-graded components is measurably harder to
agree on than a single component, and the contract's fail-closed design
handled every one of those disagreements correctly.

### Negative / fail-closed case — asset A4 / handover H3

Also on `0x796bfBD33C7fFD8330F8ff6cCD46681B7E938ACe`.

| Step | Call | Tx hash | Result |
|---|---|---|---|
| Register | `register_asset("Fleet Van Negative Case")` | `0xacf92b0896b27bf7ad6fa3e55ecf2901d877ae8c9a00f812ae51f593dbe51e7f` | `A4` |
| Component | `add_component(A4, "", "roof")` | `0xdc8c97677216e973db9d8a56c96156d954348bd1e218016fa82f88e9a4cf686e` | `C5` |
| Freeze policy | `seal_asset_definition(A4, {...})` | `0x6c1569ff613b8f1c235b52334857e65deb174c6823dd277aceebbf79784117c5` | `policy_hash` recorded |
| Propose | `propose_handover(A4, offset-bob, [C5])` | `0xd88b18e542d2c4e75f4b4c75a82dc844d0192fc632ace31b68327ea42fab8b17` | `H3` |
| Baseline evidence | `add_baseline_evidence` | `0xdacd29524869e7d8a27da82e173d40f5b543344d863a9db671bf9c1c6685ca61` | accepted |
| Accept | `accept_baseline(H3)` | `0xd79758cf75026d5038cbc0ab60b8a7e7e5191c3b1a59a7171dcded19807ee3b6` | `ACCEPTED` |
| Begin custody | `begin_custody(H3)` | `0x1e05c0f7aa4c9a3463b91f38470f77355ff84a7d247ab94b51ad80c4670b17c3` | `ACTIVE` |
| Return evidence (404 URL) | `submit_return_evidence` → `fixtures/does_not_exist.txt` (confirmed via `curl` to return a genuine `404` before use) | `0xf67822bc1e0d92892c8ac3aba34ae2c09ac3158dca511010e72c28da4d320141` | `RETURN_PENDING` |
| **Evaluate (real consensus)** | `evaluate_return(H3)` | `0x960a45c9e8dd3f1cba733c04c000cbd47867519f0e4f6fc7a23aecbcd43a989e` | `EVIDENCE_UNAVAILABLE` |

See "Bugs found during live verification" below for the real bug this
run caught.

### Evidence-assurance-tier enforcement — asset A1 / handovers H1, H2

Ran on `0x785503f0aB50C458813AdEE36B43937Ebb884077` (the third
deployment — fixed the HTTP-status bug, added evidence-assurance
enforcement and real challenge re-evaluation; since superseded by the
authorization-fix deployment, but this enforcement logic is unchanged in
the current canonical contract and re-confirmed by the Direct Mode
suite).

Proves `_evidence_meets_minimum` (section 10) is genuinely load-bearing
on-chain, not just in Direct Mode:

| Step | Call | Tx hash | Result |
|---|---|---|---|
| Register | `register_asset("Single Component Rig")` | `0x526f1fdb8df655b17ec6035f40d55df2b318e77dc3a09c5ac1c40ae852122e7f` | `A1` |
| Component | `add_component(A1, "", "front_bumper")` | `0x89929103283ccca0ea6beddeb23b67a2c06753e777d90d7d6e94d6309ffff4bd` | `C1` |
| Freeze policy (requires `SIGNED_INSPECTION` for MAJOR) | `seal_asset_definition(A1, {...})` | `0x25351a2988d8041c259dd42764f5b76f591b3500cdfd2a4285d765257fa71cac` | `policy_hash` recorded |
| Propose | `propose_handover(A1, offset-bob, [C1])` | `0xeb7408927868d2315e50c3bb2bd2c1d851998405566cdb3eb2da41ae9be459d8` | `H1` |
| Baseline evidence | `add_baseline_evidence` | `0x428cecd1f61d67c09eae0d4172f008f90d09afc3ecec695a2c081ace2b5aa5c2` | accepted |
| Accept | `accept_baseline(H1)` | `0x159a1f9920060c0b344dcf2f89836a639360f0a63ce418d953207265c253a149` | `ACCEPTED` |
| Begin custody | `begin_custody(H1)` | `0x49c3bd107f4bc0b7835b6907e90039ca63784e22ec46f41c3b68d34c5ffaabaa` | `ACTIVE` |
| Return evidence (`SELF_REPORTED`, weak) | `submit_return_evidence` → damaged-bumper fixture | `0x5912fb12f1ead75dc99080a5eb77631404dc5c2d627709128aa591c5117b2c65` | `RETURN_PENDING` |
| **Evaluate (real consensus)** | `evaluate_return(H1)` | `0xd5e6722e1b4b3d89861e7a95a211e90bf11f96a2a0402dcd02af2af45604c9a4` | Leader+validator agreed `NEW_MAJOR_DAMAGE`/`MAJOR`/`evidence_sufficient: true` — but deterministic policy check downgraded to `INCONCLUSIVE` since `SELF_REPORTED` didn't clear the bar. `get_asset(A1).defect_ids == []`: no defect created despite the model's own agreement. |
| Propose (second interval) | `propose_handover(A1, offset-bob, [C1])` | `0x45b108857a18fcbf1499fc883c68d6acfcd2faf7b2ddbc199751ee166296d5ae` | `H2` |
| Baseline evidence | `add_baseline_evidence` | `0xd9b69debe95cdc772506528cbe90d40e6c6535fdab651e3ea586c037a12ecddf` | accepted |
| Accept | `accept_baseline(H2)` | `0x010221464e42ea880c85c0725fa902013013b5033abc97edf138722c78cbe7fd` | `ACCEPTED` |
| Begin custody | `begin_custody(H2)` | `0x9b8079af9783e62ec0bd4d9a51e8da230f014d730f4209e630abe6f7bec883ba` | `ACTIVE` |
| Return evidence (`SIGNED_INSPECTION`, sufficient) | `submit_return_evidence` → same damaged-bumper fixture | `0xfb3b66cf7762f96913e5be04ef52fdc50e07a30167348e92d04ad8fa01a26b96` | `RETURN_PENDING` |
| **Evaluate (real consensus)** | `evaluate_return(H2)` | `0x5fc79ef57b7515b895c9c6ec098bbea456b40ee67145d79dd14375dc47c0eb5c` | `DEFECTS_RECORDED`, defect `D1` created, `severity: MAJOR` |

### Real challenge re-evaluation — defect D1 (also on the third deployment)

`_classify_challenge` used to be a conservative placeholder that always
returned `UPHELD`. It now independently retrieves fresh challenge
evidence and lets the model reconsider the finding against it.

| Step | Call | Tx hash | Result |
|---|---|---|---|
| Challenge | `challenge_finding(D1, PRE_EXISTING_EVIDENCE, SIGNED_INSPECTION_RECORD, ...)` → `fixtures/vehicle_challenge_preexisting_proof.txt` (pushed before use) | `0x4461e29797955cdb37e44f63edc5cd95c412f2fdc0b1ea3ef74f346e1781ccac` | `OVERTURNED` (real consensus, not a hardcoded answer) |

Confirmed via `get_defect(D1).status == 'UNRESOLVED'` and
`get_defect_history(D1)` showing the original `OPEN` event preserved
with the new `UNRESOLVED` event appended (append-only, HP8).

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
was redeployed as `0xD16141830b78A71b6F594d90fa4E1a6eF717DE85` after this
fix landed (see "No earlier address is canonical" above for the full
deployment chain since).

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

- GenVM lint beyond "schema loads against a live deployment" — no deeper
  static-analysis subcommand was discoverable in this CLI version.
- See `docs/SECURITY.md` → "Acknowledged future hardening" for the three
  items explicitly scoped by the external reviewer as later/optional/
  eventual work rather than a blocking gap: signature/attestation
  verification for high-assurance evidence, binding fetched bytes to a
  verified `content_hash` digest, and a fully automated *funded write*
  lifecycle test on Studionet (today's integration test covers real,
  reproducible reads needing no secret; the write lifecycle is documented
  by hand above instead).

## Canonical vs. disposable

Only the address/tx recorded at the top of this file is canonical.
Everything else deployed while iterating (all five earlier addresses in
this document) is disposable and must not be referenced from
README/SUBMISSION.
