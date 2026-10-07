"""Direct Mode test configuration.

Windows tempfile/unlink known failure path (spec section 17): gltest's
message-injection helper duplicates a temp file onto fd 0 via
``os.dup2(fd, 0)`` and then tries to ``os.unlink`` the original path while
the duplicated handle is still open. POSIX allows unlinking an open file;
Windows does not, and raises ``PermissionError: [WinError 32]``. This can
fail *before any contract code executes*, so every Direct Mode test would
otherwise be blocked on Windows regardless of contract correctness.

Some locally patched copies of ``genlayer-test`` already swallow this
error; a freshly `pip install`-ed copy (as of genlayer-test 0.29.2) does
not. We make the test suite robust to either case by making
``os.unlink`` tolerate "file in use" on Windows, system-wide, for the
duration of the test session. This does not touch contract code or
semantics; it only prevents a harness-level, OS-specific I/O quirk from
being mistaken for a contract failure.
"""

import os
import sys

import pytest

if sys.platform == "win32":
    _original_unlink = os.unlink

    def _tolerant_unlink(path, *args, **kwargs):
        try:
            _original_unlink(path, *args, **kwargs)
        except PermissionError:
            # Leaked temp file; OS temp-dir cleanup reclaims it eventually.
            pass

    os.unlink = _tolerant_unlink


@pytest.fixture(autouse=True)
def _enable_pickling_check(direct_vm):
    """gltest's Direct Mode can validate that every run_nondet_unsafe
    closure (leader_fn/validator_fn) is actually picklable -- the same
    constraint real multi-process GenVM execution imposes. Enabled
    session-wide so every test implicitly proves this, not just a
    dedicated one (freeze checklist: "pickling green")."""
    direct_vm.check_pickling = True
    yield
