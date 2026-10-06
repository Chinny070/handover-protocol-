#!/usr/bin/env python
"""Source-parity check: prove a deployed contract's on-chain source matches
`contracts/handover_protocol.py` at the commit that was deployed (spec
section 28).

STUB: not implemented this session — there is no deployment yet to check
against (see docs/DEPLOYMENT.md). Running this script says so and exits
non-zero.

A follow-on session should: `genlayer code <address>` the canonical
deployment, diff it byte-for-byte against `contracts/handover_protocol.py`
at the recorded deployment commit, and fail loudly on any difference
(including a differing dependency-header hash).
"""

import sys


def main() -> int:
    print("source_parity: NOT RUN — no canonical deployment address recorded yet.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
