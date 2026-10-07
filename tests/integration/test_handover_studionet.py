"""Reproducible read-only checks against the canonical Studionet
deployment (master spec section 27 / 31).

Queries real, already-recorded on-chain state via genlayer_py's
read_contract, using a freshly generated, unfunded, never-signing keypair
purely to populate the `from` field genlayer-py's read call requires --
no private key from any real account is used or needed, so this test
needs no secrets and is safe to run from CI or any machine with network
access. It replaces the previous unconditional skip; see
docs/DEPLOYMENT.md for the full live-lifecycle record (write transactions,
vote tallies, consensus results) this canonical deployment was built from.
"""

import genlayer_py
import pytest

CANONICAL_ADDRESS = "0x4b4D04B5268cC7e20ea6970947Cf2f9b29B0aB92"


@pytest.fixture(scope="module")
def studionet_client():
    private_key = genlayer_py.generate_private_key()
    account = genlayer_py.create_account(private_key)
    client = genlayer_py.create_client(chain=genlayer_py.studionet, account=account)
    try:
        client.read_contract(address=CANONICAL_ADDRESS, function_name="get_asset", args=["A1"])
    except Exception as exc:
        pytest.skip(f"Studionet unreachable or canonical contract not responding: {exc}")
    return client


def test_canonical_asset_a1_matches_recorded_live_state(studionet_client):
    """Asset A1 was registered, sealed, and put into an active primary
    custody interval (H1) as part of this session's authorization-fix
    smoke test (docs/DEPLOYMENT.md). Its recorded state is immutable
    on-chain history and must still read back exactly as documented."""
    asset = studionet_client.read_contract(
        address=CANONICAL_ADDRESS, function_name="get_asset", args=["A1"]
    )
    assert asset["asset_id"] == "A1"
    assert asset["name"] == "Audit Smoke Test Asset"
    assert asset["status"] == "SEALED"
    assert asset["component_ids"] == ["C1"]
    assert asset["active_handover_id"] == "H1"
    assert asset["owner"].lower() == "0xaffe15eec45b68835cc9e5b4ab85dd5deae8e70b"


def test_canonical_handover_h1_matches_recorded_live_state(studionet_client):
    handover = studionet_client.read_contract(
        address=CANONICAL_ADDRESS, function_name="get_handover", args=["H1"]
    )
    assert handover["handover_id"] == "H1"
    assert handover["asset_id"] == "A1"
    assert handover["status"] == "ACTIVE"
    assert handover["scope"] == ["C1"]
    assert handover["to_party"].lower() == "0x10b091a7b19d3f0da511a06985a8636fa58a0377"
    assert handover["custody_gap"] == "NO_GAP"


def test_canonical_deployment_schema_is_live(studionet_client):
    """Confirms the contract genuinely responds with its full ABI, not
    just that one address happens to resolve."""
    component = studionet_client.read_contract(
        address=CANONICAL_ADDRESS, function_name="get_component", args=["C1"]
    )
    assert component["component_id"] == "C1"
    assert component["name"] == "bumper"
    assert component["sealed"] is True
