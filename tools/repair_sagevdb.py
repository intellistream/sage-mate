#!/usr/bin/env python3
"""Repair sageVDB native extension wiring for the current Python interpreter.

The common failure mode is an ABI mismatch: an isage-vdb install may contain a
``_sagevdb`` extension built for another Python version, so ``import sagevdb``
succeeds but exports none of the compiled API symbols.  This script repairs the
source checkout and installed package using only artefacts that match the
current interpreter's extension suffix.
"""
from __future__ import annotations

import argparse
import importlib
import os
import shutil
import site
import subprocess
import sys
import sysconfig
from pathlib import Path


REQUIRED_SYMBOLS = ("DatabaseConfig", "DistanceMetric", "IndexType", "create_database")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _run(cmd: list[str], *, cwd: Path | None = None) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def _maybe_reexec_with_python(target_python: str | None) -> None:
    if not target_python:
        return
    target = Path(target_python).expanduser()
    if not target.exists():
        raise SystemExit(f"target Python does not exist: {target}")
    if target.resolve() == Path(sys.executable).resolve():
        return
    os.execv(str(target), [str(target), __file__, *sys.argv[1:]])


def _extension_suffix() -> str:
    suffix = str(sysconfig.get_config_var("EXT_SUFFIX") or "")
    if not suffix:
        raise SystemExit("Could not resolve Python extension suffix for this interpreter.")
    return suffix


def _import_is_healthy() -> bool:
    importlib.invalidate_caches()
    sys.modules.pop("sagevdb", None)
    try:
        module = importlib.import_module("sagevdb")
    except Exception as exc:
        print(f"[check] import sagevdb failed: {exc}")
        return False
    missing = [symbol for symbol in REQUIRED_SYMBOLS if not hasattr(module, symbol)]
    if missing:
        print(f"[check] sagevdb imported from {getattr(module, '__file__', '<unknown>')}")
        print(f"[check] missing symbols: {', '.join(missing)}")
        return False
    print(f"[check] sagevdb OK: {module.__file__}")
    return True


def _find_matching_extension(sagevdb_root: Path, suffix: str) -> Path | None:
    candidates = [
        sagevdb_root / "build" / "python" / f"_sagevdb{suffix}",
        sagevdb_root / "sagevdb" / f"_sagevdb{suffix}",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    matches = sorted(sagevdb_root.glob(f"**/_sagevdb*{suffix}"))
    return matches[0] if matches else None


def _find_native_library(sagevdb_root: Path) -> Path | None:
    candidates = [
        sagevdb_root / "build" / "libsage_vdb.so",
        sagevdb_root / "sagevdb" / "libsage_vdb.so",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    matches = sorted(sagevdb_root.glob("**/libsage_vdb.so"))
    return matches[0].resolve() if matches else None


def _prune_mismatched_extensions(package_dir: Path, suffix: str) -> None:
    for candidate in package_dir.glob("_sagevdb*.so"):
        if candidate.name.endswith(suffix):
            continue
        if candidate.is_symlink() or candidate.is_file():
            candidate.unlink()
            print(f"[repair] removed mismatched extension: {candidate}")


def _repair_source_checkout(
    *,
    sagevdb_root: Path,
    extension: Path,
    native_library: Path,
    suffix: str,
) -> None:
    source_pkg = sagevdb_root / "sagevdb"
    if not source_pkg.is_dir():
        raise SystemExit(f"sageVDB source package not found: {source_pkg}")

    _prune_mismatched_extensions(source_pkg, suffix)

    target_ext = source_pkg / f"_sagevdb{suffix}"
    if extension.resolve() != target_ext.resolve():
        shutil.copy2(extension, target_ext)
        print(f"[repair] installed source extension: {target_ext}")

    target_lib = source_pkg / "libsage_vdb.so"
    if target_lib.exists() or target_lib.is_symlink():
        if target_lib.resolve() == native_library.resolve():
            return
        target_lib.unlink()
    rel_target = os.path.relpath(native_library, source_pkg)
    target_lib.symlink_to(rel_target)
    print(f"[repair] linked source native library: {target_lib} -> {rel_target}")


def _site_package_dirs() -> list[Path]:
    dirs: list[Path] = []
    for key in ("purelib", "platlib"):
        value = sysconfig.get_paths().get(key)
        if value:
            dirs.append(Path(value) / "sagevdb")
    try:
        dirs.append(Path(site.getusersitepackages()) / "sagevdb")
    except Exception:
        pass

    unique: list[Path] = []
    seen: set[Path] = set()
    for directory in dirs:
        resolved = directory.resolve() if directory.exists() else directory
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(directory)
    return unique


def _repair_installed_packages(
    *,
    extension: Path,
    native_library: Path,
    suffix: str,
) -> None:
    repaired = 0
    for package_dir in _site_package_dirs():
        if not package_dir.is_dir() or not (package_dir / "__init__.py").is_file():
            continue
        _prune_mismatched_extensions(package_dir, suffix)
        shutil.copy2(extension, package_dir / f"_sagevdb{suffix}")
        shutil.copy2(native_library, package_dir / "libsage_vdb.so")
        repaired += 1
        print(f"[repair] repaired installed package: {package_dir}")
    if repaired == 0:
        print("[repair] no installed sagevdb package found; source checkout repair still completed")


def _maybe_build(sagevdb_root: Path) -> None:
    build_script = sagevdb_root / "build.sh"
    if not build_script.is_file():
        raise SystemExit(f"matching extension missing and build script not found: {build_script}")
    if shutil.which("cmake") is None:
        raise SystemExit(
            "matching extension missing and cmake is not available. "
            "Install cmake or run this script with a Python environment that already has a matching sageVDB build."
        )
    _run(["bash", str(build_script)], cwd=sagevdb_root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sagevdb-root",
        type=Path,
        default=_repo_root().parent / "sageVDB",
        help="Path to the sibling sageVDB checkout.",
    )
    parser.add_argument(
        "--python",
        dest="target_python",
        help="Re-exec the repair with this Python interpreter.",
    )
    parser.add_argument(
        "--build-if-missing",
        action="store_true",
        help="Run ../sageVDB/build.sh if no matching extension is found.",
    )
    parser.add_argument(
        "--source-only",
        action="store_true",
        help="Repair only the sibling source checkout, not site-packages.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only check whether sagevdb imports with required symbols.",
    )
    args = parser.parse_args()

    _maybe_reexec_with_python(args.target_python)

    print(f"[repair] python: {sys.executable}")
    print(f"[repair] version: {sys.version.split()[0]}")
    suffix = _extension_suffix()
    print(f"[repair] extension suffix: {suffix}")

    if args.check:
        return 0 if _import_is_healthy() else 1

    sagevdb_root = args.sagevdb_root.expanduser().resolve()
    if not sagevdb_root.is_dir():
        raise SystemExit(f"sageVDB checkout not found: {sagevdb_root}")

    extension = _find_matching_extension(sagevdb_root, suffix)
    if extension is None and args.build_if_missing:
        _maybe_build(sagevdb_root)
        extension = _find_matching_extension(sagevdb_root, suffix)
    if extension is None:
        raise SystemExit(
            f"No sageVDB extension matching {suffix} found under {sagevdb_root}. "
            "Run with --build-if-missing in an environment with cmake, or choose the project Python 3.12 environment."
        )

    native_library = _find_native_library(sagevdb_root)
    if native_library is None:
        raise SystemExit(f"No libsage_vdb.so found under {sagevdb_root}.")

    print(f"[repair] using extension: {extension}")
    print(f"[repair] using native library: {native_library}")

    _repair_source_checkout(
        sagevdb_root=sagevdb_root,
        extension=extension,
        native_library=native_library,
        suffix=suffix,
    )
    if not args.source_only:
        _repair_installed_packages(extension=extension, native_library=native_library, suffix=suffix)

    return 0 if _import_is_healthy() else 1


if __name__ == "__main__":
    raise SystemExit(main())
