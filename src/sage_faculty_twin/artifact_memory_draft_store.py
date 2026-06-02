from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from .config import AppSettings
from .models import ArtifactMemoryDraftRecordResponse


@dataclass(slots=True)
class ArtifactMemoryDraftRecord:
    draft_id: str
    conversation_id: str
    source_memory_id: str | None
    student_name: str
    student_email: str | None
    interaction_domain: str | None
    question: str
    answer: str
    artifact_names: list[str]
    artifact_sources: list[str]
    artifact_excerpt_count: int
    provenance_note: str
    retention_label: str
    status: str
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, object]:
        return {
            "draft_id": self.draft_id,
            "conversation_id": self.conversation_id,
            "source_memory_id": self.source_memory_id,
            "student_name": self.student_name,
            "student_email": self.student_email,
            "interaction_domain": self.interaction_domain,
            "question": self.question,
            "answer": self.answer,
            "artifact_names": list(self.artifact_names),
            "artifact_sources": list(self.artifact_sources),
            "artifact_excerpt_count": self.artifact_excerpt_count,
            "provenance_note": self.provenance_note,
            "retention_label": self.retention_label,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def to_response(self) -> ArtifactMemoryDraftRecordResponse:
        return ArtifactMemoryDraftRecordResponse(
            draft_id=self.draft_id,
            conversation_id=self.conversation_id,
            source_memory_id=self.source_memory_id,
            student_name=self.student_name,
            student_email=self.student_email,
            interaction_domain=self.interaction_domain,
            question=self.question,
            answer=self.answer,
            artifact_names=list(self.artifact_names),
            artifact_sources=list(self.artifact_sources),
            artifact_excerpt_count=self.artifact_excerpt_count,
            provenance_note=self.provenance_note,
            retention_label=self.retention_label,
            status=self.status,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> ArtifactMemoryDraftRecord:
        return cls(
            draft_id=str(payload["draft_id"]),
            conversation_id=str(payload["conversation_id"]),
            source_memory_id=(
                str(payload["source_memory_id"]) if payload.get("source_memory_id") else None
            ),
            student_name=str(payload["student_name"]),
            student_email=(str(payload["student_email"]) if payload.get("student_email") else None),
            interaction_domain=(
                str(payload["interaction_domain"]) if payload.get("interaction_domain") else None
            ),
            question=str(payload["question"]),
            answer=str(payload["answer"]),
            artifact_names=[str(item) for item in payload.get("artifact_names", [])],
            artifact_sources=[str(item) for item in payload.get("artifact_sources", [])],
            artifact_excerpt_count=int(payload.get("artifact_excerpt_count", 0)),
            provenance_note=str(payload.get("provenance_note") or ""),
            retention_label=str(payload.get("retention_label") or "project_followup"),
            status=str(payload.get("status") or "draft"),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
            updated_at=datetime.fromisoformat(str(payload["updated_at"])),
        )


class ArtifactMemoryDraftStore:
    def __init__(self, settings: AppSettings) -> None:
        self._path = settings.artifact_memory_draft_dir
        self._path.mkdir(parents=True, exist_ok=True)
        self._records: dict[str, ArtifactMemoryDraftRecord] = {}
        self._load_from_disk()

    def create_draft(
        self,
        *,
        conversation_id: str,
        source_memory_id: str | None,
        student_name: str,
        student_email: str | None,
        interaction_domain: str | None,
        question: str,
        answer: str,
        artifact_names: list[str],
        artifact_sources: list[str],
        artifact_excerpt_count: int,
        provenance_note: str,
        retention_label: str = "project_followup",
    ) -> ArtifactMemoryDraftRecord:
        now = datetime.now(UTC)
        record = ArtifactMemoryDraftRecord(
            draft_id=str(uuid4()),
            conversation_id=conversation_id,
            source_memory_id=source_memory_id,
            student_name=student_name,
            student_email=student_email,
            interaction_domain=interaction_domain,
            question=question,
            answer=answer,
            artifact_names=list(artifact_names),
            artifact_sources=list(artifact_sources),
            artifact_excerpt_count=artifact_excerpt_count,
            provenance_note=provenance_note,
            retention_label=retention_label,
            status="draft",
            created_at=now,
            updated_at=now,
        )
        self._records[record.draft_id] = record
        self._persist_record(record)
        return record

    def list_drafts(self) -> list[ArtifactMemoryDraftRecord]:
        return sorted(self._records.values(), key=lambda item: item.updated_at, reverse=True)

    def get_draft(self, draft_id: str) -> ArtifactMemoryDraftRecord | None:
        return self._records.get(draft_id)

    def mark_accepted(self, draft_id: str) -> ArtifactMemoryDraftRecord:
        return self._mark_status(draft_id, status="accepted")

    def mark_rejected(self, draft_id: str) -> ArtifactMemoryDraftRecord:
        return self._mark_status(draft_id, status="rejected")

    def count_drafts(self) -> int:
        return len(self._records)

    def _mark_status(self, draft_id: str, *, status: str) -> ArtifactMemoryDraftRecord:
        record = self._records.get(draft_id)
        if record is None:
            raise KeyError(draft_id)
        if record.status == status:
            return record
        if record.status != "draft":
            raise ValueError(record.status)
        record.status = status
        record.updated_at = datetime.now(UTC)
        self._persist_record(record)
        return record

    def _persist_record(self, record: ArtifactMemoryDraftRecord) -> None:
        # Defensive: re-create the directory in case it was wiped at runtime.
        self._path.mkdir(parents=True, exist_ok=True)
        (self._path / f"{record.draft_id}.json").write_text(
            json.dumps(record.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _load_from_disk(self) -> None:
        for file_path in sorted(self._path.glob("*.json")):
            payload = json.loads(file_path.read_text(encoding="utf-8"))
            record = ArtifactMemoryDraftRecord.from_dict(payload)
            self._records[record.draft_id] = record
