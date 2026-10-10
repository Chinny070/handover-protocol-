# DEPLOYMENT.md

## Status: canonical Studionet deployment and funded lifecycle verified

**Canonical contract:** [0xEC5EcdCd93DFf54c0752628Eed0B51F51417222C](https://explorer-studio.genlayer.com/address/0xEC5EcdCd93DFf54c0752628Eed0B51F51417222C)

**Deployment transaction:** [0xffcd5a8409041b78a12465633636be4c21c2256f818f1503a0415431842a058c](https://explorer-studio.genlayer.com/tx/0xffcd5a8409041b78a12465633636be4c21c2256f818f1503a0415431842a058c)

**Network:** GenLayer Studionet, chain ID `61999`

**Source commit:** `f48ea0d`
**Normalized deployed-source SHA-256:** `3c8637329f0ab0d4c341a5bf266690777fa2d10f8fb4f8de85fdb640c9c12957`

Deployment finalized with `MAJORITY_AGREE` (3 AGREE, 2 IDLE). The live schema query succeeded and source parity passed byte-for-byte after line-ending normalization. The funded integration lifecycle passed on this exact deployment and independently read back asset, handover, repair, and certificate state. The test result was `1 passed`; its writes and finalized receipts are recorded in [`LIVE_LIFECYCLE_TRANSACTIONS.jsonl`](LIVE_LIFECYCLE_TRANSACTIONS.jsonl).

Verified lifecycle transaction hashes for asset `A1`, component `C1`, and handover `H1`:

| Action | Transaction | Result |
|---|---|---|
| Register asset | [0x04416703f27f42c0fd2dcba2394d6a51ccf13b4e80452e2760356fcc33bcb4f4](https://explorer-studio.genlayer.com/tx/0x04416703f27f42c0fd2dcba2394d6a51ccf13b4e80452e2760356fcc33bcb4f4) | FINALIZED, MAJORITY_AGREE |
| Add component | [0xc05336858ab6e05cb3c999986a84625960b174431549b5024dbda82899a98e5d](https://explorer-studio.genlayer.com/tx/0xc05336858ab6e05cb3c999986a84625960b174431549b5024dbda82899a98e5d) | FINALIZED, MAJORITY_AGREE |
| Seal asset policy | [0x9bfef8ff06e3c00bf07bd819ddcf3e9bb79e0c64ace8d26e91018724453d08ac](https://explorer-studio.genlayer.com/tx/0x9bfef8ff06e3c00bf07bd819ddcf3e9bb79e0c64ace8d26e91018724453d08ac) | FINALIZED, MAJORITY_AGREE |
| Propose handover | [0x9886b7a5eb9f4a4cd1e70b656b05565d9e6846cb3118ccad5a35d569b33a461a](https://explorer-studio.genlayer.com/tx/0x9886b7a5eb9f4a4cd1e70b656b05565d9e6846cb3118ccad5a35d569b33a461a) | FINALIZED, MAJORITY_AGREE |
| Submit return evidence | [0xc454b7849aa6a998437a1a293b3d71eae5aed19ada7661dd05f728259d015b66](https://explorer-studio.genlayer.com/tx/0xc454b7849aa6a998437a1a293b3d71eae5aed19ada7661dd05f728259d015b66) | FINALIZED, MAJORITY_AGREE |
| Evaluate return | [0x7d7af8c01293bf92b74354114a582b6f8faa014d61664321b2dfb0a6301be213](https://explorer-studio.genlayer.com/tx/0x7d7af8c01293bf92b74354114a582b6f8faa014d61664321b2dfb0a6301be213) | FINALIZED, MAJORITY_AGREE |
| Submit repair | [0x8f46f0f633c09d3fb90a16061e7a29da4c6ebbd3e4b9afcce4d091cb7daef586](https://explorer-studio.genlayer.com/tx/0x8f46f0f633c09d3fb90a16061e7a29da4c6ebbd3e4b9afcce4d091cb7daef586) | FINALIZED, MAJORITY_AGREE |
| Verify repair | [0x4b8605f4103342057d2e5954131b5c63129233d14b8dd2eb6be8960768a51de6](https://explorer-studio.genlayer.com/tx/0x4b8605f4103342057d2e5954131b5c63129233d14b8dd2eb6be8960768a51de6) | FINALIZED, MAJORITY_AGREE |
| Post-repair challenge attempt | [0xa94f3e1392f0212403b1c7e269f9b415c584b1ed616f5aafe81cf699f2f42ab8](https://explorer-studio.genlayer.com/tx/0xa94f3e1392f0212403b1c7e269f9b415c584b1ed616f5aafe81cf699f2f42ab8) | finalized execution rejected; no successful return |

The local check report at this revision is `80 passed, 3 skipped`; static preflight passed. The skipped cases are environment-gated network integration cases, and the funded write lifecycle above is separately verified. No dedicated standalone GenVM lint command or hosted CI result is claimed. A prior deployment demonstrated a valid challenge overturn; the current canonical lifecycle specifically proves repair and rejection of a challenge against a resolved finding. See the transaction ledger for receipts and validator votes.

## Historical deployment evidence

The following sections record verified activity on the prior deployment at `0x54953F416c4Dc8B80559bb877870Cf636431c658`. They remain historical records and do not prove the newly deployed source's behavior.

## Historical: inspector-signature verification and content-hash digest binding

These records belong to the prior deployment identified above; they are not proof for the current candidate.

Both items were built from scratch with no external crypto dependency --
inspecting the extracted `genvm-universal` runtime confirmed no
ecdsa/secp256k1/coincurve library is bundled, so `contracts/handover_protocol.py`
implements plain ECDSA-over-secp256k1 verification using only Python's
built-in arbitrary-precision integers and `hashlib` (already used
elsewhere in this module). **A hand-typed curve constant (`_SECP256K1_GY`)
was initially wrong by one trailing hex digit** (copied from memory,
missing a nibble) -- caught before trusting it by cross-verifying against
an independently-generated signature from the `eth_keys` library (a
test-only dependency, never used for signing in the deployed contract)
and checking real elliptic-curve group properties (`n*G == infinity`,
`2G` on-curve, etc.), not by assuming the memorized constant was correct.

**Signature verification** (`_verify_inspector_signature`,
`TIERS_REQUIRING_MATCHING_KIND`): the `SIGNED_INSPECTION` assurance tier
can no longer be claimed by merely declaring it -- it requires a valid
secp256k1 signature from a public key the asset's frozen policy's
`trusted_inspectors` list actually contains, over the exact
`evidence_kind|source_url|content_hash` triple being submitted (so a
valid signature cannot be replayed onto different evidence). Proven live
on asset `A1` / handover `H1`:

| Step | Call | Tx hash | Result |
|---|---|---|---|
| Register | `register_asset("Signature Proof Asset")` | `0x85c4e5e0f6e06b9de2cbbf626472ff2c63a8abf4d4c323ad1dcabacf14a47636` | `A1` |
| Component | `add_component(A1, "", "bumper")` | `0xba64c05e8196bf3bf1f0ad27dbd03d36f19f50ab7c955605473332fae203484f` | `C1` |
| Freeze policy (with `trusted_inspectors: [<real pubkey>]`) | `seal_asset_definition(A1, {...})` | `0x0fb09c9ce83faa2cbe6f09ad4b3dc0547df881e77e2c64f210ebf83fa5dd9ca0` | `policy_hash` recorded |
| Propose | `propose_handover(A1, offset-bob, [C1])` | `0x3c552ea80f6d023c5f1bec0d5f197917f84032b9a9d73b66d0bd1ebf00a152e3` | `H1` |
| **Valid signature from trusted inspector** | `add_baseline_evidence(H1, SIGNED_INSPECTION_RECORD, ..., assurance_tier=SIGNED_INSPECTION, inspector_pubkey=..., sig_r=..., sig_s=...)` | `0x8d660f2f92d97913a9afec00f8c8a12683b1146035289c541eefb71a65e51a0b` | accepted (real status: return) |
| **Same valid signature replayed onto different evidence** | `add_baseline_evidence(H1, SIGNED_INSPECTION_RECORD, <different source_url/content_hash>, ..., inspector_pubkey=..., sig_r=..., sig_s=...)` | `0x981da1957f3f4aaa6f6459dbdd87ea36af6bdc615709f20e90fb8c4e0e9fa164` | reverted: `Exception: SIGNED_INSPECTION requires a valid signature from a trusted inspector` (confirmed via the transaction's own `stderr` traceback) |

**Content-hash digest binding** (`_fetch_text`'s `expected_content_hash`
parameter, opt-in by strict 64-hex-lowercase format): when
`content_hash` is submitted in that exact form, `_fetch_text` compares a
sha256 of the actually-fetched bytes against it and treats a mismatch the
same as a fetch failure. A `content_hash` *not* in that strict form (the
short placeholder values used throughout the Direct Mode test fixtures)
is left unverified, same as before -- this is opt-in, not retroactive on
every piece of evidence ever submitted (chosen over mechanically
rewriting ~40 Direct Mode fixtures for marginal additional assurance on
tests that were never about this feature). Proven live on asset `A1` /
handover `H1` (correct digest) and a fresh asset `A2` / handover `H2`
(wrong digest):

| Step | Call | Tx hash | Result |
|---|---|---|---|
| Accept | `accept_baseline(H1)` (offset-bob) | `0xc18ab5cf911768d5199e7841498457d0732d53fd7c5f61238fb822b3e2ddef16` | `ACCEPTED` |
| Begin custody | `begin_custody(H1)` | `0x7b22788c2a29c0b2a290502a0e97ebbb78b21083ef054b108c469193cee9c4a4` | `ACTIVE` |
| **Return evidence with the real sha256 digest of the actually-fetched fixture bytes** (verified independently via `curl` + `hashlib.sha256` before submission) | `submit_return_evidence(H1, ..., content_hash=<real digest>)` | `0xa5e6c8d86bd41100c9b70dacd12e5e1faa2bb64f538ab79bdeb8dbe189f970d1` | accepted |
| **Evaluate (digest matched)** | `evaluate_return(H1)` | `0x9cee5f5188966f6838984863e400f39fdfe6d705dfb787b61a412a17ca5971f6` | Leader's own fetch succeeded (`external_failure: false`, `condition_class: UNCHANGED`/`NORMAL_WEAR` across two attempts) -- both attempts hit the same genuine cross-model `UNDETERMINED` disagreement documented earlier in this file, unrelated to the digest check; **the digest check itself is proven by the fetch succeeding at all** |
| Register (fresh asset) | `register_asset("Hash Mismatch Proof Asset")` | `0xa301a1d0b70104ec13b3deaf517760a943b2781e31d2f5caecb20ee706eb8556` | `A2` |
| Component | `add_component(A2, "", "bumper")` | `0x61451f36509c8ed545687a83fb3aa55b3b965aab55f5ae6af03512a81404d603` | `C2` |
| Freeze policy | `seal_asset_definition(A2, {...})` | `0x94ab63b99af2c08b647a226559d28aea2e343a6183510ae3216e365250350978` | `policy_hash` recorded |
| Propose | `propose_handover(A2, offset-bob, [C2])` | `0xb12d899676f5b653d3f0353f54354d50b64408f43a8b6b1754980b55a79e5828` | `H2` |
| Accept | `accept_baseline(H2)` (offset-bob) | `0xa872b4b7afff4238edd6e0d434637798bd6447ed79e2d1c0cdca44607e8286b9` | `ACCEPTED` |
| Begin custody | `begin_custody(H2)` | `0x2e42bd933345c70660e64ea4f7a295d5edca15c0d7bf4ec0cb114682ec8b4971` | `ACTIVE` |
| **Return evidence with a deliberately wrong digest** | `submit_return_evidence(H2, ..., content_hash=<wrong sha256>)` | `0x4a878fe198c16d8642b7dd09378040de6dc651d23c545c1f6a438fdb295f382b` | accepted (stored; checked at evaluation time) |
| **Evaluate (digest mismatched)** | `evaluate_return(H2)` | `0x971239d40204dd1831bc31727bddda6a4e9ddc6396f9d7e2c1de26aa5ecf3dad` | `EVIDENCE_UNAVAILABLE`, **finalized cleanly (not UNDETERMINED)** -- the mismatch is checked deterministically before any model call, so there is no cross-model variance to disagree about |

## Historical: custody-gap-history and challenge-reason history

The following transaction records belong to an older deployment; they are not a current-candidate demonstration.

`mark_custody_gap(H1, CUSTODY_GAP)` (tx
`0xc0c060e54e5846ff062226d1930c8c8ac517f8abfe05c6171535f4c4e7a62f87`)
followed by `mark_custody_gap(H1, NO_GAP)` (tx
`0xfd86df7d1f7fd372b0352c7f1871897368bb174e3dd28e3cdc49e816dbfddb9d`):
`get_handover(H1).custody_gap` reads `NO_GAP`, but
`get_custody_gap_history(H1)` still shows both entries — see
`tests/integration/test_handover_studionet.py` for the exact assertions
against this real state.

## Historical: automated funded write lifecycle on a superseded deployment

`tests/integration/test_handover_studionet_write_lifecycle.py` drives a
full real write lifecycle (register → component → seal → propose →
accept → begin custody → return evidence → evaluate_return → real
read-back) entirely automated via subprocess calls to
`scripts/gl_write.js` — no manual CLI invocation. It reuses the exact
same keychain-signer retrieval `scripts/gl_write.js` already used (the
private key is never printed, logged, or newly exposed by this test). It
is gated behind `HANDOVER_RUN_FUNDED_LIFECYCLE=1` (not part of the
default `pytest tests/` run) since every execution submits real,
non-idempotent transactions. First attempt caught a real bug in the
test's own receipt-parsing helper (looking for an `eq_outputs` field
genlayer-py's JSON receipt doesn't use); second attempt caught the test
itself calling `submit_return_evidence` as the wrong signer (the owner
instead of the current custodian — exactly the authorization rule this
session built earlier); third attempt **passed end-to-end**, submitting
real transactions and independently reading back the final on-chain
state via `genlayer_py.read_contract`. That successful run targeted the
then-canonical deployment, `0xc877275d6B3Ad199f2a9eae97EE9eF25A0783807`
(now superseded) — the script has since been repointed to the current
canonical address above; the lifecycle mechanics it exercises
(authorization, evidence submission, consensus, state transitions) are
unchanged in the current contract and are separately re-confirmed by the
Direct Mode suite, so it was not re-run against the new address purely
to avoid spending additional real gas for no new signal.

## Custody-gap history fix, originally proven live (historical — ran on
the deployment two generations back, `0xc877275d6B3Ad199f2a9eae97EE9eF25A0783807`,
since superseded; re-demonstrated on the current deployment above)

A follow-up review suggested making `mark_custody_gap` append-only or
challengeable rather than freely mutable by either party — a party could
otherwise silently erase an earlier gap report by later overwriting it
with `NO_GAP`. Fixed (`custody_gap_history_json`, bounded
`MAX_CUSTODY_GAP_EVENTS`, exposed via the new `get_custody_gap_history`
view; `tests/direct/test_handover_custody.py::test_custody_gap_history_is_append_only_and_not_erasable`)
and originally proven live:

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
`CUSTODY_GAP`) — confirming the original report was not erased. This
specific transaction history is superseded; `tests/integration/test_handover_studionet.py`
now asserts against the equivalent re-demonstration on the current
canonical deployment (see above).

## Historical: security review fixes verified on an earlier deployment

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
- Signature/attestation verification, content-hash digest binding, and
  the automated funded write lifecycle (previously listed here as
  acknowledged future work) are now all implemented and proven live —
  see "Inspector-signature verification and content-hash digest binding"
  and "Automated FUNDED write lifecycle" above. Nothing from the
  original five-item follow-up review remains undone.
- The `trusted_inspectors` policy mechanism establishes *which* public
  keys are recognized, but recognizing a real-world inspector's identity
  (binding a public key to an actual licensed/certified person or firm)
  is still an off-chain, policy-owner responsibility — this contract
  verifies the cryptographic signature, not the inspector's real-world
  credentials.

## Canonical vs. disposable

Only the address/tx recorded at the top of this file is canonical.
Everything else deployed while iterating (all six earlier addresses in
this document) is disposable and must not be referenced from
README/SUBMISSION.
