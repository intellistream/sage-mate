"""Test-level runtime bootstrap.

Ensures PYTHONPATH includes local source checkouts (SAGE, sageVDB, neuromem)
before test modules are collected. Without this, importing
``sage_faculty_twin.llm_client`` or ``sage_faculty_twin.api`` at collection
time triggers ``bootstrap_runtime_env()`` which may fail if the SAGE source
is not yet on ``sys.path``.

This conftest is intentionally lightweight: it delegates to the same
``bootstrap_runtime_env`` used at runtime, but with ``require_policy=False``
so collection succeeds even when the full SAGE stack is not available.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project src is importable before any test module is collected.
_repo_root = Path(__file__).resolve().parent.parent
_src = str(_repo_root / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

# Prepend sibling source checkouts so local edits are visible.
for sibling in ("SAGE/src", "sageVDB", "neuromem"):
    entry = str(_repo_root.parent / sibling)
    if Path(entry).exists() and entry not in sys.path:
        sys.path.insert(0, entry)

# Bootstrap the runtime environment without hard-requiring the SAGE policy
# module.  Test modules that import sage_faculty_twin.llm_client will trigger
# a second bootstrap_runtime_env(require_policy=True) call, but the paths are
# already set up so it will succeed when the SAGE source checkout is present.
from sage_faculty_twin.runtime_env import bootstrap_runtime_env  # noqa: E402

bootstrap_runtime_env(require_policy=False, require_fastapi=False)
