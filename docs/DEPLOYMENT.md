# DEPLOYMENT.md

## Status: deployed to Studionet (Gate 1 proof)

**Canonical contract address:** `0x796bfBD33C7fFD8330F8ff6cCD46681B7E938ACe`
**Deployment transaction:** `0x491be3b3d45bf875e3c968e6eec273362125652650386c9733cba48f6f14a2b1`
**Network:** Genlayer Studio Network (`studionet`, chainId `61999`)
**Explorer:** https://genlayer-explorer.vercel.app (search the tx hash or
address above)
**Deployer account:** `0xaffE15eEc45b68835cc9E5B4Ab85dD5deaE8e70b`
(`my-studionet-wallet`)

Verified independently (not just the CLI's own "deployed successfully"
message — see the first attempt below for why that distinction matters):

- `genlayer receipt <tx>` → `status_name: 'FINALIZED'`,
  `result_name: 'MAJORITY_AGREE'`, leader result
  `{ status: 'return', payload: null }` (i.e. `__init__` actually returned
  successfully, not merely that consensus finalized on *some* outcome).
- `genlayer schema <address>` → returns the full expected ABI (all public
  write/view methods with correct param/return types).
- `python scripts/source_parity.py` → `PASS`: the deployed source is
  byte-for-byte identical to `contracts/handover_protocol.py` in this
  working tree (verified via `genlayer code <address>`, not assumed).

## A real failure, caught and fixed before trusting the deploy

The first deployment attempt used `# { "Depends": "py-genlayer:latest" }`
as the dependency header (copied from the spec's example syntax). The CLI
printed `✔ Contract deployed successfully` and the receipt showed
`status_name: 'FINALIZED'` / `result_name: 'MAJORITY_AGREE'` — which on
their own look like success. Per this repo's own "never fabricate
verification" rule, that claim was checked anyway:

- `genlayer code <address>` and `genlayer schema <address>` both returned
  `Contract <address> not found`.
- The full receipt's `leader_receipt[].result` was
  `{ status: 'contract_error', payload: 'invalid_contract' }` — the
  validators had reached majority agreement that deployment **failed**,
  not that it succeeded. `MAJORITY_AGREE`/`FINALIZED` describe consensus
  on an outcome, not which outcome.

Root cause: `"latest"` is not a deterministically resolvable dependency
pin on Studionet's live GenVM. Comparing against a previously-successful
sibling project's contract header
(`C:\Users\USERpc\continuum\contracts\continuum_protocol.py`) showed the
correct form pins an exact content hash. The locally cached Direct-Mode
runtime (`~/.cache/gltest-direct/extracted/v0.2.16/py-genlayer/`) uses the
identical hash, confirming it's the right pin for this environment's
v0.2.16 runtime:

```python
# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
```

`contracts/handover_protocol.py` was corrected to this pin, the Direct
Mode suite was re-run (47/47 still green), and the corrected contract was
redeployed — producing the canonical address/tx above, this time verified
`FOUND` and schema/source-parity green.

The disposable first deployment (`0x8620488e78b6E9FF4E7f583C7611c162C28A59f1`,
tx `0x649ab65790a719858463ac3f65d088e6f0b996ede2ca07c93879dcc999f2693a`)
is **not** canonical and must not be referenced from README/SUBMISSION.

## What's still outstanding

- **Live handover lifecycle proof** (section 31 of the master spec):
  register asset → components → frozen policy → baseline propose/accept →
  begin custody → return evidence → real validator consensus → typed
  condition delta → defect lineage case → read the Condition Certificate →
  at least one negative/fail-closed case. Not yet run against this
  deployment — see `scripts/live_verify.py` (stub) and
  `tests/integration/test_handover_studionet.py` (skipped).
- **GenVM lint/schema validation** beyond "schema loads": no deeper
  static-analysis subcommand was discoverable in this `genlayer` CLI
  version; `schema` loading successfully against the live deployment is
  the strongest check available.
- Evidence-assurance-tier enforcement and `_classify_challenge` wiring —
  see `docs/SECURITY.md` → Limitations.

## Canonical vs. disposable

Only the address/tx recorded at the top of this file is canonical.
Anything deployed while iterating (including the first, failed attempt
above) is disposable and must not be referenced from README/SUBMISSION.
