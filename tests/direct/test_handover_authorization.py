"""Authorization matrix for every public write method that mutates
handover/defect state (stranger / owner / custodian / receiver).

Found and fixed during post-build external review: most write methods had
no sender check at all, meaning any address could originate a primary
custody proposal for someone else's sealed asset, inject return evidence
into a handover it was never a party to, burn a defect's bounded
challenge/repair rounds, or close/mark-gap on a handover it had nothing
to do with. Each test below proves a stranger is rejected and at least
one legitimate party is accepted, for every affected method."""

from gltest.direct import create_address

from _helpers import make_sealed_asset, renter_address, mock_clear_evidence, finding, attach_test_baseline, deploy, default_policy_json


def _sealed_asset_and_stranger(vm):
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(vm, owner)
    stranger = renter_address("stranger")
    return c, aid, comps["bumper"], owner, stranger


def test_propose_handover_primary_requires_owner(direct_vm):
    c, aid, cid, owner, stranger = _sealed_asset_and_stranger(direct_vm)

    direct_vm.sender = stranger
    with direct_vm.expect_revert("only the asset owner may propose primary custody"):
        c.propose_handover(asset_id=aid, to_party=stranger.as_hex, scope_component_ids=[cid])

    direct_vm.sender = owner
    hid = c.propose_handover(asset_id=aid, to_party=stranger.as_hex, scope_component_ids=[cid])
    assert hid == "H1"


def test_component_graph_and_policy_mutations_require_asset_owner(direct_vm):
    owner = create_address("graph-owner")
    stranger = renter_address("graph-stranger")
    direct_vm.sender = owner
    c = deploy(direct_vm)
    aid = c.register_asset(name="Owner mutation matrix")

    direct_vm.sender = stranger
    with direct_vm.expect_revert("caller is not asset owner"):
        c.add_component(asset_id=aid, parent_id="", name="bumper")

    direct_vm.sender = owner
    cid = c.add_component(asset_id=aid, parent_id="", name="bumper")
    assert cid

    direct_vm.sender = stranger
    with direct_vm.expect_revert("caller is not asset owner"):
        c.seal_asset_definition(asset_id=aid, policy_json=default_policy_json())

    direct_vm.sender = owner
    assert c.seal_asset_definition(asset_id=aid, policy_json=default_policy_json())


def test_delegate_custody_requires_current_custodian(direct_vm):
    c, aid, cid, owner, stranger = _sealed_asset_and_stranger(direct_vm)
    renter = renter_address("renter")

    direct_vm.sender = owner
    hid = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])
    direct_vm.sender = renter
    attach_test_baseline(c, direct_vm, hid)
    c.accept_baseline(handover_id=hid)
    c.begin_custody(handover_id=hid)

    shop = renter_address("shop")

    # Neither a stranger nor the original owner may delegate -- only the
    # current custodian (renter) holds the asset to delegate from.
    direct_vm.sender = stranger
    with direct_vm.expect_revert("only current custodian may delegate"):
        c.delegate_custody(parent_handover_id=hid, to_party=shop.as_hex, scope_component_ids=[cid])

    direct_vm.sender = owner
    with direct_vm.expect_revert("only current custodian may delegate"):
        c.delegate_custody(parent_handover_id=hid, to_party=shop.as_hex, scope_component_ids=[cid])

    direct_vm.sender = renter
    hid2 = c.delegate_custody(parent_handover_id=hid, to_party=shop.as_hex, scope_component_ids=[cid])
    assert hid2 == "H2"


def test_add_baseline_evidence_requires_handover_party(direct_vm):
    c, aid, cid, owner, stranger = _sealed_asset_and_stranger(direct_vm)
    renter = renter_address("renter")
    direct_vm.sender = owner
    hid = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])

    direct_vm.sender = stranger
    with direct_vm.expect_revert("caller is not a party to this handover"):
        c.add_baseline_evidence(
            handover_id=hid, evidence_kind="WEB_RENDERED_INSPECTION",
            source_url="https://example.com/x", content_hash="h",
            component_ids=[cid], assurance_tier="SELF_REPORTED",
        )

    # Either party to the handover (owner/from_party, renter/to_party) may add it.
    direct_vm.sender = owner
    eid = c.add_baseline_evidence(
        handover_id=hid, evidence_kind="WEB_RENDERED_INSPECTION",
        source_url="https://example.com/x", content_hash="h",
        component_ids=[cid], assurance_tier="SELF_REPORTED",
    )
    assert eid


def test_submit_return_evidence_requires_current_custodian(direct_vm):
    c, aid, cid, owner, stranger = _sealed_asset_and_stranger(direct_vm)
    renter = renter_address("renter")
    direct_vm.sender = owner
    hid = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])
    direct_vm.sender = renter
    attach_test_baseline(c, direct_vm, hid)
    c.accept_baseline(handover_id=hid)
    c.begin_custody(handover_id=hid)

    # Neither a stranger nor the owner (from_party) may submit return
    # evidence -- only the current custodian (to_party) is returning it.
    direct_vm.sender = stranger
    with direct_vm.expect_revert("only the current custodian may submit return evidence"):
        c.submit_return_evidence(
            handover_id=hid, evidence_kind="WEB_RENDERED_INSPECTION",
            source_url="https://example.com/x", content_hash="h",
            component_ids=[cid], assurance_tier="SELF_REPORTED",
        )
    direct_vm.sender = owner
    with direct_vm.expect_revert("only the current custodian may submit return evidence"):
        c.submit_return_evidence(
            handover_id=hid, evidence_kind="WEB_RENDERED_INSPECTION",
            source_url="https://example.com/x", content_hash="h",
            component_ids=[cid], assurance_tier="SELF_REPORTED",
        )

    direct_vm.sender = renter
    eid = c.submit_return_evidence(
        handover_id=hid, evidence_kind="WEB_RENDERED_INSPECTION",
        source_url="https://example.com/x", content_hash="h",
        component_ids=[cid], assurance_tier="SELF_REPORTED",
    )
    assert eid


def test_begin_custody_requires_handover_party(direct_vm):
    c, aid, cid, owner, stranger = _sealed_asset_and_stranger(direct_vm)
    renter = renter_address("renter")
    direct_vm.sender = owner
    hid = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])
    direct_vm.sender = renter
    attach_test_baseline(c, direct_vm, hid)
    c.accept_baseline(handover_id=hid)

    direct_vm.sender = stranger
    with direct_vm.expect_revert("caller is not a party to this handover"):
        c.begin_custody(handover_id=hid)

    direct_vm.sender = renter
    c.begin_custody(handover_id=hid)
    assert c.get_handover(handover_id=hid)["status"] == "ACTIVE"


def test_mark_custody_gap_requires_handover_party(direct_vm):
    c, aid, cid, owner, stranger = _sealed_asset_and_stranger(direct_vm)
    renter = renter_address("renter")
    direct_vm.sender = owner
    hid = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])
    direct_vm.sender = renter
    attach_test_baseline(c, direct_vm, hid)
    c.accept_baseline(handover_id=hid)
    c.begin_custody(handover_id=hid)

    direct_vm.sender = stranger
    with direct_vm.expect_revert("caller is not a party to this handover"):
        c.mark_custody_gap(handover_id=hid, gap_state="CUSTODY_GAP")

    direct_vm.sender = owner
    c.mark_custody_gap(handover_id=hid, gap_state="CUSTODY_GAP")
    assert c.get_handover(handover_id=hid)["custody_gap"] == "CUSTODY_GAP"


def test_evaluate_return_requires_handover_party(direct_vm):
    c, aid, cid, owner, stranger = _sealed_asset_and_stranger(direct_vm)
    renter = renter_address("renter")
    direct_vm.sender = owner
    hid = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])
    direct_vm.sender = renter
    attach_test_baseline(c, direct_vm, hid)
    c.accept_baseline(handover_id=hid)
    c.begin_custody(handover_id=hid)
    mock_clear_evidence(direct_vm)
    c.submit_return_evidence(
        handover_id=hid, evidence_kind="WEB_RENDERED_INSPECTION",
        source_url="https://example.com/inspect", content_hash="h",
        component_ids=[cid], assurance_tier="SELF_REPORTED",
    )

    direct_vm.sender = stranger
    with direct_vm.expect_revert("caller is not a party to this handover"):
        c.evaluate_return(handover_id=hid)

    direct_vm.sender = owner
    status = c.evaluate_return(handover_id=hid)
    assert status == "RETURN_CLEAR"


def _defect_through_return(c, vm, aid, cid, owner, renter):
    vm.sender = owner
    hid = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])
    vm.sender = renter
    attach_test_baseline(c, vm, hid)
    c.accept_baseline(handover_id=hid)
    c.begin_custody(handover_id=hid)
    vm.mock_web("example.com/inspect", {"status": 200, "body": "Dent."})
    vm.mock_llm(
        ".*",
        finding(
            condition_class="NEW_MINOR_DAMAGE",
            defect_relation="NEW_DISTINCT_DEFECT",
            severity="MINOR",
            attribution_class="SUPPORTED_AS_NEW_IN_INTERVAL",
        ),
    )
    c.submit_return_evidence(
        handover_id=hid, evidence_kind="WEB_RENDERED_INSPECTION",
        source_url="https://example.com/inspect", content_hash="h",
        component_ids=[cid], assurance_tier="SELF_REPORTED",
    )
    c.evaluate_return(handover_id=hid)
    did = c.get_asset(asset_id=aid)["defect_ids"][0]
    return hid, did


def test_challenge_finding_requires_defect_party(direct_vm):
    c, aid, cid, owner, stranger = _sealed_asset_and_stranger(direct_vm)
    renter = renter_address("renter")
    hid, did = _defect_through_return(c, direct_vm, aid, cid, owner, renter)

    direct_vm.clear_mocks()
    direct_vm.mock_web("example.com/challenge", {"status": 200, "body": "No new info."})
    direct_vm.mock_llm(".*", '{"result": "UPHELD"}')

    direct_vm.sender = stranger
    with direct_vm.expect_revert("caller is not a party to this defect"):
        c.challenge_finding(
            defect_id=did, reason_code="WRONG_SEVERITY",
            evidence_kind="STRUCTURED_CHECKLIST",
            source_url="https://example.com/challenge", content_hash="hc",
        )

    direct_vm.sender = owner
    result = c.challenge_finding(
        defect_id=did, reason_code="WRONG_SEVERITY",
        evidence_kind="STRUCTURED_CHECKLIST",
        source_url="https://example.com/challenge", content_hash="hc",
    )
    assert result == "UPHELD"


def test_submit_repair_requires_defect_party(direct_vm):
    c, aid, cid, owner, stranger = _sealed_asset_and_stranger(direct_vm)
    renter = renter_address("renter")
    hid, did = _defect_through_return(c, direct_vm, aid, cid, owner, renter)

    direct_vm.sender = stranger
    with direct_vm.expect_revert("caller is not a party to this defect"):
        c.submit_repair(
            defect_id=did, evidence_kind="REPAIR_RECEIPT",
            source_url="https://example.com/receipt", content_hash="0000000000000000000000000000000000000000000000000000000000000000",
        )

    direct_vm.sender = renter
    c.submit_repair(
        defect_id=did, evidence_kind="REPAIR_RECEIPT",
        source_url="https://example.com/receipt", content_hash="0000000000000000000000000000000000000000000000000000000000000000",
    )
    assert c.get_defect(defect_id=did)["status"] == "REPAIR_CLAIMED"


def test_verify_repair_requires_defect_party(direct_vm):
    c, aid, cid, owner, stranger = _sealed_asset_and_stranger(direct_vm)
    renter = renter_address("renter")
    hid, did = _defect_through_return(c, direct_vm, aid, cid, owner, renter)
    direct_vm.sender = renter
    c.submit_repair(
        defect_id=did, evidence_kind="REPAIR_RECEIPT",
        source_url="https://example.com/receipt", content_hash="16694f382e9f2cba2ef9b99a9a31c31af074ca99d6171d335d2bf245446e561d",
    )

    direct_vm.clear_mocks()
    direct_vm.mock_web("example.com/inspect", {"status": 200, "body": "Dent."})
    direct_vm.mock_web("example.com/receipt", {"status": 200, "body": "Repaired."})
    direct_vm.mock_llm(".*", '{"repair_result": "REPAIRED"}')

    direct_vm.sender = stranger
    with direct_vm.expect_revert("caller is not a party to this defect"):
        c.verify_repair(defect_id=did)

    direct_vm.sender = owner
    result = c.verify_repair(defect_id=did)
    assert result == "REPAIRED"


def test_close_handover_requires_handover_party(direct_vm):
    c, aid, cid, owner, stranger = _sealed_asset_and_stranger(direct_vm)
    renter = renter_address("renter")
    direct_vm.sender = owner
    hid = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])
    direct_vm.sender = renter
    attach_test_baseline(c, direct_vm, hid)
    c.accept_baseline(handover_id=hid)
    c.begin_custody(handover_id=hid)
    mock_clear_evidence(direct_vm)
    c.submit_return_evidence(
        handover_id=hid, evidence_kind="WEB_RENDERED_INSPECTION",
        source_url="https://example.com/inspect", content_hash="h",
        component_ids=[cid], assurance_tier="SELF_REPORTED",
    )
    c.evaluate_return(handover_id=hid)

    direct_vm.sender = stranger
    with direct_vm.expect_revert("caller is not a party to this handover"):
        c.close_handover(handover_id=hid)

    direct_vm.sender = owner
    c.close_handover(handover_id=hid)
    assert c.get_handover(handover_id=hid)["status"] == "CLOSED"


def test_cancel_handover_requires_handover_party(direct_vm):
    """Previously entirely untested: cancel_handover was already
    sender-restricted in the original implementation, but had zero
    Direct Mode coverage before this review."""
    c, aid, cid, owner, stranger = _sealed_asset_and_stranger(direct_vm)
    renter = renter_address("renter")
    direct_vm.sender = owner
    hid = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])

    direct_vm.sender = stranger
    with direct_vm.expect_revert("only a party to the handover may cancel"):
        c.cancel_handover(handover_id=hid)

    direct_vm.sender = renter
    c.cancel_handover(handover_id=hid)
    assert c.get_handover(handover_id=hid)["status"] == "CANCELLED"
