from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from .config import AppSettings
from .models import BookingResponse, ChatRequest
from .profile_summarizer import ConversationProfileSummarizer


@dataclass(slots=True)
class ConversationMemoryRecord:
    memory_id: str
    conversation_id: str
    student_name: str
    student_email: str | None
    course_context: str | None
    question: str
    answer: str
    workflow_action: str
    interaction_domain: str | None
    knowledge_hit_count: int
    booking_summary: str | None
    created_at: datetime

    def to_dict(self) -> dict[str, object]:
        return {
            "memory_id": self.memory_id,
            "conversation_id": self.conversation_id,
            "student_name": self.student_name,
            "student_email": self.student_email,
            "course_context": self.course_context,
            "question": self.question,
            "answer": self.answer,
            "workflow_action": self.workflow_action,
            "interaction_domain": self.interaction_domain,
            "knowledge_hit_count": self.knowledge_hit_count,
            "booking_summary": self.booking_summary,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> ConversationMemoryRecord:
        return cls(
            memory_id=str(payload["memory_id"]),
            conversation_id=str(payload["conversation_id"]),
            student_name=str(payload["student_name"]),
            student_email=(str(payload["student_email"]) if payload.get("student_email") else None),
            course_context=(str(payload["course_context"]) if payload.get("course_context") else None),
            question=str(payload["question"]),
            answer=str(payload["answer"]),
            workflow_action=str(payload["workflow_action"]),
            interaction_domain=(str(payload["interaction_domain"]) if payload.get("interaction_domain") else None),
            knowledge_hit_count=int(payload.get("knowledge_hit_count", 0)),
            booking_summary=(str(payload["booking_summary"]) if payload.get("booking_summary") else None),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
        )

    def retrieval_text(self) -> str:
        parts = [
            f"student {self.student_name}",
            f"question {self.question}",
            f"answer {self.answer}",
            f"workflow {self.workflow_action}",
        ]
        if self.interaction_domain:
            parts.append(f"domain {self.interaction_domain}")
        parts.append(f"knowledge_hits {self.knowledge_hit_count}")
        if self.student_email:
            parts.append(f"email {self.student_email}")
        if self.course_context:
            parts.append(f"course {self.course_context}")
        if self.booking_summary:
            parts.append(f"booking {self.booking_summary}")
        return " ".join(parts)


@dataclass(slots=True)
class ConversationMemoryHit:
    memory_id: str
    conversation_id: str
    summary: str
    score: float
    created_at: datetime
    memory_type: str = "short_term"


@dataclass(slots=True)
class ProfileMemoryRecord:
    profile_id: str
    student_key: str
    student_name: str
    student_email: str | None
    category: str
    summary: str
    evidence: str
    updated_at: datetime

    def to_dict(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "student_key": self.student_key,
            "student_name": self.student_name,
            "student_email": self.student_email,
            "category": self.category,
            "summary": self.summary,
            "evidence": self.evidence,
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> ProfileMemoryRecord:
        return cls(
            profile_id=str(payload["profile_id"]),
            student_key=str(payload["student_key"]),
            student_name=str(payload["student_name"]),
            student_email=(str(payload["student_email"]) if payload.get("student_email") else None),
            category=str(payload["category"]),
            summary=str(payload["summary"]),
            evidence=str(payload["evidence"]),
            updated_at=datetime.fromisoformat(str(payload["updated_at"])),
        )

    def retrieval_text(self) -> str:
        category_aliases = {
            "identity": "用户身份 姓名 邮箱 联系方式",
            "course_context": "课程场景 交流背景 科研指导",
            "recent_topic": "近期话题 关注主题 讨论重点",
            "booking_preference": "预约偏好 预约习惯 预约需求 meeting booking preference",
            "collaboration_preference": "沟通偏好 协作偏好 会前准备 准备材料 agenda blocker draft collaboration preference",
        }
        parts = [
            f"student {self.student_name}",
            f"category {self.category}",
            category_aliases.get(self.category, ""),
            self.summary,
            self.evidence,
        ]
        if self.student_email:
            parts.append(f"email {self.student_email}")
        return " ".join(parts)


@dataclass(slots=True)
class MemorySearchPlan:
    policy_name: str
    short_term_limit: int
    long_term_limit: int


class NeuroMemConversationStore:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._base_dir = settings.conversation_memory_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._records_dir = self._base_dir / "records"
        self._records_dir.mkdir(parents=True, exist_ok=True)
        self._profiles_dir = self._base_dir / "profiles"
        self._profiles_dir.mkdir(parents=True, exist_ok=True)
        self._records: dict[str, ConversationMemoryRecord] = {}
        self._profiles: dict[str, ProfileMemoryRecord] = {}
        self._profile_summarizer = ConversationProfileSummarizer()
        self._conversation_collection = self._initialize_collection("conversation-memory")
        self._profile_collection = self._initialize_collection("conversation-profile-memory")
        self._load_records_from_disk()
        self._load_profiles_from_disk()

    def add_exchange(
        self,
        request: ChatRequest,
        *,
        conversation_id: str,
        answer: str,
        workflow_action: str,
        interaction_domain: str | None,
        knowledge_hit_count: int,
        booking_result: BookingResponse | None,
    ) -> ConversationMemoryRecord:
        record = ConversationMemoryRecord(
            memory_id=str(uuid4()),
            conversation_id=conversation_id,
            student_name=request.student_name,
            student_email=request.student_email,
            course_context=request.course_context,
            question=request.question,
            answer=answer,
            workflow_action=workflow_action,
            interaction_domain=interaction_domain,
            knowledge_hit_count=knowledge_hit_count,
            booking_summary=self._booking_summary(booking_result),
            created_at=datetime.now(UTC),
        )
        (self._records_dir / f"{record.memory_id}.json").write_text(
            json.dumps(record.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._records[record.memory_id] = record
        self._conversation_collection.insert(
            record.retrieval_text(),
            {
                "memory_id": record.memory_id,
                "conversation_id": record.conversation_id,
                "student_name": record.student_name,
                "student_email": record.student_email or "",
            },
            index_names=["search"],
        )
        return record

    def consolidate_profiles(self, record: ConversationMemoryRecord) -> int:
        profiles = self._derive_profiles(record)
        for profile in profiles:
            self._upsert_profile(profile)
        return len(profiles)

    def search(
        self,
        request: ChatRequest,
        *,
        conversation_id: str,
        top_k: int | None = None,
    ) -> list[ConversationMemoryHit]:
        if not self._records:
            return []

        plan = self._select_search_plan(request, top_k)
        short_term_hits = self._search_short_term(
            request,
            conversation_id=conversation_id,
            limit=plan.short_term_limit,
        )
        long_term_hits = self._search_long_term(request, limit=plan.long_term_limit)
        return short_term_hits + long_term_hits

    def count_records(self) -> int:
        return len(self._records)

    def get_record(self, memory_id: str) -> ConversationMemoryRecord | None:
        return self._records.get(memory_id)

    def list_records(self, *, since: datetime | None = None) -> list[ConversationMemoryRecord]:
        records = sorted(self._records.values(), key=lambda record: record.created_at, reverse=True)
        if since is not None:
            records = [record for record in records if record.created_at >= since]
        return records

    def count_profiles(self) -> int:
        return len(self._profiles)

    def available_profile_categories(self) -> list[str]:
        return self._profile_summarizer.available_categories()

    def list_profiles(
        self,
        *,
        category: str | None = None,
        student_query: str | None = None,
        limit: int = 50,
    ) -> list[ProfileMemoryRecord]:
        normalized_category = category.strip() if category else None
        normalized_query = student_query.strip().lower() if student_query else None
        profiles = sorted(self._profiles.values(), key=lambda profile: profile.updated_at, reverse=True)
        if normalized_category:
            profiles = [profile for profile in profiles if profile.category == normalized_category]
        if normalized_query:
            profiles = [
                profile
                for profile in profiles
                if normalized_query in profile.student_name.lower()
                or normalized_query in profile.student_key.lower()
                or (profile.student_email and normalized_query in profile.student_email.lower())
            ]
        return profiles[: max(1, limit)]

    def list_profiles_for_student(
        self,
        *,
        student_name: str,
        student_email: str | None,
        limit: int = 20,
    ) -> list[ProfileMemoryRecord]:
        student_key = self._student_key(student_name, student_email)
        if student_key is None:
            return []
        profiles = [profile for profile in self._profiles.values() if profile.student_key == student_key]
        profiles.sort(key=lambda profile: profile.updated_at, reverse=True)
        return profiles[: max(1, limit)]

    def backend_name(self) -> str:
        return "neuromem-layered"

    def _select_search_plan(self, request: ChatRequest, top_k: int | None) -> MemorySearchPlan:
        limit = top_k or self._settings.conversation_memory_top_k
        question = request.question.lower()
        if any(keyword in question for keyword in ("预约", "meeting", "schedule", "book", "时间")):
            return MemorySearchPlan(
                policy_name="booking-first",
                short_term_limit=max(2, limit),
                long_term_limit=1,
            )
        if any(keyword in question for keyword in ("之前", "上次", "记得", "偏好", "邮箱", "名字")):
            return MemorySearchPlan(
                policy_name="profile-aware",
                short_term_limit=max(2, limit // 2 + 1),
                long_term_limit=max(1, limit // 2),
            )
        return MemorySearchPlan(
            policy_name="balanced",
            short_term_limit=max(2, limit - 1),
            long_term_limit=1,
        )

    def _search_short_term(
        self,
        request: ChatRequest,
        *,
        conversation_id: str,
        limit: int,
    ) -> list[ConversationMemoryHit]:
        query_parts = [request.question]
        if request.course_context:
            query_parts.append(request.course_context)
        if request.student_email:
            query_parts.append(request.student_email)
        elif request.student_name.strip().lower() != "guest":
            query_parts.append(request.student_name)

        results = self._conversation_collection.retrieve(
            "search",
            " ".join(query_parts),
            top_k=max(limit * 3, limit),
        )
        hits: list[ConversationMemoryHit] = []
        seen_memory_ids: set[str] = set()

        recent_same_conversation = sorted(
            (
                record
                for record in self._records.values()
                if record.conversation_id == conversation_id and record.question != request.question
            ),
            key=lambda record: record.created_at,
            reverse=True,
        )[:limit]
        for rank, record in enumerate(recent_same_conversation, start=1):
            seen_memory_ids.add(record.memory_id)
            hits.append(
                ConversationMemoryHit(
                    memory_id=record.memory_id,
                    conversation_id=record.conversation_id,
                    summary=self._format_summary(record),
                    score=1.0 + (1.0 / float(rank)),
                    created_at=record.created_at,
                    memory_type="short_term",
                )
            )

        for rank, result in enumerate(results, start=1):
            metadata = dict(result.get("metadata") or {})
            memory_id = str(metadata.get("memory_id") or "")
            if not memory_id or memory_id in seen_memory_ids:
                continue
            record = self._records.get(memory_id)
            if record is None or not self._should_include_record(record, request, conversation_id):
                continue
            seen_memory_ids.add(memory_id)
            hits.append(
                ConversationMemoryHit(
                    memory_id=record.memory_id,
                    conversation_id=record.conversation_id,
                    summary=self._format_summary(record),
                    score=1.0 / float(rank),
                    created_at=record.created_at,
                    memory_type="short_term",
                )
            )
            if len(hits) >= limit:
                break
        return hits

    def _search_long_term(self, request: ChatRequest, *, limit: int) -> list[ConversationMemoryHit]:
        student_key = self._student_key(request.student_name, request.student_email)
        if limit <= 0 or student_key is None or not self._profiles:
            return []

        query_parts = [request.question, request.student_name]
        if request.course_context:
            query_parts.append(request.course_context)
        if request.student_email:
            query_parts.append(request.student_email)

        results = self._profile_collection.retrieve(
            "search",
            " ".join(query_parts),
            top_k=max(limit * 3, limit),
        )
        hits: list[ConversationMemoryHit] = []
        seen_profile_ids: set[str] = set()

        preferred_categories = self._preferred_profile_categories(request.question)
        if preferred_categories:
            prioritized_profiles = sorted(
                (
                    profile
                    for profile in self._profiles.values()
                    if profile.student_key == student_key and profile.category in preferred_categories
                ),
                key=lambda profile: profile.updated_at,
                reverse=True,
            )
            for profile in prioritized_profiles:
                seen_profile_ids.add(profile.profile_id)
                hits.append(
                    ConversationMemoryHit(
                        memory_id=profile.profile_id,
                        conversation_id="profile",
                        summary=self._format_profile_summary(profile),
                        score=1.5,
                        created_at=profile.updated_at,
                        memory_type="long_term",
                    )
                )
                if len(hits) >= limit:
                    return hits

        for rank, result in enumerate(results, start=1):
            metadata = dict(result.get("metadata") or {})
            profile_id = str(metadata.get("profile_id") or "")
            if not profile_id or profile_id in seen_profile_ids:
                continue
            profile = self._profiles.get(profile_id)
            if profile is None or profile.student_key != student_key:
                continue
            seen_profile_ids.add(profile_id)
            hits.append(
                ConversationMemoryHit(
                    memory_id=profile.profile_id,
                    conversation_id="profile",
                    summary=self._format_profile_summary(profile),
                    score=1.0 / float(rank),
                    created_at=profile.updated_at,
                    memory_type="long_term",
                )
            )
            if len(hits) >= limit:
                break
        return hits

    def _preferred_profile_categories(self, question: str) -> list[str]:
        lowered = question.lower()
        categories: list[str] = []
        if ("预约" in question or "booking" in lowered or "meeting" in lowered) and (
            "习惯" in question or "偏好" in question or "preference" in lowered
        ):
            categories.append("booking_preference")
        if (
            "沟通偏好" in question
            or "协作偏好" in question
            or ("准备" in question and ("偏好" in question or "习惯" in question))
            or ("prepare" in lowered and "preference" in lowered)
        ):
            categories.append("collaboration_preference")
        if "邮箱" in question or "名字" in question or "联系方式" in question:
            categories.append("identity")
        if "课程" in question or "研究方向" in question or "科研" in question:
            categories.append("course_context")
        return categories

    def _initialize_collection(self, name: str):
        try:
            from sage.neuromem import UnifiedCollection
        except ImportError as exc:
            raise RuntimeError("Conversation memory requires isage-neuromem to be installed.") from exc

        collection = UnifiedCollection(name)
        collection.add_index("search", "bm25", {})
        return collection

    def _load_records_from_disk(self) -> None:
        record_paths = list(self._records_dir.glob("*.json"))
        if not record_paths:
            record_paths = list(self._base_dir.glob("*.json"))
        for path in sorted(record_paths):
            payload = json.loads(path.read_text(encoding="utf-8"))
            record = ConversationMemoryRecord.from_dict(payload)
            self._records[record.memory_id] = record
            self._conversation_collection.insert(
                record.retrieval_text(),
                {
                    "memory_id": record.memory_id,
                    "conversation_id": record.conversation_id,
                    "student_name": record.student_name,
                    "student_email": record.student_email or "",
                },
                index_names=["search"],
            )

    def _load_profiles_from_disk(self) -> None:
        for path in sorted(self._profiles_dir.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            profile = ProfileMemoryRecord.from_dict(payload)
            self._profiles[profile.profile_id] = profile
            self._profile_collection.insert(
                profile.retrieval_text(),
                {
                    "profile_id": profile.profile_id,
                    "student_key": profile.student_key,
                    "category": profile.category,
                },
                index_names=["search"],
            )

    def _should_include_record(
        self,
        record: ConversationMemoryRecord,
        request: ChatRequest,
        conversation_id: str,
    ) -> bool:
        if record.conversation_id == conversation_id:
            return True
        if request.student_email and record.student_email == request.student_email:
            return True
        if request.student_name.strip().lower() == "guest":
            return False
        return record.student_name == request.student_name

    def _derive_profiles(self, record: ConversationMemoryRecord) -> list[ProfileMemoryRecord]:
        student_key = self._student_key(record.student_name, record.student_email)
        if student_key is None:
            return []

        suggestions = self._profile_summarizer.summarize(record)
        return [
            ProfileMemoryRecord(
                profile_id=self._profile_id(student_key, suggestion.category),
                student_key=student_key,
                student_name=record.student_name,
                student_email=record.student_email,
                category=suggestion.category,
                summary=suggestion.summary,
                evidence=suggestion.evidence,
                updated_at=record.created_at,
            )
            for suggestion in suggestions
        ]

    def _upsert_profile(self, profile: ProfileMemoryRecord) -> None:
        (self._profiles_dir / f"{profile.profile_id}.json").write_text(
            json.dumps(profile.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._profiles[profile.profile_id] = profile
        self._profile_collection.insert(
            profile.retrieval_text(),
            {
                "profile_id": profile.profile_id,
                "student_key": profile.student_key,
                "category": profile.category,
            },
            index_names=["search"],
        )

    def _format_profile_summary(self, profile: ProfileMemoryRecord) -> str:
        timestamp = profile.updated_at.astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC")
        return f"[{timestamp}] {profile.summary}\n证据：{profile.evidence}"

    def _student_key(self, student_name: str, student_email: str | None) -> str | None:
        if student_email:
            return student_email.strip().lower()
        normalized_name = student_name.strip().lower()
        if not normalized_name or normalized_name == "guest":
            return None
        return normalized_name

    def _profile_id(self, student_key: str, category: str) -> str:
        safe_key = re.sub(r"[^a-z0-9]+", "-", student_key.lower()).strip("-") or "profile"
        return f"{safe_key}-{category}"


    def _format_summary(self, record: ConversationMemoryRecord) -> str:
        timestamp = record.created_at.astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC")
        lines = [
            f"[{timestamp}] 问：{record.question}",
            f"答：{record.answer}",
        ]
        if record.booking_summary:
            lines.append(f"预约：{record.booking_summary}")
        return "\n".join(lines)

    def _booking_summary(self, booking_result: BookingResponse | None) -> str | None:
        if booking_result is None:
            return None
        if booking_result.booking is None:
            return booking_result.message
        return (
            f"{booking_result.message} | {booking_result.booking.topic} | "
            f"{booking_result.booking.start_at.isoformat()}"
        )