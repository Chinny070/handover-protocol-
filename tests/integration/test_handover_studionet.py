"""Read-only checks against the current canonical Studionet deployment.

The fresh contract starts with empty storage, so these checks verify ABI
availability and source parity without assuming prior asset IDs or state.
The funded lifecycle test creates and verifies its own records separately.
"""

import shutil
import subprocess
import sys

import pytest

CANONICAL_ADDRESS = "0xB0F0509f35846481622d6A3dEcA0601618FFfC34"
STUDIONET_RPC = "https://studio.genlayer.com/api"


def _cli(command):
    if shutil.which("genlayer") is None:
        pytest.skip("GenLayer CLI not installed")
    argv = [shutil.which("genlayer"), *command]
    cmd = subprocess.list2cmdline(argv) if sys.platform == "win32" else argv
    return subprocess.run(
        cmd, shell=(sys.platform == "win32"), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=90,
    )


def test_canonical_deployment_exposes_required_schema():
    proc = _cli(["schema", CANONICAL_ADDRESS, "--rpc", STUDIONET_RPC])
    if proc.returncode:
        pytest.skip(f"Studionet schema endpoint unavailable: {proc.stderr[-500:]}")
    for method in (
        "accept_baseline", "add_baseline_evidence", "evaluate_return",
        "get_condition_certificate", "get_defect_history", "submit_repair",
    ):
        assert method in proc.stdout


def test_canonical_deployment_source_matches_checkout():
    proc = _cli(["code", CANONICAL_ADDRESS, "--rpc", STUDIONET_RPC])
    if proc.returncode:
        pytest.skip(f"Studionet source endpoint unavailable: {proc.stderr[-500:]}")
    from scripts.source_parity import _extract_source, CONTRACT_PATH

    deployed = _extract_source(proc.stdout).replace("\r\n", "\n").rstrip("\n")
    local = CONTRACT_PATH.read_text(encoding="utf-8").replace("\r\n", "\n").rstrip("\n")
    assert deployed == local
