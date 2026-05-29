from __future__ import annotations

import asyncio
import hashlib
import re
import threading
from time import perf_counter
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from collections.abc import Callable, Iterable
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status
from sage.foundation import MapFunction, SinkFunction
from sage.runtime import FlowNetEnvironment

from .analytics_store import ConversationAnalyticsStore
from .auth import build_admin_session_token, build_user_session_token, decode_admin_session_token, decode_user_session_token, validate_admin_credentials
from .config import AppSettings
from .escalation_store import EscalationQueueStore
from .follow_up_store import FollowUpQueueStore
from .knowledge_gap_draft_store import KnowledgeGapDraftStore
from .knowledge_base import LocalKnowledgeStore
from .light_agent import LightweightActionPlanner
from .llm_client import VllmChatClient
from .memory_store import ConversationMemoryHit, ConversationMemoryRecord, NeuroMemConversationStore, ProfileMemoryRecord
from .meeting import MeetingService
from .models import (
    AnswerBasisItem,
    AdminLoginRequest,
    AdminSessionResponse,
    AnonymousSuggestionCreate,
    AnonymousSuggestionRecord,
    AvailabilitySchedule,
    BookingDecisionRequest,
    BookingRecord,
    BookingRequest,
    BookingResponse,
    ChatFeedbackRequest,
    ChatFeedbackResponse,
    ChatRequest,
    ChatResponse,
    EscalationDecisionRequest,
    EscalationRecord,
    FollowUpAction,
    FollowUpDispatchResponse,
    FollowUpQueueRecord,
    HandoffCategorySummary,
    InteractionIntent,
    KnowledgeGapDraftCreateRequest,
    KnowledgeGapDraftRecordResponse,
    KnowledgeGapSuggestion,
    KnowledgeDocumentRecord,
    KnowledgeDocumentCreate,
    KnowledgeSearchHit,
    KnowledgeSearchResponse,
    MemoryProfileListResponse,
    MemoryProfileRecordResponse,
    NotificationDeliveryStatus,
    OperationsOverviewResponse,
    OperationsQueueSummary,
    OperationsSatisfactionSummary,
    OperationsTaskItem,
    OperationsTaskStateRecord,
    OperationsTaskStateUpdateRequest,
    OperationsWorkbenchResponse,
    QuestionAnalyticsOverview,
    QuestionAnalyticsReportResponse,
    QuestionClusterSummary,
    ServiceControlResponse,
    StudentOperationsProfile,
    UserLoginRequest,
    UserRegisterRequest,
    UserSessionResponse,
    UnresolvedQuestionItem,
    WorkflowTraceStep,
)
from .notifications import BookingEmailNotifier, BookingNotificationError
from .operations_store import OperationsTaskStateStore
from .persona import build_system_prompt
from .service_runtime import ServiceRuntimeManager
from .suggestion_store import SuggestionBoardStore
from .user_store import UserAccountStore

_FLOWNET_TICK = "__flownet_tick__"
_CHAT_PIPELINE_STAGE_COUNT = 12


@dataclass
class BookingWorkflowState:
    student_name: str
    student_email: str | None = None
    topic: str | None = None
    preferred_start: datetime | None = None
    preferred_end: datetime | None = None


@dataclass
class ChatWorkflowContext:
    request: ChatRequest
    conversation_id: str
    owner_name: str
    used_model: str
    is_admin_request: bool = False
    admin_username: str | None = None
    route: str = "answer"
    workflow_action: str = "answer"
    decision_mode: str = "direct_answer"
    answer: str | None = None
    system_prompt: str | None = None
    user_prompt: str | None = None
    interaction_intent: InteractionIntent | None = None
    pending_fields: list[str] = field(default_factory=list)
    knowledge_hits: list[KnowledgeSearchHit] = field(default_factory=list)
    memory_hits: list[ConversationMemoryHit] = field(default_factory=list)
    booking_state: BookingWorkflowState | None = None
    booking_result: BookingResponse | None = None
    booking_notification: NotificationDeliveryStatus | None = None
    escalation_record: EscalationRecord | None = None
    added_knowledge_record: KnowledgeDocumentRecord | None = None
    follow_up_actions: list[FollowUpAction] = field(default_factory=list)
    persisted_memory_record: ConversationMemoryRecord | None = None
    workflow_trace: list[WorkflowTraceStep] = field(default_factory=list)


WorkflowTraceCallback = Callable[[WorkflowTraceStep], None]


@dataclass
class AdminSessionTokenInput:
    session_token: str | None = None


@dataclass
class AdminLoginWorkflowResult:
    session: AdminSessionResponse
    session_token: str


@dataclass
class UserSessionTokenInput:
    session_token: str | None = None


@dataclass
class UserAuthWorkflowResult:
    session: UserSessionResponse
    session_token: str


@dataclass
class KnowledgeSearchInput:
    query: str
    visitor_profile: str | None = None


class FacultyTwinWorkflowSupport:
    def __init__(
        self,
        settings: AppSettings,
        booking_workflows: dict[str, BookingWorkflowState],
        knowledge_store: LocalKnowledgeStore,
        conversation_store: NeuroMemConversationStore,
        analytics_store: ConversationAnalyticsStore,
        knowledge_gap_draft_store: KnowledgeGapDraftStore,
        escalation_store: EscalationQueueStore,
        follow_up_store: FollowUpQueueStore,
        suggestion_store: SuggestionBoardStore,
        user_store: UserAccountStore,
        meeting_service: MeetingService,
        llm_client: VllmChatClient,
        email_notifier: BookingEmailNotifier,
        admin_session_payload: dict[str, Any] | None = None,
        trace_callback: WorkflowTraceCallback | None = None,
    ) -> None:
        self._settings = settings
        self._booking_workflows = booking_workflows
        self._knowledge_store = knowledge_store
        self._conversation_store = conversation_store
        self._analytics_store = analytics_store
        self._knowledge_gap_draft_store = knowledge_gap_draft_store
        self._escalation_store = escalation_store
        self._follow_up_store = follow_up_store
        self._suggestion_store = suggestion_store
        self._user_store = user_store
        self._meeting_service = meeting_service
        self._llm_client = llm_client
        self._email_notifier = email_notifier
        self._admin_session_payload = admin_session_payload
        self._trace_callback = trace_callback
        self._action_planner = LightweightActionPlanner()

    def bootstrap_chat(self, request: ChatRequest) -> ChatWorkflowContext:
        started_at = perf_counter()
        context = ChatWorkflowContext(
            request=request,
            conversation_id=request.conversation_id or str(uuid4()),
            owner_name=self._settings.owner_name,
            used_model=self._settings.model_name,
            is_admin_request=self._admin_session_payload is not None,
            admin_username=(
                str(self._admin_session_payload.get("sub") or self._settings.admin_username)
                if self._admin_session_payload is not None
                else None
            ),
        )
        self._append_trace(
            context,
            key="bootstrap",
            title="接收用户请求",
            summary="已建立当前会话。",
            detail=f"已读取提问内容，并建立会话 {context.conversation_id[:8]}。",
            duration_ms=self._elapsed_ms(started_at),
        )
        return context

    def understand_interaction(self, context: ChatWorkflowContext) -> ChatWorkflowContext:
        started_at = perf_counter()
        intent, source = self._resolve_interaction_intent(context)
        context.interaction_intent = intent
        context.decision_mode = intent.decision_mode

        if intent.action == "ask_followup" and intent.needs_clarification:
            context.workflow_action = "ask_follow_up"
            context.answer = intent.clarification_message or "你是想了解研究方向、课程内容，还是想直接发起预约？"
            context.route = "done"
            summary = "问题存在歧义，先向用户澄清。"
            detail = (
                f"已识别为 {intent.domain} 场景，但需要进一步澄清；"
                f"当前理解来源：{source}，置信度 {intent.confidence:.2f}。"
            )
        elif intent.action in {"review_queue", "human_handoff"}:
            context.workflow_action = intent.action
            context.route = "done"
            context.escalation_record = self._escalation_store.create_request(
                context.request,
                conversation_id=context.conversation_id,
                route=intent.action,
                reason=intent.escalation_reason,
            )
            context.answer = self._build_escalation_message(context)
            summary = (
                "请求已转人工处理。"
                if intent.action == "human_handoff"
                else "请求已进入待审核队列。"
            )
            detail = (
                f"已创建工单 {context.escalation_record.escalation_id[:8]}，"
                f"来源：{source}；原因：{intent.escalation_reason or '需要老师判断'}；"
                f"置信度 {intent.confidence:.2f}。"
            )
        else:
            if context.is_admin_request and intent.action == "admin_add_knowledge":
                context.workflow_action = intent.action
            if intent.decision_mode == "advise_only":
                context.workflow_action = "advise_only"
            summary = f"已识别当前交互意图：{intent.action}/{intent.domain}。"
            if intent.decision_mode == "advise_only":
                summary = f"已识别当前交互意图：{intent.action}/{intent.domain}，仅提供建议。"
            detail = (
                f"当前理解来源：{source}；检索范围：{', '.join(intent.retrieval_scopes) or '默认'}；"
                f"排除范围：{', '.join(intent.exclude_scopes) or '无'}；"
                f"决策模式：{intent.decision_mode}；置信度 {intent.confidence:.2f}。"
            )

        self._append_trace(
            context,
            key="interaction_understand",
            title="理解用户意图",
            summary=summary,
            detail=detail,
            duration_ms=self._elapsed_ms(started_at),
        )
        return context

    def prepare_booking(self, context: ChatWorkflowContext) -> ChatWorkflowContext:
        started_at = perf_counter()
        request = context.request
        existing_state = self._booking_workflows.get(context.conversation_id)
        interaction_intent = context.interaction_intent or self._build_fallback_interaction_intent(request)
        if existing_state is None and interaction_intent.action != "book_meeting":
            self._append_trace(
                context,
                key="booking_prepare",
                title="预约意图判断",
                summary="未进入预约流程。",
                detail="当前问题不进入预约工作流，继续走知识检索与回答。",
                status="skipped",
                duration_ms=self._elapsed_ms(started_at),
            )
            return context

        state = existing_state or BookingWorkflowState(student_name=request.student_name)
        state.student_name = request.student_name
        if request.student_email:
            state.student_email = request.student_email.strip()

        extracted_email = self._extract_email(request.question)
        if extracted_email:
            state.student_email = extracted_email

        extracted_start, extracted_end = self._extract_time_window(request.question)
        if extracted_start is not None:
            state.preferred_start = extracted_start
            state.preferred_end = extracted_end or (
                extracted_start + timedelta(minutes=self._settings.meeting_duration_minutes)
            )

        extracted_topic = self._extract_topic(request.question, request.course_context)
        if extracted_topic:
            state.topic = extracted_topic
        elif state.topic is None and request.course_context:
            state.topic = request.course_context.strip()

        context.booking_state = state
        missing_fields = self._missing_booking_fields(state)
        if missing_fields:
            self._booking_workflows[context.conversation_id] = state
            context.pending_fields = missing_fields
            context.workflow_action = "collect_booking_details"
            context.answer = self._build_booking_follow_up(missing_fields, state)
            context.route = "done"
            self._append_trace(
                context,
                key="booking_prepare",
                title="预约信息收集",
                summary=f"仍缺少：{self._format_pending_fields(missing_fields)}。",
                detail=f"识别到预约请求，但仍缺少：{self._format_pending_fields(missing_fields)}。",
                duration_ms=self._elapsed_ms(started_at),
            )
            return context

        context.route = "book_meeting"
        self._append_trace(
            context,
            key="booking_prepare",
            title="预约信息收集",
            summary="预约字段已经齐备。",
            detail="预约所需信息已齐备，准备提交预约。",
            duration_ms=self._elapsed_ms(started_at),
        )
        return context

    def execute_booking(self, context: ChatWorkflowContext) -> ChatWorkflowContext:
        started_at = perf_counter()
        if context.route != "book_meeting" or context.booking_state is None:
            self._append_trace(
                context,
                key="booking_execute",
                title="预约执行",
                summary="本轮没有提交预约。",
                detail="本轮未触发预约提交。",
                status="skipped",
                duration_ms=self._elapsed_ms(started_at),
            )
            return context

        request = context.request
        state = context.booking_state
        booking_response = self._meeting_service.book(
            BookingRequest(
                student_name=state.student_name,
                student_email=state.student_email or "",
                topic=state.topic or request.course_context or "会议沟通",
                preferred_start=state.preferred_start,
                preferred_end=state.preferred_end,
            )
        )
        context.booking_result = booking_response

        if booking_response.accepted:
            self._booking_workflows.pop(context.conversation_id, None)
            context.pending_fields = []
            context.workflow_action = "book_meeting"
            context.booking_result = self._attach_booking_request_notification(booking_response)
            context.booking_notification = context.booking_result.notification
            context.answer = self._build_booking_success_message(context.booking_result)
            self._append_trace(
                context,
                key="booking_execute",
                title="预约执行",
                summary=self._build_booking_execute_summary(context.booking_result),
                detail=self._build_booking_execute_detail(context.booking_result),
                duration_ms=self._elapsed_ms(started_at),
            )
        else:
            state.preferred_start = None
            state.preferred_end = None
            self._booking_workflows[context.conversation_id] = state
            context.pending_fields = ["preferred_start"]
            context.workflow_action = "collect_booking_details"
            context.answer = self._build_booking_retry_message(booking_response)
            self._append_trace(
                context,
                key="booking_execute",
                title="预约执行",
                summary="时间冲突，等待用户重选。",
                detail="预约时间冲突，已返回可选时间并等待用户补充新时间。",
                duration_ms=self._elapsed_ms(started_at),
            )

        context.route = "done"
        return context

    def _attach_booking_request_notification(self, booking_response: BookingResponse) -> BookingResponse:
        booking = booking_response.booking
        if booking is None:
            return booking_response

        try:
            recipient = self._email_notifier.send_booking_request_notification(booking)
        except BookingNotificationError as exc:
            notification = NotificationDeliveryStatus(
                status="failed",
                summary=f"管理员提醒邮件发送失败。{exc}",
                detail="预约记录已经保存，不影响管理员后续在后台查看和处理；邮件可稍后重试。",
            )
        else:
            notification = NotificationDeliveryStatus(
                status="sent",
                recipient=recipient,
                summary=f"已向 {recipient} 发送预约申请提醒邮件。",
            )

        return BookingResponse(
            accepted=booking_response.accepted,
            message=booking_response.message,
            booking=booking,
            alternative_slots=booking_response.alternative_slots,
            notification=notification,
        )

    def _build_booking_execute_summary(self, booking_response: BookingResponse) -> str:
        notification = booking_response.notification
        if notification is not None and notification.status == "failed":
            return "预约申请已提交，但提醒邮件发送失败。"
        return "预约申请已提交，等待管理员确认。"

    def _build_booking_execute_detail(self, booking_response: BookingResponse) -> str:
        notification = booking_response.notification
        if notification is None:
            return "预约请求已记录。"
        if notification.status == "failed":
            detail = notification.detail or "预约记录已保存，邮件可稍后重试。"
            return f"预约请求已记录，但邮件通知失败：{notification.summary} {detail}"
        if notification.recipient:
            return f"预约请求已记录，并已向 {notification.recipient} 发送提醒邮件。"
        return notification.summary

    def retrieve_knowledge(self, context: ChatWorkflowContext) -> ChatWorkflowContext:
        started_at = perf_counter()
        if context.is_admin_request and context.workflow_action == "admin_add_knowledge":
            knowledge_request = self._build_admin_knowledge_request(context.request)
            if knowledge_request is None:
                context.answer = self._build_admin_knowledge_guidance_message()
                summary = "识别到知识入库指令，但内容还不完整。"
                detail = "管理员对话已进入知识入库模式，但还没有解析出可直接写入知识库的正文内容。"
            else:
                context.added_knowledge_record = self._knowledge_store.add_document(knowledge_request)
                context.answer = self._build_admin_knowledge_success_message(context.added_knowledge_record)
                summary = f"已写入知识库条目：{context.added_knowledge_record.title}。"
                detail = (
                    f"管理员对话已将“{context.added_knowledge_record.title}”写入知识库；"
                    f"标签：{', '.join(context.added_knowledge_record.tags) or '未设置'}；"
                    f"来源：{context.added_knowledge_record.source_name or '管理员手动录入'}。"
                )

            context.route = "done"
            self._append_trace(
                context,
                key="knowledge_write",
                title="知识入库",
                summary=summary,
                detail=detail,
                duration_ms=self._elapsed_ms(started_at),
            )
            return context

        if context.route != "answer" or context.answer is not None:
            self._append_trace(
                context,
                key="knowledge_retrieve",
                title="知识检索",
                summary="未执行知识检索。",
                detail="当前回答不需要额外知识检索。",
                status="skipped",
                duration_ms=self._elapsed_ms(started_at),
            )
            return context

        interaction_intent = context.interaction_intent or self._build_fallback_interaction_intent(context.request)
        retrieval_query = self._build_knowledge_query(context.request, interaction_intent)
        raw_hits = self._knowledge_store.search(
            retrieval_query,
            visitor_profile=context.request.visitor_profile,
        )
        context.knowledge_hits = self._filter_knowledge_hits_by_intent(raw_hits, interaction_intent)
        hit_count = len(context.knowledge_hits)
        self._append_trace(
            context,
            key="knowledge_retrieve",
            title="知识检索",
            summary=(
                f"命中 {hit_count} 条相关资料。"
                if hit_count
                else "没有命中直接相关资料。"
            ),
            detail=(
                f"检索到 {hit_count} 条相关材料，意图域为 {interaction_intent.domain}，准备构造回答上下文。"
                if hit_count
                else "未检索到直接相关材料，将基于角色设定直接回答。"
            ),
            duration_ms=self._elapsed_ms(started_at),
        )
        return context

    def retrieve_memory(self, context: ChatWorkflowContext) -> ChatWorkflowContext:
        started_at = perf_counter()
        if context.is_admin_request and context.workflow_action == "admin_add_knowledge":
            self._append_trace(
                context,
                key="memory_retrieve",
                title="对话记忆检索",
                summary="管理员知识入库不检索学生记忆。",
                detail="当前对话用于管理员知识维护，不读取学生画像或历史问答记忆。",
                status="skipped",
                duration_ms=self._elapsed_ms(started_at),
            )
            return context

        if context.route != "answer" or context.answer is not None:
            self._append_trace(
                context,
                key="memory_retrieve",
                title="对话记忆检索",
                summary="未执行对话记忆检索。",
                detail="当前回答不需要额外对话记忆检索。",
                status="skipped",
                duration_ms=self._elapsed_ms(started_at),
            )
            return context

        context.memory_hits = self._conversation_store.search(
            context.request,
            conversation_id=context.conversation_id,
        )
        hit_count = len(context.memory_hits)
        self._append_trace(
            context,
            key="memory_retrieve",
            title="对话记忆检索",
            summary=(f"命中 {hit_count} 条历史对话记忆。" if hit_count else "没有命中历史对话记忆。"),
            detail=(
                f"检索到 {hit_count} 条相关历史对话，准备补充回答上下文。"
                if hit_count
                else "未检索到可复用的历史对话，继续使用当前问题作答。"
            ),
            duration_ms=self._elapsed_ms(started_at),
        )
        return context

    def build_prompt(self, context: ChatWorkflowContext) -> ChatWorkflowContext:
        started_at = perf_counter()
        if context.route != "answer" or context.answer is not None:
            self._append_trace(
                context,
                key="prompt_build",
                title="构造回答上下文",
                summary="未构造 LLM 上下文。",
                detail="当前流程不需要构造 LLM 回答上下文。",
                status="skipped",
                duration_ms=self._elapsed_ms(started_at),
            )
            return context

        context.system_prompt = build_system_prompt(self._settings)
        context.user_prompt = self._build_student_prompt(
            context.request,
            context.knowledge_hits,
            context.memory_hits,
            context.interaction_intent,
        )
        self._append_trace(
            context,
            key="prompt_build",
            title="构造回答上下文",
            summary="已组装回答上下文。",
            detail="已合并身份设定、课程上下文和检索结果，准备生成回答。",
            duration_ms=self._elapsed_ms(started_at),
        )
        return context

    def persist_memory(self, context: ChatWorkflowContext) -> ChatWorkflowContext:
        started_at = perf_counter()
        if context.is_admin_request and context.workflow_action == "admin_add_knowledge":
            self._append_trace(
                context,
                key="memory_persist",
                title="写入对话记忆",
                summary="管理员知识入库不写入学生记忆。",
                detail="当前对话属于后台知识维护操作，不进入学生对话记忆库。",
                status="skipped",
                duration_ms=self._elapsed_ms(started_at),
            )
            return context

        if context.answer is None:
            self._append_trace(
                context,
                key="memory_persist",
                title="写入对话记忆",
                summary="未写入对话记忆。",
                detail="当前流程没有可持久化的回答内容。",
                status="skipped",
                duration_ms=self._elapsed_ms(started_at),
            )
            return context

        context.persisted_memory_record = self._conversation_store.add_exchange(
            context.request,
            conversation_id=context.conversation_id,
            answer=context.answer,
            workflow_action=context.workflow_action,
            interaction_domain=(context.interaction_intent.domain if context.interaction_intent is not None else None),
            knowledge_hit_count=len(context.knowledge_hits),
            booking_result=context.booking_result,
        )
        self._append_trace(
            context,
            key="memory_persist",
            title="写入对话记忆",
            summary="已写入本轮对话记忆。",
            detail="用户问题和当前回复已写入 NeuroMem 对话记忆库。",
            duration_ms=self._elapsed_ms(started_at),
        )
        return context

    def consolidate_profile_memory(self, context: ChatWorkflowContext) -> ChatWorkflowContext:
        started_at = perf_counter()
        if context.persisted_memory_record is None:
            self._append_trace(
                context,
                key="memory_profile_consolidate",
                title="沉淀长期画像记忆",
                summary="未沉淀长期画像记忆。",
                detail="当前流程没有新的对话记忆可供画像归纳。",
                status="skipped",
                duration_ms=self._elapsed_ms(started_at),
            )
            return context

        profile_count = self._conversation_store.consolidate_profiles(context.persisted_memory_record)
        self._append_trace(
            context,
            key="memory_profile_consolidate",
            title="沉淀长期画像记忆",
            summary=(
                f"已沉淀 {profile_count} 条长期画像记忆。"
                if profile_count
                else "本轮未形成新的长期画像记忆。"
            ),
            detail=(
                f"已根据本轮对话提炼 {profile_count} 条用户画像/偏好摘要，并写入 NeuroMem 长期层。"
                if profile_count
                else "本轮对话没有提炼出新的稳定用户画像信息。"
            ),
            duration_ms=self._elapsed_ms(started_at),
        )
        return context

    def answer_with_llm(self, context: ChatWorkflowContext) -> ChatWorkflowContext:
        started_at = perf_counter()
        if context.route != "answer" or context.answer is not None:
            self._append_trace(
                context,
                key="llm_answer",
                title="生成回答",
                summary="本轮未调用回答模型。",
                detail="当前流程已在前面阶段完成，不再调用回答模型。",
                status="skipped",
                duration_ms=self._elapsed_ms(started_at),
            )
            return context
        if context.system_prompt is None or context.user_prompt is None:
            raise RuntimeError("chat workflow reached llm stage without a prepared prompt")

        context.answer = self._llm_client.answer_question_sync(
            context.system_prompt,
            context.user_prompt,
        )
        context.workflow_action = "advise_only" if context.decision_mode == "advise_only" else "answer"
        self._append_trace(
            context,
            key="llm_answer",
            title="生成回答",
            summary=("已生成建议型回复。" if context.decision_mode == "advise_only" else "已生成最终回复。"),
            detail=(
                "已根据角色设定和上下文生成建议，但不替用户或老师做最终决定。"
                if context.decision_mode == "advise_only"
                else "已根据角色设定和上下文生成最终回复。"
            ),
            duration_ms=self._elapsed_ms(started_at),
        )
        return context

    def plan_follow_up_actions(self, context: ChatWorkflowContext) -> ChatWorkflowContext:
        started_at = perf_counter()
        if context.is_admin_request and context.workflow_action == "admin_add_knowledge":
            self._append_trace(
                context,
                key="follow_up_plan",
                title="规划后续动作",
                summary="管理员知识入库不生成后续动作。",
                detail="当前对话已经完成知识写入，不再生成学生侧后续建议。",
                status="skipped",
                duration_ms=self._elapsed_ms(started_at),
            )
            return context

        if context.answer is None:
            self._append_trace(
                context,
                key="follow_up_plan",
                title="规划后续动作",
                summary="未生成后续动作。",
                detail="当前流程没有可规划的后续动作。",
                status="skipped",
                duration_ms=self._elapsed_ms(started_at),
            )
            return context

        profiles = self._conversation_store.list_profiles_for_student(
            student_name=context.request.student_name,
            student_email=context.request.student_email,
            limit=10,
        )
        context.follow_up_actions = self._action_planner.plan_chat_actions(
            workflow_action=context.workflow_action,
            question=context.request.question,
            interaction_intent=context.interaction_intent,
            knowledge_hits=context.knowledge_hits,
            student_profiles=profiles,
            availability_schedule=self._meeting_service.get_availability_schedule(),
        )
        action_count = len(context.follow_up_actions)
        self._append_trace(
            context,
            key="follow_up_plan",
            title="规划后续动作",
            summary=(f"已生成 {action_count} 条后续动作建议。" if action_count else "未生成额外后续动作。"),
            detail=(
                "已基于知识命中、学生画像和当前问题生成后续阅读/待办/资源建议。"
                if action_count
                else "当前问题没有额外的阅读、待办或资源推荐。"
            ),
            duration_ms=self._elapsed_ms(started_at),
        )
        return context

    def render_chat_response(self, context: ChatWorkflowContext) -> ChatResponse:
        if context.answer is None:
            raise RuntimeError("chat workflow completed without producing an answer")

        started_at = perf_counter()

        self._append_trace(
            context,
            key="response_render",
            title="返回结果",
            summary="已返回工作流结果。",
            detail="已整理回答、动作结果和工作流轨迹，返回给前端。",
            duration_ms=self._elapsed_ms(started_at),
        )

        return ChatResponse(
            answer=context.answer,
            owner_name=context.owner_name,
            used_model=context.used_model,
            exchange_id=(context.persisted_memory_record.memory_id if context.persisted_memory_record is not None else None),
            knowledge_hits=context.knowledge_hits,
            answer_basis=self._build_answer_basis(context),
            follow_up_actions=context.follow_up_actions,
            conversation_id=context.conversation_id,
            workflow_action=context.workflow_action,
            decision_mode=context.decision_mode,
            pending_fields=context.pending_fields,
            booking_result=context.booking_result,
            escalation_record=context.escalation_record,
            workflow_trace=context.workflow_trace,
        )

    def add_knowledge(self, request: KnowledgeDocumentCreate | dict[str, Any]) -> KnowledgeDocumentRecord:
        normalized = request if isinstance(request, KnowledgeDocumentCreate) else KnowledgeDocumentCreate.model_validate(request)
        return self._knowledge_store.add_document(normalized)

    def list_knowledge(self) -> list[KnowledgeDocumentRecord]:
        return self._knowledge_store.list_documents()

    def search_knowledge(self, query: str, visitor_profile: str | None = None) -> KnowledgeSearchResponse:
        return KnowledgeSearchResponse(hits=self._knowledge_store.search(query, visitor_profile=visitor_profile))

    def book_meeting(self, request: BookingRequest) -> BookingResponse:
        response = self._meeting_service.book(request)
        if not response.accepted:
            return response
        return self._attach_booking_request_notification(response)

    def list_bookings(self, status: str | None = None) -> list[BookingRecord]:
        return self._meeting_service.list_bookings(status=status)

    def list_memory_profiles(
        self,
        *,
        category: str | None = None,
        student_query: str | None = None,
        limit: int = 50,
    ) -> MemoryProfileListResponse:
        all_profiles = self._conversation_store.list_profiles(limit=1000)
        category_counts: dict[str, int] = {}
        for profile in all_profiles:
            category_counts[profile.category] = category_counts.get(profile.category, 0) + 1

        profiles = self._conversation_store.list_profiles(
            category=category,
            student_query=student_query,
            limit=limit,
        )
        return MemoryProfileListResponse(
            available_categories=self._conversation_store.available_profile_categories(),
            category_counts=category_counts,
            profiles=[
                MemoryProfileRecordResponse(
                    profile_id=profile.profile_id,
                    student_key=profile.student_key,
                    student_name=profile.student_name,
                    student_email=profile.student_email,
                    category=profile.category,
                    summary=profile.summary,
                    evidence=profile.evidence,
                    updated_at=profile.updated_at,
                )
                for profile in profiles
            ],
        )

    def submit_chat_feedback(self, request: ChatFeedbackRequest) -> ChatFeedbackResponse:
        try:
            feedback = self._analytics_store.submit_feedback(
                exchange_id=request.exchange_id,
                rating=request.rating,
                resolved=request.resolved,
                needs_human_followup=request.needs_human_followup,
                issue_summary=request.issue_summary,
            )
        except KeyError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="找不到对应的问答记录。",
            ) from exc
        return ChatFeedbackResponse(
            exchange_id=feedback.exchange_id,
            rating=feedback.rating,
            resolved=feedback.resolved,
            needs_human_followup=feedback.needs_human_followup,
            issue_summary=feedback.issue_summary,
            created_at=feedback.created_at,
            updated_at=feedback.updated_at,
        )

    def submit_anonymous_suggestion(self, request: AnonymousSuggestionCreate) -> AnonymousSuggestionRecord:
        return self._suggestion_store.create_suggestion(request)

    def list_anonymous_suggestions(self, *, limit: int = 50) -> list[AnonymousSuggestionRecord]:
        return self._suggestion_store.list_suggestions(limit=limit)

    def get_question_analytics_report(self, *, days: int = 7) -> QuestionAnalyticsReportResponse:
        report = self._analytics_store.build_weekly_report(days=days)
        enriched_gap_suggestions = []
        for item in report["knowledge_gap_suggestions"]:
            draft = self._knowledge_gap_draft_store.get_by_cluster_id(str(item["cluster_id"]))
            enriched_item = dict(item)
            if draft is not None:
                enriched_item["draft_id"] = draft.draft_id
                enriched_item["draft_status"] = draft.status
            enriched_gap_suggestions.append(enriched_item)
        return QuestionAnalyticsReportResponse(
            window_days=report["window_days"],
            window_start=report["window_start"],
            window_end=report["window_end"],
            overview=QuestionAnalyticsOverview(**report["overview"]),
            top_clusters=[QuestionClusterSummary(**item) for item in report["top_clusters"]],
            knowledge_gap_suggestions=[KnowledgeGapSuggestion(**item) for item in enriched_gap_suggestions],
            unresolved_questions=[UnresolvedQuestionItem(**item) for item in report["unresolved_questions"]],
            handoff_categories=[HandoffCategorySummary(**item) for item in report["handoff_categories"]],
        )

    def create_knowledge_gap_draft(
        self,
        request: KnowledgeGapDraftCreateRequest,
    ) -> KnowledgeGapDraftRecordResponse:
        try:
            payload = self._analytics_store.build_gap_draft_payload(cluster_id=request.cluster_id, days=request.days)
        except KeyError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="找不到对应的知识缺口建议。",
            ) from exc
        return self._knowledge_gap_draft_store.upsert_generated_draft(**payload)

    def list_knowledge_gap_drafts(self) -> list[KnowledgeGapDraftRecordResponse]:
        return self._knowledge_gap_draft_store.list_drafts()

    def publish_knowledge_gap_draft(self, draft_id: str) -> KnowledgeGapDraftRecordResponse:
        draft = self._knowledge_gap_draft_store.get_draft(draft_id)
        if draft is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="找不到对应的知识草稿。",
            )
        payload = _build_published_gap_document(draft.to_response())
        if draft.status == "published" and draft.published_document_id:
            current = next(
                (
                    document
                    for document in self._knowledge_store.list_documents()
                    if document.document_id == draft.published_document_id
                ),
                None,
            )
            if current is not None and _document_matches_payload(current, payload):
                return draft.to_response()
        published_document, _ = self._knowledge_store.upsert_document(payload)
        if draft.status == "published" and draft.published_document_id == published_document.document_id:
            return draft.to_response()
        return self._knowledge_gap_draft_store.mark_published(draft_id, document_id=published_document.document_id)

    def list_escalations(
        self,
        *,
        status: str | None = None,
        route: str | None = None,
    ) -> list[EscalationRecord]:
        return self._escalation_store.list_requests(status=status, route=route)

    def resolve_escalation(
        self,
        escalation_id: str,
        decision: EscalationDecisionRequest | dict[str, Any] | None = None,
    ) -> EscalationRecord:
        normalized = (
            EscalationDecisionRequest.model_validate(decision)
            if decision is not None
            else EscalationDecisionRequest()
        )
        try:
            return self._escalation_store.resolve_request(
                escalation_id,
                resolution_note=normalized.resolution_note,
            )
        except KeyError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="找不到对应的人工处理请求。",
            ) from exc

    def list_follow_up_actions(
        self,
        *,
        status: str | None = None,
        action_type: str | None = None,
    ) -> list[FollowUpQueueRecord]:
        return self._follow_up_store.list_actions(status=status, action_type=action_type)

    def dispatch_due_follow_ups(self) -> FollowUpDispatchResponse:
        due_entries = self._follow_up_store.list_due_actions()
        sent_count = 0
        for entry in due_entries:
            self._email_notifier.send_follow_up_email(entry.student_email, entry.subject, entry.lines)
            self._follow_up_store.mark_sent(entry.action_id)
            sent_count += 1

        pending_count = len(self._follow_up_store.list_actions(status="queued"))
        return FollowUpDispatchResponse(
            processed_count=len(due_entries),
            sent_count=sent_count,
            pending_count=pending_count,
        )

    def confirm_booking(self, booking_id: str) -> BookingResponse:
        response = self._meeting_service.confirm_booking(booking_id)
        notified_response = self._attach_student_notification(
            response,
            success_message_prefix="已向 {recipient} 发送预约确认邮件。",
            notify=self._email_notifier.send_booking_approved_notification,
        )
        booking = notified_response.booking
        if notified_response.accepted and booking is not None and booking.status == "已确认":
            profiles = self._conversation_store.list_profiles_for_student(
                student_name=booking.student_name,
                student_email=booking.student_email,
                limit=10,
            )
            related_hits = self._knowledge_store.search(booking.topic, top_k=2)
            drafts = self._action_planner.build_booking_follow_up_email_drafts(
                booking=booking,
                student_profiles=profiles,
                related_hits=related_hits,
            )
            for draft in drafts:
                self._follow_up_store.queue_action(
                    booking_id=booking.booking_id,
                    student_name=booking.student_name,
                    student_email=booking.student_email,
                    action_type=draft.action_type,
                    title=draft.title,
                    detail=draft.detail,
                    subject=draft.subject,
                    lines=draft.lines,
                    due_at=draft.due_at,
                )
        return notified_response

    def reject_booking(self, booking_id: str, rejection_reason: str | None = None) -> BookingResponse:
        response = self._meeting_service.reject_booking(booking_id, rejection_reason=rejection_reason)
        return self._attach_student_notification(
            response,
            success_message_prefix="已向 {recipient} 发送预约拒绝通知邮件。",
            notify=self._email_notifier.send_booking_rejected_notification,
        )

    def read_admin_session(self, request: AdminSessionTokenInput) -> AdminSessionResponse:
        payload = decode_admin_session_token(request.session_token, self._settings)
        return self._build_admin_session_response(payload)

    def require_admin_session(self, request: AdminSessionTokenInput) -> dict[str, Any]:
        payload = decode_admin_session_token(request.session_token, self._settings)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要管理员身份验证。",
            )
        return payload

    def login_admin(self, request: AdminLoginRequest) -> AdminLoginWorkflowResult:
        validate_admin_credentials(request.username, request.password, self._settings)
        token = build_admin_session_token(self._settings)
        return AdminLoginWorkflowResult(
            session=AdminSessionResponse(
                is_admin=True,
                mode="admin",
                username=self._settings.admin_username,
            ),
            session_token=token,
        )

    def logout_admin(self, _: object) -> AdminSessionResponse:
        return AdminSessionResponse(is_admin=False, mode="user")

    def read_user_session(self, request: UserSessionTokenInput) -> UserSessionResponse:
        payload = decode_user_session_token(request.session_token, self._settings)
        return self._build_user_session_response(payload)

    def register_user(self, request: UserRegisterRequest) -> UserAuthWorkflowResult:
        account = self._user_store.register_user(
            name=request.name,
            email=request.email,
            visitor_profile=request.visitor_profile,
            password=request.password,
        )
        token = build_user_session_token(user_id=account.user_id, email=account.email, settings=self._settings)
        return UserAuthWorkflowResult(
            session=UserSessionResponse(is_authenticated=True, mode="user", account=account),
            session_token=token,
        )

    def login_user(self, request: UserLoginRequest) -> UserAuthWorkflowResult:
        account = self._user_store.authenticate_user(email=request.email, password=request.password)
        token = build_user_session_token(user_id=account.user_id, email=account.email, settings=self._settings)
        return UserAuthWorkflowResult(
            session=UserSessionResponse(is_authenticated=True, mode="user", account=account),
            session_token=token,
        )

    def logout_user(self, _: object) -> UserSessionResponse:
        return UserSessionResponse(is_authenticated=False, mode="guest")

    def _build_student_prompt(
        self,
        request: ChatRequest,
        knowledge_hits: list[KnowledgeSearchHit],
        memory_hits: list[ConversationMemoryHit] | None = None,
        interaction_intent: InteractionIntent | None = None,
    ) -> str:
        course_hint = f"Course context: {request.course_context}.\n" if request.course_context else ""
        visitor_profile = getattr(request, "visitor_profile", None)
        visitor_hint = f"Visitor profile: {visitor_profile}.\n" if visitor_profile else ""
        memory_context = self._format_memory_context(memory_hits or [])
        prompt_hits = self._select_prompt_knowledge_hits(request.question, knowledge_hits, interaction_intent)
        knowledge_context = self._format_knowledge_context(prompt_hits)
        intent_guidance = self._build_intent_guidance(interaction_intent)
        availability_context = self._meeting_service.describe_current_availability()
        return (
            f"Student name: {request.student_name}\n"
            f"{course_hint}"
            f"{visitor_hint}"
            f"{intent_guidance}"
            f"{availability_context}"
            f"{memory_context}"
            f"{knowledge_context}"
            f"Question: {request.question}\n"
            "Respond as the digital twin of the faculty owner. Keep the answer grounded and concise. "
            "Use retrieved knowledge only when it directly answers this question; ignore adjacent topics and do not add unasked facts just because they appear in context."
        )

    def _build_admin_session_response(
        self,
        payload: dict[str, Any] | None,
    ) -> AdminSessionResponse:
        if payload is None:
            return AdminSessionResponse(is_admin=False, mode="user")
        return AdminSessionResponse(
            is_admin=True,
            mode="admin",
            username=str(payload.get("sub") or self._settings.admin_username),
        )

    def _build_user_session_response(
        self,
        payload: dict[str, Any] | None,
    ) -> UserSessionResponse:
        if payload is None:
            return UserSessionResponse(is_authenticated=False, mode="guest")

        user_id = str(payload.get("sub") or "")
        if not user_id:
            return UserSessionResponse(is_authenticated=False, mode="guest")

        account = self._user_store.get_user_by_id(user_id)
        if account is None:
            return UserSessionResponse(is_authenticated=False, mode="guest")
        return UserSessionResponse(is_authenticated=True, mode="user", account=account)

    def _format_knowledge_context(self, knowledge_hits: list[KnowledgeSearchHit]) -> str:
        if not knowledge_hits:
            return ""

        sections = ["Relevant owner materials:"]
        for index, hit in enumerate(knowledge_hits, start=1):
            source_suffix = f" | source: {hit.source_name}" if hit.source_name else ""
            sections.append(
                f"{index}. {hit.title}{source_suffix}\nExcerpt: {hit.excerpt}\nTags: {', '.join(hit.tags) if hit.tags else 'none'}"
            )
        return "\n".join(sections) + "\n"

    def _select_prompt_knowledge_hits(
        self,
        question: str,
        knowledge_hits: list[KnowledgeSearchHit],
        interaction_intent: InteractionIntent | None = None,
    ) -> list[KnowledgeSearchHit]:
        if not knowledge_hits:
            return []
        if interaction_intent is not None:
            scoped_hits = self._filter_knowledge_hits_by_intent(knowledge_hits, interaction_intent)
            if interaction_intent.domain == "research":
                research_hits = [
                    hit
                    for hit in scoped_hits
                    if self._is_research_hit(hit) and not self._is_teaching_hit(hit)
                ]
                if research_hits:
                    return research_hits
            if scoped_hits:
                return scoped_hits

        if not self._is_research_question(question):
            return knowledge_hits

        research_hits = [
            hit
            for hit in knowledge_hits
            if self._is_research_hit(hit) and not self._is_teaching_hit(hit)
        ]
        if research_hits:
            return research_hits

        return [hit for hit in knowledge_hits if not self._is_teaching_hit(hit)] or knowledge_hits

    def _is_research_question(self, question: str) -> bool:
        lowered = question.lower()
        markers = (
            "研究主线",
            "研究方向",
            "主要研究",
            "研究什么",
            "做什么研究",
            "科研",
            "research",
            "publication",
            "publications",
        )
        return any(marker in lowered for marker in markers) or any(marker in question for marker in markers)

    def _is_research_hit(self, hit: KnowledgeSearchHit) -> bool:
        hit_tags = {tag.lower() for tag in hit.tags}
        if hit_tags & {"research", "publication", "paper-digest", "overview", "profile"}:
            return True
        source_name = (hit.source_name or "").lower()
        return "研究" in hit.title or "publications" in source_name or "research_papers" in source_name

    def _is_teaching_hit(self, hit: KnowledgeSearchHit) -> bool:
        hit_tags = {tag.lower() for tag in hit.tags}
        return bool(hit_tags & {"teaching", "courseware", "tutorial", "lecture", "experiment", "pdf", "resources"})

    def _build_intent_guidance(self, interaction_intent: InteractionIntent | None) -> str:
        if interaction_intent is None:
            return ""
        if interaction_intent.domain == "research":
            return (
                "Intent guidance: The student is asking about the owner's research. "
                "Prioritize research overview, publications, and paper digests. "
                "For questions about the owner's main or current research direction, answer with the current focus first: "
                "LLM inference engines, LLM inference serving systems, and memory-agent middleware. "
                "If older database-management, stream-processing, or parallel/distributed-systems materials appear, "
                "frame them as historical foundations or method background rather than the current primary direction. "
                "Do not treat courseware as the owner's main identity unless the student explicitly asks about teaching.\n"
            )
        if interaction_intent.domain == "teaching":
            return (
                "Intent guidance: The student is asking about teaching materials. "
                "Prioritize lectures, tutorials, experiments, and courseware details.\n"
            )
        if interaction_intent.domain == "advising":
            guidance = (
                "Intent guidance: The student is asking for advising or preparation guidance. "
                "Prioritize preparation checklists, meeting expectations, and communication guidance over course slides.\n"
            )
            if interaction_intent.decision_mode == "advise_only":
                guidance += (
                    "Decision guidance: Give suggestions, options, and preparation checklists only. "
                    "Do not make approvals, exceptions, commitments, or final decisions on behalf of the owner.\n"
                )
            return guidance
        if interaction_intent.domain == "booking":
            return "Intent guidance: The student is trying to arrange a meeting. Use scheduling and availability facts only.\n"
        if interaction_intent.decision_mode == "advise_only":
            return (
                "Decision guidance: Provide suggestions and options only. "
                "Do not make the final decision on behalf of the owner or the student.\n"
            )
        return ""

    def _resolve_interaction_intent(self, context: ChatWorkflowContext) -> tuple[InteractionIntent, str]:
        if context.conversation_id in self._booking_workflows:
            return self._build_booking_follow_up_intent(), "workflow_state"

        if context.is_admin_request and self._looks_like_admin_knowledge_injection(context.request.question):
            return (
                InteractionIntent(
                    action="admin_add_knowledge",
                    domain="general",
                    decision_mode="direct_answer",
                    confidence=0.98,
                ),
                "admin_command",
            )

        classify_sync = getattr(self._llm_client, "classify_interaction_intent_sync", None)
        if callable(classify_sync):
            try:
                intent = classify_sync(
                    context.request.question,
                    context.request.course_context,
                )
                if not isinstance(intent, InteractionIntent):
                    intent = InteractionIntent.model_validate(intent)
                guarded_intent, guarded = self._apply_policy_guardrails(context.request, intent)
                return guarded_intent, "llm+policy" if guarded else "llm"
            except Exception:
                pass

        intent = self._build_fallback_interaction_intent(context.request)
        guarded_intent, guarded = self._apply_policy_guardrails(context.request, intent)
        return guarded_intent, "heuristic+policy" if guarded else "heuristic"

    def _apply_policy_guardrails(
        self,
        request: ChatRequest,
        intent: InteractionIntent,
    ) -> tuple[InteractionIntent, bool]:
        if self._should_force_human_handoff(request.question):
            return (
                InteractionIntent(
                    action="human_handoff",
                    domain="advising",
                    decision_mode="human_handoff",
                    escalation_reason="涉及敏感、紧急或必须由老师本人直接处理的事项。",
                    confidence=max(intent.confidence, 0.95),
                ),
                True,
            )

        if self._should_queue_for_review(request.question):
            return (
                InteractionIntent(
                    action="review_queue",
                    domain="advising",
                    retrieval_scopes=["meeting_policy", "profile"],
                    exclude_scopes=["courseware"],
                    decision_mode="review_queue",
                    escalation_reason="这是需要老师审核后才能正式答复的请求。",
                    confidence=max(intent.confidence, 0.9),
                ),
                True,
            )

        if intent.action == "book_meeting" and self._looks_like_booking_information_request(request.question):
            return (
                InteractionIntent(
                    action="answer",
                    domain="advising",
                    retrieval_scopes=["meeting_policy", "profile"],
                    exclude_scopes=["courseware"],
                    decision_mode="direct_answer",
                    confidence=max(intent.confidence, 0.9),
                ),
                True,
            )

        if intent.action == "book_meeting" and intent.decision_mode != "review_queue":
            return intent.model_copy(update={"decision_mode": "review_queue"}), True

        if intent.action == "answer" and intent.decision_mode == "direct_answer":
            if any(marker in request.question for marker in ("准备什么", "提前准备", "怎么准备", "帮我决定", "替我决定", "该不该", "怎么选", "选哪个")):
                return intent.model_copy(update={"decision_mode": "advise_only"}), True

        return intent, False

    def _build_booking_follow_up_intent(self) -> InteractionIntent:
        return InteractionIntent(
            action="book_meeting",
            domain="booking",
            retrieval_scopes=["meeting_policy"],
            exclude_scopes=["courseware", "publications"],
            decision_mode="review_queue",
            confidence=1.0,
        )

    def _build_fallback_interaction_intent(self, request: ChatRequest) -> InteractionIntent:
        if self._should_force_human_handoff(request.question):
            return InteractionIntent(
                action="human_handoff",
                domain="advising",
                decision_mode="human_handoff",
                escalation_reason="涉及敏感、紧急或必须由老师本人直接处理的事项。",
                confidence=0.9,
            )

        if self._should_queue_for_review(request.question):
            return InteractionIntent(
                action="review_queue",
                domain="advising",
                retrieval_scopes=["meeting_policy", "profile"],
                exclude_scopes=["courseware"],
                decision_mode="review_queue",
                escalation_reason="这是需要老师审核后才能正式答复的请求。",
                confidence=0.8,
            )

        if self._looks_like_booking_information_request(request.question):
            return InteractionIntent(
                action="answer",
                domain="advising",
                retrieval_scopes=["meeting_policy", "profile"],
                exclude_scopes=["courseware"],
                decision_mode="direct_answer",
                confidence=0.75,
            )

        if self._should_start_booking_workflow(request):
            return InteractionIntent(
                action="book_meeting",
                domain="booking",
                retrieval_scopes=["meeting_policy"],
                exclude_scopes=["courseware", "publications"],
                decision_mode="review_queue",
                confidence=0.7,
            )

        if self._is_research_question(request.question):
            return InteractionIntent(
                action="answer",
                domain="research",
                retrieval_scopes=["publications", "profile"],
                exclude_scopes=["courseware"],
                confidence=0.6,
            )

        lowered = request.question.lower()
        if any(marker in lowered for marker in ("tutorial", "lecture", "experiment", "课件", "讲义", "实验")):
            return InteractionIntent(
                action="answer",
                domain="teaching",
                retrieval_scopes=["courseware"],
                exclude_scopes=["publications"],
                confidence=0.6,
            )

        if any(marker in request.question for marker in ("准备什么", "提前准备", "怎么准备")):
            return InteractionIntent(
                action="answer",
                domain="advising",
                retrieval_scopes=["preparation", "meeting_policy", "profile"],
                exclude_scopes=["courseware"],
                decision_mode="advise_only",
                confidence=0.6,
            )

        if any(marker in request.question for marker in ("帮我决定", "替我决定", "该不该", "怎么选", "选哪个")):
            return InteractionIntent(
                action="answer",
                domain="advising",
                retrieval_scopes=["profile", "meeting_policy"],
                exclude_scopes=["courseware"],
                decision_mode="advise_only",
                confidence=0.6,
            )

        return InteractionIntent(action="answer", domain="general", confidence=0.5)

    def _build_knowledge_query(self, request: ChatRequest, interaction_intent: InteractionIntent) -> str:
        if request.course_context and interaction_intent.domain in {"research", "teaching", "advising"}:
            return f"{request.question}\n{request.course_context}".strip()
        return request.question

    def _filter_knowledge_hits_by_intent(
        self,
        knowledge_hits: list[KnowledgeSearchHit],
        interaction_intent: InteractionIntent | None,
    ) -> list[KnowledgeSearchHit]:
        if interaction_intent is None or not knowledge_hits:
            return knowledge_hits

        scoped_hits = [
            hit
            for hit in knowledge_hits
            if self._matches_intent_scopes(hit, interaction_intent.retrieval_scopes)
            and not self._matches_intent_scopes(hit, interaction_intent.exclude_scopes)
        ]
        if scoped_hits:
            return scoped_hits

        non_excluded_hits = [
            hit for hit in knowledge_hits if not self._matches_intent_scopes(hit, interaction_intent.exclude_scopes)
        ]
        return non_excluded_hits or knowledge_hits

    def _matches_intent_scopes(self, hit: KnowledgeSearchHit, scopes: list[str]) -> bool:
        if not scopes:
            return True
        hit_tags = {tag.lower() for tag in hit.tags}
        scope_map = {
            "publications": {"research", "publication", "paper-digest", "overview"},
            "profile": {"profile"},
            "courseware": {"teaching", "courseware", "tutorial", "lecture", "experiment", "pdf", "resources"},
            "preparation": {"preparation", "qa", "policy", "meeting"},
            "meeting_policy": {"meeting", "policy", "preparation", "qa"},
        }
        for scope in scopes:
            allowed_tags = scope_map.get(scope, set())
            if hit_tags & allowed_tags:
                return True
            if scope == "publications" and self._is_research_hit(hit):
                return True
            if scope == "courseware" and self._is_teaching_hit(hit):
                return True
        return False

    def _format_memory_context(self, memory_hits: list[ConversationMemoryHit]) -> str:
        if not memory_hits:
            return ""

        short_term_hits = [hit for hit in memory_hits if hit.memory_type == "short_term"]
        long_term_hits = [hit for hit in memory_hits if hit.memory_type == "long_term"]

        sections: list[str] = []
        if short_term_hits:
            sections.append("Recent conversation memory:")
            for index, hit in enumerate(short_term_hits, start=1):
                sections.append(f"{index}. {hit.summary}")

        if long_term_hits:
            sections.append("Stable student profile memory:")
            for index, hit in enumerate(long_term_hits, start=1):
                sections.append(f"{index}. {hit.summary}")

        return "\n".join(sections) + "\n"

    def _build_answer_basis(self, context: ChatWorkflowContext) -> list[AnswerBasisItem]:
        basis_items: list[AnswerBasisItem] = []

        if context.added_knowledge_record is not None:
            basis_items.append(self._build_added_knowledge_basis_item(context.added_knowledge_record))

        for hit in context.knowledge_hits[:3]:
            basis_items.append(self._build_knowledge_basis_item(hit))

        for hit in context.memory_hits[:2]:
            basis_items.append(self._build_memory_basis_item(hit))

        availability_item = self._build_availability_basis_item(context)
        if availability_item is not None:
            basis_items.append(availability_item)

        deduped_items: list[AnswerBasisItem] = []
        seen_keys: set[tuple[str, str, str]] = set()
        for item in basis_items:
            item_key = (item.basis_label, item.title, item.source_label)
            if item_key in seen_keys:
                continue
            seen_keys.add(item_key)
            deduped_items.append(item)

        return deduped_items[:5]

    def _build_memory_basis_item(self, hit: ConversationMemoryHit) -> AnswerBasisItem:
        if hit.memory_type == "long_term":
            return AnswerBasisItem(
                basis_label="学生长期记录",
                title="过往交流里提到过的长期偏好",
                source_label="长期记录",
                detail=self._clip_basis_text(self._format_memory_basis_detail(hit.summary), 1000),
            )
        return AnswerBasisItem(
            basis_label="近期交流记录",
            title="这轮对话前后提到过的相关内容",
            source_label="近期对话",
            detail=self._clip_basis_text(self._format_memory_basis_detail(hit.summary), 1000),
        )

    def _build_knowledge_basis_item(self, hit: KnowledgeSearchHit) -> AnswerBasisItem:
        if self._looks_like_gap_draft_hit(hit):
            return AnswerBasisItem(
                basis_label="常见问题整理",
                title=self._clip_basis_text(self._format_gap_draft_basis_title(hit.title), 256),
                source_label="近期高频问题整理",
                detail=self._clip_basis_text(self._format_gap_draft_basis_detail(hit.excerpt), 1000),
            )

        return AnswerBasisItem(
            basis_label=self._classify_knowledge_basis_label(hit),
            title=self._clip_basis_text(self._format_basis_title(hit.title), 256),
            source_label=self._clip_basis_text(self._format_basis_source_label(hit.source_name), 256),
            detail=self._clip_basis_text(self._format_basis_detail(hit.excerpt), 1000),
        )

    def _build_added_knowledge_basis_item(self, record: KnowledgeDocumentRecord) -> AnswerBasisItem:
        detail = (
            f"已通过管理员对话写入知识库，标签：{', '.join(record.tags) or '未设置'}。"
            "后续管理员检索和普通问答都可以立即复用这条资料。"
        )
        return AnswerBasisItem(
            basis_label="知识入库结果",
            title=self._clip_basis_text(self._format_basis_title(record.title), 256),
            source_label=self._clip_basis_text(self._format_basis_source_label(record.source_name), 256),
            detail=self._clip_basis_text(detail, 1000),
        )

    def _clip_basis_text(self, value: str | None, limit: int) -> str:
        normalized = str(value or "").strip()
        if len(normalized) <= limit:
            return normalized
        return f"{normalized[: max(limit - 1, 0)].rstrip()}…"

    def _format_basis_title(self, title: str | None) -> str:
        normalized = re.sub(r"\s+", " ", str(title or "")).strip(" ：:|｜")
        if not normalized:
            return "相关材料"

        parts = [part.strip() for part in re.split(r"[|｜]", normalized) if part.strip()]
        meaningful_parts = [part for part in parts if not self._looks_like_fragmented_title_segment(part)]
        if meaningful_parts:
            return " · ".join(meaningful_parts[:2])
        return normalized

    def _format_basis_detail(self, detail: str | None) -> str:
        normalized = re.sub(r"\s+", " ", str(detail or "")).strip()
        return normalized

    def _format_memory_basis_detail(self, detail: str | None) -> str:
        normalized = str(detail or "").strip()
        normalized = re.sub(r"\[[^\]]+\]\s*", "", normalized)
        normalized = normalized.replace("**", "")

        question_match = re.search(r"问：\s*(.+?)(?:\n|$)", normalized, re.DOTALL)
        answer_match = re.search(r"答：\s*(.+)", normalized, re.DOTALL)

        question = _normalize_whitespace(question_match.group(1)) if question_match else ""
        answer = _normalize_whitespace(answer_match.group(1)) if answer_match else _normalize_whitespace(normalized)

        highlights = _extract_numbered_highlights(answer)
        if highlights:
            summary = "；".join(highlights[:4])
            if question:
                return f"你之前问过“{question}”，上次回答重点是：{summary}。"
            return f"之前相关回答重点是：{summary}。"

        compact_answer = _summarize_text(answer, limit=96)
        if question:
            return f"你之前问过“{question}”，上次回答重点是：{compact_answer}"
        return compact_answer

    def _looks_like_fragmented_title_segment(self, value: str) -> bool:
        pieces = [piece.strip() for piece in value.split("/") if piece.strip()]
        if len(pieces) < 2:
            return False
        return all(len(piece) <= 3 for piece in pieces)

    def _looks_like_gap_draft_hit(self, hit: KnowledgeSearchHit) -> bool:
        source_name = str(hit.source_name or "")
        hit_tags = {tag.lower() for tag in hit.tags}
        return source_name.startswith("analytics-gap:") or "faq-draft" in hit_tags

    def _format_gap_draft_basis_title(self, title: str | None) -> str:
        normalized = self._format_basis_title(title)
        parts = [part.strip() for part in re.split(r"[·|｜]", normalized) if part.strip()]
        topic = next((part for part in parts if part != "FAQ草稿"), normalized)
        return f"{topic}"

    def _format_gap_draft_basis_detail(self, detail: str | None) -> str:
        normalized = self._format_basis_detail(detail)
        suggested_action = self._extract_gap_draft_suggested_action(normalized)
        if suggested_action:
            return f"这类问题通常需要补充：{suggested_action}。"
        return "这类问题建议补一份更明确的说明模板，避免下次还要反复追问。"

    def _extract_gap_draft_suggested_action(self, detail: str | None) -> str:
        normalized = str(detail or "")
        matched = re.search(r"建议动作[:：]\s*([^。；]+)", normalized)
        if matched:
            return matched.group(1).strip()
        return ""

    def _build_availability_basis_item(self, context: ChatWorkflowContext) -> AnswerBasisItem | None:
        retrieval_scopes = set(context.interaction_intent.retrieval_scopes) if context.interaction_intent else set()
        should_include_availability = context.workflow_action in {"book_meeting", "collect_booking_details"} or "meeting_policy" in retrieval_scopes
        if not should_include_availability:
            return None

        schedule = self._meeting_service.get_availability_schedule()
        if schedule.days:
            preview: list[str] = []
            for day in schedule.days[:3]:
                windows = "、".join(f"{window.start}-{window.end}" for window in day.windows) or "不开放"
                preview.append(f"{day.date.isoformat()}: {windows}")
            detail = (
                f"当前依据本周可预约时段与 {self._settings.meeting_duration_minutes} 分钟单次预约规则处理。"
                f" 最近安排：{'；'.join(preview)}"
            )
        else:
            detail = (
                f"当前依据默认预约规则处理：工作时间 {self._settings.booking_start_hour:02d}:00-"
                f"{self._settings.booking_end_hour:02d}:00，单次预约 {self._settings.meeting_duration_minutes} 分钟。"
            )

        return AnswerBasisItem(
            basis_label="预约规则与时段",
            title="当前可预约规则",
            source_label="当前预约安排配置",
            detail=detail,
        )

    def _classify_knowledge_basis_label(self, hit: KnowledgeSearchHit) -> str:
        hit_tags = {tag.lower() for tag in hit.tags}
        source_name = (hit.source_name or "").lower()
        if self._is_teaching_hit(hit):
            if ".pdf" in source_name or "pdf" in hit_tags:
                return "课程 PDF"
            return "课程页面"
        if hit_tags & {"policy", "meeting", "preparation", "qa"}:
            return "过往政策说明"
        if self._is_research_hit(hit):
            if ".pdf" in source_name or "research_papers" in source_name or "paper-digest" in hit_tags:
                return "论文资料"
            return "个人主页条目"
        if source_name.startswith("homepage:"):
            return "个人主页条目"
        return "知识库条目"

    def _format_basis_source_label(self, source_name: str | None) -> str:
        if not source_name:
            return "管理员手动录入"

        normalized = re.sub(r"::part-\d+$", "", source_name)
        if normalized.startswith("knowledge-gap:"):
            return "常见问题补充条目"
        parts = normalized.split("::")
        primary_source = parts[0]
        attachment_source = next((part for part in parts[1:] if part.endswith(".pdf")), None)

        if primary_source.startswith("homepage:"):
            primary_path = primary_source.removeprefix("homepage:")
            primary_file, _, fragment = primary_path.partition("#")

            if attachment_source:
                attachment_name = attachment_source.split("/")[-1]
                if "/teaching/" in attachment_source:
                    return f"个人主页 / 课程 PDF / {attachment_name}"
                return f"个人主页 / 研究论文 PDF / {attachment_name}"

            if primary_file == "contents/home.md":
                return "个人主页 / 首页"
            if primary_file == "contents/news.md":
                return "个人主页 / 新闻动态"
            if primary_file == "contents/publications.md":
                return "个人主页 / 论文成果页"
            if primary_file == "contents/research_papers/publications_summary.md":
                return (
                    f"个人主页 / 研究论文汇总 / {fragment}"
                    if fragment
                    else "个人主页 / 研究论文汇总"
                )
            if primary_file.startswith("contents/research_papers/") and primary_file.endswith(".pdf"):
                return f"个人主页 / 研究论文 PDF / {primary_file.split('/')[-1]}"
            if primary_file == "contents/resources.md":
                return "个人主页 / 教学资源页"
            if primary_file.startswith("contents/teaching/"):
                if primary_file.endswith(".pdf"):
                    return f"个人主页 / 课程 PDF / {primary_file.split('/')[-1]}"
                course_name = primary_file.split("/")[-1].removesuffix(".md")
                if fragment and fragment != "intro":
                    return f"个人主页 / 课程页面 / {course_name} / {fragment}"
                return f"个人主页 / 课程页面 / {course_name}"
            if fragment and fragment not in {"intro", "recent-updates", "teaching-resources"}:
                return f"个人主页 / {fragment}"
            return "个人主页条目"

        if normalized.endswith("current_week.json"):
            return "当前预约安排配置"

        return normalized.split("/")[-1]

    def _append_trace(
        self,
        context: ChatWorkflowContext,
        *,
        key: str,
        title: str,
        summary: str,
        detail: str,
        status: str = "completed",
        duration_ms: int | None = None,
    ) -> None:
        step = WorkflowTraceStep(
            key=key,
            title=title,
            summary=summary,
            detail=detail,
            status=status,
            duration_ms=duration_ms,
        )
        context.workflow_trace.append(step)
        if self._trace_callback is not None:
            self._trace_callback(step.model_copy(deep=True))

    def _format_pending_fields(self, pending_fields: list[str]) -> str:
        labels = {
            "student_email": "邮箱",
            "preferred_start": "会议时间",
            "topic": "会议主题",
        }
        return "、".join(labels.get(field, field) for field in pending_fields)

    def _elapsed_ms(self, started_at: float) -> int:
        return max(0, int(round((perf_counter() - started_at) * 1000)))

    def _looks_like_booking_information_request(self, question: str) -> bool:
        lowered = question.lower()
        explicit_booking_markers = (
            "请帮我预约",
            "帮我预约",
            "请预约",
            "我要预约",
            "我想预约",
            "申请预约",
            "提交预约",
            "约在",
            "约个会",
            "book me",
            "schedule a meeting",
        )
        if any(marker in lowered for marker in explicit_booking_markers) or any(marker in question for marker in explicit_booking_markers):
            return False

        info_markers = (
            "office hour",
            "office hours",
            "想了解",
            "想知道",
            "了解一下",
            "告诉我",
            "能否告诉我",
            "可以告诉我",
            "什么时候",
            "什么时间",
            "这周",
            "本周",
            "开放时段",
            "可预约时段",
            "预约规则",
            "如何预约",
            "怎么预约",
            "以便预约",
            "方便预约",
        )
        booking_context_markers = (
            "office hour",
            "office hours",
            "预约",
            "约时间",
            "约老师",
            "时间安排",
            "开放时段",
        )
        has_info_marker = any(marker in lowered for marker in info_markers) or any(marker in question for marker in info_markers)
        has_booking_context = any(marker in lowered for marker in booking_context_markers) or any(marker in question for marker in booking_context_markers)
        return has_info_marker and has_booking_context

    def _needs_booking_intent_classification(self, question: str) -> bool:
        if self._looks_like_booking_information_request(question):
            return False
        lowered = question.lower()
        keywords = (
            "预约",
            "预定",
            "约时间",
            "约老师",
            "约个会",
            "book",
            "schedule",
            "meeting",
        )
        return any(keyword in lowered for keyword in keywords)

    def _should_force_human_handoff(self, question: str) -> bool:
        markers = ("投诉", "申诉", "成绩", "隐私", "保密", "紧急", "心理", "危机", "安全", "举报")
        lowered = question.lower()
        return any(marker in lowered for marker in markers) or any(marker in question for marker in markers)

    def _should_queue_for_review(self, question: str) -> bool:
        markers = ("破例", "例外", "延期", "审批", "审核", "批准", "推荐信", "加入课题组", "能收我吗")
        lowered = question.lower()
        return any(marker in lowered for marker in markers) or any(marker in question for marker in markers)

    def _build_escalation_message(self, context: ChatWorkflowContext) -> str:
        record = context.escalation_record
        if record is None or context.interaction_intent is None:
            return "这个请求需要老师本人进一步处理。"

        if context.interaction_intent.action == "human_handoff":
            reason = context.interaction_intent.escalation_reason or "这类问题不能由数字人代替老师处理。"
            return (
                f"这个问题需要由 {context.owner_name} 本人直接处理，我不能代为决定或表态。\n"
                f"已创建人工处理工单：{record.escalation_id}\n"
                f"原因：{reason}\n"
                "如情况紧急，请直接通过正式联系方式联系老师。"
            )

        reason = context.interaction_intent.escalation_reason or "这类请求需要老师审核后才能正式答复。"
        return (
            "这个请求需要人工审核后才能给出正式结论，我先不替老师做决定。\n"
            f"已加入待审核队列：{record.escalation_id}\n"
            f"原因：{reason}"
        )

    def _should_start_booking_workflow(self, request: ChatRequest) -> bool:
        if self._looks_like_booking_information_request(request.question):
            return False
        if not self._needs_booking_intent_classification(request.question):
            return False
        return self._llm_client.classify_booking_intent_sync(
            request.question,
            request.course_context,
        )

    def _looks_like_admin_knowledge_injection(self, question: str) -> bool:
        normalized = _normalize_whitespace(question)
        if not normalized:
            return False

        trigger_markers = (
            "加入知识库",
            "添加到知识库",
            "写入知识库",
            "录入知识库",
            "保存到知识库",
            "记到知识库",
            "注入知识",
            "补充知识库",
            "更新知识库",
        )
        has_trigger = any(marker in normalized for marker in trigger_markers)
        if not has_trigger:
            return False

        has_structured_fields = any(
            marker in normalized
            for marker in ("标题：", "标题:", "内容：", "内容:", "正文：", "正文:", "标签：", "标签:")
        )
        if has_structured_fields:
            return True

        command_body = self._strip_admin_knowledge_command(normalized)
        return len(command_body) >= 16

    def _build_admin_knowledge_request(self, request: ChatRequest) -> KnowledgeDocumentCreate | None:
        command_body = self._strip_admin_knowledge_command(request.question)
        if not command_body:
            return None

        parsed_fields = self._parse_admin_knowledge_fields(command_body)
        content = parsed_fields.get("content") or command_body
        content = content.strip()
        if len(content) < 8:
            return None

        title = parsed_fields.get("title") or self._derive_admin_knowledge_title(content, request.course_context)
        tags = self._parse_admin_knowledge_tags(parsed_fields.get("tags", ""))
        source_name = parsed_fields.get("source") or None
        return KnowledgeDocumentCreate(
            title=title,
            content=content,
            tags=tags,
            source_name=source_name,
        )

    def _build_admin_knowledge_guidance_message(self) -> str:
        return (
            "已识别为管理员知识入库指令，但当前内容还不够完整。\n"
            "你可以直接这样发：\n"
            "加入知识库：\n"
            "标题：预约前准备清单\n"
            "标签：advising, booking\n"
            "内容：学生预约前需要先发送 agenda、当前 blocker 和相关 draft。"
        )

    def _build_admin_knowledge_success_message(self, record: KnowledgeDocumentRecord) -> str:
        tags_text = "、".join(record.tags) if record.tags else "未设置"
        source_text = record.source_name or "管理员手动录入"
        return (
            f"已写入知识库：{record.title}\n"
            f"标签：{tags_text}\n"
            f"来源：{source_text}\n"
            "后续管理员检索和学生对话都可以立即使用这条资料。"
        )

    def _strip_admin_knowledge_command(self, question: str) -> str:
        normalized = str(question or "").strip()
        patterns = [
            r"^(?:请|麻烦)?(?:帮我)?(?:把下面|将下面|把这段|将这段)?(?:内容|资料|信息)?(?:直接)?(?:加入|添加到|写入|录入|保存到|记到|补充到|更新到)(?:知识库|知识)(?:里|中)?[：:，,\s-]*",
            r"^(?:请|麻烦)?(?:帮我)?(?:直接)?(?:注入|录入)(?:知识|知识库)[：:，,\s-]*",
        ]
        stripped = normalized
        for pattern in patterns:
            stripped = re.sub(pattern, "", stripped, count=1)
        return stripped.strip()

    def _parse_admin_knowledge_fields(self, body: str) -> dict[str, str]:
        alias_map = {
            "标题": "title",
            "title": "title",
            "标签": "tags",
            "tag": "tags",
            "tags": "tags",
            "来源": "source",
            "来源名": "source",
            "source": "source",
            "内容": "content",
            "正文": "content",
            "content": "content",
        }
        result: dict[str, list[str]] = {"title": [], "tags": [], "source": [], "content": []}
        fallback_lines: list[str] = []
        current_field: str | None = None

        for raw_line in body.splitlines():
            line = raw_line.strip()
            if not line:
                if current_field == "content":
                    result[current_field].append("")
                continue

            matched = re.match(r"^(标题|title|标签|tag|tags|来源|来源名|source|内容|正文|content)\s*[:：]\s*(.*)$", line, re.IGNORECASE)
            if matched:
                current_field = alias_map[matched.group(1).lower()]
                value = matched.group(2).strip()
                if value:
                    result[current_field].append(value)
                continue

            if current_field == "content":
                result[current_field].append(raw_line.rstrip())
                continue

            fallback_lines.append(raw_line.rstrip())

        parsed = {
            key: "\n".join(value).strip() if key == "content" else " ".join(value).strip()
            for key, value in result.items()
            if any(part.strip() for part in value)
        }
        if "content" not in parsed:
            fallback_content = "\n".join(line for line in fallback_lines if line.strip()).strip()
            if fallback_content:
                parsed["content"] = fallback_content
        return parsed

    def _parse_admin_knowledge_tags(self, raw_tags: str) -> list[str]:
        if not raw_tags.strip():
            return []
        normalized: list[str] = []
        for tag in re.split(r"[,，;；、\s]+", raw_tags):
            cleaned = tag.strip().lower()
            if cleaned and cleaned not in normalized:
                normalized.append(cleaned)
        return normalized

    def _derive_admin_knowledge_title(self, content: str, course_context: str | None) -> str:
        if course_context and course_context.strip():
            return _summarize_text(course_context.strip(), limit=64)

        for line in content.splitlines():
            normalized = _normalize_whitespace(line).strip(" ：:|｜")
            if normalized:
                return _summarize_text(normalized, limit=64)
        return "管理员对话录入知识"

    def _missing_booking_fields(self, state: BookingWorkflowState) -> list[str]:
        missing_fields: list[str] = []
        if not state.student_email:
            missing_fields.append("student_email")
        if state.preferred_start is None:
            missing_fields.append("preferred_start")
        if not state.topic:
            missing_fields.append("topic")
        return missing_fields

    def _build_booking_follow_up(
        self,
        missing_fields: list[str],
        state: BookingWorkflowState,
    ) -> str:
        labels = {
            "student_email": "邮箱",
            "preferred_start": "会议时间",
            "topic": "会议主题",
        }
        known_parts: list[str] = []
        if state.student_email:
            known_parts.append(f"邮箱：{state.student_email}")
        if state.preferred_start:
            known_parts.append(f"时间：{state.preferred_start.strftime('%Y-%m-%d %H:%M')}")
        if state.topic:
            known_parts.append(f"主题：{state.topic}")

        missing = "、".join(labels[field] for field in missing_fields)
        known_text = f"已记录信息：{'；'.join(known_parts)}。\n" if known_parts else ""
        return (
            f"我正在为你处理会议预约。\n{known_text}"
            f"还缺少：{missing}。"
            "请直接回复缺失信息，例如“我的邮箱是 student@example.com，明天下午 3 点讨论论文进展”。"
        )

    def _build_booking_success_message(
        self,
        booking_response: BookingResponse,
    ) -> str:
        booking = booking_response.booking
        if booking is None:
            return booking_response.message
        lines = [
            f"{booking_response.message}\n"
            f"预约编号：{booking.booking_id}\n"
            f"主题：{booking.topic}\n"
            f"时间：{booking.start_at.strftime('%Y-%m-%d %H:%M')} - {booking.end_at.strftime('%H:%M')}\n"
            f"当前状态：{booking.status}"
        ]
        notification = booking_response.notification
        if notification is not None:
            lines.append(notification.summary)
            if notification.status == "failed" and notification.detail:
                lines.append(notification.detail)
        return "\n".join(lines)

    def _build_booking_retry_message(self, booking_response: BookingResponse) -> str:
        alternatives = "、".join(booking_response.alternative_slots) if booking_response.alternative_slots else "无"
        return (
            f"{booking_response.message}\n"
            f"可选时间：{alternatives}\n"
            "请回复新的时间，我会继续为你完成预约。"
        )

    def _attach_student_notification(
        self,
        booking_response: BookingResponse,
        *,
        success_message_prefix: str,
        notify: Callable[[BookingRecord], str],
    ) -> BookingResponse:
        booking = booking_response.booking
        if not booking_response.accepted or booking is None:
            return booking_response

        if booking_response.message not in {"预约已确认。", "预约已拒绝。"}:
            return booking_response

        message = booking_response.message
        try:
            recipient = notify(booking)
        except BookingNotificationError as exc:
            notification = NotificationDeliveryStatus(
                status="failed",
                summary=str(exc),
                detail="预约状态已经更新，但学生通知邮件未成功送达；可稍后重试或改为人工联系。",
            )
        else:
            notification = NotificationDeliveryStatus(
                status="sent",
                recipient=recipient,
                summary=success_message_prefix.format(recipient=recipient),
            )

        message = f"{message} {notification.summary}"

        return BookingResponse(
            accepted=booking_response.accepted,
            message=message,
            booking=booking,
            alternative_slots=booking_response.alternative_slots,
            notification=notification,
        )

    def _extract_email(self, text: str) -> str | None:
        match = re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, re.IGNORECASE)
        if match is None:
            return None
        return match.group(0)

    def _extract_time_window(self, text: str) -> tuple[datetime | None, datetime | None]:
        explicit = self._extract_explicit_datetime_window(text)
        if explicit != (None, None):
            return explicit

        base_date = self._extract_relative_date(text)
        if base_date is None:
            return None, None

        time_matches = list(
            re.finditer(
                r"(?:(上午|中午|下午|晚上))?\s*(\d{1,2}|[零〇一二两三四五六七八九十]{1,3})(?:[:：](\d{2})|点(?:(半)|(\d{1,2})分?)?)",
                text,
            )
        )
        if not time_matches:
            return None, None

        start_prefix, start_hour, start_minute = self._normalize_time_match(time_matches[0])
        start_at = datetime.combine(base_date, time(start_hour, start_minute))

        if len(time_matches) > 1:
            _, end_hour, end_minute = self._normalize_time_match(
                time_matches[1],
                inherited_prefix=start_prefix,
            )
            end_at = datetime.combine(base_date, time(end_hour, end_minute))
        else:
            end_at = start_at + timedelta(minutes=self._settings.meeting_duration_minutes)

        return start_at, end_at

    def _extract_explicit_datetime_window(
        self,
        text: str,
    ) -> tuple[datetime | None, datetime | None]:
        pattern = re.compile(
            r"(\d{4}-\d{1,2}-\d{1,2})[ T](\d{1,2}:\d{2})(?:\s*(?:到|-|至)\s*(\d{1,2}:\d{2}))?"
        )
        match = pattern.search(text)
        if match is None:
            return None, None

        day_text, start_text, end_text = match.groups()
        start_at = datetime.strptime(f"{day_text} {start_text}", "%Y-%m-%d %H:%M")
        if end_text:
            end_at = datetime.strptime(f"{day_text} {end_text}", "%Y-%m-%d %H:%M")
        else:
            end_at = start_at + timedelta(minutes=self._settings.meeting_duration_minutes)
        return start_at, end_at

    def _extract_relative_date(self, text: str) -> date | None:
        now = datetime.now()
        if "今天" in text:
            return now.date()
        if "明天" in text:
            return (now + timedelta(days=1)).date()
        if "后天" in text:
            return (now + timedelta(days=2)).date()
        return None

    def _normalize_time_match(
        self,
        match: re.Match[str],
        inherited_prefix: str | None = None,
    ) -> tuple[str | None, int, int]:
        prefix, hour_text, minute_text, half_text, cn_minute_text = match.groups()
        resolved_prefix = prefix or inherited_prefix
        hour = self._parse_time_number(hour_text)
        if minute_text:
            minute = int(minute_text)
        elif half_text:
            minute = 30
        elif cn_minute_text:
            minute = int(cn_minute_text)
        else:
            minute = 0

        if resolved_prefix in {"下午", "晚上"} and hour < 12:
            hour += 12
        if resolved_prefix == "中午" and hour < 11:
            hour += 12
        return resolved_prefix, hour, minute

    def _parse_time_number(self, text: str) -> int:
        if text.isdigit():
            return int(text)
        digits = {"零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
        if text == "十":
            return 10
        if text.startswith("十"):
            return 10 + digits.get(text[-1], 0)
        if text.endswith("十"):
            return digits.get(text[0], 0) * 10
        if "十" in text:
            tens_text, ones_text = text.split("十", 1)
            return digits.get(tens_text, 1) * 10 + digits.get(ones_text, 0)
        return digits.get(text, 0)

    def _extract_topic(self, question: str, course_context: str | None) -> str | None:
        explicit_patterns = (
            r"(?:讨论|聊聊|沟通|关于)\s*([^，。！？?]+)",
            r"主题(?:是|为)?\s*([^，。！？?]+)",
        )
        for pattern in explicit_patterns:
            match = re.search(pattern, question)
            if match is not None:
                topic = match.group(1).strip()
                if topic:
                    return topic[:256]

        cleaned = question
        cleaned = re.sub(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", " ", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\d{4}-\d{1,2}-\d{1,2}[ T]\d{1,2}:\d{2}(?:\s*(?:到|-|至)\s*\d{1,2}:\d{2})?", " ", cleaned)
        cleaned = re.sub(r"(今天|明天|后天)", " ", cleaned)
        cleaned = re.sub(r"(上午|中午|下午|晚上)?\s*\d{1,2}(?:[:：]\d{2}|点(?:半|\d{1,2}分?)?)", " ", cleaned)
        cleaned = re.sub(
            r"(请|帮我|想|需要|安排|预约|预定|约|老师|一个|一下|个|时间|会议|meeting|book|schedule)",
            " ",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ，。！？?")
        if cleaned:
            return cleaned[:256]
        if course_context:
            return course_context.strip()[:256]
        return None


class ResultCollector(SinkFunction):
    def __init__(self, results: list[Any]) -> None:
        super().__init__()
        self._results = results

    def execute(self, data: Any) -> None:
        self._results.append(data)


class BootstrapChatContextStage(MapFunction):
    def __init__(self, support: FacultyTwinWorkflowSupport) -> None:
        super().__init__()
        self._support = support

    def execute(self, data: ChatRequest) -> ChatWorkflowContext:
        return self._support.bootstrap_chat(data)


class InteractionUnderstandingStage(MapFunction):
    def __init__(self, support: FacultyTwinWorkflowSupport) -> None:
        super().__init__()
        self._support = support

    def execute(self, data: ChatWorkflowContext) -> ChatWorkflowContext:
        return self._support.understand_interaction(data)


class BookingPreparationStage(MapFunction):
    def __init__(self, support: FacultyTwinWorkflowSupport) -> None:
        super().__init__()
        self._support = support

    def execute(self, data: ChatWorkflowContext) -> ChatWorkflowContext:
        return self._support.prepare_booking(data)


class BookingExecutionStage(MapFunction):
    def __init__(self, support: FacultyTwinWorkflowSupport) -> None:
        super().__init__()
        self._support = support

    def execute(self, data: ChatWorkflowContext) -> ChatWorkflowContext:
        return self._support.execute_booking(data)


class KnowledgeRetrievalStage(MapFunction):
    def __init__(self, support: FacultyTwinWorkflowSupport) -> None:
        super().__init__()
        self._support = support

    def execute(self, data: ChatWorkflowContext) -> ChatWorkflowContext:
        return self._support.retrieve_knowledge(data)


class MemoryRetrievalStage(MapFunction):
    def __init__(self, support: FacultyTwinWorkflowSupport) -> None:
        super().__init__()
        self._support = support

    def execute(self, data: ChatWorkflowContext) -> ChatWorkflowContext:
        return self._support.retrieve_memory(data)


class PromptBuildStage(MapFunction):
    def __init__(self, support: FacultyTwinWorkflowSupport) -> None:
        super().__init__()
        self._support = support

    def execute(self, data: ChatWorkflowContext) -> ChatWorkflowContext:
        return self._support.build_prompt(data)


class LlmAnswerStage(MapFunction):
    def __init__(self, support: FacultyTwinWorkflowSupport) -> None:
        super().__init__()
        self._support = support

    def execute(self, data: ChatWorkflowContext) -> ChatWorkflowContext:
        return self._support.answer_with_llm(data)


class MemoryPersistStage(MapFunction):
    def __init__(self, support: FacultyTwinWorkflowSupport) -> None:
        super().__init__()
        self._support = support

    def execute(self, data: ChatWorkflowContext) -> ChatWorkflowContext:
        return self._support.persist_memory(data)


class MemoryProfileConsolidationStage(MapFunction):
    def __init__(self, support: FacultyTwinWorkflowSupport) -> None:
        super().__init__()
        self._support = support

    def execute(self, data: ChatWorkflowContext) -> ChatWorkflowContext:
        return self._support.consolidate_profile_memory(data)


class FollowUpPlanningStage(MapFunction):
    def __init__(self, support: FacultyTwinWorkflowSupport) -> None:
        super().__init__()
        self._support = support

    def execute(self, data: ChatWorkflowContext) -> ChatWorkflowContext:
        return self._support.plan_follow_up_actions(data)


class ChatResponseRenderStage(MapFunction):
    def __init__(self, support: FacultyTwinWorkflowSupport) -> None:
        super().__init__()
        self._support = support

    def execute(self, data: ChatWorkflowContext) -> ChatResponse:
        return self._support.render_chat_response(data)


class ReadAdminSessionStage(MapFunction):
    def __init__(self, support: FacultyTwinWorkflowSupport) -> None:
        super().__init__()
        self._support = support

    def execute(self, data: AdminSessionTokenInput) -> AdminSessionResponse:
        return self._support.read_admin_session(data)


class RequireAdminSessionStage(MapFunction):
    def __init__(self, support: FacultyTwinWorkflowSupport) -> None:
        super().__init__()
        self._support = support

    def execute(self, data: AdminSessionTokenInput) -> dict[str, Any]:
        return self._support.require_admin_session(data)


class AdminLoginStage(MapFunction):
    def __init__(self, support: FacultyTwinWorkflowSupport) -> None:
        super().__init__()
        self._support = support

    def execute(self, data: AdminLoginRequest) -> AdminLoginWorkflowResult:
        return self._support.login_admin(data)


class AdminLogoutStage(MapFunction):
    def __init__(self, support: FacultyTwinWorkflowSupport) -> None:
        super().__init__()
        self._support = support

    def execute(self, _: object) -> AdminSessionResponse:
        return self._support.logout_admin(_)


class ReadUserSessionStage(MapFunction):
    def __init__(self, support: FacultyTwinWorkflowSupport) -> None:
        super().__init__()
        self._support = support

    def execute(self, data: UserSessionTokenInput) -> UserSessionResponse:
        return self._support.read_user_session(data)


class UserRegisterStage(MapFunction):
    def __init__(self, support: FacultyTwinWorkflowSupport) -> None:
        super().__init__()
        self._support = support

    def execute(self, data: UserRegisterRequest) -> UserAuthWorkflowResult:
        return self._support.register_user(data)


class UserLoginStage(MapFunction):
    def __init__(self, support: FacultyTwinWorkflowSupport) -> None:
        super().__init__()
        self._support = support

    def execute(self, data: UserLoginRequest) -> UserAuthWorkflowResult:
        return self._support.login_user(data)


class UserLogoutStage(MapFunction):
    def __init__(self, support: FacultyTwinWorkflowSupport) -> None:
        super().__init__()
        self._support = support

    def execute(self, _: object) -> UserSessionResponse:
        return self._support.logout_user(_)


class AddKnowledgeStage(MapFunction):
    def __init__(self, support: FacultyTwinWorkflowSupport) -> None:
        super().__init__()
        self._support = support

    def execute(self, data: KnowledgeDocumentCreate) -> KnowledgeDocumentRecord:
        return self._support.add_knowledge(data)


class ListKnowledgeStage(MapFunction):
    def __init__(self, support: FacultyTwinWorkflowSupport) -> None:
        super().__init__()
        self._support = support

    def execute(self, _: object) -> list[KnowledgeDocumentRecord]:
        return self._support.list_knowledge()


class SearchKnowledgeStage(MapFunction):
    def __init__(self, support: FacultyTwinWorkflowSupport) -> None:
        super().__init__()
        self._support = support

    def execute(self, data: KnowledgeSearchInput) -> KnowledgeSearchResponse:
        return self._support.search_knowledge(data.query, visitor_profile=data.visitor_profile)


class CreateBookingStage(MapFunction):
    def __init__(self, support: FacultyTwinWorkflowSupport) -> None:
        super().__init__()
        self._support = support

    def execute(self, data: BookingRequest) -> BookingResponse:
        return self._support.book_meeting(data)


class ListBookingsStage(MapFunction):
    def __init__(self, support: FacultyTwinWorkflowSupport) -> None:
        super().__init__()
        self._support = support

    def execute(self, status: str | None) -> list[BookingRecord]:
        return self._support.list_bookings(status=status)


class DigitalTwinService:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._llm_client = VllmChatClient(settings)
        self._knowledge_store = LocalKnowledgeStore(settings)
        self._conversation_store = NeuroMemConversationStore(settings)
        self._analytics_store = ConversationAnalyticsStore(settings, self._conversation_store)
        self._knowledge_gap_draft_store = KnowledgeGapDraftStore(settings)
        self._escalation_store = EscalationQueueStore(settings)
        self._follow_up_store = FollowUpQueueStore(settings)
        self._operations_task_state_store = OperationsTaskStateStore(settings)
        self._suggestion_store = SuggestionBoardStore(settings)
        self._user_store = UserAccountStore(settings)
        self._meeting_service = MeetingService(settings)
        self._email_notifier = BookingEmailNotifier(settings)
        self._runtime_manager = ServiceRuntimeManager(settings)
        self._sage_runtime_class = FlowNetEnvironment
        self._booking_workflows: dict[str, BookingWorkflowState] = {}
        self._normalize_published_gap_documents()

    def _normalize_published_gap_documents(self) -> None:
        changed = False
        published_drafts = [
            draft
            for draft in self._knowledge_gap_draft_store.list_drafts()
            if draft.status == "published" and draft.published_document_id
        ]

        for document in self._knowledge_store.list_documents():
            if not _is_legacy_gap_document(document.source_name, document.tags):
                continue
            draft = _match_gap_draft_for_document(document=document, drafts=published_drafts)
            formalized = (
                _build_published_gap_document(draft)
                if draft is not None
                else _build_published_gap_document_from_legacy(document)
            )
            if _document_matches_payload(document, formalized):
                continue
            self._knowledge_store.update_document(document.document_id, formalized, rebuild_indexes=False)
            changed = True

        if changed:
            self._knowledge_store.rebuild_indexes()

    async def answer(
        self,
        request: ChatRequest,
        admin_session_token: str | None = None,
        trace_callback: WorkflowTraceCallback | None = None,
    ) -> ChatResponse:
        admin_session_payload = decode_admin_session_token(admin_session_token, self._settings)
        support = self._build_support(
            admin_session_payload=admin_session_payload,
            trace_callback=trace_callback,
        )
        stages = [
            (BootstrapChatContextStage, support),
            (InteractionUnderstandingStage, support),
            (BookingPreparationStage, support),
            (BookingExecutionStage, support),
            (MemoryRetrievalStage, support),
            (KnowledgeRetrievalStage, support),
            (PromptBuildStage, support),
            (LlmAnswerStage, support),
            (MemoryPersistStage, support),
            (MemoryProfileConsolidationStage, support),
            (FollowUpPlanningStage, support),
            (ChatResponseRenderStage, support),
        ]
        return await asyncio.to_thread(
            self._run_pipeline,
            "faculty-twin-chat",
            [request],
            stages,
            "SAGE runtime completed without producing a chat response.",
        )

    def get_admin_session(self, session_token: str | None) -> AdminSessionResponse:
        support = self._build_support()
        return self._run_pipeline_blocking(
            "faculty-twin-admin-session-read",
            [AdminSessionTokenInput(session_token=session_token)],
            [(ReadAdminSessionStage, support)],
            "SAGE runtime completed without producing an admin session response.",
        )

    def require_admin_session(self, session_token: str | None) -> dict[str, Any]:
        support = self._build_support()
        return self._run_pipeline_blocking(
            "faculty-twin-admin-session-require",
            [AdminSessionTokenInput(session_token=session_token)],
            [(RequireAdminSessionStage, support)],
            "SAGE runtime completed without producing an admin authorization result.",
        )

    def login_admin(self, request: AdminLoginRequest) -> AdminLoginWorkflowResult:
        support = self._build_support()
        return self._run_pipeline_blocking(
            "faculty-twin-admin-login",
            [request],
            [(AdminLoginStage, support)],
            "SAGE runtime completed without producing an admin login result.",
        )

    def logout_admin(self) -> AdminSessionResponse:
        support = self._build_support()
        return self._run_pipeline_blocking(
            "faculty-twin-admin-logout",
            [_FLOWNET_TICK],
            [(AdminLogoutStage, support)],
            "SAGE runtime completed without producing an admin logout response.",
        )

    def get_user_session(self, session_token: str | None) -> UserSessionResponse:
        support = self._build_support()
        return self._run_pipeline_blocking(
            "faculty-twin-user-session-read",
            [UserSessionTokenInput(session_token=session_token)],
            [(ReadUserSessionStage, support)],
            "SAGE runtime completed without producing a user session response.",
        )

    def register_user(self, request: UserRegisterRequest) -> UserAuthWorkflowResult:
        support = self._build_support()
        return self._run_pipeline_blocking(
            "faculty-twin-user-register",
            [request],
            [(UserRegisterStage, support)],
            "SAGE runtime completed without producing a user registration result.",
        )

    def login_user(self, request: UserLoginRequest) -> UserAuthWorkflowResult:
        support = self._build_support()
        return self._run_pipeline_blocking(
            "faculty-twin-user-login",
            [request],
            [(UserLoginStage, support)],
            "SAGE runtime completed without producing a user login result.",
        )

    def logout_user(self) -> UserSessionResponse:
        support = self._build_support()
        return self._run_pipeline_blocking(
            "faculty-twin-user-logout",
            [_FLOWNET_TICK],
            [(UserLogoutStage, support)],
            "SAGE runtime completed without producing a user logout response.",
        )

    def add_knowledge(self, request: KnowledgeDocumentCreate) -> KnowledgeDocumentRecord:
        support = self._build_support()
        return self._run_pipeline_blocking(
            "faculty-twin-knowledge-add",
            [request],
            [(AddKnowledgeStage, support)],
            "SAGE runtime completed without producing a knowledge record.",
        )

    def list_knowledge(self) -> list[KnowledgeDocumentRecord]:
        support = self._build_support()
        return self._run_pipeline_blocking(
            "faculty-twin-knowledge-list",
            [_FLOWNET_TICK],
            [(ListKnowledgeStage, support)],
            "SAGE runtime completed without producing a knowledge document list.",
        )

    def search_knowledge(self, query: str, visitor_profile: str | None = None) -> KnowledgeSearchResponse:
        support = self._build_support()
        return self._run_pipeline_blocking(
            "faculty-twin-knowledge-search",
            [KnowledgeSearchInput(query=query, visitor_profile=visitor_profile)],
            [(SearchKnowledgeStage, support)],
            "SAGE runtime completed without producing a knowledge search response.",
        )

    def book_meeting(self, request: BookingRequest | dict[str, Any]) -> BookingResponse:
        normalized_request = request if isinstance(request, BookingRequest) else BookingRequest.model_validate(request)
        support = self._build_support()
        return self._run_pipeline_blocking(
            "faculty-twin-booking-create",
            [normalized_request],
            [(CreateBookingStage, support)],
            "SAGE runtime completed without producing a booking response.",
        )

    def list_bookings(self, status: str | None = None) -> list[BookingRecord]:
        support = self._build_support()
        return self._run_pipeline_blocking(
            "faculty-twin-booking-list",
            [status],
            [(ListBookingsStage, support)],
            "SAGE runtime completed without producing a booking list.",
        )

    def list_memory_profiles(
        self,
        *,
        category: str | None = None,
        student_query: str | None = None,
        limit: int = 50,
    ) -> MemoryProfileListResponse:
        return self._build_support().list_memory_profiles(
            category=category,
            student_query=student_query,
            limit=limit,
        )

    def submit_chat_feedback(self, request: ChatFeedbackRequest | dict[str, Any]) -> ChatFeedbackResponse:
        normalized_request = (
            request if isinstance(request, ChatFeedbackRequest) else ChatFeedbackRequest.model_validate(request)
        )
        return self._build_support().submit_chat_feedback(normalized_request)

    def submit_anonymous_suggestion(
        self,
        request: AnonymousSuggestionCreate | dict[str, Any],
        admin_session_token: str | None = None,
    ) -> AnonymousSuggestionRecord:
        normalized_request = (
            request if isinstance(request, AnonymousSuggestionCreate) else AnonymousSuggestionCreate.model_validate(request)
        )
        record = self._build_support().submit_anonymous_suggestion(normalized_request)
        return self._mask_suggestion_record(record, admin_session_token=admin_session_token)

    def list_anonymous_suggestions(
        self,
        *,
        limit: int = 50,
        admin_session_token: str | None = None,
    ) -> list[AnonymousSuggestionRecord]:
        records = self._build_support().list_anonymous_suggestions(limit=limit)
        return [
            self._mask_suggestion_record(record, admin_session_token=admin_session_token)
            for record in records
        ]

    def _mask_suggestion_record(
        self,
        record: AnonymousSuggestionRecord,
        *,
        admin_session_token: str | None = None,
    ) -> AnonymousSuggestionRecord:
        if admin_session_token and self.get_admin_session(admin_session_token).is_admin:
            return record
        return record.model_copy(update={"message": "***"})

    def get_question_analytics_report(self, *, days: int = 7) -> QuestionAnalyticsReportResponse:
        return self._build_support().get_question_analytics_report(days=days)

    def _build_student_operations_profiles(self, *, days: int, limit: int) -> list[StudentOperationsProfile]:
        profiles = self._conversation_store.list_profiles(limit=1000)
        if not profiles:
            return []

        window_start = datetime.now(UTC) - timedelta(days=days)
        recent_records = self._conversation_store.list_records(since=window_start)
        records_by_student: dict[str, list[ConversationMemoryRecord]] = {}
        for record in recent_records:
            student_key = self._student_operations_key(record.student_name, record.student_email)
            if student_key is None:
                continue
            records_by_student.setdefault(student_key, []).append(record)

        profiles_by_student: dict[str, list[ProfileMemoryRecord]] = {}
        for profile in profiles:
            profiles_by_student.setdefault(profile.student_key, []).append(profile)

        student_profiles: list[StudentOperationsProfile] = []
        for student_key, student_profile_records in profiles_by_student.items():
            student_profile_records.sort(key=lambda item: item.updated_at, reverse=True)
            records = sorted(records_by_student.get(student_key, []), key=lambda item: item.created_at, reverse=True)
            categories = sorted({profile.category for profile in student_profile_records})
            latest_profile_at = student_profile_records[0].updated_at
            latest_interaction_at = records[0].created_at if records else None
            representative = student_profile_records[0]
            student_profiles.append(
                StudentOperationsProfile(
                    student_key=student_key,
                    student_name=representative.student_name,
                    student_email=representative.student_email,
                    segment=self._student_operations_segment(
                        categories=categories,
                        interaction_count=len(records),
                    ),
                    profile_count=len(student_profile_records),
                    interaction_count=len(records),
                    categories=categories,
                    recent_questions=[record.question for record in records[:3]],
                    key_summaries=[
                        MemoryProfileRecordResponse(
                            profile_id=profile.profile_id,
                            student_key=profile.student_key,
                            student_name=profile.student_name,
                            student_email=profile.student_email,
                            category=profile.category,
                            summary=profile.summary,
                            evidence=profile.evidence,
                            updated_at=profile.updated_at,
                        )
                        for profile in student_profile_records[:3]
                    ],
                    suggested_next_action=self._student_operations_next_action(
                        categories=categories,
                        interaction_count=len(records),
                    ),
                    latest_profile_at=latest_profile_at,
                    latest_interaction_at=latest_interaction_at,
                )
            )

        student_profiles.sort(
            key=lambda item: item.latest_interaction_at or item.latest_profile_at,
            reverse=True,
        )
        return student_profiles[: max(1, limit)]

    def _student_operations_key(self, student_name: str, student_email: str | None) -> str | None:
        if student_email:
            return student_email.strip().lower()
        normalized_name = student_name.strip().lower()
        if not normalized_name or normalized_name == "guest":
            return None
        return normalized_name

    def _student_operations_segment(self, *, categories: list[str], interaction_count: int) -> str:
        if interaction_count >= 3:
            return "高互动学生"
        if "booking_preference" in categories:
            return "预约跟进"
        if "collaboration_preference" in categories:
            return "协作准备"
        if "recent_topic" in categories:
            return "持续关注"
        return "基础画像"

    def _student_operations_next_action(self, *, categories: list[str], interaction_count: int) -> str:
        if "booking_preference" in categories:
            return "复核预约偏好，必要时主动补充会前准备说明。"
        if "collaboration_preference" in categories:
            return "下次回复优先给出 agenda、blocker 和材料清单。"
        if interaction_count >= 3:
            return "检查近期高频问题，判断是否需要补充知识库或人工跟进。"
        if "recent_topic" in categories:
            return "保留近期关注主题，后续回答时优先复用相关上下文。"
        return "暂无额外动作，继续观察后续交互。"

    def _build_operational_tasks(self, *, limit: int) -> list[OperationsTaskItem]:
        now = datetime.now(UTC)
        tasks: list[OperationsTaskItem] = []

        for booking in self._meeting_service.list_bookings(status="待确认"):
            tasks.append(
                self._with_operations_task_state(
                    OperationsTaskItem(
                        task_key=f"booking:{booking.booking_id}",
                        task_type="booking_review",
                        title=f"预约审核｜{booking.topic}",
                        detail=f"{booking.student_name} 申请 {booking.start_at.astimezone(UTC).strftime('%Y-%m-%d %H:%M UTC')} 的讨论。",
                        source_status=booking.status,
                        operations_status="open",
                        priority=80,
                        action_url="/bookings",
                        student_name=booking.student_name,
                        student_email=booking.student_email,
                        due_at=booking.start_at,
                    )
                )
            )

        for draft in self._knowledge_gap_draft_store.list_drafts():
            if draft.status == "published":
                continue
            tasks.append(
                self._with_operations_task_state(
                    OperationsTaskItem(
                        task_key=f"gap_draft:{draft.draft_id}",
                        task_type="knowledge_gap_draft",
                        title=draft.title,
                        detail=draft.suggested_action,
                        source_status=draft.status,
                        operations_status="open",
                        priority=55,
                        action_url="/analytics/questions/gap-drafts",
                        created_at=draft.updated_at,
                    )
                )
            )

        for escalation in self._escalation_store.list_requests(status="待处理"):
            tasks.append(
                self._with_operations_task_state(
                    OperationsTaskItem(
                        task_key=f"escalation:{escalation.escalation_id}",
                        task_type="human_handoff",
                        title=f"人工处理｜{_format_escalation_route_label(escalation.route)}",
                        detail=escalation.reason or escalation.question,
                        source_status=escalation.status,
                        operations_status="open",
                        priority=95,
                        action_url="/escalations",
                        student_name=escalation.student_name,
                        student_email=escalation.student_email,
                        created_at=escalation.created_at,
                    )
                )
            )

        for follow_up in self._follow_up_store.list_actions(status="queued"):
            is_due = follow_up.due_at is None or follow_up.due_at <= now
            tasks.append(
                self._with_operations_task_state(
                    OperationsTaskItem(
                        task_key=f"follow_up:{follow_up.action_id}",
                        task_type="follow_up",
                        title=follow_up.title,
                        detail=follow_up.detail,
                        source_status=follow_up.status,
                        operations_status="open",
                        priority=75 if is_due else 60,
                        action_url="/follow-ups",
                        student_name=follow_up.student_name,
                        student_email=follow_up.student_email,
                        created_at=follow_up.created_at,
                        due_at=follow_up.due_at,
                    )
                )
            )

        for suggestion in self._suggestion_store.list_suggestions(limit=limit):
            tasks.append(
                self._with_operations_task_state(
                    OperationsTaskItem(
                        task_key=f"suggestion:{suggestion.suggestion_id}",
                        task_type="anonymous_suggestion",
                        title=suggestion.category or "匿名留言",
                        detail=suggestion.message,
                        source_status="new",
                        operations_status="open",
                        priority=35,
                        action_url="/suggestions",
                        created_at=suggestion.created_at,
                    )
                )
            )

        tasks.sort(
            key=lambda task: (
                1 if task.operations_status == "in_progress" else 0,
                task.priority,
                task.due_at or task.created_at or datetime.min.replace(tzinfo=UTC),
            ),
            reverse=True,
        )
        return tasks[: max(1, limit)]

    def _with_operations_task_state(self, task: OperationsTaskItem) -> OperationsTaskItem:
        state = self._operations_task_state_store.get_state(task.task_key)
        if state is None:
            return task
        return task.model_copy(
            update={
                "operations_status": state.status,
                "assigned_to": state.assigned_to,
                "note": state.note,
            }
        )

    def update_operations_task_state(
        self,
        task_key: str,
        request: OperationsTaskStateUpdateRequest | dict[str, Any],
    ) -> OperationsTaskStateRecord:
        normalized = (
            request
            if isinstance(request, OperationsTaskStateUpdateRequest)
            else OperationsTaskStateUpdateRequest.model_validate(request)
        )
        return self._operations_task_state_store.update_state(task_key, normalized)

    def get_operations_overview(self, *, days: int = 7) -> OperationsOverviewResponse:
        analytics = self.get_question_analytics_report(days=days)
        bookings = self._meeting_service.list_bookings()
        gap_drafts = self._knowledge_gap_draft_store.list_drafts()
        escalations = self._escalation_store.list_requests()
        follow_ups = self._follow_up_store.list_actions()
        suggestion_count = self._suggestion_store.count_suggestions()
        health = self.health()

        pending_bookings = [booking for booking in bookings if booking.status == "待确认"]
        open_gap_drafts = [draft for draft in gap_drafts if draft.status != "published"]
        open_escalations = [item for item in escalations if item.status == "待处理"]
        queued_follow_ups = [item for item in follow_ups if item.status == "queued"]

        return OperationsOverviewResponse(
            generated_at=datetime.now(UTC),
            window_days=days,
            health=health,
            totals={
                "bookings": len(bookings),
                "knowledge_documents": _health_int(health, "knowledge_documents"),
                "conversation_records": _health_int(health, "conversation_memory_records"),
                "memory_profiles": _health_int(health, "conversation_memory_profiles"),
                "student_profiles": len({profile.student_key for profile in self._conversation_store.list_profiles(limit=1000)}),
                "feedback_records": _health_int(health, "conversation_feedback_records"),
                "suggestions": suggestion_count,
            },
            queues=[
                OperationsQueueSummary(
                    queue_key="booking_review",
                    title="预约审核",
                    open_count=len(pending_bookings),
                    total_count=len(bookings),
                    action_url="/bookings",
                ),
                OperationsQueueSummary(
                    queue_key="knowledge_gap_drafts",
                    title="知识缺口草稿",
                    open_count=len(open_gap_drafts),
                    total_count=len(gap_drafts),
                    action_url="/analytics/questions/gap-drafts",
                ),
                OperationsQueueSummary(
                    queue_key="human_handoff",
                    title="人工处理队列",
                    open_count=len(open_escalations),
                    total_count=len(escalations),
                    action_url="/escalations",
                ),
                OperationsQueueSummary(
                    queue_key="follow_ups",
                    title="后续动作",
                    open_count=len(queued_follow_ups),
                    total_count=len(follow_ups),
                    action_url="/follow-ups",
                ),
                OperationsQueueSummary(
                    queue_key="anonymous_suggestions",
                    title="匿名留言",
                    open_count=suggestion_count,
                    total_count=suggestion_count,
                    action_url="/suggestions",
                ),
            ],
            question_analytics=analytics.overview,
        )

    def get_operations_workbench(self, *, days: int = 7, limit: int = 10) -> OperationsWorkbenchResponse:
        return OperationsWorkbenchResponse(
            overview=self.get_operations_overview(days=days),
            operational_tasks=self._build_operational_tasks(limit=limit),
            satisfaction=OperationsSatisfactionSummary(**self._analytics_store.build_satisfaction_report(days=days)),
            pending_bookings=self._meeting_service.list_bookings(status="待确认")[:limit],
            student_profiles=self._build_student_operations_profiles(days=days, limit=limit),
            knowledge_gap_drafts=self._knowledge_gap_draft_store.list_drafts()[:limit],
            escalations=self._escalation_store.list_requests(status="待处理")[:limit],
            follow_up_actions=self._follow_up_store.list_actions(status="queued")[:limit],
            anonymous_suggestions=self._suggestion_store.list_suggestions(limit=limit),
            question_analytics=self.get_question_analytics_report(days=days),
        )

    def create_knowledge_gap_draft(
        self,
        request: KnowledgeGapDraftCreateRequest | dict[str, Any],
    ) -> KnowledgeGapDraftRecordResponse:
        normalized_request = (
            request if isinstance(request, KnowledgeGapDraftCreateRequest) else KnowledgeGapDraftCreateRequest.model_validate(request)
        )
        return self._build_support().create_knowledge_gap_draft(normalized_request)

    def list_knowledge_gap_drafts(self) -> list[KnowledgeGapDraftRecordResponse]:
        return self._build_support().list_knowledge_gap_drafts()

    def publish_knowledge_gap_draft(self, draft_id: str) -> KnowledgeGapDraftRecordResponse:
        return self._build_support().publish_knowledge_gap_draft(draft_id)

    def list_escalations(
        self,
        *,
        status: str | None = None,
        route: str | None = None,
    ) -> list[EscalationRecord]:
        return self._build_support().list_escalations(status=status, route=route)

    def resolve_escalation(
        self,
        escalation_id: str,
        decision: EscalationDecisionRequest | dict[str, Any] | None = None,
    ) -> EscalationRecord:
        return self._build_support().resolve_escalation(escalation_id, decision)

    def list_follow_up_actions(
        self,
        *,
        status: str | None = None,
        action_type: str | None = None,
    ) -> list[FollowUpQueueRecord]:
        return self._build_support().list_follow_up_actions(status=status, action_type=action_type)

    def dispatch_due_follow_ups(self) -> FollowUpDispatchResponse:
        return self._build_support().dispatch_due_follow_ups()

    def confirm_booking(self, booking_id: str) -> BookingResponse:
        return self._build_support().confirm_booking(booking_id)

    def reject_booking(
        self,
        booking_id: str,
        decision: BookingDecisionRequest | dict[str, Any] | None = None,
    ) -> BookingResponse:
        normalized = (
            BookingDecisionRequest.model_validate(decision)
            if decision is not None
            else BookingDecisionRequest()
        )
        return self._build_support().reject_booking(
            booking_id,
            rejection_reason=normalized.rejection_reason,
        )

    def get_availability_schedule(self) -> AvailabilitySchedule:
        return self._meeting_service.get_availability_schedule()

    def get_previous_week_availability_template(self, week_of: date | None = None) -> AvailabilitySchedule:
        return self._meeting_service.get_previous_week_availability_template(week_of)

    def update_availability_schedule(self, schedule: AvailabilitySchedule) -> AvailabilitySchedule:
        return self._meeting_service.update_availability_schedule(schedule)

    def get_managed_services(self) -> ServiceControlResponse:
        return self._runtime_manager.status()

    def control_managed_services(self, action: str) -> ServiceControlResponse:
        if action == "status":
            return self._runtime_manager.status()
        if action == "start":
            return self._runtime_manager.start()
        if action == "stop":
            return self._runtime_manager.stop()
        if action == "restart":
            return self._runtime_manager.restart()
        raise ValueError(f"Unsupported service action: {action}")

    def health(self) -> dict[str, str]:
        due_follow_ups = self._follow_up_store.list_due_actions()
        payload = {
            "status": "ok",
            "owner_name": self._settings.owner_name,
            "owner_role": self._settings.owner_role,
            "homepage_public_url": self._settings.homepage_public_url,
            "model_name": self._settings.model_name,
            "sage_runtime": self._describe_sage_runtime(),
            "knowledge_backend": self._knowledge_store.backend_name(),
            "knowledge_embedding_backend": self._knowledge_store.embedding_backend_name(),
            "knowledge_documents": str(self._knowledge_store.count_documents()),
            "conversation_memory_backend": self._conversation_store.backend_name(),
            "conversation_memory_records": str(self._conversation_store.count_records()),
            "conversation_memory_profiles": str(self._conversation_store.count_profiles()),
            "conversation_feedback_records": str(self._analytics_store.count_feedback()),
            "registered_user_accounts": str(self._user_store.count_users()),
            "knowledge_gap_drafts": str(self._knowledge_gap_draft_store.count_drafts()),
            "escalation_queue_records": str(self._escalation_store.count_records()),
            "follow_up_queue_records": str(self._follow_up_store.count_actions()),
            "suggestion_board_records": str(self._suggestion_store.count_suggestions()),
            "follow_up_dispatch_sent": "0",
            "follow_up_dispatch_due": str(len(due_follow_ups)),
            "chat_pipeline_stages": str(_CHAT_PIPELINE_STAGE_COUNT),
            "admin_pipeline_stages": "4",
        }
        runtime_snapshot = getattr(self._llm_client, "runtime_snapshot", None)
        if callable(runtime_snapshot):
            payload.update(runtime_snapshot())
        else:
            payload.update(
                {
                    "llm_status": "not_checked",
                    "llm_request_count": "0",
                    "llm_success_count": "0",
                    "llm_error_count": "0",
                    "llm_cache_hit_count": "0",
                    "llm_cache_entries": "0",
                    "llm_last_error": "",
                    "llm_last_request_at": "",
                    "llm_last_success_at": "",
                    "llm_last_error_at": "",
                }
            )
        return payload

    async def aclose(self) -> None:
        await self._llm_client.aclose()

    def _describe_sage_runtime(self) -> str:
        return self._sage_runtime_class.__name__

    def _build_student_prompt(
        self,
        request: ChatRequest,
        knowledge_hits: list[KnowledgeSearchHit],
        memory_hits: list[ConversationMemoryHit] | None = None,
        interaction_intent: InteractionIntent | None = None,
    ) -> str:
        return self._build_support()._build_student_prompt(request, knowledge_hits, memory_hits, interaction_intent)

    def _build_support(
        self,
        admin_session_payload: dict[str, Any] | None = None,
        trace_callback: WorkflowTraceCallback | None = None,
    ) -> FacultyTwinWorkflowSupport:
        return FacultyTwinWorkflowSupport(
            self._settings,
            self._booking_workflows,
            self._knowledge_store,
            self._conversation_store,
            self._analytics_store,
            self._knowledge_gap_draft_store,
            self._escalation_store,
            self._follow_up_store,
            self._suggestion_store,
            self._user_store,
            self._meeting_service,
            self._llm_client,
            self._email_notifier,
            admin_session_payload=admin_session_payload,
            trace_callback=trace_callback,
        )

    def _run_pipeline(
        self,
        environment_name: str,
        source_items: list[Any],
        stages: list[tuple[type[MapFunction], FacultyTwinWorkflowSupport]],
        empty_result_message: str,
    ) -> Any:
        env = FlowNetEnvironment(environment_name)
        results: list[Any] = []
        stream = env.from_batch(source_items)
        for stage_class, support in stages:
            stream = stream.map(stage_class, support)
        stream.sink(ResultCollector, results)
        env.submit(autostop=True)

        if not results:
            raise RuntimeError(empty_result_message)
        return results[-1]

    def _run_pipeline_blocking(
        self,
        environment_name: str,
        source_items: list[Any],
        stages: list[tuple[type[MapFunction], FacultyTwinWorkflowSupport]],
        empty_result_message: str,
    ) -> Any:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return self._run_pipeline(
                environment_name,
                source_items,
                stages,
                empty_result_message,
            )

        result_holder: dict[str, Any] = {}
        error_holder: list[BaseException] = []

        def runner() -> None:
            try:
                result_holder["value"] = self._run_pipeline(
                    environment_name,
                    source_items,
                    stages,
                    empty_result_message,
                )
            except BaseException as exc:  # noqa: BLE001
                error_holder.append(exc)

        thread = threading.Thread(target=runner, daemon=False)
        thread.start()
        thread.join()

        if error_holder:
            raise error_holder[0]
        return result_holder["value"]


def _document_matches_payload(
    document: KnowledgeDocumentRecord,
    payload: KnowledgeDocumentCreate,
) -> bool:
    return (
        document.title == payload.title
        and document.content == payload.content
        and document.tags == payload.tags
        and document.source_name == payload.source_name
    )


def _health_int(health: dict[str, str], key: str) -> int:
    try:
        return int(health.get(key, "0"))
    except ValueError:
        return 0


def _format_escalation_route_label(route: str) -> str:
    if route == "human_handoff":
        return "人工接管"
    if route == "review_queue":
        return "复核队列"
    return route


def _is_legacy_gap_document(source_name: str | None, tags: list[str]) -> bool:
    normalized_tags = {tag.strip().lower() for tag in tags}
    return (
        bool(source_name and (source_name.startswith("analytics-gap:") or source_name.startswith("knowledge-gap:")))
        or "faq-draft" in normalized_tags
        or "draft" in normalized_tags
        or "knowledge-gap" in normalized_tags
    )


def _match_gap_draft_for_document(
    *,
    document: KnowledgeDocumentRecord,
    drafts: Iterable[KnowledgeGapDraftRecordResponse],
) -> KnowledgeGapDraftRecordResponse | None:
    source_name = document.source_name or ""
    cluster_id = source_name.split(":", 1)[1] if source_name.startswith("analytics-gap:") and ":" in source_name else None
    for draft in drafts:
        if draft.published_document_id == document.document_id:
            return draft
        if cluster_id and draft.cluster_id == cluster_id:
            return draft
    return None


def _build_published_gap_document(draft: KnowledgeGapDraftRecordResponse) -> KnowledgeDocumentCreate:
    title = _format_gap_document_title(
        label=draft.label,
        interaction_domain=draft.interaction_domain,
        sample_questions=draft.sample_questions,
    )
    return KnowledgeDocumentCreate(
        title=title,
        content=_build_gap_document_content(draft),
        tags=_normalize_gap_document_tags(draft.tags, draft.interaction_domain),
        source_name=_build_gap_document_source_name(
            title=title,
            interaction_domain=draft.interaction_domain,
        ),
    )


def _build_published_gap_document_from_legacy(document: KnowledgeDocumentRecord) -> KnowledgeDocumentCreate:
    parsed = _parse_legacy_gap_document(document)
    title = _format_gap_document_title(
        label=parsed["label"],
        interaction_domain=parsed["interaction_domain"],
        sample_questions=parsed["sample_questions"],
    )
    return KnowledgeDocumentCreate(
        title=title,
        content=_build_gap_document_content_from_parts(
            interaction_domain=parsed["interaction_domain"],
            sample_questions=parsed["sample_questions"],
            suggested_action=parsed["suggested_action"],
            reason=parsed["reason"],
        ),
        tags=_normalize_gap_document_tags(document.tags, parsed["interaction_domain"]),
        source_name=_build_gap_document_source_name(
            title=title,
            interaction_domain=parsed["interaction_domain"],
        ),
    )


def _build_gap_document_source_name(*, title: str, interaction_domain: str) -> str:
    normalized_title = re.sub(r"\s+", " ", str(title or "").strip().lower()).strip(" ：:|｜")
    if not normalized_title:
        normalized_title = _domain_label(interaction_domain).strip().lower()
    digest = hashlib.sha1(f"{interaction_domain}|{normalized_title}".encode("utf-8")).hexdigest()[:16]
    return f"knowledge-gap:{interaction_domain}:{digest}"


def _format_gap_document_title(
    *,
    label: str,
    interaction_domain: str,
    sample_questions: list[str],
) -> str:
    cleaned = label.replace("FAQ草稿｜", "").replace("FAQ草稿 |", "").strip(" ：:|｜")
    cleaned = re.sub(r"^(常见问题[:：]\s*)+", "", cleaned).strip(" ：:|｜")
    if "｜" in cleaned:
        cleaned = cleaned.split("｜", 1)[-1].strip()
    if _looks_like_fragmented_gap_text(cleaned) or len(cleaned) < 4:
        cleaned = _question_to_topic(sample_questions[0]) if sample_questions else ""
    if not cleaned:
        cleaned = _domain_label(interaction_domain)
    return f"常见问题：{_summarize_text(cleaned, limit=24).rstrip('。')}"


def _build_gap_document_content(draft: KnowledgeGapDraftRecordResponse) -> str:
    return _build_gap_document_content_from_parts(
        interaction_domain=draft.interaction_domain,
        sample_questions=draft.sample_questions,
        suggested_action=draft.suggested_action,
        reason=draft.reason,
    )


def _build_gap_document_content_from_parts(
    *,
    interaction_domain: str,
    sample_questions: list[str],
    suggested_action: str,
    reason: str,
) -> str:
    question_lines = [
        f"- {str(question).strip()}"
        for question in sample_questions[:3]
        if str(question).strip()
    ]
    if not question_lines:
        question_lines = ["- 暂无代表性问题样例"]
    questions_block = "\n".join(question_lines)
    return (
        f"主题：{_domain_label(interaction_domain)}\n"
        "适用问题：\n"
        f"{questions_block}\n\n"
        f"标准说明：{_summarize_text(suggested_action, limit=160)}\n"
        f"补充背景：{_summarize_text(reason, limit=120)}\n"
        "使用边界：涉及老师本人审批、例外政策或个性化承诺时，需要人工确认。"
    )


def _parse_legacy_gap_document(document: KnowledgeDocumentRecord) -> dict[str, str | list[str]]:
    source_name = document.source_name or ""
    cluster_id = source_name.split(":", 1)[1] if source_name.startswith("analytics-gap:") and ":" in source_name else document.document_id
    interaction_domain = next((tag for tag in document.tags if tag not in {"analytics-gap", "draft", "faq-draft"}), "general")
    sample_questions = re.findall(r"^-\s+(.+)$", document.content, re.MULTILINE)
    suggested_action = _extract_prefixed_field(document.content, "建议动作")
    reason = _extract_prefixed_field(document.content, "为何需要补充")
    label = document.title.replace("FAQ草稿｜", "").strip()
    return {
        "cluster_id": cluster_id,
        "interaction_domain": str(interaction_domain),
        "sample_questions": sample_questions,
        "suggested_action": suggested_action or "补充与当前问题直接相关的标准说明、准备清单和边界提醒。",
        "reason": reason or "近期多次出现相似提问，现有标准材料还不够集中。",
        "label": label,
    }


def _extract_prefixed_field(content: str, prefix: str) -> str:
    matched = re.search(rf"{re.escape(prefix)}[:：]\s*(.+)", content)
    return matched.group(1).strip() if matched else ""


def _normalize_gap_document_tags(tags: list[str], interaction_domain: str) -> list[str]:
    normalized: list[str] = []
    for tag in tags:
        cleaned = tag.strip().lower()
        if not cleaned or cleaned in {"draft", "faq-draft", "analytics-gap"}:
            continue
        if cleaned not in normalized:
            normalized.append(cleaned)
    for tag in (interaction_domain.strip().lower(), "faq", "knowledge-gap"):
        if tag and tag not in normalized:
            normalized.append(tag)
    return normalized


def _domain_label(interaction_domain: str) -> str:
    return {
        "research": "科研指导",
        "teaching": "课程答疑",
        "advising": "指导建议",
        "booking": "预约说明",
        "general": "常见说明",
    }.get(interaction_domain, "常见说明")


def _looks_like_fragmented_gap_text(text: str) -> bool:
    normalized = _normalize_whitespace(text).strip(" ：:|｜")
    if not normalized:
        return True
    pieces = [piece.strip() for piece in text.split("/") if piece.strip()]
    if len(pieces) >= 2 and all(len(piece) <= 3 for piece in pieces):
        return True
    if normalized.endswith(("…", "...")):
        generic_fragment = normalized.removesuffix("…").removesuffix("...")
        if len(generic_fragment) <= 6 and re.fullmatch(r"[常见问题说明预约指导课程科研答疑管理服务登录注册账号设置信息维护]+", generic_fragment):
            return True
    return False


def _question_to_topic(question: str) -> str:
    normalized = str(question).strip().strip("？?。！!")
    return _summarize_text(normalized, limit=24)


def _extract_numbered_highlights(text: str) -> list[str]:
    matches = re.findall(r"\d+[\.、]\s*(.+?)(?=\s*\d+[\.、]\s*|$)", text)
    highlights: list[str] = []
    for match in matches:
        item = _summarize_text(_normalize_whitespace(match), limit=24).rstrip("。")
        if item:
            highlights.append(item)
    return highlights


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _summarize_text(text: str, *, limit: int) -> str:
    normalized = _normalize_whitespace(text)
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip("，、；： ") + "…"
