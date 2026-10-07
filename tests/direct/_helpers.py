"""Shared Direct Mode test helpers (not collected as tests themselves)."""

import hashlib
import json
from pathlib import Path

from gltest.direct import deploy_contract, create_address

CONTRACT_PATH = Path(__file__).resolve().parents[2] / "contracts" / "handover_protocol.py"

# A fixed test keypair standing in for a "trusted inspector" (section:
# "verify signatures/attestations for high-assurance evidence"). Test-only
# private key, never used for anything real; eth_keys is a test dependency
# used only to produce valid signatures for the contract's pure-Python
# secp256k1 verifier to check -- the contract itself never signs anything,
# only verifies.
from eth_keys import keys as _eth_keys

TEST_INSPECTOR_PRIVATE_KEY = _eth_keys.PrivateKey(b"\x11" * 32)
TEST_INSPECTOR_PUBKEY_HEX = ("04" + TEST_INSPECTOR_PRIVATE_KEY.public_key.to_bytes().hex())


def sign_as_inspector(evidence_kind: str, source_url: str, content_hash: str):
    """Signs the exact canonical message contracts/handover_protocol.py's
    _inspector_signing_message constructs, so the contract's verifier
    accepts it. Returns (pubkey_hex, sig_r_hex, sig_s_hex)."""
    message = f"{evidence_kind}|{source_url}|{content_hash}".encode("utf-8")
    digest = hashlib.sha256(message).digest()
    sig = TEST_INSPECTOR_PRIVATE_KEY.sign_msg_hash(digest)
    return TEST_INSPECTOR_PUBKEY_HEX, hex(sig.r), hex(sig.s)


DEFAULT_POLICY = {
    "component_rules": {"bumper": "cosmetic", "engine": "functional"},
    "wear_budget": {"scuff_mm": 5, "scratch_count": 2},
    "evidence_minimums": {
        "minor": ["SELF_REPORTED"],
        "major": ["SELF_REPORTED", "SIGNED_INSPECTION"],
        "critical": ["SIGNED_INSPECTION"],
    },
    "attribution_minimums": {"supported": ["WEB_RENDERED_INSPECTION"]},
    "repair_closure_requirements": {"receipt": True},
    "challenge_window": 3,
    "trusted_inspectors": [TEST_INSPECTOR_PUBKEY_HEX],
}


def default_policy_json() -> str:
    return json.dumps(DEFAULT_POLICY)


def deploy(vm):
    return deploy_contract(CONTRACT_PATH, vm)


def renter_address(seed="renter"):
    """Create a test Address *after* the contract/SDK is loaded.

    ``gltest.direct.create_address`` falls back to raw ``bytes`` when the
    genlayer SDK is not yet importable (i.e. before any contract has been
    deployed in the current VM). Call this only after ``deploy``/
    ``make_sealed_asset`` so it returns a real ``Address`` with ``.as_hex``.
    """
    return create_address(seed)


def make_sealed_asset(vm, owner, name="Car1", component_names=("bumper",)):
    """Deploys the contract, registers an asset, adds components, and seals
    the definition. Returns (contract, asset_id, {name: component_id})."""
    vm.sender = owner
    c = deploy(vm)
    aid = c.register_asset(name=name)
    comp_ids = {}
    for n in component_names:
        comp_ids[n] = c.add_component(asset_id=aid, parent_id="", name=n)
    c.seal_asset_definition(asset_id=aid, policy_json=default_policy_json())
    return c, aid, comp_ids


FINDING_CLEAR = {
    "condition_class": "UNCHANGED",
    "defect_relation": "INSUFFICIENT_EVIDENCE",
    "severity": "NONE",
    "normal_wear": False,
    "evidence_sufficient": True,
    "external_failure": False,
    "attribution_class": "INSUFFICIENT_EVIDENCE",
    "matched_defect_id": "",
    "rationale_codes": [1],
}


def finding(**overrides) -> str:
    f = dict(FINDING_CLEAR)
    f.update(overrides)
    return json.dumps(f)


def mock_clear_evidence(vm, url="https://example.com/inspect"):
    vm.mock_web(url.split("//", 1)[-1], {"status": 200, "body": "No visible change."})
    vm.mock_llm(".*", finding())
