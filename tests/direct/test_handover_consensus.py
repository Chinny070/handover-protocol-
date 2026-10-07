"""Custom validator / forged-leader defense (section 16.7, 18, 30).

Uses gltest.direct's `run_validator` cheatcode to feed a forged leader
result directly at the captured `run_nondet_unsafe` validator closure, and
prove the independent validator rejects a leader that:
  - claims NORMAL_WEAR when the validator's own (mocked) re-evaluation
    shows major damage,
  - claims REPAIRED when the validator independently sees no repair
    evidence (via the repair-verification consensus call),
  - omits a critical field,
  - smuggles an unknown enum value,
  - uses bool/float where an int or bool is expected (by invalidating
    shape in the forged payload itself).
"""

from gltest.direct import create_address

from _helpers import make_sealed_asset, renter_address, finding


def _start_return_pending(direct_vm):
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner)
    cid = comps["bumper"]
    renter = renter_address("renter")
    hid = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])
    direct_vm.sender = renter
    c.accept_baseline(handover_id=hid)
    c.begin_custody(handover_id=hid)
    return c, aid, cid, hid, renter


def test_forged_leader_claims_normal_wear_is_rejected(direct_vm):
    c, aid, cid, hid, renter = _start_return_pending(direct_vm)

    # Validator's own re-evaluation (via the mocked web/llm it will use when
    # it reruns leader_fn internally) sees major damage.
    direct_vm.mock_web("example.com/inspect", {"status": 200, "body": "Large crack across the bumper."})
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
        content_hash="h",
        component_ids=[cid],
        assurance_tier="SELF_REPORTED",
    )
    # Trigger the real call once so a validator is captured; its honest
    # result will actually be accepted (both sides see the same mock).
    status = c.evaluate_return(handover_id=hid)
    assert status == "DEFECTS_RECORDED"

    # Now forge a leader result claiming NORMAL_WEAR / no defect, and feed
    # it directly at the captured validator: the validator reruns its own
    # (honest) classification against the same mocks and must disagree.
    forged = [
        {
            "component_id": cid,
            "condition_class": "NORMAL_WEAR",
            "defect_relation": "INSUFFICIENT_EVIDENCE",
            "severity": "NONE",
            "normal_wear": True,
            "evidence_sufficient": True,
            "external_failure": False,
            "attribution_class": "INSUFFICIENT_EVIDENCE",
            "matched_defect_id": "",
            "rationale_codes": [9],
        }
    ]
    accepted = direct_vm.run_validator(leader_result=forged)
    assert accepted is False


def test_forged_leader_claims_repaired_when_no_evidence_is_rejected(direct_vm):
    c, aid, cid, hid, renter = _start_return_pending(direct_vm)
    direct_vm.mock_web("example.com/inspect", {"status": 200, "body": "Dent."})
    direct_vm.mock_llm(
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
    did = c.get_asset(asset_id=aid)["defect_ids"][0]

    c.submit_repair(
        defect_id=did, evidence_kind="REPAIR_RECEIPT", source_url="https://unreachable.example/receipt", content_hash="r"
    )
    # Validator independently cannot fetch the receipt -> its honest answer
    # is EXTERNAL_FAILURE. A forged leader claiming REPAIRED must be rejected.
    result = c.verify_repair(defect_id=did)
    assert result == "EXTERNAL_FAILURE"

    forged = {"repair_result": "REPAIRED"}
    accepted = direct_vm.run_validator(leader_result=forged)
    assert accepted is False


def test_forged_leader_omits_critical_field_is_rejected(direct_vm):
    c, aid, cid, hid, renter = _start_return_pending(direct_vm)
    direct_vm.mock_web("example.com/inspect", {"status": 200, "body": "No visible change."})
    direct_vm.mock_llm(".*", finding())
    c.submit_return_evidence(
        handover_id=hid,
        evidence_kind="WEB_RENDERED_INSPECTION",
        source_url="https://example.com/inspect",
        content_hash="h",
        component_ids=[cid],
        assurance_tier="SELF_REPORTED",
    )
    c.evaluate_return(handover_id=hid)

    forged = [
        {
            "component_id": cid,
            # "condition_class" omitted entirely
            "defect_relation": "INSUFFICIENT_EVIDENCE",
            "severity": "NONE",
            "normal_wear": False,
            "evidence_sufficient": True,
            "external_failure": False,
            "attribution_class": "INSUFFICIENT_EVIDENCE",
            "matched_defect_id": "",
            "rationale_codes": [],
        }
    ]
    accepted = direct_vm.run_validator(leader_result=forged)
    assert accepted is False


def test_forged_leader_smuggles_unknown_enum_is_rejected(direct_vm):
    c, aid, cid, hid, renter = _start_return_pending(direct_vm)
    direct_vm.mock_web("example.com/inspect", {"status": 200, "body": "No visible change."})
    direct_vm.mock_llm(".*", finding())
    c.submit_return_evidence(
        handover_id=hid,
        evidence_kind="WEB_RENDERED_INSPECTION",
        source_url="https://example.com/inspect",
        content_hash="h",
        component_ids=[cid],
        assurance_tier="SELF_REPORTED",
    )
    c.evaluate_return(handover_id=hid)

    forged = [
        {
            "component_id": cid,
            "condition_class": "TOTALED",  # unknown enum value
            "defect_relation": "INSUFFICIENT_EVIDENCE",
            "severity": "NONE",
            "normal_wear": False,
            "evidence_sufficient": True,
            "external_failure": False,
            "attribution_class": "INSUFFICIENT_EVIDENCE",
            "matched_defect_id": "",
            "rationale_codes": [],
        }
    ]
    accepted = direct_vm.run_validator(leader_result=forged)
    assert accepted is False


def test_forged_leader_uses_bool_for_flag_is_rejected(direct_vm):
    c, aid, cid, hid, renter = _start_return_pending(direct_vm)
    direct_vm.mock_web("example.com/inspect", {"status": 200, "body": "No visible change."})
    direct_vm.mock_llm(".*", finding())
    c.submit_return_evidence(
        handover_id=hid,
        evidence_kind="WEB_RENDERED_INSPECTION",
        source_url="https://example.com/inspect",
        content_hash="h",
        component_ids=[cid],
        assurance_tier="SELF_REPORTED",
    )
    c.evaluate_return(handover_id=hid)

    forged = [
        {
            "component_id": cid,
            "condition_class": "UNCHANGED",
            "defect_relation": "INSUFFICIENT_EVIDENCE",
            "severity": "NONE",
            "normal_wear": "yes",  # truthy string, not a real bool
            "evidence_sufficient": True,
            "external_failure": False,
            "attribution_class": "INSUFFICIENT_EVIDENCE",
            "matched_defect_id": "",
            "rationale_codes": [],
        }
    ]
    accepted = direct_vm.run_validator(leader_result=forged)
    assert accepted is False


def test_forged_leader_claims_attribution_despite_custody_gap(direct_vm):
    """A leader claiming SUPPORTED_AS_NEW_IN_INTERVAL attribution while the
    validator's own re-evaluation sees CUSTODY_GAP must be rejected; the two
    attribution classes are never treated as equivalent (section 18)."""
    c, aid, cid, hid, renter = _start_return_pending(direct_vm)
    c.mark_custody_gap(handover_id=hid, gap_state="CUSTODY_GAP")
    direct_vm.mock_web("example.com/inspect", {"status": 200, "body": "Dent, but custody chain has a gap."})
    direct_vm.mock_llm(
        ".*",
        finding(
            condition_class="NEW_MINOR_DAMAGE",
            defect_relation="NEW_DISTINCT_DEFECT",
            severity="MINOR",
            attribution_class="CUSTODY_GAP",
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

    forged = [
        {
            "component_id": cid,
            "condition_class": "NEW_MINOR_DAMAGE",
            "defect_relation": "NEW_DISTINCT_DEFECT",
            "severity": "MINOR",
            "normal_wear": False,
            "evidence_sufficient": True,
            "external_failure": False,
            "attribution_class": "SUPPORTED_AS_NEW_IN_INTERVAL",  # overstates attribution
            "matched_defect_id": "",
            "rationale_codes": [],
        }
    ]
    accepted = direct_vm.run_validator(leader_result=forged)
    assert accepted is False


def test_forged_leader_matches_wrong_candidate_defect_is_rejected(direct_vm):
    """A leader that agrees on every typed field (condition_class,
    defect_relation=SAME_DEFECT, severity, attribution_class, ...) but
    points `matched_defect_id` at a different, still-valid candidate defect
    for the same component must still be rejected. `matched_defect_id`
    selects which stored defect gets mutated to WORSENED, so it is
    decision-critical even though it is not in CRITICAL_FIELDS (HP4, HP7)."""
    c, aid, cid, hid, renter = _start_return_pending(direct_vm)

    # Round 1: create DEFECT-1 on this component.
    direct_vm.mock_web("example.com/inspect", {"status": 200, "body": "Small scuff."})
    direct_vm.mock_llm(
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
    defect_1 = c.get_asset(asset_id=aid)["defect_ids"][0]

    # Round 2: a second, independent new defect on the SAME component, so
    # there are now two valid candidate defect ids for this component.
    direct_vm.sender = create_address("owner")
    hid2 = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])
    direct_vm.sender = renter
    c.accept_baseline(handover_id=hid2)
    c.begin_custody(handover_id=hid2)
    direct_vm.clear_mocks()
    direct_vm.mock_web("example.com/inspect2", {"status": 200, "body": "Separate fresh dent elsewhere."})
    direct_vm.mock_llm(
        ".*",
        finding(
            condition_class="NEW_MINOR_DAMAGE",
            defect_relation="NEW_DISTINCT_DEFECT",
            severity="MINOR",
            attribution_class="SUPPORTED_AS_NEW_IN_INTERVAL",
        ),
    )
    c.submit_return_evidence(
        handover_id=hid2,
        evidence_kind="WEB_RENDERED_INSPECTION",
        source_url="https://example.com/inspect2",
        content_hash="h",
        component_ids=[cid],
        assurance_tier="SELF_REPORTED",
    )
    c.evaluate_return(handover_id=hid2)
    defect_ids = c.get_asset(asset_id=aid)["defect_ids"]
    assert len(defect_ids) == 2
    defect_2 = [d for d in defect_ids if d != defect_1][0]

    # Round 3: evidence honestly matches defect_1 (worsening it). Trigger
    # the real call once so a validator closure is captured.
    direct_vm.sender = create_address("owner")
    hid3 = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])
    direct_vm.sender = renter
    c.accept_baseline(handover_id=hid3)
    c.begin_custody(handover_id=hid3)
    direct_vm.clear_mocks()
    direct_vm.mock_web("example.com/inspect3", {"status": 200, "body": "The scuff is now a deep gouge."})
    direct_vm.mock_llm(
        ".*",
        finding(
            condition_class="WORSENED_EXISTING_DEFECT",
            defect_relation="SAME_DEFECT",
            severity="MAJOR",
            attribution_class="WORSENED_IN_INTERVAL",
            matched_defect_id=defect_1,
        ),
    )
    c.submit_return_evidence(
        handover_id=hid3,
        evidence_kind="WEB_RENDERED_INSPECTION",
        source_url="https://example.com/inspect3",
        content_hash="h",
        component_ids=[cid],
        assurance_tier="SELF_REPORTED",
    )
    status = c.evaluate_return(handover_id=hid3)
    assert status == "DEFECTS_RECORDED"

    # Forge a leader result identical in every CRITICAL_FIELDS value but
    # pointing matched_defect_id at the OTHER valid candidate (defect_2).
    forged = [
        {
            "component_id": cid,
            "condition_class": "WORSENED_EXISTING_DEFECT",
            "defect_relation": "SAME_DEFECT",
            "severity": "MAJOR",
            "normal_wear": False,
            "evidence_sufficient": True,
            "external_failure": False,
            "attribution_class": "WORSENED_IN_INTERVAL",
            "matched_defect_id": defect_2,
            "rationale_codes": [9],
        }
    ]
    accepted = direct_vm.run_validator(leader_result=forged)
    assert accepted is False


def test_honest_leader_result_is_accepted(direct_vm):
    """Sanity check: an honest leader result (identical to what the
    validator independently derives) IS accepted — the validator is
    substantive, not merely rejecting everything."""
    c, aid, cid, hid, renter = _start_return_pending(direct_vm)
    direct_vm.mock_web("example.com/inspect", {"status": 200, "body": "No visible change."})
    direct_vm.mock_llm(".*", finding())
    c.submit_return_evidence(
        handover_id=hid,
        evidence_kind="WEB_RENDERED_INSPECTION",
        source_url="https://example.com/inspect",
        content_hash="h",
        component_ids=[cid],
        assurance_tier="SELF_REPORTED",
    )
    c.evaluate_return(handover_id=hid)
    accepted = direct_vm.run_validator()  # replays the stored honest leader result
    assert accepted is True


def test_forged_leader_claims_overturned_when_evidence_is_unreachable_is_rejected(direct_vm):
    """_classify_challenge's leader/validator consensus must also reject a
    forged leader: claiming OVERTURNED when the validator's own
    independent fetch of the same challenge evidence fails
    (EXTERNAL_FAILURE), not just the component-classification consensus."""
    c, aid, cid, hid, renter = _start_return_pending(direct_vm)
    direct_vm.mock_web("example.com/inspect", {"status": 200, "body": "Dent."})
    direct_vm.mock_llm(
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
    did = c.get_asset(asset_id=aid)["defect_ids"][0]

    direct_vm.clear_mocks()
    # No mock_web for the challenge evidence URL -> validator's own
    # independent re-fetch fails -> its honest answer is EXTERNAL_FAILURE.
    c.challenge_finding(
        defect_id=did,
        reason_code="PRE_EXISTING_EVIDENCE",
        evidence_kind="SIGNED_INSPECTION_RECORD",
        source_url="https://unreachable.example/nothing",
        content_hash="hc",
    )

    forged = {"result": "OVERTURNED"}
    accepted = direct_vm.run_validator(leader_result=forged)
    assert accepted is False
