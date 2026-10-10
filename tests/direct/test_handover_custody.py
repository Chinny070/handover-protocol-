"""Custody chain: delegation, scope conservation, delegation depth bound,
custody-gap honesty (HP3, HP11)."""

from gltest.direct import create_address

from _helpers import deploy, make_sealed_asset, renter_address, mock_clear_evidence, attach_test_baseline


def _accept_and_begin(c, vm, hid, custodian):
    vm.sender = custodian
    attach_test_baseline(c, vm, hid)
    c.accept_baseline(handover_id=hid)
    c.begin_custody(handover_id=hid)


def test_delegated_custody_scope_subset_enforced(direct_vm):
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner, component_names=("bumper", "engine"))
    bumper, engine = comps["bumper"], comps["engine"]
    renter = renter_address("renter")
    shop = renter_address("shop")

    hid1 = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[bumper])
    _accept_and_begin(c, direct_vm, hid1, renter)

    # Renter may delegate only a subset of its own scope.
    direct_vm.sender = renter
    hid2 = c.delegate_custody(parent_handover_id=hid1, to_party=shop.as_hex, scope_component_ids=[bumper])
    h2 = c.get_handover(handover_id=hid2)
    assert h2["scope"] == [bumper]
    assert h2["delegation_depth"] == 1

    # Delegating a component outside the parent's scope (engine, which the
    # parent handover never held) must be rejected (HP11).
    outsider = renter_address("outsider")
    with direct_vm.expect_revert("delegated scope exceeds parent scope"):
        c.propose_handover(
            asset_id=aid,
            to_party=outsider.as_hex,
            scope_component_ids=[bumper, engine],
            parent_handover_id=hid1,
        )

    # Only the current custodian (renter) may delegate.
    direct_vm.sender = owner
    with direct_vm.expect_revert("only current custodian may delegate"):
        c.propose_handover(
            asset_id=aid, to_party=shop.as_hex, scope_component_ids=[bumper], parent_handover_id=hid1
        )


def test_delegation_depth_bound(direct_vm):
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner, component_names=("bumper",))
    cid = comps["bumper"]

    custodians = [renter_address(f"party{i}") for i in range(7)]
    hid = c.propose_handover(asset_id=aid, to_party=custodians[0].as_hex, scope_component_ids=[cid])
    _accept_and_begin(c, direct_vm, hid, custodians[0])

    current = custodians[0]
    for depth in range(1, 5):  # depths 1..4 succeed (MAX_DELEGATION_DEPTH = 4)
        direct_vm.sender = current
        hid = c.delegate_custody(
            parent_handover_id=hid, to_party=custodians[depth].as_hex, scope_component_ids=[cid]
        )
        h = c.get_handover(handover_id=hid)
        assert h["delegation_depth"] == depth
        _accept_and_begin(c, direct_vm, hid, custodians[depth])
        current = custodians[depth]

    direct_vm.sender = current
    with direct_vm.expect_revert("delegation depth bound exceeded"):
        c.delegate_custody(parent_handover_id=hid, to_party=custodians[5].as_hex, scope_component_ids=[cid])


def test_custody_gap_recorded_not_silently_assigned(direct_vm):
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner)
    cid = comps["bumper"]
    renter = renter_address("renter")
    hid = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])
    _accept_and_begin(c, direct_vm, hid, renter)

    h = c.get_handover(handover_id=hid)
    assert h["custody_gap"] == "NO_GAP"

    c.mark_custody_gap(handover_id=hid, gap_state="CUSTODY_GAP")
    h = c.get_handover(handover_id=hid)
    assert h["custody_gap"] == "CUSTODY_GAP"

    mock_clear_evidence(direct_vm)
    direct_vm.sender = renter
    c.submit_return_evidence(
        handover_id=hid,
        evidence_kind="WEB_RENDERED_INSPECTION",
        source_url="https://example.com/inspect",
        content_hash="h1",
        component_ids=[cid],
        assurance_tier="SELF_REPORTED",
    )
    c.evaluate_return(handover_id=hid)

    cert = c.get_condition_certificate(asset_id=aid)
    assert cert["custody_gap_present"] is True
    assert cert["certificate_status"] == "GAP_PRESENT"


def test_unknown_gap_state_rejected(direct_vm):
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner)
    cid = comps["bumper"]
    renter = renter_address("renter")
    hid = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])
    with direct_vm.expect_revert("unknown gap state"):
        c.mark_custody_gap(handover_id=hid, gap_state="SOMETHING_ELSE")


def test_custody_gap_history_is_append_only_and_not_erasable(direct_vm):
    """A party cannot silently erase an earlier gap report by later
    overwriting handover.custody_gap with NO_GAP -- the original report
    must remain visible in get_custody_gap_history even though the
    current/latest custody_gap field reflects the newest call."""
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner)
    cid = comps["bumper"]
    renter = renter_address("renter")
    hid = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])

    c.mark_custody_gap(handover_id=hid, gap_state="CUSTODY_GAP")
    direct_vm.sender = renter
    with direct_vm.expect_revert("cannot be cleared without verified resolution"):
        c.mark_custody_gap(handover_id=hid, gap_state="NO_GAP")

    h = c.get_handover(handover_id=hid)
    assert h["custody_gap"] == "CUSTODY_GAP"

    history = c.get_custody_gap_history(handover_id=hid)
    assert len(history) == 1
    assert history[0]["gap_state"] == "CUSTODY_GAP"
    assert history[0]["previous_gap_state"] == "NO_GAP"
    # The original CUSTODY_GAP report is still visible despite being
    # "overwritten" in the live field -- nothing was erased.
