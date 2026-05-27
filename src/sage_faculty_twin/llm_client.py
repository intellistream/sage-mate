from __future__ import annotations

import asyncio
import json
import re
import threading
import time
from collections import OrderedDict
from typing import Any, Literal

import httpx
from pydantic import BaseModel
from pydantic import Field
from pydantic import ValidationError

from .config import AppSettings
from .models import InteractionIntent


_DEFAULT_RETRIEVAL_SCOPES: dict[str, list[str]] = {
    "general": [],
    "research": ["publications", "profile"],
    "teaching": ["courseware"],
    "advising": ["preparation", "meeting_policy", "profile"],
    "booking": ["meeting_policy"],
}

_DEFAULT_EXCLUDE_SCOPES: dict[str, list[str]] = {
    "general": [],
    "research": ["courseware"],
    "teaching": ["publications"],
    "advising": ["courseware"],
    "booking": ["courseware", "publications"],
}

class _InteractionIntentPayload(BaseModel):
    action: Literal["answer", "book_meeting", "ask_followup", "review_queue", "human_handoff"] = "answer"
    domain: Literal["general", "research", "teaching", "advising", "booking"] = "general"
    retrieval_scopes: list[str] = Field(default_factory=list)
    exclude_scopes: list[str] = Field(default_factory=list)
    decision_mode: Literal["direct_answer", "advise_only", "review_queue", "human_handoff"] | None = None
    needs_clarification: bool = False
    clarification_message: str | None = None
    escalation_reason: str | None = None


class VllmChatClient:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._client = httpx.Client(
            base_url=self._settings.llm_base_url,
            headers={
                "Authorization": f"Bearer {self._settings.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
        self._cache_lock = threading.Lock()
        self._response_cache: OrderedDict[str, tuple[float, str]] = OrderedDict()
        self._metrics_lock = threading.Lock()
        self._request_count = 0
        self._success_count = 0
        self._error_count = 0
        self._cache_hit_count = 0
        self._last_request_at: float | None = None
        self._last_success_at: float | None = None
        self._last_error_at: float | None = None
        self._last_error_message: str | None = None

    def close(self) -> None:
        self._client.close()

    async def aclose(self) -> None:
        await asyncio.to_thread(self.close)

    def runtime_snapshot(self) -> dict[str, str]:
        cache_entries = self._active_cache_entries()
        with self._metrics_lock:
            last_status = "not_checked"
            if self._last_success_at is not None and (
                self._last_error_at is None or self._last_success_at >= self._last_error_at
            ):
                last_status = "ok"
            elif self._last_error_at is not None:
                last_status = "error"
            return {
                "llm_status": last_status,
                "llm_request_count": str(self._request_count),
                "llm_success_count": str(self._success_count),
                "llm_error_count": str(self._error_count),
                "llm_cache_hit_count": str(self._cache_hit_count),
                "llm_cache_entries": str(cache_entries),
                "llm_last_error": self._last_error_message or "",
                "llm_last_request_at": self._format_timestamp(self._last_request_at),
                "llm_last_success_at": self._format_timestamp(self._last_success_at),
                "llm_last_error_at": self._format_timestamp(self._last_error_at),
            }

    def classify_interaction_intent_sync(
        self,
        question: str,
        course_context: str | None = None,
    ) -> InteractionIntent:
        system_prompt = (
            "Classify the student's request for a faculty digital twin. "
            "Return JSON only with keys: action, domain, retrieval_scopes, exclude_scopes, decision_mode, needs_clarification, clarification_message, escalation_reason. "
            'Allowed action values: "answer", "book_meeting", "ask_followup", "review_queue", "human_handoff". '
            'Allowed domain values: "general", "research", "teaching", "advising", "booking". '
            'Allowed decision_mode values: "direct_answer", "advise_only", "review_queue", "human_handoff". '
            'Allowed retrieval scopes: "publications", "profile", "courseware", "preparation", "meeting_policy". '
            'Allowed exclude scopes: "publications", "profile", "courseware", "preparation", "meeting_policy". '
            "Use book_meeting only when the student is actually asking to schedule or submit a meeting request now. "
            "Questions about what to prepare before booking are advising, not booking. "
            "Use advise_only when the assistant may give suggestions, checklists, draft ideas, or options but must not make the final decision for the owner or the student. "
            "Use review_queue when the student is asking for approval, exception, endorsement, recommendation, commitment, or another action that must be reviewed before the avatar can respond formally. "
            "Use human_handoff when the topic is sensitive, urgent, grievance-related, confidential, safety-related, or otherwise requires the real owner to respond personally. "
            "Use research for research direction, papers, projects, or publication questions. "
            "Use teaching for course lectures, tutorials, experiments, or teaching materials. "
            "Use advising for preparation, expectations, communication style, or meeting-readiness guidance. "
            "If the request is genuinely ambiguous and you need clarification, set action to ask_followup, needs_clarification to true, and provide a short clarification_message in Chinese."
        )
        context_line = course_context or ""
        user_prompt = f"context: {context_line}\nquestion: {question}"
        content = self.answer_question_sync(
            system_prompt,
            user_prompt,
            temperature=0.0,
            max_tokens=160,
        )
        payload = self._parse_interaction_intent_payload(content)
        raw_intent = self._coerce_interaction_intent(payload)
        return self._normalize_interaction_intent(question, course_context, raw_intent)

    async def classify_interaction_intent(
        self,
        question: str,
        course_context: str | None = None,
    ) -> InteractionIntent:
        return await asyncio.to_thread(
            self.classify_interaction_intent_sync,
            question,
            course_context,
        )

    def classify_booking_intent_sync(
        self,
        question: str,
        course_context: str | None = None,
    ) -> bool:
        try:
            return self.classify_interaction_intent_sync(question, course_context).action == "book_meeting"
        except Exception:
            return False

    async def classify_booking_intent(
        self,
        question: str,
        course_context: str | None = None,
    ) -> bool:
        return await asyncio.to_thread(
            self.classify_booking_intent_sync,
            question,
            course_context,
        )

    def answer_question_sync(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.2,
        max_tokens: int | None = 256,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self._settings.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        return self._request_chat_completion_sync(payload)

    def _request_chat_completion_sync(self, payload: dict[str, Any]) -> str:

        cache_key = self._cache_key(payload)
        cached = self._get_cached_response(cache_key)
        if cached is not None:
            self._record_cache_hit()
            return cached

        self._record_request_start()
        try:
            response = self._client.post("/chat/completions", json=payload)
            response.raise_for_status()

            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                raise RuntimeError("vllm-hust returned no chat choices")
            message = choices[0].get("message", {})
            content = message.get("content")
            if not content:
                raise RuntimeError("vllm-hust returned an empty chat message")
            answer = str(content)
        except Exception as exc:
            self._record_request_error(exc)
            raise
        self._record_request_success()
        self._store_cached_response(cache_key, answer)
        return answer

    async def answer_question(self, system_prompt: str, user_prompt: str) -> str:
        return await asyncio.to_thread(self.answer_question_sync, system_prompt, user_prompt)

    def _extract_json_object(self, text: str) -> dict[str, Any]:
        cleaned = text.strip()
        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match is None:
                raise RuntimeError("vllm-hust did not return JSON for booking intent classification") from None
            payload = json.loads(match.group(0))

        if not isinstance(payload, dict):
            raise RuntimeError("vllm-hust returned a non-object JSON payload for booking intent classification")
        return payload

    def _parse_interaction_intent_payload(self, content: str) -> _InteractionIntentPayload:
        try:
            payload = self._extract_json_object(content)
            return _InteractionIntentPayload.model_validate(payload)
        except (RuntimeError, ValidationError) as exc:
            repaired_content = self._repair_interaction_intent_payload(content, str(exc))
            repaired_payload = self._extract_json_object(repaired_content)
            return _InteractionIntentPayload.model_validate(repaired_payload)

    def _repair_interaction_intent_payload(self, content: str, validation_error: str) -> str:
        system_prompt = (
            "You repair JSON emitted by an interaction-intent classifier. "
            "Preserve the original intent meaning, but return valid JSON only. "
            "The JSON object must include exactly these keys: action, domain, retrieval_scopes, exclude_scopes, decision_mode, needs_clarification, clarification_message, escalation_reason. "
            "retrieval_scopes and exclude_scopes must be JSON arrays of strings."
        )
        user_prompt = (
            "Original classifier output:\n"
            f"{content}\n\n"
            "Validation error:\n"
            f"{validation_error}\n\n"
            "Rewrite the JSON so it is valid without adding explanations."
        )
        return self.answer_question_sync(
            system_prompt,
            user_prompt,
            temperature=0.0,
            max_tokens=220,
        )

    def _coerce_interaction_intent(self, payload: _InteractionIntentPayload) -> InteractionIntent:
        action = payload.action
        domain = payload.domain
        decision_mode = payload.decision_mode
        retrieval_scopes = payload.retrieval_scopes or _DEFAULT_RETRIEVAL_SCOPES.get(domain, [])
        exclude_scopes = payload.exclude_scopes or _DEFAULT_EXCLUDE_SCOPES.get(domain, [])
        if decision_mode is None:
            decision_mode = action if action in {"review_queue", "human_handoff"} else "direct_answer"
        normalized_payload = {
            "action": action,
            "domain": domain,
            "retrieval_scopes": [item for item in retrieval_scopes if item.strip()],
            "exclude_scopes": [item for item in exclude_scopes if item.strip()],
            "decision_mode": str(decision_mode),
            "needs_clarification": payload.needs_clarification,
            "clarification_message": payload.clarification_message,
            "escalation_reason": payload.escalation_reason,
            "confidence": self._derive_confidence(
                action=action,
                decision_mode=str(decision_mode),
                needs_clarification=payload.needs_clarification,
            ),
        }
        return InteractionIntent.model_validate(normalized_payload)

    def _derive_confidence(self, *, action: str, decision_mode: str, needs_clarification: bool) -> float:
        if needs_clarification or action == "ask_followup":
            return 0.45
        if action == "human_handoff" or decision_mode == "human_handoff":
            return 0.92
        if action == "review_queue" or decision_mode == "review_queue":
            return 0.85
        if action == "book_meeting":
            return 0.8
        if decision_mode == "advise_only":
            return 0.72
        return 0.68

    def _normalize_interaction_intent(
        self,
        question: str,
        course_context: str | None,
        intent: InteractionIntent,
    ) -> InteractionIntent:
        lowered = question.lower()
        course_context_text = (course_context or "").lower()

        if _looks_like_human_handoff_request(lowered, question):
            return intent.model_copy(
                update={
                    "action": "human_handoff",
                    "decision_mode": "human_handoff",
                    "domain": "advising",
                    "retrieval_scopes": [],
                    "exclude_scopes": [],
                    "needs_clarification": False,
                    "clarification_message": None,
                    "escalation_reason": "涉及敏感、紧急或必须由老师本人直接处理的事项。",
                    "confidence": max(intent.confidence, 0.98),
                }
            )

        if _looks_like_review_queue_request(lowered, question):
            return intent.model_copy(
                update={
                    "action": "review_queue",
                    "decision_mode": "review_queue",
                    "domain": "advising",
                    "retrieval_scopes": ["meeting_policy", "profile"],
                    "exclude_scopes": ["courseware"],
                    "needs_clarification": False,
                    "clarification_message": None,
                    "escalation_reason": "这是需要老师审核后才能正式答复的请求。",
                    "confidence": max(intent.confidence, 0.95),
                }
            )

        if _looks_like_teaching_question(lowered, question):
            return intent.model_copy(
                update={
                    "action": "answer",
                    "domain": "teaching",
                    "retrieval_scopes": ["courseware"],
                    "exclude_scopes": ["publications"],
                    "needs_clarification": False,
                    "clarification_message": None,
                    "confidence": max(intent.confidence, 0.95),
                }
            )

        if _looks_like_advising_question(lowered, question, course_context_text):
            return intent.model_copy(
                update={
                    "action": "answer",
                    "domain": "advising",
                    "retrieval_scopes": ["preparation", "meeting_policy", "profile"],
                    "exclude_scopes": ["courseware"],
                    "decision_mode": "advise_only",
                    "needs_clarification": False,
                    "clarification_message": None,
                    "confidence": max(intent.confidence, 0.9),
                }
            )

        if _looks_like_booking_information_question(lowered, question):
            return intent.model_copy(
                update={
                    "action": "answer",
                    "domain": "advising",
                    "retrieval_scopes": ["meeting_policy", "profile"],
                    "exclude_scopes": ["courseware"],
                    "decision_mode": "direct_answer",
                    "needs_clarification": False,
                    "clarification_message": None,
                    "confidence": max(intent.confidence, 0.9),
                }
            )

        if _looks_like_decision_request(lowered, question):
            return intent.model_copy(
                update={
                    "action": "answer",
                    "domain": "advising",
                    "retrieval_scopes": ["profile", "meeting_policy"],
                    "exclude_scopes": ["courseware"],
                    "decision_mode": "advise_only",
                    "needs_clarification": False,
                    "clarification_message": None,
                    "confidence": max(intent.confidence, 0.85),
                }
            )

        if _looks_like_booking_request(lowered, question):
            return intent.model_copy(
                update={
                    "action": "book_meeting",
                    "domain": "booking",
                    "retrieval_scopes": ["meeting_policy"],
                    "exclude_scopes": ["courseware", "publications"],
                    "decision_mode": "review_queue",
                    "needs_clarification": False,
                    "clarification_message": None,
                    "confidence": max(intent.confidence, 0.99),
                }
            )

        if _looks_like_research_question(lowered, question):
            return intent.model_copy(
                update={
                    "action": "answer",
                    "domain": "research",
                    "retrieval_scopes": ["publications", "profile"],
                    "exclude_scopes": ["courseware"],
                    "needs_clarification": False,
                    "clarification_message": None,
                    "confidence": max(intent.confidence, 0.9),
                }
            )

        if intent.action == "book_meeting" and intent.domain != "booking":
            return intent.model_copy(
                update={
                    "domain": "booking",
                    "retrieval_scopes": ["meeting_policy"],
                    "exclude_scopes": ["courseware", "publications"],
                }
            )

        return intent

    def _cache_key(self, payload: dict[str, Any]) -> str:
        return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

    def _get_cached_response(self, cache_key: str) -> str | None:
        ttl_seconds = self._settings.llm_cache_ttl_seconds
        max_entries = self._settings.llm_cache_max_entries
        if ttl_seconds <= 0 or max_entries <= 0:
            return None

        now = time.time()
        with self._cache_lock:
            self._evict_expired_locked(now)
            cached = self._response_cache.get(cache_key)
            if cached is None:
                return None
            expires_at, value = cached
            if expires_at <= now:
                self._response_cache.pop(cache_key, None)
                return None
            self._response_cache.move_to_end(cache_key)
            return value

    def _store_cached_response(self, cache_key: str, value: str) -> None:
        ttl_seconds = self._settings.llm_cache_ttl_seconds
        max_entries = self._settings.llm_cache_max_entries
        if ttl_seconds <= 0 or max_entries <= 0:
            return

        expires_at = time.time() + ttl_seconds
        with self._cache_lock:
            self._evict_expired_locked(time.time())
            self._response_cache[cache_key] = (expires_at, value)
            self._response_cache.move_to_end(cache_key)
            while len(self._response_cache) > max_entries:
                self._response_cache.popitem(last=False)

    def _evict_expired_locked(self, now: float) -> None:
        expired_keys = [key for key, (expires_at, _) in self._response_cache.items() if expires_at <= now]
        for key in expired_keys:
            self._response_cache.pop(key, None)

    def _record_request_start(self) -> None:
        with self._metrics_lock:
            self._request_count += 1
            self._last_request_at = time.time()

    def _record_request_success(self) -> None:
        with self._metrics_lock:
            self._success_count += 1
            self._last_success_at = time.time()
            self._last_error_message = None

    def _record_request_error(self, exc: Exception) -> None:
        with self._metrics_lock:
            self._error_count += 1
            self._last_error_at = time.time()
            self._last_error_message = str(exc)[:240]

    def _record_cache_hit(self) -> None:
        with self._metrics_lock:
            self._cache_hit_count += 1

    def _active_cache_entries(self) -> int:
        with self._cache_lock:
            self._evict_expired_locked(time.time())
            return len(self._response_cache)

    def _format_timestamp(self, timestamp: float | None) -> str:
        if timestamp is None:
            return ""
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(timestamp))


def _looks_like_booking_request(lowered: str, question: str) -> bool:
    if _looks_like_booking_information_question(lowered, question):
        return False
    booking_markers = (
        "请帮我预约",
        "帮我预约",
        "请预约",
        "我要预约",
        "我想预约",
        "预定",
        "约时间",
        "约个会",
        "book",
        "schedule a meeting",
        "meeting",
        "预约",
    )
    return any(marker in lowered for marker in booking_markers) or any(marker in question for marker in booking_markers)


def _looks_like_booking_information_question(lowered: str, question: str) -> bool:
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


def _looks_like_teaching_question(lowered: str, question: str) -> bool:
    if bool(re.search(r"第\s*\d+\s*讲", question)):
        return True
    teaching_markers = ("tutorial", "lecture", "experiment")
    if any(marker in lowered for marker in teaching_markers):
        return True
    return any(marker in question for marker in ("讲义", "课件", "实验", "教程", "习题"))


def _looks_like_advising_question(lowered: str, question: str, course_context_text: str) -> bool:
    advising_markers = ("准备什么", "提前准备", "怎么准备", "agenda", "blocker")
    role_markers = ("老师", "导师", "meeting", "预约", "约时间")
    if any(marker in question for marker in advising_markers) and any(marker in question for marker in role_markers):
        return True
    return "科研指导" in course_context_text and "准备" in question


def _looks_like_decision_request(lowered: str, question: str) -> bool:
    markers = (
        "帮我决定",
        "替我决定",
        "直接告诉我",
        "该不该",
        "怎么选",
        "选哪个",
        "应该选",
    )
    return any(marker in lowered for marker in markers) or any(marker in question for marker in markers)


def _looks_like_review_queue_request(lowered: str, question: str) -> bool:
    markers = (
        "破例",
        "例外",
        "延期",
        "审批",
        "审核",
        "批准",
        "同意我",
        "推荐信",
        "推荐一下",
        "加入课题组",
        "加入你们组",
        "能收我吗",
        "能不能给我",
    )
    return any(marker in lowered for marker in markers) or any(marker in question for marker in markers)


def _looks_like_human_handoff_request(lowered: str, question: str) -> bool:
    markers = (
        "投诉",
        "申诉",
        "成绩",
        "保密",
        "隐私",
        "紧急",
        "马上联系",
        "尽快联系",
        "心理",
        "危机",
        "安全",
        "举报",
        "冲突",
        "误会",
    )
    return any(marker in lowered for marker in markers) or any(marker in question for marker in markers)


def _looks_like_research_question(lowered: str, question: str) -> bool:
    research_markers = (
        "研究主线",
        "研究方向",
        "主要研究",
        "研究什么",
        "做什么研究",
        "科研",
        "flowrag",
        "libamm",
        "publication",
        "publications",
        "research",
    )
    return any(marker in lowered for marker in research_markers) or any(marker in question for marker in research_markers)
