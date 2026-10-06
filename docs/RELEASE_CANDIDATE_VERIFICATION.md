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

## Direct Mode: green

```text
collected: 46
passed: 46
failed: 0
skipped: 0
duration: ~13-14s (full suite, warm SDK cache)
Python: 3.12.10
genlayer-test: 0.29.2
command: pytest tests/direct/ -v
```

Breakdown by file:

- `test_handover_protocol.py` — 10 passed (registration, component graph
  bounds/cycle rejection, seal/policy validation, baseline propose/accept/
  dispute/immutability, custody begin/overlap rejection, evaluate_return
  terminal states RETURN_CLEAR/DEFECTS_RECORDED/EVIDENCE_UNAVAILABLE,
  certificate basics, close_handover gating).
- `test_handover_custody.py` — 4 passed (delegation scope-subset
  enforcement, delegation depth bound, custody-gap recording and
  certificate reflection, unknown gap-state rejection).
- `test_handover_defects.py` — 5 passed (contract-assigned sequential
  defect IDs, worsening with append-only history, invented-matched-id
  fail-closed, bounded challenge rounds, unknown challenge-reason
  rejection).
- `test_handover_hardening.py` — 15 passed (malformed JSON, fenced JSON
  recovery, missing keys, smuggled extra fields, unknown enum, bool-for-int,
  float-for-int, truthy-string-for-bool, int-for-bool, invented
  evidence-id-shaped field, invented matched-defect-id, oversized
  rationale list, non-dict payload, empty string payload, prompt-injection
  text proven inert).
- `test_handover_consensus.py` — 7 passed (five distinct forged-leader
  rejection cases via `direct_vm.run_validator`, plus one honest-leader
  acceptance sanity check).
- `test_handover_repairs.py` — 5 passed (repaired, not-repaired reopening,
  external-failure-is-not-repaired-or-failure, bounded repair rounds,
  re-submission gating).

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

## What was NOT run (explicitly out of scope this session)

- GenVM AST lint / full schema validation: the `genlayer` CLI's `schema`
  subcommand operates on an already-deployed contract address against a
  running node (localnet simulator or Studionet); no standalone
  static-lint subcommand was discoverable. Running it would require
  either `genlayer up` (local simulator) or a live Studionet deployment,
  both out of this session's explicit scope.
- Any Studionet deployment, GitHub push, PR, or issue creation — all
  explicitly excluded from this session's task.
- `tests/integration/test_handover_studionet.py` and
  `scripts/{preflight,live_verify,source_parity}.py` are stubs (see
  `docs/DEPLOYMENT.md`) pending a follow-on session that is allowed to
  deploy.

## Visual/image claims

None made. No vision/image test exists in this release; see
`docs/EVIDENCE.md` → "Physical-World Limitations" and HP17.
