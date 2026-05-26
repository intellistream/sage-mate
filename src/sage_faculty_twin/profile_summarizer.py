from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


class ConversationProfileSource(Protocol):
    conversation_id: str
    student_name: str
    student_email: str | None
    course_context: str | None
    question: str
    answer: str
    workflow_action: str
    booking_summary: str | None
    created_at: datetime


@dataclass(slots=True)
class ProfileSummarySuggestion:
    category: str
    summary: str
    evidence: str


class ProfileSummarizer(Protocol):
    def summarize(self, record: ConversationProfileSource) -> list[ProfileSummarySuggestion]: ...


class ProfileSummarizerRegistry:
    _registry: dict[str, type[ProfileSummarizer]] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[type[ProfileSummarizer]], type[ProfileSummarizer]]:
        def decorator(summarizer_cls: type[ProfileSummarizer]) -> type[ProfileSummarizer]:
            cls._registry[name] = summarizer_cls
            return summarizer_cls

        return decorator

    @classmethod
    def create_all(cls) -> tuple[ProfileSummarizer, ...]:
        return tuple(summarizer_cls() for summarizer_cls in cls._registry.values())

    @classmethod
    def categories(cls) -> list[str]:
        return list(cls._registry.keys())


@ProfileSummarizerRegistry.register("identity")
class IdentityProfileSummarizer:
    def summarize(self, record: ConversationProfileSource) -> list[ProfileSummarySuggestion]:
        return [
            ProfileSummarySuggestion(
                category="identity",
                summary=self._identity_summary(record),
                evidence=f"Latest conversation id: {record.conversation_id}",
            )
        ]

    def _identity_summary(self, record: ConversationProfileSource) -> str:
        parts = [f"该用户名称为：{record.student_name}"]
        if record.student_email:
            parts.append(f"联系邮箱：{record.student_email}")
        return "；".join(parts)



@ProfileSummarizerRegistry.register("course_context")
class CourseContextProfileSummarizer:
    def summarize(self, record: ConversationProfileSource) -> list[ProfileSummarySuggestion]:
        if not record.course_context:
            return []
        return [
            ProfileSummarySuggestion(
                category="course_context",
                summary=f"该用户最近的主要交流场景是：{record.course_context}",
                evidence=f"Question: {record.question}",
            )
        ]



@ProfileSummarizerRegistry.register("recent_topic")
class RecentTopicProfileSummarizer:
    def summarize(self, record: ConversationProfileSource) -> list[ProfileSummarySuggestion]:
        topic = self._extract_topic(record.question, record.course_context)
        if not topic:
            return []
        return [
            ProfileSummarySuggestion(
                category="recent_topic",
                summary=f"该用户近期反复关注的话题：{topic}",
                evidence=f"Question: {record.question}",
            )
        ]

    def _extract_topic(self, question: str, course_context: str | None) -> str | None:
        match = re.search(r"(?:讨论|关于|聊聊)\s*([^，。！？?]+)", question)
        if match is not None:
            topic = match.group(1).strip()
            if topic:
                return topic[:128]
        cleaned = re.sub(r"(请|帮我|预约|预定|约|时间|老师|一下|个)", " ", question)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ，。！？?")
        if cleaned:
            return cleaned[:128]
        if course_context:
            return course_context.strip()[:128]
        return None



@ProfileSummarizerRegistry.register("booking_preference")
class BookingPreferenceProfileSummarizer:
    def summarize(self, record: ConversationProfileSource) -> list[ProfileSummarySuggestion]:
        booking_profile = self._booking_preference_summary(record)
        return [booking_profile] if booking_profile is not None else []

    def _booking_preference_summary(
        self,
        record: ConversationProfileSource,
    ) -> ProfileSummarySuggestion | None:
        if record.booking_summary is None and record.workflow_action not in {
            "book_meeting",
            "collect_booking_details",
        }:
            return None

        topic = RecentTopicProfileSummarizer()._extract_topic(record.question, record.course_context)
        preferred_time = self._extract_explicit_time(record.question, record.booking_summary)

        summary_parts = ["该用户存在持续的预约沟通需求"]
        if topic:
            summary_parts.append(f"常见预约主题：{topic}")
        if preferred_time:
            summary_parts.append(f"最近一次明确给出的时间偏好：{preferred_time}")
        if record.student_email:
            summary_parts.append(f"预约联系邮箱：{record.student_email}")

        evidence_parts = [f"Workflow: {record.workflow_action}"]
        if record.booking_summary:
            evidence_parts.append(f"Booking: {record.booking_summary}")
        else:
            evidence_parts.append(f"Question: {record.question}")

        return ProfileSummarySuggestion(
            category="booking_preference",
            summary="；".join(summary_parts),
            evidence=" | ".join(evidence_parts),
        )

    def _extract_explicit_time(self, question: str, booking_summary: str | None) -> str | None:
        combined = " ".join(part for part in (question, booking_summary or "") if part)
        match = re.search(r"(\d{4}-\d{1,2}-\d{1,2}[ T]\d{1,2}:\d{2})", combined)
        if match is not None:
            return match.group(1)
        return None



@ProfileSummarizerRegistry.register("collaboration_preference")
class CollaborationPreferenceProfileSummarizer:
    def summarize(self, record: ConversationProfileSource) -> list[ProfileSummarySuggestion]:
        preference = self._extract_preparation_preference(record.question, record.answer)
        if preference is None:
            return []
        return [
            ProfileSummarySuggestion(
                category="collaboration_preference",
                summary=preference,
                evidence=f"Question: {record.question} | Answer: {record.answer}",
            )
        ]

    def _extract_preparation_preference(self, question: str, answer: str) -> str | None:
        lowered_question = question.lower()
        lowered_answer = answer.lower()
        if not any(keyword in lowered_question for keyword in ("准备", "agenda", "blocker", "draft", "meeting")):
            return None

        preparation_items: list[str] = []
        if "agenda" in lowered_answer:
            preparation_items.append("agenda")
        if "blocker" in lowered_answer:
            preparation_items.append("current blocker")
        if "draft" in lowered_answer or "草稿" in answer:
            preparation_items.append("draft")
        if "问题" in answer or "question" in lowered_answer:
            preparation_items.append("问题清单")

        if not preparation_items:
            return None

        item_text = "、".join(preparation_items)
        return f"该用户适合按清单式准备沟通材料；建议提前准备：{item_text}"


class ConversationProfileSummarizer:
    def __init__(self) -> None:
        self._summarizers = ProfileSummarizerRegistry.create_all()

    def summarize(self, record: ConversationProfileSource) -> list[ProfileSummarySuggestion]:
        suggestions: list[ProfileSummarySuggestion] = []
        for summarizer in self._summarizers:
            suggestions.extend(summarizer.summarize(record))
        return suggestions

    def available_categories(self) -> list[str]:
        return ProfileSummarizerRegistry.categories()