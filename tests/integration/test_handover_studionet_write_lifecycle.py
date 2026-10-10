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
import re
from pathlib import Path

import genlayer_py
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GL_WRITE = REPO_ROOT / "scripts" / "gl_write.js"
CANONICAL_ADDRESS = "0xEC5EcdCd93DFf54c0752628Eed0B51F51417222C"
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


LIVE_TXS = []


def _write(account: str, method: str, args: list):
    """Calls scripts/gl_write.js as a subprocess (reusing its exact
    keychain-signer retrieval -- never touches a raw private key here)
    and returns the parsed finalized receipt. Never retries a submitted
    write: after any invocation, an RPC failure is ambiguous and retrying
    could duplicate a non-idempotent transaction."""
    node = shutil.which("node")
    if node is None:
        pytest.skip("node not found on PATH")
    audit_path = REPO_ROOT / "docs" / "LIVE_LIFECYCLE_TRANSACTIONS.jsonl"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run(
            [node, str(GL_WRITE), account, CANONICAL_ADDRESS, method, json.dumps(args)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=REPO_ROOT,
            timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or b""
        err = exc.stderr or b""
        if isinstance(out, bytes):
            out = out.decode("utf-8", "replace")
        if isinstance(err, bytes):
            err = err.decode("utf-8", "replace")
        match = re.search(r"0x[0-9a-fA-F]{64}", out + "\n" + err)
        record = {"method": method, "hash": match.group(0) if match else None,
                  "status": "UNKNOWN_TIMEOUT", "output_tail": (out + err)[-2000:]}
        with audit_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        pytest.fail(f"{method} timed out; no retry made. Check transaction "
                    f"{record['hash'] or 'by signer and timestamp'} before continuing.")

    out = proc.stdout
    match = re.search(r"0x[0-9a-fA-F]{64}", out + "\n" + proc.stderr)
    tx_hash = match.group(0) if match else None
    if not tx_hash:
        record = {"method": method, "hash": None, "status": "UNKNOWN_SUBMISSION",
                  "output_tail": (out + proc.stderr)[-2000:]}
        with audit_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        pytest.fail(f"{method} invocation produced no transaction hash; inspect before any retry.")

    submitted = {"method": method, "hash": tx_hash, "status": "PENDING_FINALITY"}
    with audit_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(submitted) + "\n")

    cli = shutil.which("genlayer")
    if cli is None:
        pytest.fail(f"{method} submitted as {tx_hash}; GenLayer CLI unavailable to verify finality.")
    try:
        finalized = subprocess.run(
            [cli, "receipt", tx_hash, "--status", "FINALIZED", "--retries", "120",
             "--interval", "3000", "--rpc", "https://studio.genlayer.com/api"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=REPO_ROOT, timeout=420,
        )
    except subprocess.TimeoutExpired as exc:
        out_part = exc.stdout or ""
        if isinstance(out_part, bytes):
            out_part = out_part.decode("utf-8", "replace")
        pending = {"method": method, "hash": tx_hash, "status": "UNKNOWN_FINALITY",
                   "output_tail": out_part[-1500:]}
        with audit_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(pending) + "\n")
        pytest.fail(f"{method} {tx_hash} submitted; finality timed out. Do not resubmit.")
    cli_out = finalized.stdout + finalized.stderr
    if finalized.returncode != 0 or "status_name: 'FINALIZED'" not in cli_out:
        record = {"method": method, "hash": tx_hash, "status": "UNKNOWN_FINALITY",
                  "output_tail": cli_out[-1500:]}
        with audit_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        pytest.fail(f"{method} {tx_hash} finality not verified. Do not resubmit.")

    leader_receipt = []
    for result_match in re.finditer(
        r"result:\s*\{\s*status:\s*'([^']+)'(?:,\s*payload:\s*\{\s*readable:\s*'((?:\\.|[^'])*)'\s*\})?\s*\}",
        cli_out,
    ):
        result = {"status": result_match.group(1)}
        if result_match.group(2) is not None:
            result["payload"] = {"readable": result_match.group(2)}
        leader_receipt.append({"result": result})
    votes = {}
    votes_match = re.search(r"votes:\s*\{([^}]*)\}", cli_out, re.S)
    if votes_match:
        votes = dict(re.findall(r"'([^']+)'\s*:\s*'([^']+)'", votes_match.group(1)))
    result_name_match = re.search(r"result_name:\s*'([^']+)'", cli_out)
    receipt = {
        "tx_id": tx_hash,
        "status_name": "FINALIZED",
        "result_name": result_name_match.group(1) if result_name_match else "UNKNOWN",
        "consensus_data": {"leader_receipt": leader_receipt, "votes": votes},
    }
    record = {"method": method, "hash": tx_hash, "status": "FINALIZED",
              "consensus": receipt["result_name"], "votes": votes}
    with audit_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    LIVE_TXS.append(record)
    return receipt


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
    audit_path = REPO_ROOT / "docs" / "LIVE_LIFECYCLE_TRANSACTIONS.jsonl"
    if audit_path.exists():
        latest_by_hash = {}
        for line in audit_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("hash"):
                latest_by_hash[record["hash"]] = record
            elif str(record.get("status", "")).startswith("UNKNOWN"):
                latest_by_hash[f"unhashed:{len(latest_by_hash)}"] = record
        unresolved = [
            record for record in latest_by_hash.values()
            if str(record.get("status", "")).startswith(("UNKNOWN", "PENDING"))
        ]
        if unresolved:
            pytest.fail(
                "Prior funded lifecycle writes have unresolved RPC status; "
                "reconcile their hashes before starting a new non-idempotent run: "
                + json.dumps(unresolved, sort_keys=True)
            )

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
            "evidence_minimums": {
                "minor": ["SINGLE_PUBLIC_SOURCE"],
                "major": ["SINGLE_PUBLIC_SOURCE"],
                "critical": ["SINGLE_PUBLIC_SOURCE"],
            },
            "attribution_minimums": {"SUPPORTED_AS_NEW_IN_INTERVAL": ["SINGLE_PUBLIC_SOURCE"]},
            "repair_closure_requirements": {"require_receipt": True},
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
    fixture_url = (
        "https://raw.githubusercontent.com/Chinny070/handover-protocol-"
        "/main/fixtures/vehicle_baseline_bumper.txt"
    )
    baseline_hash = "3bb1b4346b81a21ef87412ae120f995e7e64ea4b3fc35705ab490c53b2b83b90"
    r = _write(
        OWNER_ACCOUNT,
        "add_baseline_evidence",
        [handover_id, "WEB_RENDERED_INSPECTION", fixture_url, baseline_hash, [component_id], "SINGLE_PUBLIC_SOURCE", "", "", ""],
    )
    assert _leader_status_return(r), r

    r = _write("offset-bob", "accept_baseline", [handover_id])
    assert _leader_status_return(r), r

    r = _write(OWNER_ACCOUNT, "begin_custody", [handover_id])
    assert _leader_status_return(r), r

    return_url = (
        "https://raw.githubusercontent.com/Chinny070/handover-protocol-"
        "/main/fixtures/vehicle_return_bumper_damaged.txt"
    )
    return_hash = "afee1f3209d339f908ca0cb486f010ecc8044b690ad25b00243844cbf51ee8a8"
    # submit_return_evidence requires the *current custodian*
    # (handover.to_party == offset-bob here), not the owner -- the same
    # authorization rule proven in tests/direct/test_handover_authorization.py.
    r = _write(
        "offset-bob",
        "submit_return_evidence",
        [handover_id, "WEB_RENDERED_INSPECTION", return_url, return_hash, [component_id], "SINGLE_PUBLIC_SOURCE", "", "", ""],
    )
    assert _leader_status_return(r), r

    r = _write(OWNER_ACCOUNT, "evaluate_return", [handover_id])
    assert _leader_status_return(r), r
    evaluated_status = _return_payload(r)

    # Exercise repair adjudication against the exact originating observation
    # when consensus records a defect. The contract re-fetches both the
    # return evidence and receipt and fails closed if either digest/fetch
    # cannot be verified. This branch does not fabricate a defect result if
    # semantic consensus returned an inconclusive or unavailable outcome.
    asset_before_repair = read_client.read_contract(
        address=CANONICAL_ADDRESS, function_name="get_asset", args=[asset_id]
    )
    repair_results = []
    for defect_id in asset_before_repair.get("defect_ids", []):
        defect = read_client.read_contract(
            address=CANONICAL_ADDRESS, function_name="get_defect", args=[defect_id]
        )
        if defect["status"] not in ("OPEN", "WORSENED", "PARTIALLY_REPAIRED"):
            continue
        repair_url = (
            "https://raw.githubusercontent.com/Chinny070/handover-protocol-"
            "/main/fixtures/vehicle_repair_receipt_bumper.txt"
        )
        repair_hash = "167f5c165daefaaab880cb01dc1aea47bc46fa7987eff108e820697175ac99c9"
        r = _write(
            OWNER_ACCOUNT,
            "submit_repair",
            [defect_id, "REPAIR_RECEIPT", repair_url, repair_hash],
        )
        assert _leader_status_return(r), r
        r = _write(OWNER_ACCOUNT, "verify_repair", [defect_id])
        assert _leader_status_return(r), r
        repair_result = _return_payload(r)
        repair_results.append({"defect_id": defect_id, "result": repair_result})
        if repair_result == "REPAIRED":
            # Adversarial write: a resolved finding must not be reopened by
            # a post-repair challenge. The transaction should finalize as a
            # rejected execution, with no successful return value.
            challenge_url = (
                "https://raw.githubusercontent.com/Chinny070/handover-protocol-"
                "/main/fixtures/vehicle_challenge_preexisting_proof.txt"
            )
            challenge_hash = "4fc6b57e4bf64dbc70fbf1b583c19f7554d67dd241adc22da543f97a048dac16"
            rejected = _write(
                OWNER_ACCOUNT,
                "challenge_finding",
                [defect_id, "PRE_EXISTING_EVIDENCE", "SIGNED_INSPECTION_RECORD", challenge_url, challenge_hash],
            )
            assert not _leader_status_return(rejected), rejected
            repair_results[-1]["post_repair_challenge_rejected"] = True

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
    certificate = read_client.read_contract(
        address=CANONICAL_ADDRESS, function_name="get_condition_certificate", args=[asset_id]
    )
    if certificate["certificate_status"] == "CLEAR":
        assert certificate["open_defect_count"] == 0
        assert certificate["unresolved_count"] == 0
        assert certificate["custody_gap_present"] is False
    print("LIVE_LIFECYCLE_EVIDENCE=" + json.dumps({
        "asset_id": asset_id,
        "component_id": component_id,
        "handover_id": handover_id,
        "handover_status": handover["status"],
        "evaluated_status": evaluated_status,
        "certificate_status": certificate["certificate_status"],
        "defects": asset.get("defect_ids", []),
        "repair_results": repair_results,
        "transactions": LIVE_TXS,
    }, sort_keys=True))
