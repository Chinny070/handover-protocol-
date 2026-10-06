"""Studionet integration tests — NOT IMPLEMENTED this session.

Live deployment is explicitly out of scope for this build session (see
docs/DEPLOYMENT.md). This module is a placeholder that documents the
intended shape (per master-spec section 27) and skips rather than fakes a
pass, so a bare `pytest` run of the whole repo does not silently report a
green integration suite that never actually touched a network.

A follow-on session implementing these should use `gltest`'s Studio Mode
`get_contract_factory`/`default_account` helpers (as in the bundled
`genlayer` CLI template, see `docs/RELEASE_CANDIDATE_VERIFICATION.md`),
target the canonical Studionet deployment, and assert on contract *state*
via its public views — not merely on transaction receipt status.
"""

import pytest


pytestmark = pytest.mark.skip(
    reason="No Studionet deployment exists yet; live deployment is out of "
    "scope for this session (see docs/DEPLOYMENT.md)."
)


def test_live_lifecycle_placeholder():
    raise NotImplementedError(
        "Implement once a canonical Studionet deployment exists; see "
        "scripts/live_verify.py for the intended lifecycle steps."
    )
