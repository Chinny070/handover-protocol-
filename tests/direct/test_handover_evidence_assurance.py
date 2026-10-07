"""Evidence assurance-tier enforcement (master spec section 10).

The frozen policy's `evidence_minimums` maps a severity bucket to the set
of assurance tiers that may support a finding of that severity. This is
deterministic policy enforcement in `_evidence_meets_minimum`, applied
*after* consensus already agreed on the typed finding -- it is not a
model decision, and it cannot be satisfied by the model's own
"evidence_sufficient" self-assessment. A self-reported note must not
silently become sufficient evidence for a CRITICAL finding."""

from gltest.direct import create_address

from _helpers import make_sealed_asset, renter_address, finding


def _handover_through_return(
    c, vm, aid, cid, custodian, web_body, llm_json, assurance_tier,
    url="https://example.com/inspect", evidence_kind="WEB_RENDERED_INSPECTION",
):
    hid = c.propose_handover(asset_id=aid, to_party=custodian.as_hex, scope_component_ids=[cid])
    vm.sender = custodian
    c.accept_baseline(handover_id=hid)
    c.begin_custody(handover_id=hid)
    vm.mock_web(url.split("//", 1)[-1], {"status": 200, "body": web_body})
    vm.mock_llm(".*", llm_json)
    c.submit_return_evidence(
        handover_id=hid,
        evidence_kind=evidence_kind,
        source_url=url,
        content_hash="h",
        component_ids=[cid],
        assurance_tier=assurance_tier,
    )
    status = c.evaluate_return(handover_id=hid)
    return hid, status


def test_critical_finding_on_self_reported_evidence_fails_closed(direct_vm):
    """DEFAULT_POLICY requires SIGNED_INSPECTION for a CRITICAL finding.
    SELF_REPORTED evidence must not be enough, even though the model
    agreed on CRITICAL severity and set evidence_sufficient=true itself --
    that flag is advisory model output, not a policy decision."""
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner)
    renter = renter_address("renter")

    _, status = _handover_through_return(
        c, direct_vm, aid, comps["bumper"], renter,
        "Catastrophic structural failure.",
        finding(
            condition_class="NEW_CRITICAL_DAMAGE",
            defect_relation="NEW_DISTINCT_DEFECT",
            severity="CRITICAL",
            attribution_class="SUPPORTED_AS_NEW_IN_INTERVAL",
            evidence_sufficient=True,
        ),
        assurance_tier="SELF_REPORTED",
    )
    assert status == "INCONCLUSIVE"

    asset = c.get_asset(asset_id=aid)
    assert asset["defect_ids"] == []


def test_critical_finding_on_signed_inspection_evidence_is_accepted(direct_vm):
    """The same CRITICAL finding, backed by SIGNED_INSPECTION evidence
    (which DEFAULT_POLICY does list as sufficient for CRITICAL), must be
    accepted normally and create the defect."""
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner)
    renter = renter_address("renter")

    _, status = _handover_through_return(
        c, direct_vm, aid, comps["bumper"], renter,
        "Catastrophic structural failure.",
        finding(
            condition_class="NEW_CRITICAL_DAMAGE",
            defect_relation="NEW_DISTINCT_DEFECT",
            severity="CRITICAL",
            attribution_class="SUPPORTED_AS_NEW_IN_INTERVAL",
            evidence_sufficient=True,
        ),
        assurance_tier="SIGNED_INSPECTION",
        evidence_kind="SIGNED_INSPECTION_RECORD",
    )
    assert status == "DEFECTS_RECORDED"

    asset = c.get_asset(asset_id=aid)
    assert len(asset["defect_ids"]) == 1
    defect = c.get_defect(defect_id=asset["defect_ids"][0])
    assert defect["severity"] == "CRITICAL"


def test_unknown_assurance_tier_is_rejected_at_submission(direct_vm):
    owner = create_address("owner")
    c, aid, comps = make_sealed_asset(direct_vm, owner)
    renter = renter_address("renter")
    cid = comps["bumper"]
    hid = c.propose_handover(asset_id=aid, to_party=renter.as_hex, scope_component_ids=[cid])
    direct_vm.sender = renter
    c.accept_baseline(handover_id=hid)
    c.begin_custody(handover_id=hid)

    with direct_vm.expect_revert("unknown assurance tier"):
        c.submit_return_evidence(
            handover_id=hid,
            evidence_kind="WEB_RENDERED_INSPECTION",
            source_url="https://example.com/inspect",
            content_hash="h",
            component_ids=[cid],
            assurance_tier="TOTALLY_TRUST_ME",
        )


def test_missing_policy_coverage_for_severity_fails_closed(direct_vm):
    """If the frozen policy doesn't specify evidence_minimums for a given
    severity bucket at all, that must fail closed (never implicitly accept)."""
    import json
    from _helpers import deploy

    owner = create_address("owner")
    direct_vm.sender = owner
    c = deploy(direct_vm)
    aid = c.register_asset(name="Car1")
    cid = c.add_component(asset_id=aid, parent_id="", name="bumper")
    policy = {
        "component_rules": {},
        "wear_budget": {},
        "evidence_minimums": {"minor": ["SELF_REPORTED"]},  # no "major" entry at all
        "attribution_minimums": {},
        "repair_closure_requirements": {},
        "challenge_window": 3,
    }
    c.seal_asset_definition(asset_id=aid, policy_json=json.dumps(policy))
    renter = renter_address("renter")

    _, status = _handover_through_return(
        c, direct_vm, aid, cid, renter,
        "Large dent.",
        finding(
            condition_class="NEW_MAJOR_DAMAGE",
            defect_relation="NEW_DISTINCT_DEFECT",
            severity="MAJOR",
            attribution_class="SUPPORTED_AS_NEW_IN_INTERVAL",
        ),
        assurance_tier="SIGNED_INSPECTION",
        evidence_kind="SIGNED_INSPECTION_RECORD",
    )
    assert status == "INCONCLUSIVE"
