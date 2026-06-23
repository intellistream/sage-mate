#!/usr/bin/env python3
"""Prune KB entries that are now covered by installed curated skills.

This is intentionally conservative:
- it only removes explicit source_name matches listed below;
- it refuses to remove admin/private entries;
- it does not touch courseware, raw lecture PDFs, accounts, memory, or logs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_DUPLICATE_SOURCE_NAMES = {
    "curated_faq:meeting-preparation-checklist",
    "private-materials:paper-revision-lessons-zh-summary",
}

PROTECTED_AUDIENCES = {"admin", "private"}


def _audience(record: dict) -> str:
    metadata = record.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    audience = record.get("audience") or metadata.get("audience") or ""
    if audience:
        return str(audience)
    for tag in record.get("tags") or []:
        if isinstance(tag, str) and tag.startswith("audience:"):
            return tag.split(":", 1)[1]
    return ""


def _is_courseware(record: dict) -> bool:
    tags = {str(tag) for tag in record.get("tags") or []}
    return bool(tags & {"courseware", "teaching", "material:lecture", "material:pdf"})


def _load_record(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--knowledge-base-dir",
        type=Path,
        default=Path("../sage-faculty-twin-runtime-private/data/knowledge_base"),
    )
    parser.add_argument("--apply", action="store_true", help="Actually delete matched files.")
    args = parser.parse_args()

    kb_dir = args.knowledge_base_dir.resolve()
    if not kb_dir.is_dir():
        raise SystemExit(f"Knowledge base dir not found: {kb_dir}")

    candidates: list[tuple[Path, dict]] = []
    skipped: list[tuple[Path, str]] = []
    for path in sorted(kb_dir.glob("*.json")):
        record = _load_record(path)
        if record is None:
            continue
        source_name = str(record.get("source_name") or "")
        if source_name not in DEFAULT_DUPLICATE_SOURCE_NAMES:
            continue
        audience = _audience(record)
        if audience in PROTECTED_AUDIENCES:
            skipped.append((path, f"protected audience={audience}"))
            continue
        if _is_courseware(record):
            skipped.append((path, "courseware"))
            continue
        candidates.append((path, record))

    for path, record in candidates:
        action = "delete" if args.apply else "would-delete"
        print(f"{action}\t{path.name}\t{record.get('title')}\t{record.get('source_name')}")

    for path, reason in skipped:
        print(f"skip\t{path.name}\t{reason}")

    if args.apply:
        for path, _record in candidates:
            path.unlink()

    print(f"matched={len(candidates)} applied={args.apply}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
