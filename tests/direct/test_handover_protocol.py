"""Core lifecycle: registration, component graph, baseline handshake,
custody begin/end, return evaluation terminal states, certificate basics."""

import json
import pytest
from gltest.direct import create_address

from _helpers import deploy, make_sealed_asset, default_policy_json, finding


def test_register_and_component_graph_bounds(direct_vm):
    owner = create_address("owner")
    direct_vm.sender = owner
    c = deploy(direct_vm)
    aid = c.register_asset(name="Car1")
    assert aid == "A1"

    cid1 = c.add_component(asset_id=aid, parent_id="", name="EXTERIOR")
    cid2 = c.add_component(asset_id=aid, parent_id=cid1, name="front_bumper")
    asset = c.get_asset(asset_id=aid)
    assert asset["component_ids"] == [cid1, cid2]

    # cycle rejection: parent must already exist in this asset
    with direct_vm.expect_revert("unknown parent"):
        c.add_component(asset_id=aid, parent_id="C999", name="ghost")


def test_component_bound_enforced(direct_vm):
    owner = create_address("owner")
    direct_vm.sender = owner
    c = deploy(direct_vm)
    aid = c.register_asset(name="Car1")
    # Push well past the bound cheaply by calling repeatedly; use a small
    # local bound check via monkeypatching is avoided — instead verify the
    # contract's own constant is enforced near a reachable count.
    for i in range(64):
        c.add_component(asset_id=aid, parent_id="", name=f"part{i}")
    with direct_vm.expect_revert("component bound exceeded"):
        c.add_component(asset_id=aid, parent_id="", name="one_too_many")


def test_seal_requires_components_and_policy_keys(direct_vm):
    owner = create_address("owner")
    direct_vm.sender = owner
    c = deploy(direct_vm)
    aid = c.register_asset(name="Car1")
    with direct_vm.expect_revert("at least one component"):
        c.seal_asset_definition(asset_id=aid, policy_json=default_policy_json())

    c.add_component(asset_id=aid, parent_id="", name="bumper")
    with direct_vm.expect_revert("policy missing keys"):
        c.seal_asset_definition(asset_id=aid, policy_json=json.dumps({"component_rules": {}}))

    h1 = c.seal_asset_definition(asset_id=aid, policy_json=default_policy_json())
    assert h1.startswith("h_")
    with direct_vm.expect_revert("already sealed"):
        c.seal_asset_definition(asset_id=aid, policy_json=default_policy_json())


def test_baseline_propose_accept_and_immutability(direct_vm):
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner)
    renter = create_address("renter")
    cid = comps["bumper"]

    hid = c.propose_handover(
        asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid], parent_handover_id=""
    )
    h = c.get_handover(handover_id=hid)
    assert h["status"] == "BASELINE_PROPOSED"

    # wrong caller cannot accept
    with direct_vm.expect_revert("only the receiving party"):
        c.accept_baseline(handover_id=hid)

    direct_vm.sender = renter
    c.accept_baseline(handover_id=hid)
    h = c.get_handover(handover_id=hid)
    assert h["status"] == "ACCEPTED"

    # double acceptance / any later mutation attempt is rejected (HP1)
    with direct_vm.expect_revert("already resolved"):
        c.accept_baseline(handover_id=hid)
    with direct_vm.expect_revert("already resolved"):
        c.dispute_baseline(handover_id=hid, reason="too late")


def test_baseline_dispute_path(direct_vm):
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner)
    renter = create_address("renter")
    cid = comps["bumper"]
    hid = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])

    direct_vm.sender = renter
    c.dispute_baseline(handover_id=hid, reason="baseline evidence insufficient")
    h = c.get_handover(handover_id=hid)
    assert h["status"] == "BASELINE_DISPUTED"
    assert h["acceptance_status"] == "DISPUTED"


def test_custody_begin_end_and_overlap_rejection(direct_vm):
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner)
    renter = create_address("renter")
    cid = comps["bumper"]

    hid1 = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])
    direct_vm.sender = renter
    c.accept_baseline(handover_id=hid1)
    c.begin_custody(handover_id=hid1)

    direct_vm.sender = owner
    # overlapping primary custody for the same scope must be rejected (HP2)
    with direct_vm.expect_revert("overlapping primary custody"):
        c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])

    mock_evidence(direct_vm)
    direct_vm.sender = renter
    c.submit_return_evidence(
        handover_id=hid1,
        evidence_kind="WEB_RENDERED_INSPECTION",
        source_url="https://example.com/inspect",
        content_hash="h1",
        component_ids=[cid],
        assurance_tier="SELF_REPORTED",
    )
    status = c.evaluate_return(handover_id=hid1)
    assert status == "RETURN_CLEAR"

    direct_vm.sender = owner
    asset = c.get_asset(asset_id=aid)
    assert asset["active_handover_id"] == ""

    # scope is free again
    hid2 = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])
    assert hid2 != hid1


def mock_evidence(vm, url="https://example.com/inspect"):
    vm.mock_web("example.com/inspect", {"status": 200, "body": "No visible change."})
    vm.mock_llm(".*", finding())


def test_evaluate_return_terminal_states(direct_vm):
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner)
    renter = create_address("renter")
    cid = comps["bumper"]
    hid = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])
    direct_vm.sender = renter
    c.accept_baseline(handover_id=hid)
    c.begin_custody(handover_id=hid)

    mock_evidence(direct_vm)
    c.submit_return_evidence(
        handover_id=hid,
        evidence_kind="WEB_RENDERED_INSPECTION",
        source_url="https://example.com/inspect",
        content_hash="h1",
        component_ids=[cid],
        assurance_tier="SELF_REPORTED",
    )
    status = c.evaluate_return(handover_id=hid)
    assert status == "RETURN_CLEAR"

    cert = c.get_condition_certificate(asset_id=aid)
    assert cert["certificate_status"] == "CLEAR"
    assert c.is_handover_clear(asset_id=aid) is True


def test_evaluate_return_new_damage_creates_defect(direct_vm):
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner)
    renter = create_address("renter")
    cid = comps["bumper"]
    hid = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])
    direct_vm.sender = renter
    c.accept_baseline(handover_id=hid)
    c.begin_custody(handover_id=hid)

    direct_vm.mock_web("example.com/inspect", {"status": 200, "body": "Large dent in bumper."})
    direct_vm.mock_llm(
        ".*",
        finding(
            condition_class="NEW_MAJOR_DAMAGE",
            defect_relation="NEW_DISTINCT_DEFECT",
            severity="MAJOR",
            attribution_class="SUPPORTED_AS_NEW_IN_INTERVAL",
        ),
    )
    c.submit_return_evidence(
        handover_id=hid,
        evidence_kind="WEB_RENDERED_INSPECTION",
        source_url="https://example.com/inspect",
        content_hash="h2",
        component_ids=[cid],
        assurance_tier="SELF_REPORTED",
    )
    status = c.evaluate_return(handover_id=hid)
    assert status == "DEFECTS_RECORDED"

    asset = c.get_asset(asset_id=aid)
    assert len(asset["defect_ids"]) == 1
    did = asset["defect_ids"][0]
    defect = c.get_defect(defect_id=did)
    assert defect["status"] == "OPEN"
    assert defect["severity"] == "MAJOR"
    assert defect["origin_class"] == "SUPPORTED_AS_NEW_IN_INTERVAL"

    history = c.get_defect_history(defect_id=did)
    assert history[0]["event"] == "OPEN"
    # the attribution wording never claims legal causation
    for event in history:
        assert "caused" not in json.dumps(event).lower()

    cert = c.get_condition_certificate(asset_id=aid)
    assert cert["certificate_status"] == "MAJOR_OPEN"
    assert c.is_handover_clear(asset_id=aid) is False


def test_evaluate_return_evidence_unavailable(direct_vm):
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner)
    renter = create_address("renter")
    cid = comps["bumper"]
    hid = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])
    direct_vm.sender = renter
    c.accept_baseline(handover_id=hid)
    c.begin_custody(handover_id=hid)

    # No mock registered for this URL -> web fetch raises -> UNAVAILABLE -> EVIDENCE_UNAVAILABLE
    c.submit_return_evidence(
        handover_id=hid,
        evidence_kind="WEB_RENDERED_INSPECTION",
        source_url="https://unreachable.example/inspect",
        content_hash="h3",
        component_ids=[cid],
        assurance_tier="SELF_REPORTED",
    )
    status = c.evaluate_return(handover_id=hid)
    assert status == "EVIDENCE_UNAVAILABLE"


def test_evaluate_return_http_404_is_deterministically_unavailable(direct_vm):
    """A non-2xx HTTP status must be treated as a fetch failure by status
    code alone (HP14), not left for the model to notice from the response
    body text. No LLM mock is registered: if the contract tried to feed a
    404 body to the model instead of failing closed first, this test would
    hang/error on an unmocked LLM call, not just assert the wrong status.

    Found live on Studionet: the original implementation didn't check
    resp.status, decoded whatever body came back, and relied on the model
    recognizing GitHub's 404 HTML page as "evidence unavailable" -- which
    happened to work, but was never a guarantee."""
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner)
    renter = create_address("renter")
    cid = comps["bumper"]
    hid = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])
    direct_vm.sender = renter
    c.accept_baseline(handover_id=hid)
    c.begin_custody(handover_id=hid)

    direct_vm.mock_web(
        "example.com/missing",
        {"status": 404, "body": "<html><body>404: Not Found</body></html>"},
    )
    c.submit_return_evidence(
        handover_id=hid,
        evidence_kind="WEB_RENDERED_INSPECTION",
        source_url="https://example.com/missing",
        content_hash="h4",
        component_ids=[cid],
        assurance_tier="SELF_REPORTED",
    )
    status = c.evaluate_return(handover_id=hid)
    assert status == "EVIDENCE_UNAVAILABLE"


def test_close_handover_requires_terminal_state(direct_vm):
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner)
    renter = create_address("renter")
    cid = comps["bumper"]
    hid = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])

    with direct_vm.expect_revert("not ready to close"):
        c.close_handover(handover_id=hid)

    direct_vm.sender = renter
    c.accept_baseline(handover_id=hid)
    c.begin_custody(handover_id=hid)
    mock_evidence(direct_vm)
    c.submit_return_evidence(
        handover_id=hid,
        evidence_kind="WEB_RENDERED_INSPECTION",
        source_url="https://example.com/inspect",
        content_hash="h1",
        component_ids=[cid],
        assurance_tier="SELF_REPORTED",
    )
    c.evaluate_return(handover_id=hid)
    c.close_handover(handover_id=hid)
    h = c.get_handover(handover_id=hid)
    assert h["status"] == "CLOSED"
