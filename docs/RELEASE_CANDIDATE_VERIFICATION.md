# RELEASE_CANDIDATE_VERIFICATION.md

Honest record of what was verified in this build session versus what
remains for a follow-on session, per the master spec's "never fabricate
verification" rule.

## Environment discovered

- `genlayer` CLI: **0.39.2** (npm global install,
  `C:\Users\USERpc\AppData\Roaming\npm\node_modules\genlayer`).
- `genlayer-py` (Python client SDK): **0.16.3**.
- `genlayer-test` (`gltest`, Direct Mode + Studio Mode test harness):
  **0.29.2**.
- Python: **3.12.10**.
- The contract-facing SDK (`import genlayer` / `genlayer.gl.*`,
  `genlayer.py.*`) is **not** a standalone pip package; `gltest`'s Direct
  Mode downloads the matching `genvm-universal` release tarball from
  `github.com/genlayerlabs/genvm/releases` (pinned by the contract
  header's `{"Depends": "py-genlayer:<hash-or-"latest">"}` comment) and
  extracts it on demand. This succeeded in this environment (network
  access confirmed) and cached `v0.2.16` locally at
  `~/.cache/gltest-direct/`.

## Clean-clone reproducibility: verified

A fresh `gh repo clone Chinny070/handover-protocol-` into a separate
directory, a fresh `python -m venv .venv-test`, a plain
`pip install -r requirements-test.txt`, then `pytest tests/ -v`: **55
passed, 1 skipped**, identical to the primary working tree. No
local-machine state, cached account, or absolute path outside
`scripts/gl_write.js` (which resolves the `genlayer` CLI's install
directory dynamically via `npm root -g`, overridable via
`GENLAYER_CLI_DIR`, rather than hardcoding a path) is required to
reproduce the Direct Mode suite.

## API verified empirically (not assumed from the spec's example syntax)

The spec explicitly warned that example GenLayer syntax may be stale. We
did not trust `genlayer`'s own bundled `football_bets.py` template at face
value either — running it in Direct Mode exposed that its flat
`gl.exec_prompt(...)` / `gl.get_webpage(...)` / `gl.eq_principle_strict_eq(...)`
calls do not exist on the currently-downloaded `v0.2.16` runtime. By
reading the extracted SDK source directly
(`genlayer/gl/__init__.py`, `genlayer/gl/nondet/__init__.py`,
`genlayer/gl/nondet/web.py`, `genlayer/gl/vm.py`,
`genlayer/gl/eq_principle.py`) we confirmed the actual current API used
throughout `contracts/handover_protocol.py`:

- `gl.nondet.web.get(url)` → `Response(status, headers, body)` (eager call,
  no `.get()` needed — `.lazy(...)` is the Lazy-returning variant, not the
  default).
- `gl.nondet.exec_prompt(prompt, response_format="json")` → `str | dict`
  (same eager/`.lazy` distinction).
- `gl.vm.run_nondet_unsafe(leader_fn, validator_fn)` → runs `leader_fn()`
  as the leader, `validator_fn(Result)` as the independent validator
  check; this is the "generic" consensus primitive section 18 of the
  master spec calls for (a substantive custom validator, not `strict_eq`
  over prose).
- `@gl.public.write` / `@gl.public.view` method decorators, `gl.Contract`
  base class, `TreeMap`/`DynArray`/`Array` storage collections, `Address`,
  `u256`, `@allow_storage @dataclass` for storage-backed record types — all
  confirmed by successfully deploying and exercising
  `contracts/handover_protocol.py` under `gltest.direct`.

## Direct Mode + integration: green

```text
collected: 72
passed: 72
failed: 0
skipped: 0
duration: ~30-55s (full suite, includes 4 real Studionet network reads)
Python: 3.12.10
genlayer-test: 0.29.2
genlayer-py: 0.16.3
command: pytest tests/ -v
```

Breakdown by file:

- `test_handover_protocol.py` — 11 passed (registration, component graph
  bounds/cycle rejection, seal/policy validation, baseline propose/accept/
  dispute/immutability, custody begin/overlap rejection, evaluate_return
  terminal states RETURN_CLEAR/DEFECTS_RECORDED/EVIDENCE_UNAVAILABLE
  (including a deterministic-by-HTTP-status-code case added after the
  live Studionet run surfaced the original implementation's gap — see
  docs/DEPLOYMENT.md), certificate basics, close_handover gating).
- `test_handover_custody.py` — 5 passed (delegation scope-subset
  enforcement, delegation depth bound, custody-gap recording and
  certificate reflection, unknown gap-state rejection, custody-gap
  history append-only and not erasable by a later overwrite).
- `test_handover_defects.py` — 7 passed (contract-assigned sequential
  defect IDs, worsening with append-only history, invented-matched-id
  fail-closed, bounded challenge rounds, unknown challenge-reason
  rejection, real challenge OVERTURNED by fresh contradicting evidence,
  challenge with unreachable evidence fails closed to EXTERNAL_FAILURE).
- `test_handover_hardening.py` — 15 passed (malformed JSON, fenced JSON
  recovery, missing keys, smuggled extra fields, unknown enum, bool-for-int,
  float-for-int, truthy-string-for-bool, int-for-bool, invented
  evidence-id-shaped field, invented matched-defect-id, oversized
  rationale list, non-dict payload, empty string payload, prompt-injection
  text proven inert).
- `test_handover_consensus.py` — 9 passed (eight distinct forged-leader
  rejection cases via `direct_vm.run_validator` — including a
  `matched_defect_id`-mismatch case and a forged-challenge-OVERTURNED
  case, both found and fixed/tested during post-build review — plus one
  honest-leader acceptance sanity check).
- `test_handover_repairs.py` — 5 passed (repaired, not-repaired reopening,
  external-failure-is-not-repaired-or-failure, bounded repair rounds,
  re-submission gating).
- `test_handover_evidence_assurance.py` — 4 passed (CRITICAL finding on
  SELF_REPORTED evidence fails closed to INCONCLUSIVE, the same finding
  on SIGNED_INSPECTION evidence is accepted, unknown assurance tier
  rejected at submission, missing policy coverage for a severity fails
  closed).
- `test_handover_authorization.py` — 12 passed (stranger/owner/custodian
  matrix for every write method found unauthorized during the external
  security review: primary-proposal owner check, delegation custodian
  check, baseline/return evidence party checks, begin_custody/
  mark_custody_gap/evaluate_return/close_handover party checks,
  challenge/repair/verify_repair defect-party checks, and
  previously-untested cancel_handover coverage).
- `tests/integration/test_handover_studionet.py` — 4 passed (real
  `genlayer_py.read_contract` calls against the canonical Studionet
  deployment, using a freshly generated never-signing keypair; asserts
  on asset A1 / handover H1's exact recorded live state, including that
  `get_custody_gap_history` still shows an earlier gap report that was
  later overwritten in the live field — see docs/DEPLOYMENT.md).

## Pickling validation: green

`gltest.direct`'s `VMContext.check_pickling` flag validates that every
`run_nondet_unsafe(leader_fn, validator_fn)` closure is actually
picklable — the same constraint real multi-process GenVM execution
imposes. Enabled session-wide via an autouse fixture in
`tests/direct/conftest.py` rather than left as a one-off opt-in, so every
test (not just a dedicated one) proves this. All 55 tests pass with it
enabled.

## Windows Direct Mode tempfile/unlink issue (spec section 17)

Reproduced exactly as documented: `gltest`'s stdin-injection helper
(`_inject_message_to_fd0`) duplicates a temp file onto fd 0 and then tries
to `os.unlink` it while the duplicate handle is still open — Windows
raises `PermissionError: [WinError 32]`, before any contract code runs.
Confirmed by temporarily reverting a local patch and reproducing the
failure, then fixing it generically via
`tests/direct/conftest.py` (makes `os.unlink` tolerate `PermissionError`
on `win32` for the test session, rather than depending on whichever copy
of `genlayer-test` happens to already carry a fix). Verified green both
with and without a pre-patched `gltest` install.

## Studionet deployment and live lifecycle: now done

A follow-on session deployed the canonical contract to Studionet, caught
and fixed a real bug this way (`_fetch_text` not checking HTTP status —
see `docs/DEPLOYMENT.md`), and ran the full live handover lifecycle:
baseline propose/accept, custody, real leader/validator consensus over
public GitHub fixture evidence, a genuine condition-delta + defect +
repair cycle, a genuine case of validator disagreement
(`UNDETERMINED`, correctly not committed to state), and a genuine
negative/fail-closed case (404 evidence → `EVIDENCE_UNAVAILABLE`). See
`docs/DEPLOYMENT.md` for the full record with real addresses,
transaction hashes, and vote tallies — nothing there is fabricated or
assumed from a CLI success message.

## What is still NOT run

- GenVM AST lint / full static schema validation beyond "schema loads
  against the live deployment": no standalone static-lint subcommand was
  discoverable in this `genlayer` CLI version (0.39.2).
- `scripts/live_verify.py` remains an honest stub; the live lifecycles
  documented in `docs/DEPLOYMENT.md` were driven by hand via
  `scripts/gl_write.js` and the `genlayer` CLI's `call`/`receipt`
  commands, not by a single automated write-driving script.
  `tests/integration/test_handover_studionet.py` now runs for real
  (3/3 passed, no skip), but only covers read-only state checks against
  the canonical deployment, not a fully automated end-to-end write
  lifecycle — that still needs a funded signer.
- `content_hash` is not cryptographically verified against fetched
  evidence bytes — explicitly documented as caller-asserted only (see
  `docs/DEPLOYMENT.md` → "Security review fixes" and
  `docs/SECURITY.md` → Limitations), chosen over mechanically rewriting
  ~40 Direct Mode test fixtures for marginal additional assurance.

## Visual/image claims

None made. No vision/image test exists in this release; see
`docs/EVIDENCE.md` → "Physical-World Limitations" and HP17.
