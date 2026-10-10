#!/usr/bin/env python
"""Source-parity check: prove a deployed contract's on-chain source matches
`contracts/handover_protocol.py` in this working tree (spec section 28).

Runs `genlayer code <address>` for real, extracts the source from its
output, and diffs it byte-for-byte (ignoring a trailing-newline-only
difference introduced by the CLI's own output formatting) against the
local contract file. Fails loudly on any real difference, including a
differing dependency-header hash.

Usage:
    python scripts/source_parity.py [contract_address]

If no address is given, uses the canonical address recorded in
docs/DEPLOYMENT.md.
"""

import shutil
import subprocess
import sys
from pathlib import Path

CONTRACT_PATH = Path(__file__).resolve().parents[1] / "contracts" / "handover_protocol.py"
DEFAULT_ADDRESS = "0xEC5EcdCd93DFf54c0752628Eed0B51F51417222C"  # latest finalized Studionet deployment
STUDIONET_RPC = "https://studio.genlayer.com/api"


def _extract_source(cli_output: str) -> str:
    """The `genlayer code` CLI prints the raw decoded contract source
    directly after a line that is exactly 'Result:', up to (but not
    including) the trailing '✔ ... retrieved successfully' line."""
    lines = cli_output.splitlines()
    try:
        marker = next(i for i, l in enumerate(lines) if l.strip() == "Result:")
    except StopIteration:
        raise RuntimeError(f"could not find 'Result:' marker in CLI output:\n{cli_output}")
    # Skip any blank line(s) immediately after the marker (console framing
    # varies between a TTY and a piped subprocess), then take everything up
    # to the CLI's own trailing success line.
    start = marker + 1
    while start < len(lines) and lines[start].strip() == "":
        start += 1
    end = next(
        (i for i, l in enumerate(lines) if l.strip().startswith("✔")),
        len(lines),
    )
    return "\n".join(lines[start:end])


def main() -> int:
    address = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ADDRESS

    genlayer_cli = shutil.which("genlayer") or "genlayer"
    cmd = [genlayer_cli, "code", address, "--rpc", STUDIONET_RPC]
    proc = subprocess.run(
        " ".join(cmd) if sys.platform == "win32" else cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=(sys.platform == "win32"),
    )
    if proc.returncode != 0:
        print(f"source_parity: FAILED — `genlayer code {address}` exited {proc.returncode}")
        print(proc.stdout)
        print(proc.stderr)
        return 2

    try:
        deployed_src = _extract_source(proc.stdout).replace("\r\n", "\n").rstrip("\n")
    except RuntimeError as exc:
        print(f"source_parity: FAILED — {exc}")
        return 2

    local_src = CONTRACT_PATH.read_text(encoding="utf-8").replace("\r\n", "\n").rstrip("\n")

    if deployed_src == local_src:
        print(f"source_parity: PASS — {address} byte-for-byte matches {CONTRACT_PATH}")
        return 0

    print(f"source_parity: FAILED — {address} does NOT match {CONTRACT_PATH}")
    deployed_lines = deployed_src.split("\n")
    local_lines = local_src.split("\n")
    for i, (a, b) in enumerate(zip(deployed_lines, local_lines)):
        if a != b:
            print(f"  first differing line ({i + 1}):")
            print(f"    deployed: {a!r}")
            print(f"    local:    {b!r}")
            break
    else:
        print(f"  length differs: deployed={len(deployed_lines)} lines, local={len(local_lines)} lines")
    return 1


if __name__ == "__main__":
    sys.exit(main())
