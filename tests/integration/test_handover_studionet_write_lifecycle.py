"""Automated FUNDED write lifecycle against Studionet (section: "automate
a funded write lifecycle on Studionet if the tooling/environment makes
that practical").

This environment already has a funded Studionet signer stored safely in
the OS keychain (the `my-studionet-wallet` account `genlayer account`
manages), and `scripts/gl_write.js` already retrieves it the same way the
`genlayer` CLI itself does -- the private key is never printed or logged.
This test reuses that exact mechanism via subprocess, so it introduces no
new secret-handling surface.

Every run of this test submits real transactions to Studionet (gas cost,
new on-chain asset/handover/defect records) -- it is NOT part of the
default `pytest tests/` run. It only executes when
`HANDOVER_RUN_FUNDED_LIFECYCLE=1` is set in the environment, and skips
cleanly (not an error) otherwise, including when `node`/`genlayer` aren't
on PATH or the keychain account isn't unlocked. Run explicitly with:

    HANDOVER_RUN_FUNDED_LIFECYCLE=1 pytest tests/integration/test_handover_studionet_write_lifecycle.py -v
"""

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import genlayer_py
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GL_WRITE = REPO_ROOT / "scripts" / "gl_write.js"
CANONICAL_ADDRESS = "0x54953F416c4Dc8B80559bb877870Cf636431c658"
OWNER_ACCOUNT = "my-studionet-wallet"
RENTER_ADDRESS = "0x10b091a7b19d3f0da511a06985a8636fa58a0377"  # offset-bob

pytestmark = pytest.mark.skipif(
    os.environ.get("HANDOVER_RUN_FUNDED_LIFECYCLE") != "1",
    reason=(
        "Submits real funded transactions to Studionet (gas cost, new "
        "on-chain records). Opt in explicitly with "
        "HANDOVER_RUN_FUNDED_LIFECYCLE=1."
    ),
)


def _write(account: str, method: str, args: list, retries: int = 3):
    """Calls scripts/gl_write.js as a subprocess (reusing its exact
    keychain-signer retrieval -- never touches a raw private key here)
    and returns the parsed receipt dict. Retries on transient RPC errors
    (observed throughout this project's live work: 500s, rate limits)."""
    node = shutil.which("node")
    if node is None:
        pytest.skip("node not found on PATH")
    last_err = None
    for attempt in range(retries):
        proc = subprocess.run(
            [node, str(GL_WRITE), account, CANONICAL_ADDRESS, method, json.dumps(args)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=REPO_ROOT,
            timeout=120,
        )
        out = proc.stdout
        if proc.returncode == 0 and '"status_name"' in out:
            receipt = json.loads(out[out.index("{") :])
            return receipt
        last_err = proc.stdout + proc.stderr
        time.sleep(5 * (attempt + 1))
    pytest.fail(f"gl_write.js failed after {retries} attempts for {method}: {last_err[-2000:]}")


def _leader_status_return(receipt: dict) -> bool:
    for entry in receipt.get("consensus_data", {}).get("leader_receipt", []):
        if entry.get("result", {}).get("status") == "return":
            return True
    return False


def _return_payload(receipt: dict) -> str:
    """Extracts the leader's returned value's `readable` string (still
    JSON-encoded, e.g. '"A2"') from the first leader_receipt entry whose
    result.status is 'return'."""
    for entry in receipt.get("consensus_data", {}).get("leader_receipt", []):
        result = entry.get("result", {})
        if result.get("status") == "return":
            payload = result.get("payload")
            if isinstance(payload, dict) and "readable" in payload:
                return json.loads(payload["readable"])
    return None


@pytest.fixture(scope="module")
def read_client():
    private_key = genlayer_py.generate_private_key()
    account = genlayer_py.create_account(private_key)
    return genlayer_py.create_client(chain=genlayer_py.studionet, account=account)


def test_full_funded_write_lifecycle(read_client):
    """register -> component -> seal -> propose -> accept -> begin ->
    return evidence -> evaluate_return -> real state readback, fully
    automated, no manual CLI invocation."""
    suffix = str(int(time.time()))
    asset_name = f"Automated Lifecycle Test {suffix}"

    r = _write(OWNER_ACCOUNT, "register_asset", [asset_name])
    assert _leader_status_return(r), r
    asset_id = _return_payload(r)
    assert asset_id, f"could not determine asset_id from receipt: {r}"

    r = _write(OWNER_ACCOUNT, "add_component", [asset_id, "", "bumper"])
    assert _leader_status_return(r), r
    component_id = _return_payload(r)
    assert component_id, f"could not determine component_id from receipt: {r}"

    policy = json.dumps(
        {
            "component_rules": {"bumper": "cosmetic"},
            "wear_budget": {},
            "evidence_minimums": {"minor": ["SELF_REPORTED"]},
            "attribution_minimums": {},
            "repair_closure_requirements": {},
            "challenge_window": 3,
        }
    )
    r = _write(OWNER_ACCOUNT, "seal_asset_definition", [asset_id, policy])
    assert _leader_status_return(r), r

    r = _write(
        OWNER_ACCOUNT, "propose_handover", [asset_id, RENTER_ADDRESS, [component_id], ""]
    )
    assert _leader_status_return(r), r
    handover_id = _return_payload(r)
    assert handover_id, f"could not determine handover_id from receipt: {r}"

    # offset-bob (RENTER_ADDRESS) must accept -- its key is a pre-existing
    # genlayer account in this environment ("offset-bob"), same pattern
    # used throughout docs/DEPLOYMENT.md's manual runs.
    r = _write("offset-bob", "accept_baseline", [handover_id])
    assert _leader_status_return(r), r

    r = _write(OWNER_ACCOUNT, "begin_custody", [handover_id])
    assert _leader_status_return(r), r

    fixture_url = (
        "https://raw.githubusercontent.com/Chinny070/handover-protocol-"
        "/main/fixtures/vehicle_baseline_bumper.txt"
    )
    # submit_return_evidence requires the *current custodian*
    # (handover.to_party == offset-bob here), not the owner -- the same
    # authorization rule proven in tests/direct/test_handover_authorization.py.
    r = _write(
        "offset-bob",
        "submit_return_evidence",
        [handover_id, "WEB_RENDERED_INSPECTION", fixture_url, "x", [component_id], "SELF_REPORTED"],
    )
    assert _leader_status_return(r), r

    r = _write(OWNER_ACCOUNT, "evaluate_return", [handover_id])
    assert _leader_status_return(r), r

    # Real, independent read-back confirming the automated write lifecycle
    # actually landed on-chain, not just that the CLI reported success.
    asset = read_client.read_contract(address=CANONICAL_ADDRESS, function_name="get_asset", args=[asset_id])
    assert asset["asset_id"] == asset_id
    assert asset["name"] == asset_name
    assert asset["status"] == "SEALED"

    handover = read_client.read_contract(
        address=CANONICAL_ADDRESS, function_name="get_handover", args=[handover_id]
    )
    assert handover["handover_id"] == handover_id
    assert handover["status"] in ("RETURN_CLEAR", "DEFECTS_RECORDED", "INCONCLUSIVE", "EVIDENCE_UNAVAILABLE")
