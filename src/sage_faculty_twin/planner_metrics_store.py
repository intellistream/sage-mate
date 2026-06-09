from __future__ import annotations

import json
import sqlite3
import re
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from .config import AppSettings

_STEP_PATTERN = re.compile(r"\bstep\s+([a-z_][a-z0-9_]*)\b", re.IGNORECASE)


@dataclass(slots=True)
class PlannerMetricsEntry:
    record_id: str
    conversation_id: str
    planner_stage: str
    planner_mode: str
    question: str
    goal: str
    accepted: bool
    status: str
    fallback_template: str | None
    fallback_reason: str | None
    validation_errors: list[str]
    planned_steps: list[str]
    latency_ms: float
    created_at: datetime

    def to_dict(self) -> dict[str, object]:
        return {
            "record_id": self.record_id,
            "conversation_id": self.conversation_id,
            "planner_stage": self.planner_stage,
            "planner_mode": self.planner_mode,
            "question": self.question,
            "goal": self.goal,
            "accepted": self.accepted,
            "status": self.status,
            "fallback_template": self.fallback_template,
            "fallback_reason": self.fallback_reason,
            "validation_errors": list(self.validation_errors),
            "planned_steps": list(self.planned_steps),
            "latency_ms": self.latency_ms,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> PlannerMetricsEntry:
        return cls(
            record_id=str(payload["record_id"]),
            conversation_id=str(payload.get("conversation_id") or ""),
            planner_stage=str(payload.get("planner_stage") or "deterministic"),
            planner_mode=str(payload.get("planner_mode") or "deterministic"),
            question=str(payload.get("question") or ""),
            goal=str(payload.get("goal") or ""),
            accepted=bool(payload.get("accepted", False)),
            status=str(payload.get("status") or "accepted"),
            fallback_template=(
                str(payload["fallback_template"]) if payload.get("fallback_template") else None
            ),
            fallback_reason=(
                str(payload["fallback_reason"]) if payload.get("fallback_reason") else None
            ),
            validation_errors=[str(item) for item in payload.get("validation_errors", [])],
            planned_steps=[str(item) for item in payload.get("planned_steps", [])],
            latency_ms=float(payload.get("latency_ms") or 0.0),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
        )


class PlannerMetricsStore:
    def __init__(self, settings: AppSettings) -> None:
        self._path = settings.planner_metrics_dir or (
            settings.conversation_memory_dir / "planner-metrics"
        )
        self._path.mkdir(parents=True, exist_ok=True)
        self._db_path = self._path / "planner_metrics.sqlite3"
        self._ensure_database()
        self._entries: dict[str, PlannerMetricsEntry] = {}
        self._load_from_db()
        self._migrate_legacy_json_files()

    def record_entry(
        self,
        *,
        conversation_id: str,
        planner_stage: str,
        planner_mode: str,
        question: str,
        goal: str,
        accepted: bool,
        status: str,
        fallback_template: str | None,
        fallback_reason: str | None,
        validation_errors: list[str],
        planned_steps: list[str],
        latency_ms: float,
    ) -> PlannerMetricsEntry:
        entry = PlannerMetricsEntry(
            record_id=str(uuid4()),
            conversation_id=conversation_id,
            planner_stage=planner_stage,
            planner_mode=planner_mode,
            question=question.strip(),
            goal=goal,
            accepted=accepted,
            status=status,
            fallback_template=fallback_template,
            fallback_reason=fallback_reason.strip() if fallback_reason else None,
            validation_errors=[item.strip() for item in validation_errors if item.strip()],
            planned_steps=list(planned_steps),
            latency_ms=max(0.0, float(latency_ms)),
            created_at=datetime.now(UTC),
        )
        self._entries[entry.record_id] = entry
        self._persist_entry(entry)
        return entry

    def count_entries(self) -> int:
        return len(self._entries)

    def list_entries(self, *, limit: int | None = None) -> list[PlannerMetricsEntry]:
        entries = sorted(self._entries.values(), key=lambda item: item.created_at, reverse=True)
        if limit is not None:
            entries = entries[: max(0, limit)]
        return entries

    def build_summary(self) -> dict[str, object]:
        entries = list(self._entries.values())
        deterministic = [entry for entry in entries if entry.planner_stage == "deterministic"]
        shadow = [entry for entry in entries if entry.planner_stage == "shadow"]
        shadow_ready = [entry for entry in shadow if entry.status in {"accepted", "rejected"}]
        deterministic_fallbacks = [entry for entry in deterministic if entry.status == "fallback"]
        shadow_errors = [entry for entry in shadow if entry.status == "shadow_error"]
        shadow_disabled = [entry for entry in shadow if entry.status == "shadow_disabled"]
        shadow_rejected = [entry for entry in shadow if entry.status == "rejected"]
        rejection_reasons: Counter[str] = Counter()
        rejected_steps: Counter[str] = Counter()
        fallback_templates: Counter[str] = Counter()

        for entry in entries:
            if entry.fallback_template:
                fallback_templates[entry.fallback_template] += 1
            if entry.accepted:
                continue
            reason = entry.fallback_reason or (
                entry.validation_errors[0] if entry.validation_errors else entry.status
            )
            rejection_reasons[reason] += 1
            for error in entry.validation_errors:
                for step_id in _STEP_PATTERN.findall(error):
                    rejected_steps[step_id] += 1

        return {
            "record_count": len(entries),
            "deterministic_total": len(deterministic),
            "deterministic_accepted": sum(1 for entry in deterministic if entry.accepted),
            "deterministic_fallbacks": len(deterministic_fallbacks),
            "deterministic_acceptance_rate": _ratio(
                sum(1 for entry in deterministic if entry.accepted),
                len(deterministic),
            ),
            "deterministic_fallback_rate": _ratio(len(deterministic_fallbacks), len(deterministic)),
            "shadow_total": len(shadow),
            "shadow_ready": len(shadow_ready),
            "shadow_accepted": sum(1 for entry in shadow_ready if entry.accepted),
            "shadow_rejected": len(shadow_rejected),
            "shadow_disabled": len(shadow_disabled),
            "shadow_errors": len(shadow_errors),
            "shadow_acceptance_rate": _ratio(
                sum(1 for entry in shadow_ready if entry.accepted),
                len(shadow_ready),
            ),
            "shadow_error_rate": _ratio(len(shadow_errors), len(shadow)),
            "avg_deterministic_latency_ms": _average_latency(deterministic),
            "avg_shadow_latency_ms": _average_latency(shadow),
            "max_deterministic_latency_ms": _max_latency(deterministic),
            "max_shadow_latency_ms": _max_latency(shadow),
            "rejection_reasons": dict(rejection_reasons.most_common()),
            "rejected_steps": dict(rejected_steps.most_common()),
            "fallback_templates": dict(fallback_templates.most_common()),
        }

    def _persist_entry(self, entry: PlannerMetricsEntry) -> None:
        self._ensure_database()
        payload = json.dumps(entry.to_dict(), ensure_ascii=False)
        with sqlite3.connect(self._db_path) as connection:
            connection.execute(
                """
                INSERT INTO planner_metrics_entries (record_id, created_at, payload)
                VALUES (?, ?, ?)
                ON CONFLICT(record_id) DO UPDATE SET
                    created_at = excluded.created_at,
                    payload = excluded.payload
                """,
                (entry.record_id, entry.created_at.isoformat(), payload),
            )
            connection.commit()

    def _ensure_database(self) -> None:
        self._path.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS planner_metrics_entries (
                    record_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def _load_from_db(self) -> None:
        self._ensure_database()
        with sqlite3.connect(self._db_path) as connection:
            rows = connection.execute("SELECT payload FROM planner_metrics_entries").fetchall()
        for (payload_raw,) in rows:
            payload = json.loads(str(payload_raw))
            entry = PlannerMetricsEntry.from_dict(payload)
            self._entries[entry.record_id] = entry

    def _migrate_legacy_json_files(self) -> None:
        for file_path in sorted(self._path.glob("*.json")):
            payload = json.loads(file_path.read_text(encoding="utf-8"))
            entry = PlannerMetricsEntry.from_dict(payload)
            if entry.record_id not in self._entries:
                self._entries[entry.record_id] = entry
                self._persist_entry(entry)
            file_path.unlink(missing_ok=True)


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(float(numerator) / float(denominator), 4)


def _average_latency(entries: list[PlannerMetricsEntry]) -> float:
    if not entries:
        return 0.0
    return round(sum(entry.latency_ms for entry in entries) / float(len(entries)), 2)


def _max_latency(entries: list[PlannerMetricsEntry]) -> float:
    if not entries:
        return 0.0
    return round(max(entry.latency_ms for entry in entries), 2)
