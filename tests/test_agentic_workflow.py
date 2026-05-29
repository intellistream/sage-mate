import asyncio
from datetime import datetime, timedelta
from pathlib import Path

from sage_faculty_twin.config import AppSettings
from sage_faculty_twin.config import settings
from sage_faculty_twin.models import ChatRequest, InteractionIntent, KnowledgeDocumentCreate
from sage_faculty_twin.notifications import BookingNotificationError
from sage_faculty_twin.service import DigitalTwinService


class FailingLLMClient:
    def classify_booking_intent_sync(self, question: str, course_context: str | None = None) -> bool:
        return True

    async def classify_booking_intent(self, question: str, course_context: str | None = None) -> bool:
        return True

    def answer_question_sync(self, system_prompt: str, user_prompt: str) -> str:
        raise AssertionError("booking workflow should not call the LLM")

    async def answer_question(self, system_prompt: str, user_prompt: str) -> str:
        raise AssertionError("booking workflow should not call the LLM")


class IntentAwareLLMClient:
    def __init__(self, booking_intent: bool, answer: str) -> None:
        self._booking_intent = booking_intent
        self._answer = answer

    def classify_interaction_intent_sync(
        self,
        question: str,
        course_context: str | None = None,
    ) -> InteractionIntent:
        if self._booking_intent:
            return InteractionIntent(
                action="book_meeting",
                domain="booking",
                retrieval_scopes=["meeting_policy"],
                exclude_scopes=["courseware", "publications"],
                decision_mode="review_queue",
                confidence=0.95,
            )
        return InteractionIntent(
            action="answer",
            domain="advising",
            retrieval_scopes=["preparation", "meeting_policy", "profile"],
            exclude_scopes=["courseware"],
            decision_mode="advise_only",
            confidence=0.95,
        )

    async def classify_interaction_intent(
        self,
        question: str,
        course_context: str | None = None,
    ) -> InteractionIntent:
        return self.classify_interaction_intent_sync(question, course_context)

    def classify_booking_intent_sync(self, question: str, course_context: str | None = None) -> bool:
        return self._booking_intent

    async def classify_booking_intent(self, question: str, course_context: str | None = None) -> bool:
        return self._booking_intent

    def answer_question_sync(self, system_prompt: str, user_prompt: str) -> str:
        return self._answer

    async def answer_question(self, system_prompt: str, user_prompt: str) -> str:
        return self._answer


class RecordingLLMClient(IntentAwareLLMClient):
    def __init__(self, booking_intent: bool, answer: str) -> None:
        super().__init__(booking_intent=booking_intent, answer=answer)
        self.prompts: list[str] = []

    def answer_question_sync(self, system_prompt: str, user_prompt: str) -> str:
        self.prompts.append(user_prompt)
        return super().answer_question_sync(system_prompt, user_prompt)


class KeywordIntentLLMClient(RecordingLLMClient):
    def __init__(self, answer: str) -> None:
        super().__init__(booking_intent=False, answer=answer)

    def classify_interaction_intent_sync(
        self,
        question: str,
        course_context: str | None = None,
    ) -> InteractionIntent:
        if self.classify_booking_intent_sync(question, course_context):
            return InteractionIntent(
                action="book_meeting",
                domain="booking",
                retrieval_scopes=["meeting_policy"],
                exclude_scopes=["courseware", "publications"],
                decision_mode="review_queue",
                confidence=0.95,
            )
        return InteractionIntent(
            action="answer",
            domain="advising",
            retrieval_scopes=["preparation", "meeting_policy", "profile"],
            exclude_scopes=["courseware"],
            decision_mode="advise_only",
            confidence=0.95,
        )

    async def classify_interaction_intent(
        self,
        question: str,
        course_context: str | None = None,
    ) -> InteractionIntent:
        return self.classify_interaction_intent_sync(question, course_context)

    def classify_booking_intent_sync(self, question: str, course_context: str | None = None) -> bool:
        lowered = question.lower()
        booking_keywords = ("请帮我预约", "帮我预约", "请预约", "预定", "约时间", "book", "schedule a meeting")
        return any(keyword in lowered for keyword in booking_keywords)

    async def classify_booking_intent(self, question: str, course_context: str | None = None) -> bool:
        return self.classify_booking_intent_sync(question, course_context)


class RecordingNotifier:
    def __init__(self) -> None:
        self.request_bookings = []
        self.approved_bookings = []
        self.rejected_bookings = []
        self.follow_up_emails = []

    def send_booking_request_notification(self, booking) -> str:
        self.request_bookings.append(booking)
        return settings.booking_notification_email

    def send_booking_approved_notification(self, booking) -> str:
        self.approved_bookings.append(booking)
        return booking.student_email

    def send_booking_rejected_notification(self, booking) -> str:
        self.rejected_bookings.append(booking)
        return booking.student_email

    def send_follow_up_email(self, recipient: str, subject: str, lines: list[str]) -> str:
        self.follow_up_emails.append({"recipient": recipient, "subject": subject, "lines": list(lines)})
        return recipient


class FailingNotifier:
    def send_booking_request_notification(self, booking) -> str:
        raise BookingNotificationError("SMTP 未配置")

    def send_booking_approved_notification(self, booking) -> str:
        raise BookingNotificationError("SMTP 未配置")

    def send_booking_rejected_notification(self, booking) -> str:
        raise BookingNotificationError("SMTP 未配置")


def test_chat_books_meeting_when_details_are_complete(tmp_path: Path) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path)
    service = DigitalTwinService(settings)
    service._llm_client = FailingLLMClient()
    notifier = RecordingNotifier()
    service._email_notifier = notifier

    response = asyncio.run(
        service.answer(
            ChatRequest(
                student_name="Alice",
                student_email="alice@example.com",
                course_context="科研指导",
                conversation_id="conv-complete",
                question="请帮我预约 2026-05-26 15:00 讨论论文进展",
            )
        )
    )

    assert response.workflow_action == "book_meeting"
    assert response.booking_result is not None
    assert response.booking_result.accepted is True
    assert response.booking_result.booking is not None
    assert response.booking_result.booking.topic == "论文进展"
    assert response.booking_result.booking.status == "待确认"
    assert response.booking_result.notification is not None
    assert response.booking_result.notification.status == "sent"
    assert response.booking_result.notification.recipient == settings.booking_notification_email
    assert [step.key for step in response.workflow_trace] == [
        "bootstrap",
        "interaction_understand",
        "booking_prepare",
        "booking_execute",
        "memory_retrieve",
        "knowledge_retrieve",
        "prompt_build",
        "llm_answer",
        "memory_persist",
        "memory_profile_consolidate",
        "follow_up_plan",
        "response_render",
    ]
    assert response.workflow_trace[2].status == "completed"
    assert all(step.duration_ms is not None for step in response.workflow_trace)
    assert response.workflow_trace[1].summary == "已识别当前交互意图：book_meeting/booking。"
    assert response.workflow_trace[2].summary == "预约字段已经齐备。"
    assert response.workflow_trace[3].summary == "预约申请已提交，等待管理员确认。"
    assert settings.booking_notification_email in response.workflow_trace[3].detail
    assert any(item.basis_label == "预约规则与时段" for item in response.answer_basis)
    assert any(item.source_label == "当前预约安排配置" for item in response.answer_basis)
    assert len(notifier.request_bookings) == 1
    assert settings.booking_notification_email in response.answer
    assert "待确认" in response.answer


def test_chat_books_meeting_with_chinese_relative_time(tmp_path: Path) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path)
    service = DigitalTwinService(settings)
    service._llm_client = FailingLLMClient()
    service._email_notifier = RecordingNotifier()

    response = asyncio.run(
        service.answer(
            ChatRequest(
                student_name="Alice",
                student_email="alice@example.com",
                course_context="数据库实验课",
                conversation_id="conv-cn-time",
                question="请帮我预约明天下午三点讨论数据库实验课报告。",
            )
        )
    )

    assert response.workflow_action == "book_meeting"
    assert response.pending_fields == []
    assert response.booking_result is not None
    assert response.booking_result.booking is not None
    booking = response.booking_result.booking
    assert booking.topic == "数据库实验课报告"
    assert booking.start_at.date() == (datetime.now() + timedelta(days=1)).date()
    assert booking.start_at.hour == 15
    assert booking.start_at.minute == 0
    assert booking.end_at.hour == 15
    assert booking.end_at.minute == 30


def test_admin_confirmation_sends_student_email(tmp_path: Path) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path)
    service = DigitalTwinService(settings)
    notifier = RecordingNotifier()
    service._email_notifier = notifier

    created = service.book_meeting(
        {
            "student_name": "Alice",
            "student_email": "alice@example.com",
            "topic": "论文进展",
            "preferred_start": "2026-05-26T15:00:00",
            "preferred_end": "2026-05-26T15:45:00",
        }
    )

    assert created.booking is not None
    assert created.notification is not None
    assert created.notification.status == "sent"
    assert created.notification.recipient == settings.booking_notification_email
    confirmed = service.confirm_booking(created.booking.booking_id)

    assert confirmed.accepted is True
    assert confirmed.booking is not None
    assert confirmed.booking.status == "已确认"
    assert confirmed.notification is not None
    assert confirmed.notification.status == "sent"
    assert confirmed.notification.recipient == "alice@example.com"
    assert len(notifier.approved_bookings) == 1
    assert "alice@example.com" in confirmed.message


def test_admin_rejection_sends_student_email(tmp_path: Path) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path)
    service = DigitalTwinService(settings)
    notifier = RecordingNotifier()
    service._email_notifier = notifier

    created = service.book_meeting(
        {
            "student_name": "Alice",
            "student_email": "alice@example.com",
            "topic": "论文进展",
            "preferred_start": "2026-05-26T15:00:00",
            "preferred_end": "2026-05-26T15:45:00",
        }
    )

    assert created.booking is not None
    assert created.notification is not None
    assert created.notification.status == "sent"
    rejected = service.reject_booking(created.booking.booking_id)

    assert rejected.accepted is True
    assert rejected.booking is not None
    assert rejected.booking.status == "已拒绝"
    assert rejected.notification is not None
    assert rejected.notification.status == "sent"
    assert rejected.notification.recipient == "alice@example.com"
    assert len(notifier.rejected_bookings) == 1
    assert "alice@example.com" in rejected.message


def test_admin_rejection_includes_reason_in_booking(tmp_path: Path) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path)
    service = DigitalTwinService(settings)
    notifier = RecordingNotifier()
    service._email_notifier = notifier

    created = service.book_meeting(
        {
            "student_name": "Alice",
            "student_email": "alice@example.com",
            "topic": "论文进展",
            "preferred_start": "2026-05-26T15:00:00",
            "preferred_end": "2026-05-26T15:45:00",
        }
    )

    assert created.booking is not None
    assert created.notification is not None
    rejected = service.reject_booking(
        created.booking.booking_id,
        {"rejection_reason": "这周安排已满，请改约下周。"},
    )

    assert rejected.accepted is True
    assert rejected.booking is not None
    assert rejected.booking.rejection_reason == "这周安排已满，请改约下周。"


def test_direct_booking_keeps_record_when_notification_fails(tmp_path: Path) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path)
    service = DigitalTwinService(settings)
    service._email_notifier = FailingNotifier()

    created = service.book_meeting(
        {
            "student_name": "Alice",
            "student_email": "alice@example.com",
            "topic": "论文进展",
            "preferred_start": "2026-05-26T15:00:00",
            "preferred_end": "2026-05-26T15:45:00",
        }
    )

    assert created.accepted is True
    assert created.booking is not None
    assert created.booking.status == "待确认"
    assert created.notification is not None
    assert created.notification.status == "failed"
    assert "SMTP 未配置" in created.notification.summary
    assert created.notification.detail is not None


def test_chat_collects_missing_booking_details_and_then_books(tmp_path: Path) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path)
    service = DigitalTwinService(settings)
    service._llm_client = FailingLLMClient()
    service._email_notifier = RecordingNotifier()

    first = asyncio.run(
        service.answer(
            ChatRequest(
                student_name="Alice",
                course_context="科研指导",
                conversation_id="conv-follow-up",
                question="请帮我预约 2026-05-26 15:00 讨论论文进展",
            )
        )
    )

    assert first.workflow_action == "collect_booking_details"
    assert first.pending_fields == ["student_email"]
    assert first.workflow_trace[1].key == "interaction_understand"
    assert first.workflow_trace[2].key == "booking_prepare"
    assert first.workflow_trace[4].key == "memory_retrieve"
    assert "邮箱" in first.workflow_trace[2].detail
    assert first.workflow_trace[2].duration_ms is not None
    assert first.workflow_trace[2].summary == "仍缺少：邮箱。"

    second = asyncio.run(
        service.answer(
            ChatRequest(
                student_name="Alice",
                course_context="科研指导",
                conversation_id="conv-follow-up",
                question="我的邮箱是 alice@example.com",
            )
        )
    )

    assert second.workflow_action == "book_meeting"
    assert second.booking_result is not None
    assert second.booking_result.accepted is True
    assert second.booking_result.booking is not None
    assert second.booking_result.booking.status == "待确认"
    assert second.workflow_trace[3].key == "booking_execute"
    assert second.workflow_trace[3].status == "completed"


def test_chat_booking_reports_notification_failure_without_rolling_back_booking(tmp_path: Path) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path)
    service = DigitalTwinService(settings)
    service._llm_client = FailingLLMClient()
    service._email_notifier = FailingNotifier()

    response = asyncio.run(
        service.answer(
            ChatRequest(
                student_name="Alice",
                student_email="alice@example.com",
                course_context="科研指导",
                conversation_id="conv-notify-fail",
                question="请帮我预约 2026-05-26 15:00 讨论论文进展",
            )
        )
    )

    assert response.workflow_action == "book_meeting"
    assert response.booking_result is not None
    assert response.booking_result.accepted is True
    assert response.booking_result.notification is not None
    assert response.booking_result.notification.status == "failed"
    assert "SMTP 未配置" in response.booking_result.notification.summary
    assert response.booking_result.notification.detail is not None
    assert "预约记录已经保存" in response.booking_result.notification.detail
    assert response.workflow_trace[3].summary == "预约申请已提交，但提醒邮件发送失败。"
    assert "邮件通知失败" in response.workflow_trace[3].detail
    assert "SMTP 未配置" in response.answer


def test_chat_uses_llm_intent_to_avoid_false_booking_positive(tmp_path: Path) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path)
    service = DigitalTwinService(settings)
    service._llm_client = IntentAwareLLMClient(
        booking_intent=False,
        answer="预约前建议先准备 agenda、当前 blocker 和你最想讨论的问题。",
    )

    response = asyncio.run(
        service.answer(
            ChatRequest(
                student_name="Alice",
                student_email="alice@example.com",
                course_context="科研指导",
                question="和老师约时间前，我应该先准备什么？",
            )
        )
    )

    assert response.workflow_action == "advise_only"
    assert response.decision_mode == "advise_only"
    assert response.pending_fields == []
    assert response.booking_result is None
    assert any(action.action_type == "todo_review" for action in response.follow_up_actions)
    assert any(action.action_type == "office_hour_recommendation" for action in response.follow_up_actions)
    assert "agenda" in response.answer
    assert response.workflow_trace[1].status == "completed"
    assert response.workflow_trace[2].status == "skipped"
    assert response.workflow_trace[3].status == "skipped"
    assert response.workflow_trace[4].key == "memory_retrieve"
    assert response.workflow_trace[5].key == "knowledge_retrieve"
    assert all(step.duration_ms is not None for step in response.workflow_trace)
    assert response.workflow_trace[1].summary == "已识别当前交互意图：answer/advising，仅提供建议。"
    assert response.workflow_trace[2].summary == "未进入预约流程。"


def test_chat_answers_office_hour_query_without_starting_booking_workflow(tmp_path: Path) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path)
    service = DigitalTwinService(settings)
    service._llm_client = IntentAwareLLMClient(
        booking_intent=True,
        answer="本周默认开放预约时间仍按工作日 09:00-18:00 处理；如果你想继续预约，再告诉我具体时间即可。",
    )

    response = asyncio.run(
        service.answer(
            ChatRequest(
                student_name="Alice",
                student_email="alice@example.com",
                course_context="科研指导",
                question="能否告诉我老师这周的 office hours？我想了解以便预约。",
            )
        )
    )

    assert response.workflow_action == "answer"
    assert response.pending_fields == []
    assert response.booking_result is None
    assert "09:00-18:00" in response.answer
    assert response.workflow_trace[1].summary == "已识别当前交互意图：answer/advising。"
    assert response.workflow_trace[2].summary == "未进入预约流程。"


def test_chat_emits_trace_steps_via_callback(tmp_path: Path) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path)
    service = DigitalTwinService(settings)
    service._llm_client = FailingLLMClient()
    emitted_steps = []

    response = asyncio.run(
        service.answer(
            ChatRequest(
                student_name="Alice",
                student_email="alice@example.com",
                course_context="科研指导",
                conversation_id="conv-callback",
                question="请帮我预约 2026-05-26 15:00 讨论论文进展",
            ),
            trace_callback=emitted_steps.append,
        )
    )

    assert [step.key for step in emitted_steps] == [step.key for step in response.workflow_trace]
    assert emitted_steps[0].summary == "已建立当前会话。"
    assert emitted_steps[-1].key == "response_render"
    assert any(step.key == "memory_profile_consolidate" for step in emitted_steps)


def test_chat_reuses_neuromem_conversation_memory_in_follow_up_prompt(tmp_path: Path) -> None:
    settings = AppSettings(
        knowledge_base_dir=tmp_path,
        conversation_memory_dir=tmp_path / "conversation-memory",
    )
    service = DigitalTwinService(settings)
    llm = RecordingLLMClient(booking_intent=False, answer="好的，我继续回答。")
    service._llm_client = llm

    asyncio.run(
        service.answer(
            ChatRequest(
                student_name="Alice",
                student_email="alice@example.com",
                course_context="科研指导",
                conversation_id="conv-memory",
                question="我之前说我想讨论什么主题？",
            )
        )
    )

    follow_up = asyncio.run(
        service.answer(
            ChatRequest(
                student_name="Alice",
                student_email="alice@example.com",
                course_context="科研指导",
                conversation_id="conv-memory",
                question="再根据刚才的上下文给我一个建议。",
            )
        )
    )

    assert len(llm.prompts) == 2
    assert "Recent conversation memory:" in llm.prompts[-1]
    assert "Stable student profile memory:" in llm.prompts[-1]
    assert "我之前说我想讨论什么主题？" in llm.prompts[-1]
    assert "科研指导" in llm.prompts[-1]
    assert any(item.basis_label in {"近期交流记录", "学生长期记录"} for item in follow_up.answer_basis)
    recent_basis = next(item for item in follow_up.answer_basis if item.basis_label == "近期交流记录")
    assert "你之前问过“我之前说我想讨论什么主题？”" in recent_basis.detail
    assert "学生之前提到：" not in recent_basis.detail

    health = service.health()
    assert health["conversation_memory_backend"] == "neuromem-layered"
    assert int(health["conversation_memory_profiles"]) >= 1
    assert health["chat_pipeline_stages"] == "12"


def test_chat_returns_traceable_basis_for_knowledge_hits(tmp_path: Path) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path, knowledge_backend="local")
    service = DigitalTwinService(settings)
    service._llm_client = IntentAwareLLMClient(
        booking_intent=False,
        answer="FlowRAG 主要解决检索与生成协同时的信息流组织问题。",
    )
    service.add_knowledge(
        KnowledgeDocumentCreate(
            title="FlowRAG 论文解读",
            content="FlowRAG 关注在复杂问答流程中组织检索结果和生成步骤，提高回答质量与可控性。",
            tags=["research", "paper-digest"],
            source_name="homepage:contents/research_papers/flowrag.pdf",
        )
    )

    response = asyncio.run(
        service.answer(
            ChatRequest(
                student_name="Alice",
                student_email="alice@example.com",
                course_context="科研指导",
                question="FlowRAG 主要做什么？",
            )
        )
    )

    assert any(item.basis_label == "论文资料" for item in response.answer_basis)
    assert any(item.source_label == "个人主页 / 研究论文 PDF / flowrag.pdf" for item in response.answer_basis)


def test_chat_reuses_booking_preference_profile_memory_in_follow_up_prompt(tmp_path: Path) -> None:
    settings = AppSettings(
        knowledge_base_dir=tmp_path,
        conversation_memory_dir=tmp_path / "conversation-memory",
    )
    service = DigitalTwinService(settings)
    llm = KeywordIntentLLMClient(answer="好的，我会结合你的历史预约偏好来提醒你。")
    service._llm_client = llm
    service._email_notifier = RecordingNotifier()

    booking_response = asyncio.run(
        service.answer(
            ChatRequest(
                student_name="Alice",
                student_email="alice@example.com",
                course_context="科研指导",
                conversation_id="conv-booking-profile",
                question="请帮我预约 2026-05-26 15:00 讨论论文进展",
            )
        )
    )

    assert booking_response.workflow_action == "book_meeting"

    follow_up = asyncio.run(
        service.answer(
            ChatRequest(
                student_name="Alice",
                student_email="alice@example.com",
                course_context="科研指导",
                conversation_id="conv-booking-profile",
                question="根据你记得的我的预约习惯，提醒我还要准备什么？",
            )
        )
    )

    assert follow_up.workflow_action == "advise_only"
    assert len(llm.prompts) == 1
    assert "Stable student profile memory:" in llm.prompts[-1]
    assert "常见预约主题：论文进展" in llm.prompts[-1]
    assert "最近一次明确给出的时间偏好：2026-05-26 15:00" in llm.prompts[-1]
    assert "预约联系邮箱：alice@example.com" in llm.prompts[-1]


def test_chat_routes_sensitive_issue_to_human_handoff(tmp_path: Path) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path, escalation_queue_dir=tmp_path / "escalations")
    service = DigitalTwinService(settings)
    service._llm_client = IntentAwareLLMClient(booking_intent=False, answer="不应调用")

    response = asyncio.run(
        service.answer(
            ChatRequest(
                student_name="Alice",
                student_email="alice@example.com",
                course_context="科研指导",
                conversation_id="conv-human-handoff",
                question="我想正式投诉这次成绩处理有误，请你马上联系老师。",
            )
        )
    )

    assert response.workflow_action == "human_handoff"
    assert response.decision_mode == "human_handoff"
    assert response.escalation_record is not None
    assert response.escalation_record.route == "human_handoff"
    assert response.escalation_record.status == "待处理"
    assert "本人直接处理" in response.answer


def test_chat_routes_review_request_to_pending_queue(tmp_path: Path) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path, escalation_queue_dir=tmp_path / "escalations")
    service = DigitalTwinService(settings)
    service._llm_client = IntentAwareLLMClient(booking_intent=False, answer="不应调用")

    response = asyncio.run(
        service.answer(
            ChatRequest(
                student_name="Alice",
                student_email="alice@example.com",
                course_context="科研指导",
                conversation_id="conv-review-queue",
                question="能不能破例帮我把截止时间延期一天？",
            )
        )
    )

    assert response.workflow_action == "review_queue"
    assert response.decision_mode == "review_queue"
    assert response.escalation_record is not None
    assert response.escalation_record.route == "review_queue"
    assert response.escalation_record.status == "待处理"
    assert "待审核队列" in response.answer


def test_chat_reuses_collaboration_preference_profile_memory_in_follow_up_prompt(tmp_path: Path) -> None:
    settings = AppSettings(
        knowledge_base_dir=tmp_path,
        conversation_memory_dir=tmp_path / "conversation-memory",
    )
    service = DigitalTwinService(settings)
    llm = RecordingLLMClient(
        booking_intent=False,
        answer="建议先准备 agenda、当前 blocker、相关 draft，再带上你最想讨论的问题。",
    )
    service._llm_client = llm

    asyncio.run(
        service.answer(
            ChatRequest(
                student_name="Alice",
                student_email="alice@example.com",
                course_context="科研指导",
                conversation_id="conv-collaboration-profile",
                question="和老师约时间前，我应该先准备什么？",
            )
        )
    )

    asyncio.run(
        service.answer(
            ChatRequest(
                student_name="Alice",
                student_email="alice@example.com",
                course_context="科研指导",
                conversation_id="conv-collaboration-profile",
                question="按你记得的我的沟通偏好，我这次找你前应该先准备什么？",
            )
        )
    )

    assert len(llm.prompts) == 2
    assert "Stable student profile memory:" in llm.prompts[-1]
    assert "该用户适合按清单式准备沟通材料" in llm.prompts[-1]
    assert "agenda、current blocker、draft、问题清单" in llm.prompts[-1]


def test_chat_returns_recommended_reading_and_resource_actions(tmp_path: Path) -> None:
    settings = AppSettings(
        knowledge_base_dir=tmp_path / "knowledge-base",
        conversation_memory_dir=tmp_path / "conversation-memory",
    )
    service = DigitalTwinService(settings)
    service._llm_client = RecordingLLMClient(
        booking_intent=False,
        answer="建议先阅读相关课程资料，再准备 agenda 和问题清单。",
    )
    service.add_knowledge(
        {
            "title": "Tutorial 7：执行优化与异构路径",
            "content": "介绍实验优化、执行路径和常见性能分析方法。",
            "tags": ["teaching", "tutorial", "courseware"],
            "source_name": "tutorials/week7.md",
        }
    )

    response = asyncio.run(
        service.answer(
            ChatRequest(
                student_name="Alice",
                student_email="alice@example.com",
                course_context="科研指导",
                conversation_id="conv-followup-actions",
                question="和老师约时间前，我应该先准备什么？",
            )
        )
    )

    action_types = {action.action_type for action in response.follow_up_actions}
    assert "recommended_reading" in action_types
    assert "todo_review" in action_types
    assert "office_hour_recommendation" in action_types
    assert "course_resource_recommendation" in action_types
    assert any("Tutorial 7" in action.title for action in response.follow_up_actions)


def test_chat_sanitizes_internalish_follow_up_reading_titles(tmp_path: Path) -> None:
    settings = AppSettings(
        knowledge_base_dir=tmp_path / "knowledge-base",
        conversation_memory_dir=tmp_path / "conversation-memory",
    )
    service = DigitalTwinService(settings)
    service._llm_client = RecordingLLMClient(
        booking_intent=False,
        answer="建议你先看看这条 FAQ，再准备 agenda 和问题清单。",
    )
    service.add_knowledge(
        {
            "title": "FAQ草稿 | 指导建议 | 和老 / 备什 / 我应",
            "content": "和老师约时间前，建议先准备 agenda、当前 blocker、已有 draft/结果，以及最想确认的 2-3 个问题。",
            "tags": ["advising", "faq"],
            "source_name": "analytics-gap:demo",
        }
    )

    response = asyncio.run(
        service.answer(
            ChatRequest(
                student_name="Alice",
                student_email="alice@example.com",
                course_context="科研指导",
                conversation_id="conv-followup-sanitized-reading",
                question="和老师约时间前，我应该先准备什么？",
            )
        )
    )

    reading_actions = [action for action in response.follow_up_actions if action.action_type == "recommended_reading"]
    assert reading_actions
    assert reading_actions[0].title == "先看：FAQ草稿 · 指导建议"
    assert "和老 / 备什 / 我应" not in reading_actions[0].title


def test_service_normalizes_published_gap_documents_on_boot(tmp_path: Path) -> None:
    settings = AppSettings(
        knowledge_base_dir=tmp_path / "knowledge-base",
        conversation_memory_dir=tmp_path / "conversation-memory",
        knowledge_gap_draft_dir=tmp_path / "gap-drafts",
    )
    service = DigitalTwinService(settings)
    draft = service._knowledge_gap_draft_store.upsert_generated_draft(
        cluster_id="demo-cluster",
        interaction_domain="advising",
        label="指导建议｜和老 / 备什 / 我应",
        reason="近期多次问到会前准备，但标准答复还不够稳定。",
        suggested_action="补充会前准备模板、议程模板和常见指导边界说明。",
        sample_questions=["和老师约时间前，我应该先准备什么？"],
        title="FAQ草稿｜指导建议｜和老 / 备什 / 我应",
        content="建议 FAQ/知识正文草稿：先给 checklist。",
        tags=["analytics-gap", "draft", "faq-draft", "advising"],
        source_name="analytics-gap:demo-cluster",
    )
    legacy_document = service.add_knowledge(
        {
            "title": "FAQ草稿｜指导建议｜和老 / 备什 / 我应",
            "content": "建议 FAQ/知识正文草稿：先给 checklist。",
            "tags": ["analytics-gap", "draft", "faq-draft", "advising"],
            "source_name": "analytics-gap:demo-cluster",
        }
    )
    service._knowledge_gap_draft_store.mark_published(draft.draft_id, document_id=legacy_document.document_id)

    reloaded = DigitalTwinService(settings)
    documents = reloaded.list_knowledge()
    normalized = next(item for item in documents if item.document_id == legacy_document.document_id)
    assert normalized.source_name.startswith("knowledge-gap:advising:")
    assert normalized.title.startswith("常见问题：")
    assert "faq-draft" not in normalized.tags


def test_publish_gap_document_upserts_same_semantic_topic(tmp_path: Path) -> None:
    settings = AppSettings(
        knowledge_base_dir=tmp_path / "knowledge-base",
        conversation_memory_dir=tmp_path / "conversation-memory",
        knowledge_gap_draft_dir=tmp_path / "knowledge-gap-drafts",
        knowledge_backend="local",
    )
    service = DigitalTwinService(settings)

    first = service._knowledge_gap_draft_store.upsert_generated_draft(
        cluster_id="cluster-a",
        interaction_domain="advising",
        label="指导建议｜会前准备",
        reason="这类问题反复出现。",
        suggested_action="补充会前准备模板、议程模板和边界说明。",
        sample_questions=["和老师约时间前，我应该先准备什么？"],
        title="FAQ草稿｜指导建议｜会前准备",
        content="建议 FAQ/知识正文草稿：先给 checklist。",
        tags=["analytics-gap", "draft", "faq-draft", "advising"],
        source_name="analytics-gap:cluster-a",
    )
    first_published = service.publish_knowledge_gap_draft(first.draft_id)

    second = service._knowledge_gap_draft_store.upsert_generated_draft(
        cluster_id="cluster-b",
        interaction_domain="advising",
        label="指导建议｜会前准备",
        reason="同类问题在不同轮次仍反复出现。",
        suggested_action="补充会前准备模板、议程模板和边界说明。",
        sample_questions=["和老师约时间前，我应该先准备什么？", "约讨论前需要准备哪些材料？"],
        title="FAQ草稿｜指导建议｜会前准备",
        content="建议 FAQ/知识正文草稿：先给 checklist。",
        tags=["analytics-gap", "draft", "faq-draft", "advising"],
        source_name="analytics-gap:cluster-b",
    )
    second_published = service.publish_knowledge_gap_draft(second.draft_id)

    documents = [document for document in service.list_knowledge() if "knowledge-gap" in document.tags]
    assert len(documents) == 1
    assert second_published.published_document_id == first_published.published_document_id
    assert documents[0].document_id == first_published.published_document_id
    assert documents[0].source_name.startswith("knowledge-gap:advising:")


def test_service_normalizes_duplicate_published_gap_documents_on_startup(tmp_path: Path) -> None:
    settings = AppSettings(
        knowledge_base_dir=tmp_path / "knowledge-base",
        conversation_memory_dir=tmp_path / "conversation-memory",
        knowledge_backend="local",
    )
    service = DigitalTwinService(settings)
    for suffix in ("a", "b", "c"):
        service.add_knowledge(
            KnowledgeDocumentCreate(
                title="常见问题：和老师约时间前，我应该先准备什么",
                content="主题：指导建议\n适用问题：\n- 和老师约时间前，我应该先准备什么？\n\n标准说明：补充会前准备模板、议程模板和常见指导边界说明。\n补充背景：指导建议类问题经常需要追问或人工接管。\n使用边界：涉及老师本人审批、例外政策或个性化承诺时，需要人工确认。",
                tags=["advising", "faq", "knowledge-gap"],
                source_name=f"knowledge-gap:{suffix}",
            )
        )

    reloaded = DigitalTwinService(settings)
    documents = [document for document in reloaded.list_knowledge() if "knowledge-gap" in document.tags]
    assert len(documents) == 1
    assert documents[0].source_name.startswith("knowledge-gap:advising:")


def test_service_normalizes_repeated_gap_title_prefixes_on_startup(tmp_path: Path) -> None:
    settings = AppSettings(
        knowledge_base_dir=tmp_path / "knowledge-base",
        conversation_memory_dir=tmp_path / "conversation-memory",
        knowledge_backend="local",
    )
    service = DigitalTwinService(settings)
    for title, source_name in (
        ("常见问题：和老师约时间前，我应该先准备什么", "knowledge-gap:a"),
        ("常见问题：常见问题：和老师约时间前，我应该先准备什么", "knowledge-gap:b"),
    ):
        service.add_knowledge(
            KnowledgeDocumentCreate(
                title=title,
                content="主题：指导建议\n适用问题：\n- 和老师约时间前，我应该先准备什么？\n\n标准说明：补充与当前问题直接相关的标准说明、准备清单和边界提醒。\n补充背景：近期多次出现相似提问，现有标准材料还不够集中。\n使用边界：涉及老师本人审批、例外政策或个性化承诺时，需要人工确认。",
                tags=["advising", "faq", "knowledge-gap"],
                source_name=source_name,
            )
        )

    reloaded = DigitalTwinService(settings)
    documents = [document for document in reloaded.list_knowledge() if "knowledge-gap" in document.tags]
    assert len(documents) == 1
    assert documents[0].title == "常见问题：和老师约时间前，我应该先准备什么"


def test_service_normalizes_truncated_gap_titles_on_startup(tmp_path: Path) -> None:
    settings = AppSettings(
        knowledge_base_dir=tmp_path / "knowledge-base",
        conversation_memory_dir=tmp_path / "conversation-memory",
        knowledge_backend="local",
    )
    service = DigitalTwinService(settings)
    for title, source_name in (
        ("常见问题：和老师约时间前，我应该先准备什么", "knowledge-gap:a"),
        ("常见问题：常见问…", "knowledge-gap:b"),
    ):
        service.add_knowledge(
            KnowledgeDocumentCreate(
                title=title,
                content="主题：指导建议\n适用问题：\n- 和老师约时间前，我应该先准备什么？\n- 和老师约时间前，我应该先准备什么？\n\n标准说明：补充与当前问题直接相关的标准说明、准备清单和边界提醒。\n补充背景：近期多次出现相似提问，现有标准材料还不够集中。\n使用边界：涉及老师本人审批、例外政策或个性化承诺时，需要人工确认。",
                tags=["advising", "faq", "knowledge-gap"],
                source_name=source_name,
            )
        )

    reloaded = DigitalTwinService(settings)
    documents = [document for document in reloaded.list_knowledge() if "knowledge-gap" in document.tags]
    assert len(documents) == 1
    assert documents[0].title == "常见问题：和老师约时间前，我应该先准备什么"


def test_chat_dedupes_same_title_published_gap_hits(tmp_path: Path) -> None:
    settings = AppSettings(
        knowledge_base_dir=tmp_path / "knowledge-base",
        conversation_memory_dir=tmp_path / "conversation-memory",
        knowledge_backend="local",
    )
    service = DigitalTwinService(settings)
    service._llm_client = RecordingLLMClient(
        booking_intent=False,
        answer="建议你先按会前准备清单整理材料。",
    )
    for suffix in ("a", "b", "c"):
        service.add_knowledge(
            KnowledgeDocumentCreate(
                title="常见问题：和老师约时间前，我应该先准备什么",
                content="主题：指导建议\n适用问题：\n- 和老师约时间前，我应该先准备什么？\n\n标准说明：补充会前准备模板、议程模板和常见指导边界说明。",
                tags=["advising", "faq", "knowledge-gap"],
                source_name=f"knowledge-gap:{suffix}",
            )
        )

    response = asyncio.run(
        service.answer(
            ChatRequest(
                student_name="Alice",
                student_email="alice@example.com",
                course_context="科研指导",
                question="和老师约时间前，我应该先准备什么？",
            )
        )
    )

    knowledge_basis = [item for item in response.answer_basis if item.title == "常见问题：和老师约时间前，我应该先准备什么"]
    assert len(knowledge_basis) == 1


def test_confirm_booking_queues_post_meeting_follow_ups(tmp_path: Path) -> None:
    settings = AppSettings(
        knowledge_base_dir=tmp_path / "knowledge-base",
        conversation_memory_dir=tmp_path / "conversation-memory",
        follow_up_queue_dir=tmp_path / "follow-ups",
    )
    service = DigitalTwinService(settings)
    service._email_notifier = RecordingNotifier()
    service.add_knowledge(
        {
            "title": "Meeting Prep Note",
            "content": "讨论论文时建议准备 draft 和关键问题。",
            "tags": ["teaching", "resources"],
            "source_name": "notes/meeting-prep.md",
        }
    )

    created = service.book_meeting(
        {
            "student_name": "Alice",
            "student_email": "alice@example.com",
            "topic": "论文进展",
            "preferred_start": "2026-05-26T15:00:00",
            "preferred_end": "2026-05-26T15:45:00",
        }
    )
    assert created.booking is not None

    confirmed = service.confirm_booking(created.booking.booking_id)
    assert confirmed.booking is not None
    assert confirmed.booking.status == "已确认"

    queued = service.list_follow_up_actions(status="queued")
    action_types = {item.action_type for item in queued}
    assert "post_meeting_summary" in action_types
    assert "todo_review" in action_types


def test_dispatch_due_follow_ups_sends_email(tmp_path: Path) -> None:
    settings = AppSettings(
        knowledge_base_dir=tmp_path / "knowledge-base",
        conversation_memory_dir=tmp_path / "conversation-memory",
        follow_up_queue_dir=tmp_path / "follow-ups",
    )
    service = DigitalTwinService(settings)
    notifier = RecordingNotifier()
    service._email_notifier = notifier

    created = service.book_meeting(
        {
            "student_name": "Alice",
            "student_email": "alice@example.com",
            "topic": "论文进展",
            "preferred_start": "2026-05-20T10:00:00",
            "preferred_end": "2026-05-20T10:45:00",
        }
    )
    assert created.booking is not None
    service.confirm_booking(created.booking.booking_id)

    dispatch = service.dispatch_due_follow_ups()
    assert dispatch.sent_count >= 2
    assert len(notifier.follow_up_emails) >= 2
    assert all(item.status == "sent" for item in service.list_follow_up_actions(status="sent"))


def test_health_does_not_dispatch_follow_ups(tmp_path: Path) -> None:
    settings = AppSettings(
        knowledge_base_dir=tmp_path / "knowledge-base",
        conversation_memory_dir=tmp_path / "conversation-memory",
        follow_up_queue_dir=tmp_path / "follow-ups",
    )
    service = DigitalTwinService(settings)
    notifier = RecordingNotifier()
    service._email_notifier = notifier

    service._follow_up_store.queue_action(
        booking_id="booking-1",
        student_name="Alice",
        student_email="alice@example.com",
        action_type="todo_review",
        title="会后整理 TODO",
        detail="整理讨论后的任务清单。",
        subject="请整理讨论后 TODO",
        lines=["请在会后补充 TODO 清单。"],
        due_at=None,
    )

    health = service.health()

    assert health["status"] == "ok"
    assert health["follow_up_dispatch_sent"] == "0"
    assert health["follow_up_dispatch_due"] == "1"
    assert notifier.follow_up_emails == []
    assert len(service.list_follow_up_actions(status="queued")) == 1