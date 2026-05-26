from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta

from .models import AvailabilitySchedule, BookingRecord, FollowUpAction, InteractionIntent, KnowledgeSearchHit
from .memory_store import ProfileMemoryRecord


@dataclass(slots=True)
class EmailFollowUpDraft:
    action_type: str
    title: str
    detail: str
    subject: str
    lines: list[str]
    due_at: datetime | None


class LightweightActionPlanner:
    def plan_chat_actions(
        self,
        *,
        workflow_action: str,
        question: str,
        interaction_intent: InteractionIntent | None,
        knowledge_hits: list[KnowledgeSearchHit],
        student_profiles: list[ProfileMemoryRecord],
        availability_schedule: AvailabilitySchedule,
    ) -> list[FollowUpAction]:
        actions: list[FollowUpAction] = []
        lowered_question = question.lower()
        profile_by_category = {profile.category: profile for profile in student_profiles}

        for hit in knowledge_hits[:2]:
            actions.append(
                FollowUpAction(
                    action_type="recommended_reading",
                    title=f"先看：{self._summarize_material_title(hit.title)}",
                    detail=self._build_recommended_reading_detail(hit),
                    channel="chat",
                    status="suggested",
                    source_label=self._format_source_label(hit.source_name),
                )
            )

        should_review_todo = workflow_action in {"advise_only", "book_meeting", "collect_booking_details"} or any(
            marker in lowered_question for marker in ("准备", "todo", "checklist", "agenda", "blocker", "meeting")
        )
        if should_review_todo:
            checklist = self._build_todo_review(profile_by_category)
            actions.append(
                FollowUpAction(
                    action_type="todo_review",
                    title="待办事项回顾",
                    detail=checklist,
                    channel="chat",
                    status="suggested",
                    source_label="学生画像与当前问题",
                )
            )

        if availability_schedule.days and (
            (interaction_intent is not None and interaction_intent.domain in {"advising", "booking"})
            or "booking_preference" in profile_by_category
        ):
            slot_preview = self._format_availability_preview(availability_schedule)
            if slot_preview:
                actions.append(
                    FollowUpAction(
                        action_type="office_hour_recommendation",
                        title="建议安排 office hour / 会议时段",
                        detail=f"如果需要进一步沟通，可优先考虑这些可预约时段：{slot_preview}",
                        channel="chat",
                        status="suggested",
                        source_label="当前可预约时段",
                    )
                )
        elif interaction_intent is not None and interaction_intent.domain in {"advising", "booking"}:
            actions.append(
                FollowUpAction(
                    action_type="office_hour_recommendation",
                    title="建议安排 office hour / 会议时段",
                    detail="如果你需要进一步沟通，建议尽早查看当前 office hour 或本周开放预约时段并提交预约申请。",
                    channel="chat",
                    status="suggested",
                    source_label="默认预约规则",
                )
            )

        teaching_hit = next((hit for hit in knowledge_hits if self._looks_like_teaching_hit(hit)), None)
        if teaching_hit is not None:
            actions.append(
                FollowUpAction(
                    action_type="course_resource_recommendation",
                    title=f"继续看：{self._summarize_material_title(teaching_hit.title)}",
                    detail=(
                        "如果你想继续自学，建议先把这条课程材料看完，再带着不明白的点继续提问。"
                    ),
                    channel="chat",
                    status="suggested",
                    source_label=self._format_source_label(teaching_hit.source_name),
                )
            )

        return self._dedupe_actions(actions)[:4]

    def _build_todo_review(self, profile_by_category: dict[str, ProfileMemoryRecord]) -> str:
        collaboration = profile_by_category.get("collaboration_preference")
        booking = profile_by_category.get("booking_preference")

        checklist_parts = ["建议回顾：agenda、当前 blocker、已有 draft / 结果、最想确认的 2-3 个问题"]
        if collaboration is not None:
            checklist_parts.append(f"画像提示：{collaboration.summary}")
        if booking is not None:
            checklist_parts.append(f"预约偏好：{booking.summary}")
        return "；".join(checklist_parts)[:512]

    def _format_availability_preview(self, schedule: AvailabilitySchedule) -> str:
        previews: list[str] = []
        for day in schedule.days[:2]:
            if not day.windows:
                continue
            windows = "、".join(f"{window.start}-{window.end}" for window in day.windows[:2])
            previews.append(f"{day.date.isoformat()} {windows}")
        return "；".join(previews)

    def _looks_like_teaching_hit(self, hit: KnowledgeSearchHit) -> bool:
        tags = {tag.lower() for tag in hit.tags}
        return bool(tags & {"teaching", "courseware", "tutorial", "lecture", "experiment", "resources", "pdf"})

    def _build_recommended_reading_detail(self, hit: KnowledgeSearchHit) -> str:
        if self._looks_like_gap_draft(hit):
            suggested_action = self._extract_gap_draft_suggested_action(hit.excerpt)
            if suggested_action:
                return f"这是一份和你当前问题直接相关的 FAQ 草稿，建议先看：{suggested_action}"[:512]
            return "这是一份和你当前问题直接相关的 FAQ 草稿，建议先快速看会前准备模板和常见问题说明。"

        if self._looks_like_published_gap(hit):
            excerpt = self._normalize_excerpt(hit.excerpt)
            if excerpt:
                return f"这条常见问题整理和你当前的问题最接近，建议先看：{excerpt}"[:512]
            return "这条常见问题整理和你当前的问题最接近，建议先快速看一遍。"

        excerpt = self._normalize_excerpt(hit.excerpt)
        if excerpt:
            return f"这条材料和你当前的问题最相关，建议先看这一部分：{excerpt}"[:512]
        return "这条材料和你当前的问题最相关，建议先快速读一遍，再继续问更具体的问题。"

    def _looks_like_gap_draft(self, hit: KnowledgeSearchHit) -> bool:
        source_name = str(hit.source_name or "")
        excerpt = str(hit.excerpt or "")
        return source_name.startswith("analytics-gap:") or "建议 FAQ/知识正文草稿" in excerpt

    def _looks_like_published_gap(self, hit: KnowledgeSearchHit) -> bool:
        source_name = str(hit.source_name or "")
        tags = {tag.lower() for tag in hit.tags}
        return source_name.startswith("knowledge-gap:") or "knowledge-gap" in tags

    def _extract_gap_draft_suggested_action(self, excerpt: str | None) -> str:
        normalized = self._normalize_excerpt(excerpt)
        if not normalized:
            return ""
        matched = re.search(r"建议动作[:：]\s*([^。；]+)", normalized)
        if matched:
            return matched.group(1).strip()[:180]
        return ""

    def _summarize_material_title(self, title: str) -> str:
        normalized = re.sub(r"\s+", " ", str(title or "")).strip(" ：:|｜")
        if not normalized:
            return "相关材料"

        normalized = re.sub(r"^(推荐阅读|课程资源推荐|先看|继续看)[：:]\s*", "", normalized)
        normalized = re.sub(r"^常见问题[:：]\s*", "", normalized)
        parts = [part.strip() for part in re.split(r"[|｜]", normalized) if part.strip()]
        meaningful_parts = [part for part in parts if not self._looks_like_fragment_segment(part)]
        if meaningful_parts:
            return " · ".join(meaningful_parts[:2])[:80]
        return normalized[:80]

    def _format_source_label(self, source_name: str | None) -> str:
        normalized = str(source_name or "")
        if normalized.startswith("knowledge-gap:"):
            return "常见问题整理"
        return normalized

    def _looks_like_fragment_segment(self, value: str) -> bool:
        chunks = [chunk.strip() for chunk in value.split("/") if chunk.strip()]
        if len(chunks) < 2:
            return False
        return all(len(chunk) <= 3 for chunk in chunks)

    def _normalize_excerpt(self, excerpt: str | None) -> str:
        normalized = re.sub(r"\s+", " ", str(excerpt or "")).strip()
        if not normalized:
            return ""
        return normalized[:180]

    def _dedupe_actions(self, actions: list[FollowUpAction]) -> list[FollowUpAction]:
        deduped: list[FollowUpAction] = []
        seen_keys: set[tuple[str, str]] = set()
        for action in actions:
            key = (action.action_type, action.title)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            deduped.append(action)
        return deduped

    def build_booking_follow_up_email_drafts(
        self,
        *,
        booking: BookingRecord,
        student_profiles: list[ProfileMemoryRecord],
        related_hits: list[KnowledgeSearchHit],
    ) -> list[EmailFollowUpDraft]:
        profile_by_category = {profile.category: profile for profile in student_profiles}
        reading_titles = [hit.title for hit in related_hits[:2]]
        base_checklist = self._build_todo_review(profile_by_category)

        post_meeting_lines = [
            f"你好，{booking.student_name}：",
            "这是一次自动生成的会后跟进摘要，请你据此整理本次沟通的后续动作。",
            f"会议主题：{booking.topic}",
            f"会议时间：{booking.start_at.strftime('%Y-%m-%d %H:%M')} - {booking.end_at.strftime('%H:%M')}",
            f"建议回顾：{base_checklist}",
        ]
        if reading_titles:
            post_meeting_lines.append(f"建议继续阅读：{'；'.join(reading_titles)}")
        post_meeting_lines.append("如果本次会议形成了新的结论、 blocker 或 next step，建议直接回复这封邮件补充。")

        todo_review_lines = [
            f"你好，{booking.student_name}：",
            "这是系统生成的会后待办回顾，请检查哪些事项已经完成、哪些仍需推进。",
            f"会议主题：{booking.topic}",
            f"待办清单：{base_checklist}",
            "建议把已完成项、未完成项和需要老师继续反馈的问题分别列出来，便于下一次沟通快速进入主题。",
        ]

        return [
            EmailFollowUpDraft(
                action_type="post_meeting_summary",
                title="会后总结自动邮件",
                detail="在会议结束后自动发送一封会后跟进摘要邮件。",
                subject=f"[Faculty Twin] 会后跟进摘要：{booking.topic}",
                lines=post_meeting_lines,
                due_at=booking.end_at + timedelta(minutes=30),
            ),
            EmailFollowUpDraft(
                action_type="todo_review",
                title="待办事项回顾",
                detail="在会议结束后发送待办回顾邮件，推动学生整理 next step。",
                subject=f"[Faculty Twin] 待办回顾：{booking.topic}",
                lines=todo_review_lines,
                due_at=booking.end_at + timedelta(days=1),
            ),
        ]