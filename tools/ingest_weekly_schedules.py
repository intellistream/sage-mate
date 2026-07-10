"""Ingest team weekly schedule documents into the sage-mate knowledge base.

These schedules describe the PI's and team members' weekly routines, meeting cadence,
and collaboration interfaces — essential context for the digital twin to answer
availability, scheduling, and team management questions.

Usage:
    cd /home/shuhao/sage-mate
    python tools/ingest_weekly_schedules.py

If sentence-transformers is available, the script uses the full knowledge store API
(with embedding and indexing). Otherwise it falls back to writing raw JSON documents
into the knowledge base directory; indexes will be rebuilt on next service start.
"""
from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

_MAX_CONTENT_LEN = 18000

_SCHEDULE_DIR = Path("/home/shuhao/private-materials/课题组管理/周工作安排")
_KNOWLEDGE_BASE_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge_base"

_SCHEDULE_SOURCES = [
    {
        "file": "pi-weekly-schedule.md",
        "title": "团队管理｜项目负责人周工作安排",
        "tags": ["team-management", "schedule", "weekly-routine", "pi", "availability", "meeting"],
        "source_name": "team-schedule/pi-weekly-schedule",
    },
    {
        "file": "engineer-weekly-schedule.md",
        "title": "团队管理｜工程师周工作安排",
        "tags": ["team-management", "schedule", "weekly-routine", "engineer", "meeting"],
        "source_name": "team-schedule/engineer-weekly-schedule",
    },
    {
        "file": "project-assistant-weekly-schedule.md",
        "title": "团队管理｜项目助理周工作安排",
        "tags": ["team-management", "schedule", "weekly-routine", "project-assistant", "meeting"],
        "source_name": "team-schedule/project-assistant-weekly-schedule",
    },
    {
        "file": "part-time-assistant-weekly-schedule.md",
        "title": "团队管理｜兼职助理周工作安排",
        "tags": ["team-management", "schedule", "weekly-routine", "part-time-assistant", "meeting"],
        "source_name": "team-schedule/part-time-assistant-weekly-schedule",
    },
    {
        "file": "academic-student-weekly-schedule.md",
        "title": "团队管理｜学术路线学生周工作安排",
        "tags": ["team-management", "schedule", "weekly-routine", "student", "academic", "meeting"],
        "source_name": "team-schedule/academic-student-weekly-schedule",
    },
    {
        "file": "engineering-student-weekly-schedule.md",
        "title": "团队管理｜工程路线学生周工作安排",
        "tags": ["team-management", "schedule", "weekly-routine", "student", "engineering", "meeting"],
        "source_name": "team-schedule/engineering-student-weekly-schedule",
    },
]


def _read_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")[:_MAX_CONTENT_LEN]


def _find_existing_by_source(source_name: str) -> Path | None:
    """Find existing document JSON by source_name."""
    for json_path in _KNOWLEDGE_BASE_DIR.glob("*.json"):
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if data.get("source_name") == source_name:
            return json_path
    return None


def _write_document(
    *,
    document_id: str,
    title: str,
    content: str,
    tags: list[str],
    source_name: str,
) -> Path:
    """Write a knowledge document JSON to disk."""
    record = {
        "document_id": document_id,
        "title": title,
        "content": content,
        "tags": tags,
        "source_name": source_name,
        "metadata": {
            "domain": "meeting",
            "identity": "pi",
            "source_kind": "manual",
        },
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    target = _KNOWLEDGE_BASE_DIR / f"{document_id}.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def main() -> int:
    _KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)

    created = updated = skipped = 0
    for src in _SCHEDULE_SOURCES:
        file_path = _SCHEDULE_DIR / src["file"]
        content = _read_file(file_path)
        if not content.strip():
            print(f"  SKIP (empty or missing): {file_path}")
            skipped += 1
            continue

        existing_path = _find_existing_by_source(src["source_name"])
        if existing_path:
            # Re-use existing document_id for upsert semantics
            doc_id = existing_path.stem
            _write_document(
                document_id=doc_id,
                title=src["title"],
                content=content,
                tags=src["tags"],
                source_name=src["source_name"],
            )
            print(f"  UPDATED: {src['title']} ({doc_id[:8]})")
            updated += 1
        else:
            doc_id = str(uuid4())
            _write_document(
                document_id=doc_id,
                title=src["title"],
                content=content,
                tags=src["tags"],
                source_name=src["source_name"],
            )
            print(f"  CREATED: {src['title']} ({doc_id[:8]})")
            created += 1

    print(f"\nDone. created={created}, updated={updated}, skipped={skipped}")
    print("Note: Embedding indexes will be rebuilt on next service start.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
