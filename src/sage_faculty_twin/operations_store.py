from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime

from .config import AppSettings
from .models import OperationsTaskStateRecord, OperationsTaskStateUpdateRequest


@dataclass(slots=True)
class OperationsTaskStateEntry:
    task_key: str
    status: str
    assigned_to: str | None
    note: str | None
    updated_at: datetime

    def to_dict(self) -> dict[str, object]:
        return {
            "task_key": self.task_key,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "note": self.note,
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> OperationsTaskStateEntry:
        return cls(
            task_key=str(payload["task_key"]),
            status=str(payload.get("status") or "open"),
            assigned_to=(str(payload["assigned_to"]) if payload.get("assigned_to") else None),
            note=(str(payload["note"]) if payload.get("note") else None),
            updated_at=datetime.fromisoformat(str(payload["updated_at"])),
        )

    def to_response(self) -> OperationsTaskStateRecord:
        return OperationsTaskStateRecord(
            task_key=self.task_key,
            status=self.status,
            assigned_to=self.assigned_to,
            note=self.note,
            updated_at=self.updated_at,
        )


class OperationsTaskStateStore:
    def __init__(self, settings: AppSettings) -> None:
        self._path = settings.operations_task_state_dir
        self._path.mkdir(parents=True, exist_ok=True)
        self._entries: dict[str, OperationsTaskStateEntry] = {}
        self._load_from_disk()

    def get_state(self, task_key: str) -> OperationsTaskStateRecord | None:
        entry = self._entries.get(task_key)
        return entry.to_response() if entry is not None else None

    def update_state(
        self,
        task_key: str,
        request: OperationsTaskStateUpdateRequest,
    ) -> OperationsTaskStateRecord:
        existing = self._entries.get(task_key)
        entry = OperationsTaskStateEntry(
            task_key=task_key,
            status=request.status or (existing.status if existing else "open"),
            assigned_to=self._normalize_optional_text(
                request.assigned_to if request.assigned_to is not None else (existing.assigned_to if existing else None)
            ),
            note=self._normalize_optional_text(request.note if request.note is not None else (existing.note if existing else None)),
            updated_at=datetime.now(UTC),
        )
        self._entries[task_key] = entry
        self._persist_entry(entry)
        return entry.to_response()

    def _persist_entry(self, entry: OperationsTaskStateEntry) -> None:
        file_name = re.sub(r"[^a-zA-Z0-9_.-]+", "-", entry.task_key).strip("-") or "task"
        (self._path / f"{file_name}.json").write_text(
            json.dumps(entry.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _load_from_disk(self) -> None:
        for file_path in sorted(self._path.glob("*.json")):
            payload = json.loads(file_path.read_text(encoding="utf-8"))
            entry = OperationsTaskStateEntry.from_dict(payload)
            self._entries[entry.task_key] = entry

    def _normalize_optional_text(self, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None