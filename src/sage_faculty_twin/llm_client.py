from __future__ import annotations

import asyncio
import json
import re
import threading
import time
from collections import OrderedDict
from typing import Any, Callable, Literal

import httpx
from pydantic import BaseModel, Field, ValidationError

from .config import AppSettings
from .models import InteractionIntent
from .workflow_context import WorkflowRequestContext
from .workflow_planner import PlanSpec, ShadowPlanCandidate
from .workflow_steps import get_default_step_registry

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
    action: Literal["answer", "book_meeting", "ask_followup", "review_queue", "human_handoff"] = (
        "answer"
    )
    domain: Literal["general", "research", "teaching", "advising", "booking"] = "general"
    retrieval_scopes: list[str] = Field(default_factory=list)
    exclude_scopes: list[str] = Field(default_factory=list)
    decision_mode: (
        Literal["direct_answer", "advise_only", "review_queue", "human_handoff"] | None
    ) = None
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
            timeout=float(self._settings.llm_timeout_seconds),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
        # Intent classification client: use a smaller/faster model when configured.
        intent_base_url = self._settings.intent_llm_base_url or self._settings.llm_base_url
        self._intent_client = httpx.Client(
            base_url=intent_base_url,
            headers={
                "Authorization": f"Bearer {self._settings.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
        self._intent_model_name = self._settings.intent_model_name or self._settings.model_name
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
        self._intent_client.close()

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
        recent_session_context: str | None = None,
    ) -> InteractionIntent:
        # Goal: stop the model from reflexively choosing ask_followup. Default
        # to ``answer`` for any question that has even a thin academic anchor.
        # ask_followup is reserved for genuinely unintelligible inputs.
        system_prompt = (
            "Classify the student's request for a faculty digital twin. "
            "Return JSON only with keys: action, domain, retrieval_scopes, exclude_scopes, decision_mode, needs_clarification, clarification_message, escalation_reason. "
            'Allowed action values: "answer", "book_meeting", "ask_followup", "review_queue", "human_handoff". '
            'Allowed domain values: "general", "research", "teaching", "advising", "booking". '
            'Allowed decision_mode values: "direct_answer", "advise_only", "review_queue", "human_handoff". '
            'Allowed retrieval scopes: "publications", "profile", "courseware", "preparation", "meeting_policy". '
            'Allowed exclude scopes: "publications", "profile", "courseware", "preparation", "meeting_policy". '
            "DEFAULT BEHAVIOR: choose action=answer. The downstream pipeline retrieves the owner's papers, course slides and biography and grounds the answer; you do NOT need to ask the student for more info before classifying. "
            "Use ask_followup ONLY as a last resort and ONLY when ALL of the following are true: "
            "(a) the question contains no concrete academic anchor (no paper title, system name, course term, KV/TTFT/batching/scheduling/inference keyword, no '论文/文献/汇报/写作/研究方向/招生/课题'), "
            "(b) the recent_session_context block is empty (so we cannot resolve references like '具体内容', '这个', '上面那个'), "
            "(c) without clarification, no reasonable answer can be drafted at all. "
            "If the question is short but recent_session_context exists, RESOLVE the reference against that prior turn and choose action=answer with the appropriate domain. "
            "Use book_meeting only when the student is actually asking to schedule or submit a meeting request now. Questions about what to prepare before booking are advising, not booking. "
            "Use advise_only when you may give suggestions, checklists, draft ideas, or options but must not make the final decision for the owner or the student. "
            "Use review_queue ONLY for requests for approval, exception, endorsement, recommendation, or commitment that must be reviewed before the avatar can respond formally. Open academic questions like '顶会论文叙事是什么样', '怎么整理文献', '如何选研究方向' are NOT review_queue \u2014 they are answer/advise_only with domain=research or advising. "
            "Use human_handoff only when the topic is sensitive, urgent, grievance-related, confidential, or safety-related. "
            "Use research for research direction, papers, projects, publications, or system-building questions (SAGE / Neuromem / vLLM-HUST / KV cache / TTFT / batching / scheduling / inference engine). "
            "Use teaching for course lectures, tutorials, experiments, or teaching-material questions. "
            "Use advising for preparation, expectations, communication style, meeting-readiness, or paper-writing-process guidance. "
            "Positive examples (all must be answer, not ask_followup): "
            "'我已经整理了十篇文献，然后进行汇报，汇报的内容应该包括什么' -> answer / advising / advise_only. "
            "'研究目标是降低TTFT，希望得到怎么整理相关文献的建议' -> answer / research / advise_only. "
            "'我的研究思路是当kv可复用时重计算也比复用更快...' -> answer / research / advise_only. "
            "'你能帮我看论文吗' -> answer / advising / advise_only (do NOT ask which paper before retrieval). "
            "'kvpr这篇' (with prior turn mentioning a paper) -> answer / research. "
            "'一篇好的顶会论文应该是什么样的叙事' -> answer / advising / advise_only. "
            "'你的学术背景' / '你的主要研究方向' -> answer / research / direct_answer. "
            "If you do choose ask_followup, the clarification_message must be one short Chinese sentence asking ONE specific missing fact, never a generic '能否提供更多信息'."
        )
        context_line = course_context or ""
        recent_block = (recent_session_context or "").strip()
        user_prompt_parts: list[str] = []
        if context_line:
            user_prompt_parts.append(f"course_context: {context_line}")
        if recent_block:
            user_prompt_parts.append(f"recent_session_context (use to resolve short references):\n{recent_block}")
        else:
            user_prompt_parts.append("recent_session_context: <empty>")
        user_prompt_parts.append(f"current_question: {question}")
        user_prompt = "\n".join(user_prompt_parts)
        content = self._request_intent_classification(system_prompt, user_prompt)
        payload = self._parse_interaction_intent_payload(content)
        raw_intent = self._coerce_interaction_intent(payload)
        return self._normalize_interaction_intent(
            question, course_context, raw_intent, recent_session_context=recent_block
        )

    async def classify_interaction_intent(
        self,
        question: str,
        course_context: str | None = None,
        recent_session_context: str | None = None,
    ) -> InteractionIntent:
        return await asyncio.to_thread(
            self.classify_interaction_intent_sync,
            question,
            course_context,
            recent_session_context,
        )

    def classify_booking_intent_sync(
        self,
        question: str,
        course_context: str | None = None,
    ) -> bool:
        try:
            return (
                self.classify_interaction_intent_sync(question, course_context).action
                == "book_meeting"
            )
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

    def propose_shadow_plan_candidate_sync(
        self,
        context: WorkflowRequestContext,
        deterministic_plan: PlanSpec,
    ) -> ShadowPlanCandidate:
        step_registry = get_default_step_registry()
        allowed_step_ids = ", ".join(sorted(step_registry))
        allowed_sources = ", ".join(sorted(context.available_evidence_sources)) or "none"
        deterministic_steps = ", ".join(step.step_id for step in deterministic_plan.steps)
        system_prompt = (
            "You are a shadow workflow planner for an academic digital twin. "
            "Return JSON only. Do not execute anything. Do not invent unregistered steps. "
            "Propose a conservative comparison plan for analysis only."
        )
        user_prompt = (
            "Return a JSON object with exactly these keys: goal, fallback_template, step_ids, allowed_sources, "
            "requires_citations, explain_to_operator.\n"
            f"Allowed step_ids: {allowed_step_ids}.\n"
            f"Allowed evidence sources for this request: {allowed_sources}.\n"
            f"Question: {context.question}\n"
            f"Course context: {context.course_context or 'none'}\n"
            f"Visitor profile: {context.visitor_profile or 'none'}\n"
            f"Role mode: {context.role_mode}\n"
            f"Journey state: {context.journey_state}\n"
            f"Session identity: {context.session_identity}\n"
            f"Deterministic goal: {deterministic_plan.goal}\n"
            f"Deterministic fallback template: {deterministic_plan.fallback_template}\n"
            f"Deterministic steps: {deterministic_steps}\n"
            "Rules: keep the proposal read-only unless a draft step is clearly justified, do not use admin-only steps for "
            "normal users, and do not add any text outside the JSON object."
        )
        content = self.answer_question_sync(
            system_prompt,
            user_prompt,
            temperature=self._settings.shadow_planner_temperature,
            max_tokens=self._settings.shadow_planner_max_tokens,
        )
        return self._parse_shadow_plan_candidate(content)

    async def propose_shadow_plan_candidate(
        self,
        context: WorkflowRequestContext,
        deterministic_plan: PlanSpec,
    ) -> ShadowPlanCandidate:
        return await asyncio.to_thread(
            self.propose_shadow_plan_candidate_sync,
            context,
            deterministic_plan,
        )

    def _request_intent_classification(self, system_prompt: str, user_prompt: str) -> str:
        """Run intent classification on the dedicated (smaller) model."""
        payload: dict[str, Any] = {
            "model": self._intent_model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.0,
            "max_tokens": 160,
            "chat_template_kwargs": {"enable_thinking": False},
        }
        self._record_request_start()
        try:
            response = self._intent_client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                raise RuntimeError("Intent model returned no choices")
            content = choices[0].get("message", {}).get("content", "")
            if not content:
                raise RuntimeError("Intent model returned empty content")
            self._record_request_success()
            return str(content)
        except Exception as exc:
            self._record_request_error(exc)
            raise

    def answer_question_sync(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.2,
        max_tokens: int | None = 2048,
        token_callback: Callable[[str], None] | None = None,
        enable_thinking: bool = True,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self._settings.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }
        if not enable_thinking:
            payload["chat_template_kwargs"] = {"enable_thinking": False}
            # Without thinking, we don't need as many tokens
            if max_tokens is not None and max_tokens > 1024:
                max_tokens = 1024
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        if token_callback is not None:
            # Chat Latency Optimizations Task 5: stream tokens via
            # OpenAI-compatible ``stream=true`` so the SSE channel can
            # forward each chunk to the browser. Streaming responses
            # bypass the response cache because we cannot replay an
            # already-flushed stream to a callback.
            stream_payload = dict(payload)
            stream_payload["stream"] = True
            return self._request_chat_completion_stream(stream_payload, token_callback)

        return self._request_chat_completion_sync(payload)

    def _request_chat_completion_stream(
        self,
        payload: dict[str, Any],
        token_callback: Callable[[str], None],
    ) -> str:
        # We deliberately skip the response cache for streaming requests:
        # the cache stores the final string and cannot replay deltas to
        # ``token_callback``. Cached non-streaming completions are still
        # served by ``_request_chat_completion_sync`` for callers that
        # don't pass a callback.
        self._record_request_start()
        max_retries = self._settings.llm_retry_attempts
        for attempt in range(max_retries + 1):
            collected: list[str] = []
            try:
                with self._client.stream("POST", "/chat/completions", json=payload) as response:
                    response.raise_for_status()
                    for raw_line in response.iter_lines():
                        if not raw_line:
                            continue
                        line = (
                            raw_line.decode("utf-8")
                            if isinstance(raw_line, (bytes, bytearray))
                            else raw_line
                        )
                        if not line.startswith("data:"):
                            continue
                        data_text = line[len("data:") :].strip()
                        if not data_text or data_text == "[DONE]":
                            if data_text == "[DONE]":
                                break
                            continue
                        try:
                            chunk = json.loads(data_text)
                        except json.JSONDecodeError:
                            continue
                        choices = chunk.get("choices") or []
                        if not choices:
                            continue
                        delta = choices[0].get("delta") or {}
                        delta_content = delta.get("content")
                        if not delta_content:
                            continue
                        text = str(delta_content)
                        collected.append(text)
                        try:
                            token_callback(text)
                        except Exception:  # pragma: no cover - defensive
                            pass
                answer = "".join(collected)
                if not answer:
                    raise RuntimeError("vllm-hust returned an empty streaming chat message")
                break
            except httpx.TimeoutException as exc:
                if attempt >= max_retries:
                    self._record_request_error(exc)
                    raise
                self._sleep_before_retry(attempt + 1)
            except Exception as exc:
                self._record_request_error(exc)
                raise
        self._record_request_success()
        return answer

    def _request_chat_completion_sync(self, payload: dict[str, Any]) -> str:

        cache_key = self._cache_key(payload)
        cached = self._get_cached_response(cache_key)
        if cached is not None:
            self._record_cache_hit()
            return cached

        self._record_request_start()
        max_retries = self._settings.llm_retry_attempts
        for attempt in range(max_retries + 1):
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
                break
            except httpx.TimeoutException as exc:
                if attempt >= max_retries:
                    self._record_request_error(exc)
                    raise
                self._sleep_before_retry(attempt + 1)
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
                raise RuntimeError(
                    "vllm-hust did not return JSON for booking intent classification"
                ) from None
            payload = json.loads(match.group(0))

        if not isinstance(payload, dict):
            raise RuntimeError(
                "vllm-hust returned a non-object JSON payload for booking intent classification"
            )
        return payload

    def _parse_interaction_intent_payload(self, content: str) -> _InteractionIntentPayload:
        try:
            payload = self._extract_json_object(content)
            return _InteractionIntentPayload.model_validate(payload)
        except (RuntimeError, ValidationError) as exc:
            repaired_content = self._repair_interaction_intent_payload(content, str(exc))
            repaired_payload = self._extract_json_object(repaired_content)
            return _InteractionIntentPayload.model_validate(repaired_payload)

    def _parse_shadow_plan_candidate(self, content: str) -> ShadowPlanCandidate:
        try:
            payload = self._extract_json_object(content)
            return ShadowPlanCandidate.model_validate(payload)
        except (RuntimeError, ValidationError) as exc:
            repaired_content = self._repair_shadow_plan_candidate(content, str(exc))
            repaired_payload = self._extract_json_object(repaired_content)
            return ShadowPlanCandidate.model_validate(repaired_payload)

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

    def _repair_shadow_plan_candidate(self, content: str, validation_error: str) -> str:
        step_registry = get_default_step_registry()
        allowed_step_ids = ", ".join(sorted(step_registry))
        system_prompt = (
            "You repair JSON emitted by a shadow workflow planner. Return valid JSON only. "
            "The JSON object must include exactly these keys: goal, fallback_template, step_ids, allowed_sources, "
            "requires_citations, explain_to_operator. step_ids and allowed_sources must be JSON arrays of strings."
        )
        user_prompt = (
            "Original shadow planner output:\n"
            f"{content}\n\n"
            "Validation error:\n"
            f"{validation_error}\n\n"
            f"Allowed step_ids: {allowed_step_ids}\n"
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
            decision_mode = (
                action if action in {"review_queue", "human_handoff"} else "direct_answer"
            )
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

    def _derive_confidence(
        self, *, action: str, decision_mode: str, needs_clarification: bool
    ) -> float:
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
        *,
        recent_session_context: str | None = None,
    ) -> InteractionIntent:
        lowered = question.lower()
        course_context_text = (course_context or "").lower()
        recent_block = (recent_session_context or "").strip()

        # Task 2 guardrails: undo the model's reflexive ask_followup choice when
        # we have enough material to answer. These run BEFORE every other
        # specialized branch so a demoted intent flows through the normal
        # research / advising / teaching dispatch below.
        if intent.action == "ask_followup":
            if recent_block and len(question.strip()) < 25:
                intent = intent.model_copy(
                    update={
                        "action": "answer",
                        "decision_mode": "direct_answer"
                        if intent.decision_mode in {"", "review_queue"}
                        else intent.decision_mode,
                        "needs_clarification": False,
                        "clarification_message": None,
                        "confidence": max(intent.confidence, 0.7),
                    }
                )
            elif _has_research_anchor(lowered, question):
                intent = intent.model_copy(
                    update={
                        "action": "answer",
                        "domain": "research",
                        "retrieval_scopes": ["publications", "profile"],
                        "exclude_scopes": ["courseware"],
                        "decision_mode": "direct_answer"
                        if intent.decision_mode == ""
                        else intent.decision_mode,
                        "needs_clarification": False,
                        "clarification_message": None,
                        "confidence": max(intent.confidence, 0.78),
                    }
                )
            elif _has_advising_anchor(lowered, question):
                intent = intent.model_copy(
                    update={
                        "action": "answer",
                        "domain": "advising",
                        "retrieval_scopes": ["preparation", "meeting_policy", "profile"],
                        "exclude_scopes": ["courseware"],
                        "decision_mode": "advise_only",
                        "needs_clarification": False,
                        "clarification_message": None,
                        "confidence": max(intent.confidence, 0.75),
                    }
                )

        # Task 2: demote review_queue to advise_only when the topic is a
        # clearly answerable academic question.
        if intent.decision_mode == "review_queue" or intent.action == "review_queue":
            if _looks_like_answerable_academic_question(lowered, question):
                intent = intent.model_copy(
                    update={
                        "action": "answer",
                        "domain": "advising"
                        if intent.domain in {"", "general"}
                        else intent.domain,
                        "retrieval_scopes": ["preparation", "profile", "publications"],
                        "exclude_scopes": ["courseware"],
                        "decision_mode": "advise_only",
                        "needs_clarification": False,
                        "clarification_message": None,
                        "escalation_reason": None,
                        "confidence": max(intent.confidence, 0.8),
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

        if _looks_like_mixed_course_research_boundary_question(lowered, question):
            return intent.model_copy(
                update={
                    "action": "answer",
                    "domain": "advising",
                    "retrieval_scopes": ["preparation", "meeting_policy", "profile"],
                    "exclude_scopes": ["courseware"],
                    "decision_mode": "advise_only",
                    "needs_clarification": False,
                    "clarification_message": None,
                    "confidence": max(intent.confidence, 0.92),
                }
            )

        if _looks_like_progress_followup_advising_question(lowered, question, course_context_text):
            return intent.model_copy(
                update={
                    "action": "answer",
                    "domain": "advising",
                    "retrieval_scopes": ["preparation", "meeting_policy", "profile"],
                    "exclude_scopes": ["courseware"],
                    "decision_mode": "advise_only",
                    "needs_clarification": False,
                    "clarification_message": None,
                    "confidence": max(intent.confidence, 0.92),
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
        expired_keys = [
            key for key, (expires_at, _) in self._response_cache.items() if expires_at <= now
        ]
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

    def _sleep_before_retry(self, retry_number: int) -> None:
        delay_seconds = self._settings.llm_retry_backoff_seconds * (2 ** max(0, retry_number - 1))
        if delay_seconds > 0:
            time.sleep(delay_seconds)


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
        "预约",
    )
    return any(marker in lowered for marker in booking_markers) or any(
        marker in question for marker in booking_markers
    )


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
    if any(marker in lowered for marker in explicit_booking_markers) or any(
        marker in question for marker in explicit_booking_markers
    ):
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
        "准备什么",
        "先准备",
        "提前准备",
        "约时间前",
        "预约前",
        "什么时候",
        "什么时间",
        "哪几天",
        "什么时候方便",
        "哪些时候方便",
        "这周",
        "本周",
        "开放时段",
        "可预约时段",
        "预约规则",
        "如何预约",
        "怎么预约",
        "以便预约",
        "方便预约",
        "先发邮件",
        "直接发邮件",
        "发邮件",
        "线下聊",
        "当面聊",
        "更合适",
        "什么类型的问题",
        "适合先邮件",
        "等有更多内容再约",
    )
    booking_context_markers = (
        "office hour",
        "office hours",
        "预约",
        "约时间",
        "约老师",
        "时间安排",
        "开放时段",
        "找您",
        "发邮件",
        "线下聊",
        "当面聊",
    )
    has_info_marker = any(marker in lowered for marker in info_markers) or any(
        marker in question for marker in info_markers
    )
    has_booking_context = any(marker in lowered for marker in booking_context_markers) or any(
        marker in question for marker in booking_context_markers
    )
    return has_info_marker and has_booking_context


def _looks_like_teaching_question(lowered: str, question: str) -> bool:
    if _looks_like_mixed_course_research_boundary_question(lowered, question):
        return False
    if bool(re.search(r"第\s*\d+\s*讲", question)):
        return True
    teaching_markers = ("tutorial", "lecture", "experiment", "assignment", "course")
    if any(marker in lowered for marker in teaching_markers):
        return True
    return any(
        marker in question
        for marker in (
            "讲义",
            "课件",
            "实验",
            "教程",
            "习题",
            "课上问题",
            "作业",
            "端到端",
            "kernel",
            "性能分析",
        )
    )


def _looks_like_mixed_course_research_boundary_question(lowered: str, question: str) -> bool:
    has_course = any(marker in lowered for marker in ("course", "assignment")) or any(
        marker in question for marker in ("课程", "作业", "课上问题")
    )
    has_research = any(marker in lowered for marker in ("research", "paper", "project")) or any(
        marker in question for marker in ("研究", "科研", "论文", "项目")
    )
    has_boundary = any(marker in lowered for marker in ("separately", "split", "together")) or any(
        marker in question
        for marker in ("分开准备", "分开", "分别", "一次都问完", "一起问", "一起聊")
    )
    return has_course and has_research and has_boundary


def _looks_like_advising_question(lowered: str, question: str, course_context_text: str) -> bool:
    advising_markers = (
        "准备什么",
        "提前准备",
        "怎么准备",
        "先准备",
        "先整理",
        "怎么组织",
        "agenda",
        "blocker",
        "更看重哪些准备",
        "反馈更集中",
        "带 draft",
        "初稿",
        "合作前",
        "合作空间",
        "先补什么",
        "安排阅读顺序",
        "下一步",
        "继续补实验",
    )
    scope_markers = (
        "怎么收窄",
        "收窄",
        "收拢结构",
        "题目太大",
        "砍掉哪些",
        "最先会删什么",
    )
    contact_markers = (
        "发邮件",
        "线下聊",
        "当面聊",
        "分开准备",
        "更合适",
        "哪几天",
        "什么时候方便",
    )
    role_markers = ("老师", "导师", "meeting", "预约", "约时间", "找您", "邮件", "线下")
    if any(marker in question for marker in advising_markers) and any(
        marker in question for marker in role_markers
    ):
        return True
    if any(marker in question for marker in scope_markers) and any(
        marker in question for marker in ("老师", "研究", "项目", "题目", "论文", "摘要")
    ):
        return True
    if any(marker in question for marker in contact_markers) and any(
        marker in question for marker in role_markers
    ):
        return True
    if "科研指导" in course_context_text and any(
        marker in question
        for marker in ("准备", "收窄", "整理", "下一步", "发邮件", "线下", "合作")
    ):
        return True
    return False


def _looks_like_progress_followup_advising_question(
    lowered: str,
    question: str,
    course_context_text: str,
) -> bool:
    progress_markers = (
        "上次已被建议",
        "整理成三类",
        "下一步",
        "先发邮件还是继续补实验",
        "减少来回修改",
    )
    contact_markers = ("老师", "请教老师", "邮件", "补实验", "继续补实验", "当前进展")
    has_progress = any(marker in question for marker in progress_markers) or any(
        marker in lowered for marker in progress_markers
    )
    has_contact_context = any(marker in question for marker in contact_markers) or any(
        marker in lowered for marker in contact_markers
    )
    if has_progress and has_contact_context:
        return True
    return "lamp personalization benchmark" in course_context_text and has_progress


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
    return any(marker in lowered for marker in markers) or any(
        marker in question for marker in markers
    )


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
    return any(marker in lowered for marker in markers) or any(
        marker in question for marker in markers
    )


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
    return any(marker in lowered for marker in markers) or any(
        marker in question for marker in markers
    )


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
    return any(marker in lowered for marker in research_markers) or any(
        marker in question for marker in research_markers
    )


_RESEARCH_ANCHOR_TOKENS: tuple[str, ...] = (
    "kv",
    "kv cache",
    "kvpr",
    "ttft",
    "vllm",
    "sage",
    "neuromem",
    "sagevdb",
    "batching",
    "scheduling",
    "inference",
    "prefill",
    "decoding",
    "throughput",
    "latency",
    "flowrag",
    "libamm",
    "论文",
    "文献",
    "汇报",
    "研究",
    "写作",
    "推理",
    "复用",
    "重计算",
    "开题",
    "组会",
    "投稿",
    "实验",
    "benchmark",
)


_ADVISING_ANCHOR_TOKENS: tuple[str, ...] = (
    "准备",
    "如何整理",
    "怎么整理",
    "看论文",
    "读论文",
    "选研究",
    "选方向",
    "选课题",
    "叙事",
    "招生",
    "招什么",
    "meeting",
    "office hour",
)


_ANSWERABLE_ACADEMIC_TOKENS: tuple[str, ...] = (
    "顶会",
    "叙事",
    "如何整理",
    "怎么整理",
    "如何选",
    "怎么选",
    "研究方向",
    "研究目标",
    "研究方法",
    "文献阅读",
    "读论文",
    "看论文",
    "写论文",
    "论文写作",
    "论文叙事",
    "组会",
    "开题",
    "汇报",
)


def _has_research_anchor(lowered: str, question: str) -> bool:
    return any(token in lowered for token in _RESEARCH_ANCHOR_TOKENS) or any(
        token in question for token in _RESEARCH_ANCHOR_TOKENS
    )


def _has_advising_anchor(lowered: str, question: str) -> bool:
    return any(token in lowered for token in _ADVISING_ANCHOR_TOKENS) or any(
        token in question for token in _ADVISING_ANCHOR_TOKENS
    )


def _looks_like_answerable_academic_question(lowered: str, question: str) -> bool:
    return any(token in lowered for token in _ANSWERABLE_ACADEMIC_TOKENS) or any(
        token in question for token in _ANSWERABLE_ACADEMIC_TOKENS
    )
