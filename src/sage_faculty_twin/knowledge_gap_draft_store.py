from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from .config import AppSettings
from .models import KnowledgeGapDraftRecordResponse


@dataclass(slots=True)
class KnowledgeGapDraftRecord:
    draft_id: str
    cluster_id: str
    interaction_domain: str
    label: str
    reason: str
    suggested_action: str
    sample_questions: list[str]
    title: str
    content: str
    tags: list[str]
    source_name: str
    status: str
    published_document_id: str | None
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None

    def to_dict(self) -> dict[str, object]:
        return {
            "draft_id": self.draft_id,
            "cluster_id": self.cluster_id,
            "interaction_domain": self.interaction_domain,
            "label": self.label,
            "reason": self.reason,
            "suggested_action": self.suggested_action,
            "sample_questions": list(self.sample_questions),
            "title": self.title,
            "content": self.content,
            "tags": list(self.tags),
            "source_name": self.source_name,
            "status": self.status,
            "published_document_id": self.published_document_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "published_at": self.published_at.isoformat() if self.published_at else None,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> KnowledgeGapDraftRecord:
        published_at_raw = payload.get("published_at")
        return cls(
            draft_id=str(payload["draft_id"]),
            cluster_id=str(payload["cluster_id"]),
            interaction_domain=str(payload["interaction_domain"]),
            label=str(payload["label"]),
            reason=str(payload["reason"]),
            suggested_action=str(payload["suggested_action"]),
            sample_questions=[str(item) for item in payload.get("sample_questions", [])],
            title=str(payload["title"]),
            content=str(payload["content"]),
            tags=[str(item) for item in payload.get("tags", [])],
            source_name=str(payload["source_name"]),
            status=str(payload["status"]),
            published_document_id=(str(payload["published_document_id"]) if payload.get("published_document_id") else None),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
            updated_at=datetime.fromisoformat(str(payload["updated_at"])),
            published_at=datetime.fromisoformat(str(published_at_raw)) if published_at_raw else None,
        )

    def to_response(self) -> KnowledgeGapDraftRecordResponse:
        return KnowledgeGapDraftRecordResponse(
            draft_id=self.draft_id,
            cluster_id=self.cluster_id,
            interaction_domain=self.interaction_domain,
            label=self.label,
            reason=self.reason,
            suggested_action=self.suggested_action,
            sample_questions=list(self.sample_questions),
            title=self.title,
            content=self.content,
            tags=list(self.tags),
            source_name=self.source_name,
            status=self.status,
            published_document_id=self.published_document_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
            published_at=self.published_at,
        )


class KnowledgeGapDraftStore:
    def __init__(self, settings: AppSettings) -> None:
        self._path = settings.knowledge_gap_draft_dir
        self._path.mkdir(parents=True, exist_ok=True)
        self._records: dict[str, KnowledgeGapDraftRecord] = {}
        self._load_from_disk()

    def upsert_generated_draft(
        self,
        *,
        cluster_id: str,
        interaction_domain: str,
        label: str,
        reason: str,
        suggested_action: str,
        sample_questions: list[str],
        title: str,
        content: str,
        tags: list[str],
        source_name: str,
    ) -> KnowledgeGapDraftRecordResponse:
        existing = self.get_by_cluster_id(cluster_id)
        now = datetime.now(UTC)
        record = KnowledgeGapDraftRecord(
            draft_id=existing.draft_id if existing else str(uuid4()),
            cluster_id=cluster_id,
            interaction_domain=interaction_domain,
            label=label,
            reason=reason,
            suggested_action=suggested_action,
            sample_questions=list(sample_questions),
            title=title,
            content=content,
            tags=list(tags),
            source_name=source_name,
            status=(existing.status if existing and existing.status == "published" else "draft"),
            published_document_id=(existing.published_document_id if existing else None),
            created_at=(existing.created_at if existing else now),
            updated_at=now,
            published_at=(existing.published_at if existing else None),
        )
        self._records[record.draft_id] = record
        self._persist_record(record)
        return record.to_response()

    def list_drafts(self) -> list[KnowledgeGapDraftRecordResponse]:
        records = sorted(self._records.values(), key=lambda item: item.updated_at, reverse=True)
        return [record.to_response() for record in records]

    def get_draft(self, draft_id: str) -> KnowledgeGapDraftRecord | None:
        return self._records.get(draft_id)

    def get_by_cluster_id(self, cluster_id: str) -> KnowledgeGapDraftRecord | None:
        for record in self._records.values():
            if record.cluster_id == cluster_id:
                return record
        return None

    def mark_published(self, draft_id: str, *, document_id: str) -> KnowledgeGapDraftRecordResponse:
        record = self._records.get(draft_id)
        if record is None:
            raise KeyError(draft_id)
        now = datetime.now(UTC)
        record.status = "published"
        record.published_document_id = document_id
        record.updated_at = now
        record.published_at = now
        self._persist_record(record)
        return record.to_response()

    def count_drafts(self) -> int:
        return len(self._records)

    def _persist_record(self, record: KnowledgeGapDraftRecord) -> None:
        (self._path / f"{record.draft_id}.json").write_text(
            json.dumps(record.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _load_from_disk(self) -> None:
        for file_path in sorted(self._path.glob("*.json")):
            payload = json.loads(file_path.read_text(encoding="utf-8"))
            record = KnowledgeGapDraftRecord.from_dict(payload)
            self._records[record.draft_id] = record
