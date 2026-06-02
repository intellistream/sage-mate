from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from .config import AppSettings
from .models import AnonymousSuggestionCreate, AnonymousSuggestionRecord


@dataclass(slots=True)
class SuggestionBoardEntry:
    suggestion_id: str
    message: str
    category: str | None
    created_at: datetime

    def to_dict(self) -> dict[str, object]:
        return {
            "suggestion_id": self.suggestion_id,
            "message": self.message,
            "category": self.category,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> SuggestionBoardEntry:
        return cls(
            suggestion_id=str(payload["suggestion_id"]),
            message=str(payload["message"]),
            category=(str(payload["category"]) if payload.get("category") else None),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
        )

    def to_response(self) -> AnonymousSuggestionRecord:
        return AnonymousSuggestionRecord(
            suggestion_id=self.suggestion_id,
            message=self.message,
            category=self.category,
            created_at=self.created_at,
        )


class SuggestionBoardStore:
    def __init__(self, settings: AppSettings) -> None:
        self._path = settings.suggestion_board_dir
        self._path.mkdir(parents=True, exist_ok=True)
        self._records: dict[str, SuggestionBoardEntry] = {}
        self._load_from_disk()

    def create_suggestion(self, request: AnonymousSuggestionCreate) -> AnonymousSuggestionRecord:
        category = request.category.strip() if request.category else None
        record = SuggestionBoardEntry(
            suggestion_id=str(uuid4()),
            message=request.message.strip(),
            category=category or None,
            created_at=datetime.now(UTC),
        )
        self._persist_record(record)
        self._records[record.suggestion_id] = record
        return record.to_response()

    def list_suggestions(self, *, limit: int = 50) -> list[AnonymousSuggestionRecord]:
        records = sorted(self._records.values(), key=lambda item: item.created_at, reverse=True)
        return [record.to_response() for record in records[:limit]]

    def count_suggestions(self) -> int:
        return len(self._records)

    def _persist_record(self, record: SuggestionBoardEntry) -> None:
        # Defensive: re-create the directory in case it was wiped at runtime.
        self._path.mkdir(parents=True, exist_ok=True)
        (self._path / f"{record.suggestion_id}.json").write_text(
            json.dumps(record.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _load_from_disk(self) -> None:
        for file_path in sorted(self._path.glob("*.json")):
            payload = json.loads(file_path.read_text(encoding="utf-8"))
            record = SuggestionBoardEntry.from_dict(payload)
            self._records[record.suggestion_id] = record
