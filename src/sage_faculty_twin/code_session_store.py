from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from .config import AppSettings
from .models import (
    CodeSessionAppendMessageRequest,
    CodeSessionCreateRequest,
    CodeSessionMessage,
    CodeSessionRecord,
    CodeSessionSummary,
)


@dataclass(slots=True)
class CodeSessionEntry:
    session_id: str
    workspace_id: str
    backend: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[CodeSessionMessage] = field(default_factory=list)
    last_proposal_summary: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "workspace_id": self.workspace_id,
            "backend": self.backend,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "messages": [
                message.model_dump(mode="json")
                for message in self.messages
            ],
            "last_proposal_summary": self.last_proposal_summary,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "CodeSessionEntry":
        return cls(
            session_id=str(payload["session_id"]),
            workspace_id=str(payload["workspace_id"]),
            backend=str(payload.get("backend") or "internal"),
            title=str(payload.get("title") or "Untitled code session"),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
            updated_at=datetime.fromisoformat(str(payload["updated_at"])),
            messages=[
                CodeSessionMessage.model_validate(message)
                for message in payload.get("messages", [])
                if isinstance(message, dict)
            ],
            last_proposal_summary=(
                str(payload["last_proposal_summary"])
                if payload.get("last_proposal_summary")
                else None
            ),
        )

    def to_summary(self) -> CodeSessionSummary:
        return CodeSessionSummary(
            session_id=self.session_id,
            workspace_id=self.workspace_id,
            backend=self.backend,
            title=self.title,
            created_at=self.created_at,
            updated_at=self.updated_at,
            message_count=len(self.messages),
            last_proposal_summary=self.last_proposal_summary,
        )

    def to_record(self) -> CodeSessionRecord:
        return CodeSessionRecord(
            **self.to_summary().model_dump(),
            messages=self.messages,
        )


class CodeSessionStore:
    def __init__(self, settings: AppSettings) -> None:
        self._path = settings.code_session_dir
        self._path.mkdir(parents=True, exist_ok=True)
        self._sessions: dict[str, CodeSessionEntry] = {}
        self._load_from_disk()

    def list_sessions(self, *, workspace_id: str | None = None) -> list[CodeSessionSummary]:
        sessions = self._sessions.values()
        if workspace_id:
            sessions = [
                session
                for session in sessions
                if session.workspace_id == workspace_id
            ]
        ordered = sorted(sessions, key=lambda session: session.updated_at, reverse=True)
        return [session.to_summary() for session in ordered]

    def create_session(
        self,
        request: CodeSessionCreateRequest,
        *,
        default_backend: str,
    ) -> CodeSessionRecord:
        now = datetime.now(UTC)
        initial_messages: list[CodeSessionMessage] = []
        if request.initial_message is not None:
            initial = request.initial_message
            initial_messages.append(
                initial.model_copy(update={"created_at": initial.created_at or now})
            )
        entry = CodeSessionEntry(
            session_id=str(uuid4()),
            workspace_id=request.workspace_id,
            backend=request.backend or default_backend,
            title=self._title_from_request(request),
            created_at=now,
            updated_at=now,
            messages=initial_messages,
        )
        self._sessions[entry.session_id] = entry
        self._persist_entry(entry)
        return entry.to_record()

    def get_session(self, session_id: str) -> CodeSessionRecord | None:
        entry = self._sessions.get(session_id)
        return entry.to_record() if entry is not None else None

    def append_message(
        self,
        session_id: str,
        request: CodeSessionAppendMessageRequest,
    ) -> CodeSessionRecord | None:
        entry = self._sessions.get(session_id)
        if entry is None:
            return None
        now = datetime.now(UTC)
        entry.messages.append(
            CodeSessionMessage(
                role=request.role,
                content=request.content,
                created_at=now,
                metadata=request.metadata,
            )
        )
        if request.last_proposal_summary is not None:
            stripped = request.last_proposal_summary.strip()
            entry.last_proposal_summary = stripped or None
        entry.updated_at = now
        self._persist_entry(entry)
        return entry.to_record()

    def _persist_entry(self, entry: CodeSessionEntry) -> None:
        self._path.mkdir(parents=True, exist_ok=True)
        (self._path / f"{self._safe_file_stem(entry.session_id)}.json").write_text(
            json.dumps(entry.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _load_from_disk(self) -> None:
        for file_path in sorted(self._path.glob("*.json")):
            payload = json.loads(file_path.read_text(encoding="utf-8"))
            entry = CodeSessionEntry.from_dict(payload)
            self._sessions[entry.session_id] = entry

    def _title_from_request(self, request: CodeSessionCreateRequest) -> str:
        if request.title and request.title.strip():
            return request.title.strip()
        if request.initial_message is not None:
            first_line = request.initial_message.content.strip().splitlines()[0]
            if first_line:
                return first_line[:80]
        return "Untitled code session"

    def _safe_file_stem(self, value: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_.-]+", "-", value).strip("-") or "session"
