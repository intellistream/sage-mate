from __future__ import annotations

import importlib
import os
import sys
import warnings
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _candidate_pythonpath_entries(repo_root: Path) -> list[Path]:
    return [
        repo_root / "src",
        repo_root.parent / "SAGE" / "src",
        repo_root.parent / "sageVDB",
        repo_root.parent / "neuromem",
    ]


def _prepend_repo_paths(repo_root: Path) -> list[Path]:
    added: list[Path] = []
    for entry in reversed(_candidate_pythonpath_entries(repo_root)):
        if not entry.exists():
            continue
        entry_str = str(entry)
        if entry_str not in sys.path:
            sys.path.insert(0, entry_str)
            added.append(entry)
    return added


def _ensure_local_policy_preferred(repo_root: Path) -> None:
    local_policy_file = (
        repo_root.parent / "SAGE" / "src" / "sage" / "serving" / "integrations" / "policy.py"
    )
    if not local_policy_file.exists():
        return

    try:
        policy_module = importlib.import_module("sage.serving.integrations.policy")
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise RuntimeError(
            "Failed to import 'sage.serving.integrations.policy'. Set "
            "PYTHONPATH to include ../SAGE/src."
        ) from exc

    policy_path = Path(getattr(policy_module, "__file__", "")).resolve()
    expected_root = (repo_root.parent / "SAGE" / "src").resolve()
    if expected_root not in policy_path.parents:
        raise RuntimeError(
            "Imported policy module from a non-local path: "
            f"{policy_path}. Expected local checkout under {expected_root}. "
            "Run commands with the project interpreter to avoid interpreter/path drift."
        )


def _validate_sagevdb_source(repo_root: Path) -> None:
    """Verify the source sageVDB checkout can export its compiled API.

    The source sageVDB directory is placed on PYTHONPATH so that local Python
    edits take effect without a reinstall.  However, the source tree does NOT
    ship the compiled C extension (.so files).  If those files are missing,
    ``sagevdb/__init__.py`` silently catches the ImportError and sets
    ``__all__ = []``, making DatabaseConfig / DistanceMetric / IndexType /
    create_database unavailable — a notoriously confusing failure.

    Fix: ``bash ../sageVDB/scripts/link_shared_libs.sh``
    """
    source_pkg = repo_root.parent / "sageVDB" / "sagevdb"
    if not source_pkg.is_dir():
        return  # source checkout absent — rely on the PyPI package

    try:
        mod = importlib.import_module("sagevdb")
    except Exception:
        _remove_sagevdb_from_path(repo_root)
        warnings.warn(
            "sageVDB source checkout could not be imported; falling back to PyPI package.",
            stacklevel=2,
        )
        return

    # The critical check: DatabaseConfig must be accessible.
    if not hasattr(mod, "DatabaseConfig"):
        _remove_sagevdb_from_path(repo_root)
        # Invalidate cached import so subsequent imports pick up PyPI version.
        sys.modules.pop("sagevdb", None)
        warnings.warn(
            "sageVDB source checkout is missing compiled C extension (.so); "
            "falling back to PyPI package. "
            "Run: bash ../sageVDB/scripts/link_shared_libs.sh to fix.",
            stacklevel=2,
        )
        return


def _remove_sagevdb_from_path(repo_root: Path) -> None:
    """Remove the sageVDB source directory from sys.path."""
    sagevdb_entry = str(repo_root.parent / "sageVDB")
    sys.path[:] = [p for p in sys.path if p != sagevdb_entry]


def _require_module(module_name: str, install_hint: str) -> None:
    try:
        importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise RuntimeError(
            f"Missing runtime dependency '{module_name}'. {install_hint}"
        ) from exc


def bootstrap_runtime_env(
    *,
    require_policy: bool = True,
    require_fastapi: bool = False,
) -> None:
    repo_root = _repo_root()

    # Avoid torch trying to auto-load optional device extensions (e.g. torch_npu).
    os.environ.setdefault("TORCH_DEVICE_BACKEND_AUTOLOAD", "0")

    _prepend_repo_paths(repo_root)
    _validate_sagevdb_source(repo_root)

    sage_source_present = (
        repo_root.parent / "SAGE" / "src" / "sage" / "serving" / "integrations" / "policy.py"
    ).exists()
    if sage_source_present:
        _ensure_local_policy_preferred(repo_root)

    _require_module(
        "pydantic_settings",
        "Run: python -m pip install -e .",
    )
    if require_fastapi:
        _require_module(
            "fastapi",
            "Run: python -m pip install -e .",
        )

    if require_policy and sage_source_present:
        _require_module(
            "sage.serving.integrations.policy",
            "Ensure local SAGE source is visible (../SAGE/src) on PYTHONPATH.",
        )
