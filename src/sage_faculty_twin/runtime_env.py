from __future__ import annotations

import importlib
import os
import sys
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
            "Failed to import 'sage.serving.integrations.policy'. Use tools/run_repo_python.sh or set "
            "PYTHONPATH to include ../SAGE/src."
        ) from exc

    policy_path = Path(getattr(policy_module, "__file__", "")).resolve()
    expected_root = (repo_root.parent / "SAGE" / "src").resolve()
    if expected_root not in policy_path.parents:
        raise RuntimeError(
            "Imported policy module from a non-local path: "
            f"{policy_path}. Expected local checkout under {expected_root}. "
            "Run commands via tools/run_repo_python.sh to avoid interpreter/path drift."
        )


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
    _ensure_local_policy_preferred(repo_root)

    _require_module(
        "pydantic_settings",
        "Use the project interpreter and run: tools/run_repo_python.sh -m pip install -e .",
    )
    if require_fastapi:
        _require_module(
            "fastapi",
            "Use the project interpreter and run: tools/run_repo_python.sh -m pip install -e .",
        )

    if require_policy:
        _require_module(
            "sage.serving.integrations.policy",
            "Ensure local SAGE source is visible (../SAGE/src) and run via tools/run_repo_python.sh.",
        )
