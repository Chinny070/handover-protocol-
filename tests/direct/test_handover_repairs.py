"""Repair verification lifecycle (section 23, HP8, HP14)."""

from gltest.direct import create_address

from _helpers import make_sealed_asset, renter_address, finding, attach_test_baseline


def _create_open_defect(c, vm, aid, cid, renter):
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
        handover_id=hid,
        evidence_kind="WEB_RENDERED_INSPECTION",
        source_url="https://example.com/inspect",
        content_hash="h",
        component_ids=[cid],
        assurance_tier="SELF_REPORTED",
    )
    c.evaluate_return(handover_id=hid)
    vm.clear_mocks()
    return c.get_asset(asset_id=aid)["defect_ids"][0]


def test_repair_submission_and_verified_repaired(direct_vm):
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner)
    cid = comps["bumper"]
    renter = renter_address("renter")
    did = _create_open_defect(c, direct_vm, aid, cid, renter)

    c.submit_repair(
        defect_id=did,
        evidence_kind="REPAIR_RECEIPT",
        source_url="https://example.com/receipt",
        content_hash="4f90f07cdd8ba6d32f9c9d79586e8b42737880b059dd0e20d8f43f74e0c8681c",
    )
    assert c.get_defect(defect_id=did)["status"] == "REPAIR_CLAIMED"

    direct_vm.mock_web("example.com/receipt", {"status": 200, "body": "Bumper replaced and repainted."})
    direct_vm.mock_llm(".*", '{"repair_result": "REPAIRED"}')
    result = c.verify_repair(defect_id=did)
    assert result == "REPAIRED"
    defect = c.get_defect(defect_id=did)
    assert defect["status"] == "REPAIRED"
    assert defect["repair_count"] == 1

    history = c.get_defect_history(defect_id=did)
    assert [h["event"] for h in history] == ["OPEN", "REPAIR_CLAIMED", "REPAIRED"]

    # certificate reflects the closed defect
    cert = c.get_condition_certificate(asset_id=aid)
    assert cert["open_defect_count"] == 0
    assert c.is_handover_clear(asset_id=aid) is True


def test_repair_not_repaired_reopens_defect(direct_vm):
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner)
    cid = comps["bumper"]
    renter = renter_address("renter")
    did = _create_open_defect(c, direct_vm, aid, cid, renter)

    c.submit_repair(
        defect_id=did,
        evidence_kind="REPAIR_RECEIPT",
        source_url="https://example.com/receipt",
        content_hash="dc74af31d7b60b3ed559d7c4fb84d85e9885d772d38d029c50ff6e701ef5ce9c",
    )
    direct_vm.mock_web("example.com/receipt", {"status": 200, "body": "Receipt for an unrelated oil change."})
    direct_vm.mock_llm(".*", '{"repair_result": "NOT_REPAIRED"}')
    result = c.verify_repair(defect_id=did)
    assert result == "NOT_REPAIRED"
    assert c.get_defect(defect_id=did)["status"] == "OPEN"


def test_repair_receipt_unavailable_is_external_failure_not_repaired(direct_vm):
    """A receipt the validator cannot fetch must resolve EXTERNAL_FAILURE,
    never REPAIRED or NOT_REPAIRED (HP14)."""
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner)
    cid = comps["bumper"]
    renter = renter_address("renter")
    did = _create_open_defect(c, direct_vm, aid, cid, renter)

    c.submit_repair(
        defect_id=did,
        evidence_kind="REPAIR_RECEIPT",
        source_url="https://unreachable.example/receipt",
        content_hash="0000000000000000000000000000000000000000000000000000000000000000",
    )
    result = c.verify_repair(defect_id=did)
    assert result == "EXTERNAL_FAILURE"
    # defect status is left untouched pending real evidence, not silently
    # resolved either way
    assert c.get_defect(defect_id=did)["status"] == "REPAIR_CLAIMED"


def test_repair_round_bound_enforced(direct_vm):
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner)
    cid = comps["bumper"]
    renter = renter_address("renter")
    did = _create_open_defect(c, direct_vm, aid, cid, renter)

    direct_vm.mock_web("example.com/receipt", {"status": 200, "body": "Unrelated work."})
    direct_vm.mock_llm(".*", '{"repair_result": "NOT_REPAIRED"}')

    for _ in range(5):  # MAX_REPAIR_ROUNDS = 5
        c.submit_repair(
            defect_id=did,
            evidence_kind="REPAIR_RECEIPT",
            source_url="https://example.com/receipt",
            content_hash="00177462b5d91f6336f1594a75a20cabbb9a6d74379a11c05be498ce9106df7a",
        )
        c.verify_repair(defect_id=did)

    with direct_vm.expect_revert("repair round bound exceeded"):
        c.submit_repair(
            defect_id=did,
            evidence_kind="REPAIR_RECEIPT",
            source_url="https://example.com/receipt",
            content_hash="0000000000000000000000000000000000000000000000000000000000000000",
        )


def test_submit_repair_requires_open_defect(direct_vm):
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner)
    cid = comps["bumper"]
    renter = renter_address("renter")
    did = _create_open_defect(c, direct_vm, aid, cid, renter)

    c.submit_repair(
        defect_id=did, evidence_kind="REPAIR_RECEIPT", source_url="https://example.com/receipt", content_hash="0000000000000000000000000000000000000000000000000000000000000000"
    )
    with direct_vm.expect_revert("not open for repair"):
        c.submit_repair(
            defect_id=did, evidence_kind="REPAIR_RECEIPT", source_url="https://example.com/receipt", content_hash="0000000000000000000000000000000000000000000000000000000000000000"
        )
