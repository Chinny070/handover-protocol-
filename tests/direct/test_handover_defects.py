"""Defect identity + lineage: contract-assigned IDs, worsening, bounded
history, temporal attribution outcomes (HP7, HP8, HP9)."""

import json
from gltest.direct import create_address

from _helpers import make_sealed_asset, renter_address, finding


def _handover_through_return(c, vm, aid, cid, custodian, web_body, llm_json, url="https://example.com/inspect"):
    hid = c.propose_handover(asset_id=aid, to_party=custodian.as_hex, scope_component_ids=[cid])
    vm.sender = custodian
    c.accept_baseline(handover_id=hid)
    c.begin_custody(handover_id=hid)
    vm.mock_web(url.split("//", 1)[-1], {"status": 200, "body": web_body})
    vm.mock_llm(".*", llm_json)
    c.submit_return_evidence(
        handover_id=hid,
        evidence_kind="WEB_RENDERED_INSPECTION",
        source_url=url,
        content_hash="h",
        component_ids=[cid],
        assurance_tier="SELF_REPORTED",
    )
    status = c.evaluate_return(handover_id=hid)
    return hid, status


def test_defect_ids_are_contract_assigned_and_sequential(direct_vm):
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner, component_names=("bumper", "door"))
    renter = renter_address("renter")

    _, status1 = _handover_through_return(
        c, direct_vm, aid, comps["bumper"], renter,
        "Dent.",
        finding(condition_class="NEW_MINOR_DAMAGE", defect_relation="NEW_DISTINCT_DEFECT",
                severity="MINOR", attribution_class="SUPPORTED_AS_NEW_IN_INTERVAL"),
    )
    assert status1 == "DEFECTS_RECORDED"
    asset = c.get_asset(asset_id=aid)
    assert asset["defect_ids"] == ["D1"]
    assert c.get_defect(defect_id="D1")["defect_id"] == "D1"


def test_worsened_defect_links_to_predecessor_history(direct_vm):
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner)
    cid = comps["bumper"]
    renter = renter_address("renter")

    hid1, status1 = _handover_through_return(
        c, direct_vm, aid, cid, renter,
        "Small scratch.",
        finding(condition_class="NEW_MINOR_DAMAGE", defect_relation="NEW_DISTINCT_DEFECT",
                severity="MINOR", attribution_class="SUPPORTED_AS_NEW_IN_INTERVAL"),
    )
    assert status1 == "DEFECTS_RECORDED"
    did = c.get_asset(asset_id=aid)["defect_ids"][0]

    # Second custody interval: re-propose over the same (now free) scope and
    # worsen the existing defect explicitly via matched_defect_id.
    owner_vm_sender = owner
    direct_vm.sender = owner
    hid2 = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])
    direct_vm.sender = renter
    c.accept_baseline(handover_id=hid2)
    c.begin_custody(handover_id=hid2)
    direct_vm.clear_mocks()  # the first stage's ".*" LLM mock must not leak into this one
    direct_vm.mock_web(
        "example.com/inspect2", {"status": 200, "body": "The scratch is now a crack."}
    )
    direct_vm.mock_llm(
        ".*",
        finding(
            condition_class="WORSENED_EXISTING_DEFECT",
            defect_relation="SAME_DEFECT",
            severity="MAJOR",
            attribution_class="WORSENED_IN_INTERVAL",
            matched_defect_id=did,
        ),
    )
    c.submit_return_evidence(
        handover_id=hid2,
        evidence_kind="WEB_RENDERED_INSPECTION",
        source_url="https://example.com/inspect2",
        content_hash="h2",
        component_ids=[cid],
        assurance_tier="SELF_REPORTED",
    )
    status2 = c.evaluate_return(handover_id=hid2)
    assert status2 == "DEFECTS_RECORDED"

    defect = c.get_defect(defect_id=did)
    assert defect["status"] == "WORSENED"
    assert defect["severity"] == "MAJOR"

    history = c.get_defect_history(defect_id=did)
    events = [h["event"] for h in history]
    assert events == ["OPEN", "WORSENED"]
    # history is never deleted — the OPEN event is still first (HP8)
    assert history[0]["attribution_class"] == "SUPPORTED_AS_NEW_IN_INTERVAL"
    assert history[1]["attribution_class"] == "WORSENED_IN_INTERVAL"

    # still only one defect record — no duplicate created for "same defect"
    asset = c.get_asset(asset_id=aid)
    assert asset["defect_ids"] == [did]


def test_invented_matched_defect_id_fails_closed(direct_vm):
    """A finding referencing a defect id that is not an open candidate for
    this component is invented output. Output hardening must fail closed
    to INCONCLUSIVE rather than attach the finding to a real-but-wrong
    defect or silently drop the matched_defect_id and treat it as new
    (HP5, HP7, section 28 OUTPUT HARDENING)."""
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner)
    cid = comps["bumper"]
    renter = renter_address("renter")

    hid = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])
    direct_vm.sender = renter
    c.accept_baseline(handover_id=hid)
    c.begin_custody(handover_id=hid)
    direct_vm.mock_web("example.com/inspect", {"status": 200, "body": "Dent."})
    # No open defects exist yet, so ANY matched_defect_id is invented.
    direct_vm.mock_llm(
        ".*",
        finding(
            condition_class="WORSENED_EXISTING_DEFECT",
            defect_relation="SAME_DEFECT",
            severity="MAJOR",
            attribution_class="WORSENED_IN_INTERVAL",
            matched_defect_id="D999",
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
    status = c.evaluate_return(handover_id=hid)
    assert status == "INCONCLUSIVE"
    # No defect was fabricated from the invented-id finding.
    assert c.get_asset(asset_id=aid)["defect_ids"] == []


def test_max_challenge_rounds_bounded(direct_vm):
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner)
    cid = comps["bumper"]
    renter = renter_address("renter")
    _, status = _handover_through_return(
        c, direct_vm, aid, cid, renter,
        "Dent.",
        finding(condition_class="NEW_MINOR_DAMAGE", defect_relation="NEW_DISTINCT_DEFECT",
                severity="MINOR", attribution_class="SUPPORTED_AS_NEW_IN_INTERVAL"),
    )
    did = c.get_asset(asset_id=aid)["defect_ids"][0]

    direct_vm.clear_mocks()
    direct_vm.mock_web("example.com/challenge", {"status": 200, "body": "Nothing new; severity assessment stands."})
    direct_vm.mock_llm(".*", '{"result": "UPHELD"}')

    for _ in range(3):  # MAX_CHALLENGE_ROUNDS = 3
        c.challenge_finding(
            defect_id=did,
            reason_code="WRONG_SEVERITY",
            evidence_kind="STRUCTURED_CHECKLIST",
            source_url="https://example.com/challenge",
            content_hash="hc",
        )

    with direct_vm.expect_revert("challenge bound exceeded"):
        c.challenge_finding(
            defect_id=did,
            reason_code="WRONG_SEVERITY",
            evidence_kind="STRUCTURED_CHECKLIST",
            source_url="https://example.com/challenge",
            content_hash="hc",
        )


def test_unknown_challenge_reason_rejected(direct_vm):
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner)
    cid = comps["bumper"]
    renter = renter_address("renter")
    _, status = _handover_through_return(
        c, direct_vm, aid, cid, renter,
        "Dent.",
        finding(condition_class="NEW_MINOR_DAMAGE", defect_relation="NEW_DISTINCT_DEFECT",
                severity="MINOR", attribution_class="SUPPORTED_AS_NEW_IN_INTERVAL"),
    )
    did = c.get_asset(asset_id=aid)["defect_ids"][0]
    with direct_vm.expect_revert("unknown challenge reason"):
        c.challenge_finding(
            defect_id=did,
            reason_code="NOT_A_REAL_REASON",
            evidence_kind="STRUCTURED_CHECKLIST",
            source_url="https://example.com/challenge",
            content_hash="hc",
        )


def test_challenge_overturned_by_fresh_contradicting_evidence(direct_vm):
    """_classify_challenge independently retrieves fresh evidence and
    lets the model reconsider the finding against it -- this is not the
    old placeholder that always UPHELD regardless of evidence."""
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner)
    cid = comps["bumper"]
    renter = renter_address("renter")
    _, status = _handover_through_return(
        c, direct_vm, aid, cid, renter,
        "Dent.",
        finding(condition_class="NEW_MINOR_DAMAGE", defect_relation="NEW_DISTINCT_DEFECT",
                severity="MINOR", attribution_class="SUPPORTED_AS_NEW_IN_INTERVAL"),
    )
    did = c.get_asset(asset_id=aid)["defect_ids"][0]

    direct_vm.clear_mocks()
    direct_vm.mock_web(
        "example.com/preexisting-proof",
        {"status": 200, "body": "Pre-handover inspection photo, timestamped before custody began, clearly shows this exact dent already present."},
    )
    direct_vm.mock_llm(".*", '{"result": "OVERTURNED"}')

    result = c.challenge_finding(
        defect_id=did,
        reason_code="PRE_EXISTING_EVIDENCE",
        evidence_kind="SIGNED_INSPECTION_RECORD",
        source_url="https://example.com/preexisting-proof",
        content_hash="hc",
    )
    assert result == "OVERTURNED"
    assert c.get_defect(defect_id=did)["status"] == "UNRESOLVED"


def test_challenge_with_unreachable_evidence_is_external_failure_not_overturned(direct_vm):
    """An unreachable challenge evidence source must fail closed to
    EXTERNAL_FAILURE, never silently becoming OVERTURNED/UPHELD (HP14)."""
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner)
    cid = comps["bumper"]
    renter = renter_address("renter")
    _, status = _handover_through_return(
        c, direct_vm, aid, cid, renter,
        "Dent.",
        finding(condition_class="NEW_MINOR_DAMAGE", defect_relation="NEW_DISTINCT_DEFECT",
                severity="MINOR", attribution_class="SUPPORTED_AS_NEW_IN_INTERVAL"),
    )
    did = c.get_asset(asset_id=aid)["defect_ids"][0]

    direct_vm.clear_mocks()
    # No mock_web registered for this URL -> fetch fails -> EXTERNAL_FAILURE,
    # and the unmocked LLM call must never even be reached.
    result = c.challenge_finding(
        defect_id=did,
        reason_code="WRONG_SEVERITY",
        evidence_kind="STRUCTURED_CHECKLIST",
        source_url="https://unreachable.example/nothing",
        content_hash="hc",
    )
    assert result == "EXTERNAL_FAILURE"
    defect = c.get_defect(defect_id=did)
    assert defect["status"] == "OPEN"  # unchanged
