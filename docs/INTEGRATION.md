# INTEGRATION.md

Three unrelated downstream consumers, each reading only the public view
surface of `HandoverProtocol` (no web/LLM/equivalence logic of their own):

## 1. Deposit-refund contract

```python
cert = gl.get_contract_at(handover_protocol_address).get_condition_certificate(asset_id)
if cert["certificate_status"] == "CLEAR":
    refund_full_deposit()
elif cert["certificate_status"] in ("MINOR_OPEN", "MAJOR_OPEN", "CRITICAL_OPEN"):
    withhold_partial_deposit(cert["open_defect_count"], cert["major_defect_count"], cert["critical_defect_count"])
else:  # GAP_PRESENT
    escalate_to_manual_review()
```

## 2. Insurance-eligibility gate

```python
is_clear = gl.get_contract_at(handover_protocol_address).is_handover_clear(asset_id)
if not is_clear:
    deny_claim_fast_path()  # falls back to manual adjuster review
```

## 3. Resale-trust-score contract

```python
cert = gl.get_contract_at(handover_protocol_address).get_condition_certificate(asset_id)
history = gl.get_contract_at(handover_protocol_address).get_custody_chain(asset_id)
score = compute_trust_score(
    open_defects=cert["open_defect_count"],
    unresolved=cert["unresolved_count"],
    gap_present=cert["custody_gap_present"],
    custody_hops=len(history),
)
```

None of these three consumers need to know anything about evidence
retrieval, prompt construction, or validator equivalence — they only read
`get_condition_certificate` / `is_handover_clear` / `get_custody_chain`,
exactly the "reuse surface" section 8.7/29 of the master spec calls for.
