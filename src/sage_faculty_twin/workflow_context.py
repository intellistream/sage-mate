from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .models import ChatRequest

_ROLE_MODE_PATTERN = "^(course_instructor|paper_writing_teacher|research_pi|collaboration_contact|front_desk|system_operator)$"
_JOURNEY_STATE_PATTERN = "^(first_time_visitor|course_student|meeting_candidate|project_advisee|recurring_collaborator|lab_member|high_priority_escalation)$"
_SESSION_IDENTITY_PATTERN = "^(anonymous|user|admin)$"


class WorkflowRequestContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=4000)
    course_context: str | None = Field(default=None, max_length=512)
    visitor_profile: str | None = Field(default=None, max_length=64)
    role_mode: str = Field(default="front_desk", pattern=_ROLE_MODE_PATTERN)
    journey_state: str = Field(
        default="first_time_visitor", pattern=_JOURNEY_STATE_PATTERN
    )
    session_identity: str = Field(
        default="anonymous", pattern=_SESSION_IDENTITY_PATTERN
    )
    policy_version: str = Field(
        default="faculty-default-2026-05", min_length=1, max_length=64
    )
    recent_memory_available: bool = False
    recent_session_context_attached: bool = False
    profile_memory_available: bool = False
    consent_profile_memory: bool = False
    allow_draft_write: bool = False
    attachment_count: int = Field(default=0, ge=0, le=4)
    attachment_media_types: list[str] = Field(default_factory=list, max_length=4)
    artifact_context_available: bool = False
    available_evidence_sources: list[str] = Field(default_factory=list)

    @classmethod
    def from_chat_request(
        cls,
        request: ChatRequest,
        *,
        is_admin_request: bool = False,
        policy_version: str = "faculty-default-2026-05",
        recent_memory_available: bool | None = None,
        recent_session_context_attached: bool | None = None,
        profile_memory_available: bool | None = None,
        consent_profile_memory: bool | None = None,
        allow_draft_write: bool = False,
    ) -> WorkflowRequestContext:
        visitor_profile = request.visitor_profile
        course_context = request.course_context
        session_identity = (
            "admin"
            if is_admin_request
            else ("user" if request.student_email else "anonymous")
        )
        inferred_recent_memory = (
            recent_memory_available
            if recent_memory_available is not None
            else bool(request.conversation_id)
        )
        inferred_recent_session_context = (
            recent_session_context_attached
            if recent_session_context_attached is not None
            else False
        )
        inferred_profile_memory = (
            profile_memory_available
            if profile_memory_available is not None
            else bool(request.student_email)
        )
        inferred_consent = (
            consent_profile_memory
            if consent_profile_memory is not None
            else bool(request.student_email)
        )
        attachment_count = len(request.attachments)
        attachment_media_types = sorted(
            {attachment.media_type for attachment in request.attachments}
        )
        artifact_context_available = (
            attachment_count > 0 or _question_mentions_artifact(request.question)
        )
        role_mode = _infer_role_mode(request)
        journey_state = _infer_journey_state(request)
        evidence_sources = _infer_evidence_sources(
            request,
            recent_memory_available=inferred_recent_memory,
            recent_session_context_attached=inferred_recent_session_context,
            profile_memory_available=inferred_profile_memory,
            artifact_context_available=artifact_context_available,
        )

        return cls(
            question=request.question,
            course_context=course_context,
            visitor_profile=visitor_profile,
            role_mode=role_mode,
            journey_state=journey_state,
            session_identity=session_identity,
            policy_version=policy_version,
            recent_memory_available=inferred_recent_memory,
            recent_session_context_attached=inferred_recent_session_context,
            profile_memory_available=inferred_profile_memory,
            consent_profile_memory=inferred_consent,
            allow_draft_write=allow_draft_write,
            attachment_count=attachment_count,
            attachment_media_types=attachment_media_types,
            artifact_context_available=artifact_context_available,
            available_evidence_sources=evidence_sources,
        )


def _infer_role_mode(request: ChatRequest) -> str:
    question = request.question.lower()
    course_context = (request.course_context or "").lower()
    visitor_profile = request.visitor_profile or ""
    if any(
        marker in question
        for marker in (
            "服务",
            "systemd",
            "deploy",
            "router",
            "health",
            "日志",
            "端口",
            "重启",
        )
    ):
        return "system_operator"
    if any(
        marker in question
        for marker in (
            "合作",
            "collaboration",
            "joint work",
            "联合投稿",
            "coauthor",
            "co-author",
        )
    ):
        return "collaboration_contact"
    if (
        visitor_profile == "paper_writing_student"
        or "论文" in question
        or "paper" in question
    ):
        return "paper_writing_teacher"
    if visitor_profile == "lab_member" or any(
        marker in question for marker in ("研究", "paper", "project", "collaboration")
    ):
        return "research_pi"
    if course_context or visitor_profile == "hust_undergraduate":
        return "course_instructor"
    return "front_desk"


def _infer_journey_state(request: ChatRequest) -> str:
    question = request.question.lower()
    visitor_profile = request.visitor_profile or ""
    if any(
        marker in question
        for marker in ("紧急", "urgent", "asap", "尽快", "投诉", "升级处理", "人工处理")
    ):
        return "high_priority_escalation"
    if any(marker in question for marker in ("预约", "meeting", "office hour")):
        return "meeting_candidate"
    if visitor_profile == "lab_member" and any(
        marker in question
        for marker in (
            "proposal",
            "开题",
            "project",
            "milestone",
            "实验计划",
            "进展",
            "roadmap",
            "draft",
        )
    ):
        return "project_advisee"
    if (request.conversation_id or request.student_email) and any(
        marker in question
        for marker in (
            "之前",
            "上次",
            "继续",
            "follow up",
            "collaboration",
            "合作",
            "proposal",
            "agenda",
            "draft",
            "上传",
        )
    ):
        return "recurring_collaborator"
    if (
        visitor_profile in {"hust_undergraduate", "paper_writing_student"}
        or request.course_context
    ):
        return "course_student"
    if visitor_profile == "lab_member":
        return "lab_member"
    return "first_time_visitor"


def _infer_evidence_sources(
    request: ChatRequest,
    *,
    recent_memory_available: bool,
    recent_session_context_attached: bool,
    profile_memory_available: bool,
    artifact_context_available: bool,
) -> list[str]:
    sources = {"public_homepage", "faq"}
    question = request.question.lower()
    if request.course_context or request.visitor_profile in {
        "hust_undergraduate",
        "paper_writing_student",
    }:
        sources.add("course_material")
    if any(marker in question for marker in ("预约", "meeting", "office hour", "时段")):
        sources.add("booking_policy")
    if recent_session_context_attached:
        sources.add("recent_session_context")
    if recent_memory_available:
        sources.add("recent_memory")
    if profile_memory_available:
        sources.add("profile_memory")
    if request.attachments:
        sources.add("attachment_excerpt")
    if artifact_context_available and (
        request.attachments or recent_memory_available or profile_memory_available
    ):
        sources.add("artifact_memory")
    return sorted(sources)


def _question_mentions_artifact(question: str) -> bool:
    normalized = question.lower()
    return any(
        marker in normalized
        for marker in (
            "附件",
            "上传",
            "upload",
            "agenda",
            "proposal",
            "draft",
            "pdf",
            "材料",
            "文档",
            "报告",
            "notes",
            "slide",
            "outline",
        )
    )
