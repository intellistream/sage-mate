import asyncio
import hashlib
import hmac
import json
import logging
import os
import secrets
import threading
import time
import urllib.parse
import urllib.request
from collections.abc import AsyncIterator
from datetime import date
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from . import __version__
from .runtime_env import bootstrap_runtime_env

bootstrap_runtime_env(require_policy=True, require_fastapi=False)

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from sage.edge.app import create_app as create_edge_app

from .auth import (
    ADMIN_COOKIE_NAME,
    USER_COOKIE_NAME,
    clear_admin_session_cookie,
    clear_user_session_cookie,
    set_admin_session_cookie,
    set_user_session_cookie,
)
from .config import settings
from .models import (
    AdminLoginRequest,
    AdminSessionResponse,
    AnonymousSuggestionCreate,
    AnonymousSuggestionRecord,
    ArtifactMemoryDraftRecordResponse,
    AvailabilitySchedule,
    BookingDecisionRequest,
    BookingRecord,
    BookingRequest,
    BookingResponse,
    ChatAttachment,
    ChatFeedbackRequest,
    ChatFeedbackResponse,
    ChatRequest,
    ChatResponse,
    ConversationHistoryListResponse,
    ConversationTranscriptResponse,
    EscalationDecisionRequest,
    EscalationRecord,
    FollowUpDispatchResponse,
    FollowUpQueueRecord,
    KnowledgeDocumentActionResponse,
    KnowledgeDocumentCreate,
    KnowledgeDocumentRecord,
    KnowledgeDocumentReviewRequest,
    KnowledgeDocumentReviewSummary,
    KnowledgeGapDraftCreateRequest,
    KnowledgeGapDraftRecordResponse,
    KnowledgeSearchResponse,
    MemoryProfileListResponse,
    OnlinePresenceHeartbeatRequest,
    OnlinePresenceHeartbeatResponse,
    OperationsOverviewResponse,
    OperationsTaskStateRecord,
    OperationsTaskStateUpdateRequest,
    OperationsWorkbenchResponse,
    QuestionAnalyticsReportResponse,
    ServiceControlResponse,
    SlackTwinLinkCodeResponse,
    SlackTwinLinkStatusResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserSessionResponse,
    WorkflowReplayReportResponse,
)
from .history_auth import resolve_authenticated_history_email
from .service import DigitalTwinService, build_stack_versions_payload, build_hardware_payload
from .capability_plugins import CapabilityPluginRegistry, CapabilityPluginStatus
from .slack_link_store import SlackUserLinkRecord, SlackUserLinkStore


_logger = logging.getLogger(__name__)


def configure_local_cors(target_app: FastAPI) -> None:
    target_app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


llm_app = FastAPI(title="SAGE Faculty Twin", version="1.1")
configure_local_cors(llm_app)


class LazyDigitalTwinService:
    """Delay heavy service construction until endpoints actually need it."""

    def __init__(self) -> None:
        self._instance: DigitalTwinService | None = None
        self._lock = threading.Lock()

    def is_initialized(self) -> bool:
        return self._instance is not None

    def ensure_initialized(self) -> DigitalTwinService:
        if self._instance is not None:
            return self._instance
        with self._lock:
            if self._instance is None:
                self._instance = DigitalTwinService(settings)
        return self._instance

    def __getattr__(self, name: str):
        return getattr(self.ensure_initialized(), name)

    def __setattr__(self, name: str, value: object) -> None:
        # Private attributes (_instance, _lock) belong to the proxy itself.
        # Everything else is forwarded to the underlying DigitalTwinService
        # so that test fixtures (``service._llm_client = stub``) correctly
        # mutate the real service instance.
        if name.startswith("_") and name in self.__dict__:
            object.__setattr__(self, name, value)
        elif name.startswith("_"):
            # Use object.__getattribute__ to avoid __getattr__ recursion.
            inst = object.__getattribute__(self, "__dict__").get("_instance")
            if inst is None:
                object.__setattr__(self, name, value)
            else:
                setattr(inst, name, value)
        else:
            setattr(self.ensure_initialized(), name, value)


service = LazyDigitalTwinService()
slack_link_store = SlackUserLinkStore(settings.slack_user_link_dir)
web_dir = Path(__file__).with_name("web")
NO_STORE_HEADERS = {"Cache-Control": "no-store, no-cache, must-revalidate"}
MAX_CHAT_ATTACHMENTS = 4
MAX_CHAT_ATTACHMENT_BYTES = 5 * 1024 * 1024
MAX_CHAT_ATTACHMENT_TEXT_CHARS = 12000
# Hard upper bound for one /chat round-trip. Slightly under Cloudflare's free
# tier 100s edge-timeout so we can return a structured 504 with workflow
# trace progress before the proxy gives up. Tune via
# ``DIGITAL_TWIN_CHAT_REQUEST_TIMEOUT_SECONDS`` if the upstream LLM is
# consistently slower than this budget.
CHAT_REQUEST_TIMEOUT_SECONDS = float(
    os.environ.get("DIGITAL_TWIN_CHAT_REQUEST_TIMEOUT_SECONDS", "80")
)
# Chat Latency Optimizations Task 4: SSE keepalive cadence on the
# ``/chat/workflow-events`` stream. While ``/chat`` is in-flight the LLM
# stage may not emit a trace step for tens of seconds; without a heartbeat
# Cloudflare's idle proxy timeout (~100s on the free plan) can drop the SSE
# connection mid-answer. We emit a typed ``{"type": "keepalive"}`` event
# every ``CHAT_SSE_KEEPALIVE_SECONDS`` seconds so the connection stays warm.
CHAT_SSE_KEEPALIVE_SECONDS = float(os.environ.get("DIGITAL_TWIN_CHAT_SSE_KEEPALIVE_SECONDS", "15"))
# Chat Latency Optimizations Task 5: when this flag is enabled the LLM
# stage emits each token chunk over the workflow-events SSE channel as a
# typed ``answer_delta`` event, followed by a final ``answer_done`` event
# carrying the full ChatResponse dict. The /chat POST still returns the
# same JSON ChatResponse so CLI/test callers see the same contract; the
# browser uses the SSE deltas to paint the answer progressively. Defaults
# to on so streaming works out of the box; set to ``false`` to disable.
STREAM_CHAT_ANSWER = os.environ.get(
    "DIGITAL_TWIN_STREAM_CHAT_ANSWER", "true"
).strip().lower() not in {"0", "false", "no", "off"}
SLACK_TWIN_SIGNING_SECRET = os.environ.get("SLACK_TWIN_SIGNING_SECRET", "").strip()
SLACK_TWIN_ALLOWED_USER_IDS = {
    user_id.strip()
    for user_id in os.environ.get("SLACK_TWIN_ALLOWED_USER_IDS", "").split(",")
    if user_id.strip()
}
SLACK_TWIN_VISITOR_PROFILE = os.environ.get("SLACK_TWIN_VISITOR_PROFILE", "lab_member").strip()
SLACK_TWIN_RESPONSE_TIMEOUT_SECONDS = float(
    os.environ.get("SLACK_TWIN_RESPONSE_TIMEOUT_SECONDS", "95")
)
SLACK_TWIN_BIND_CODE_TTL_SECONDS = int(os.environ.get("SLACK_TWIN_BIND_CODE_TTL_SECONDS", "600"))
SLACK_TWIN_BOT_TOKEN = (
    os.environ.get("SLACK_TWIN_BOT_TOKEN", "").strip()
    or os.environ.get("TWIN_MONITOR_SLACK_BOT_TOKEN", "").strip()
)
SUPPORTED_CHAT_ATTACHMENT_SUFFIXES = {
    ".pdf",
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".py",
    ".yaml",
    ".yml",
    ".log",
}
SUPPORTED_CHAT_ATTACHMENT_MEDIA_TYPES = {
    "application/json",
    "application/pdf",
    "application/x-yaml",
    "text/csv",
    "text/markdown",
    "text/plain",
    "text/x-python",
}


class WorkflowEventBroker:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._streams: dict[
            str,
            tuple[asyncio.AbstractEventLoop, asyncio.Queue[dict[str, object] | None]],
        ] = {}

    async def stream(self, request_id: str) -> AsyncIterator[str]:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[dict[str, object] | None] = asyncio.Queue()
        with self._lock:
            self._streams[request_id] = (loop, queue)

        try:
            while True:
                # Chat Latency Optimizations Task 4: emit a keepalive event
                # whenever no trace step has arrived within the heartbeat
                # window so Cloudflare/edge proxies don't drop the SSE
                # connection while the LLM stage is decoding. The keepalive
                # is a typed JSON event the frontend can ignore explicitly
                # rather than an SSE comment, keeping it observable in dev
                # tools.
                try:
                    payload = await asyncio.wait_for(
                        queue.get(), timeout=CHAT_SSE_KEEPALIVE_SECONDS
                    )
                except asyncio.TimeoutError:
                    yield (
                        "data: " + json.dumps({"type": "keepalive"}, ensure_ascii=False) + "\n\n"
                    )
                    continue
                if payload is None:
                    break
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        finally:
            with self._lock:
                current = self._streams.get(request_id)
                if current is not None and current[1] is queue:
                    self._streams.pop(request_id, None)

    def publish_step(self, request_id: str, step: object) -> None:
        payload = {
            "type": "trace-step",
            "step": getattr(step, "model_dump")(mode="json"),
        }
        self._publish(request_id, payload)

    def publish_answer_chunk(self, request_id: str, delta: str) -> None:
        # Chat Latency Optimizations Task 5: surface streaming LLM tokens
        # to the browser. The frontend appends ``delta`` to the pending
        # assistant message body. Empty deltas are dropped so we don't
        # spam the SSE stream with no-op events when the upstream emits
        # heartbeat/keepalive lines without content tokens.
        if not delta:
            return
        self._publish(request_id, {"type": "answer_delta", "text": delta})

    def publish_answer_done(self, request_id: str, response_dict: dict[str, object]) -> None:
        # Final structured payload — the browser replaces the streamed text
        # with the rendered ChatResponse so it can show ``answer_basis``,
        # ``follow_up_actions``, ``knowledge_hits`` and ``booking_result``
        # consistently with non-streaming sessions.
        self._publish(request_id, {"type": "answer_done", "response": response_dict})

    def publish_error(self, request_id: str, message: str) -> None:
        self._publish(request_id, {"type": "error", "message": message})
        self.close(request_id)

    def publish_complete(self, request_id: str) -> None:
        self._publish(request_id, {"type": "complete"})
        self.close(request_id)

    def close(self, request_id: str) -> None:
        self._publish(request_id, None)

    def _publish(self, request_id: str, payload: dict[str, object] | None) -> None:
        with self._lock:
            stream = self._streams.get(request_id)
        if stream is None:
            return

        loop, queue = stream
        loop.call_soon_threadsafe(queue.put_nowait, payload)


workflow_event_broker = WorkflowEventBroker()


def _raise_chat_validation_error(exc: ValidationError) -> None:
    raise RequestValidationError(exc.errors()) from exc


def _coerce_optional_form_value(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _truncate_attachment_text(text: str) -> str:
    normalized = text.strip()
    if len(normalized) <= MAX_CHAT_ATTACHMENT_TEXT_CHARS:
        return normalized
    return normalized[: MAX_CHAT_ATTACHMENT_TEXT_CHARS - 9].rstrip() + "\n[已截断]"


def _extract_pdf_text(content: bytes, file_name: str) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise HTTPException(status_code=500, detail="当前环境缺少 PDF 解析依赖 pypdf。") from exc

    try:
        reader = PdfReader(BytesIO(content))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"无法读取 PDF 文件：{file_name}") from exc

    text = "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    if not text:
        raise HTTPException(status_code=400, detail=f"PDF 文件没有可提取的文本内容：{file_name}")
    return _truncate_attachment_text(text)


def _extract_text_attachment(content: bytes, file_name: str) -> str:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400, detail=f"文本附件必须使用 UTF-8 编码：{file_name}"
        ) from exc

    text = text.strip()
    if not text:
        raise HTTPException(status_code=400, detail=f"附件没有可用文本内容：{file_name}")
    return _truncate_attachment_text(text)


def _extract_chat_attachment_text(file_name: str, media_type: str, content: bytes) -> str:
    suffix = Path(file_name).suffix.lower()
    normalized_media_type = (media_type or "application/octet-stream").lower()

    if suffix == ".pdf" or normalized_media_type == "application/pdf":
        return _extract_pdf_text(content, file_name)

    if (
        suffix in SUPPORTED_CHAT_ATTACHMENT_SUFFIXES
        or normalized_media_type.startswith("text/")
        or normalized_media_type in SUPPORTED_CHAT_ATTACHMENT_MEDIA_TYPES
    ):
        return _extract_text_attachment(content, file_name)

    raise HTTPException(
        status_code=400,
        detail=f"暂只支持 PDF、TXT、MD、CSV、JSON、PY、YAML、LOG 文件：{file_name}",
    )


async def _parse_chat_attachments(files: list[object]) -> list[ChatAttachment]:
    if len(files) > MAX_CHAT_ATTACHMENTS:
        raise HTTPException(status_code=400, detail=f"一次最多上传 {MAX_CHAT_ATTACHMENTS} 个附件。")

    attachments: list[ChatAttachment] = []
    for upload in files:
        if (
            not hasattr(upload, "filename")
            or not hasattr(upload, "read")
            or not hasattr(upload, "close")
        ):
            continue
        file_name = (upload.filename or "").strip()
        if not file_name:
            raise HTTPException(status_code=400, detail="上传文件必须带文件名。")

        content = await upload.read()
        await upload.close()
        if not content:
            raise HTTPException(status_code=400, detail=f"附件为空：{file_name}")
        if len(content) > MAX_CHAT_ATTACHMENT_BYTES:
            raise HTTPException(status_code=400, detail=f"附件超过 5MB 限制：{file_name}")

        media_type = (
            upload.content_type or "application/octet-stream"
        ).strip() or "application/octet-stream"
        text_content = _extract_chat_attachment_text(file_name, media_type, content)
        try:
            attachments.append(
                ChatAttachment(
                    file_name=file_name,
                    media_type=media_type,
                    size_bytes=len(content),
                    text_content=text_content,
                )
            )
        except ValidationError as exc:
            _raise_chat_validation_error(exc)

    return attachments


async def _parse_chat_request(raw_request: Request) -> ChatRequest:
    content_type = raw_request.headers.get("content-type", "")

    if content_type.startswith("multipart/form-data"):
        form = await raw_request.form()
        files = [item for item in form.getlist("files") if hasattr(item, "filename")]
        payload = {
            "student_name": _coerce_optional_form_value(form.get("student_name")),
            "student_email": _coerce_optional_form_value(form.get("student_email")),
            "course_context": _coerce_optional_form_value(form.get("course_context")),
            "visitor_profile": _coerce_optional_form_value(form.get("visitor_profile")),
            "question": _coerce_optional_form_value(form.get("question")),
            "conversation_id": _coerce_optional_form_value(form.get("conversation_id")),
            "deep_thinking": _coerce_optional_form_value(form.get("deep_thinking")) not in ("false", "0", None),
            "deep_thinking_explicit": _coerce_optional_form_value(
                form.get("deep_thinking_explicit")
            )
            not in ("false", "0", None),
            "web_search": _coerce_optional_form_value(form.get("web_search"))
            in ("true", "1", "on", "yes"),
            "attachments": await _parse_chat_attachments(files),
        }
        try:
            return ChatRequest.model_validate(payload)
        except ValidationError as exc:
            _raise_chat_validation_error(exc)

    try:
        payload = await raw_request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="聊天请求体不是合法 JSON。") from exc

    try:
        return ChatRequest.model_validate(payload)
    except ValidationError as exc:
        _raise_chat_validation_error(exc)


def _resolve_effective_chat_visitor_profile(
    raw_request: Request,
    requested_visitor_profile: str | None,
) -> str | None:
    session_token = raw_request.cookies.get(USER_COOKIE_NAME)
    if not session_token:
        return requested_visitor_profile
    user_session = service.get_user_session(session_token)
    if user_session.is_authenticated and user_session.account is not None:
        return user_session.account.visitor_profile
    return requested_visitor_profile


def _require_user_account(raw_request: Request):
    session = service.get_user_session(raw_request.cookies.get(USER_COOKIE_NAME))
    if not session.is_authenticated or session.account is None:
        raise HTTPException(status_code=403, detail="需要先登录用户账号。")
    return session.account


def _slack_link_status_for_account(account) -> SlackTwinLinkStatusResponse:
    is_lab_member = account.visitor_profile == "lab_member"
    link = slack_link_store.get_link_for_user(account.user_id)
    if not is_lab_member:
        return SlackTwinLinkStatusResponse(
            is_authenticated=True,
            is_lab_member=False,
            can_link=False,
            linked=False,
            message="需要邀请码升级为课题组成员后才能绑定 Slack /twin。",
        )
    return SlackTwinLinkStatusResponse(
        is_authenticated=True,
        is_lab_member=True,
        can_link=True,
        linked=link is not None,
        slack_user_id=link.slack_user_id if link else None,
        linked_at=link.linked_at if link else None,
        message="Slack /twin 已绑定。" if link else "可以生成 Slack 绑定码。",
    )


def _verify_slack_signature(raw_body: bytes, request: Request) -> None:
    if not SLACK_TWIN_SIGNING_SECRET:
        raise HTTPException(status_code=503, detail="Slack twin command is not configured.")

    timestamp = request.headers.get("x-slack-request-timestamp", "")
    signature = request.headers.get("x-slack-signature", "")
    try:
        request_ts = int(timestamp)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid Slack request timestamp.") from exc

    if abs(time.time() - request_ts) > 60 * 5:
        raise HTTPException(status_code=401, detail="Stale Slack request.")

    base = b"v0:" + str(request_ts).encode("ascii") + b":" + raw_body
    expected = "v0=" + hmac.new(
        SLACK_TWIN_SIGNING_SECRET.encode("utf-8"),
        base,
        hashlib.sha256,
    ).hexdigest()
    if not secrets.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid Slack signature.")


def _post_slack_response(response_url: str, text: str, *, response_type: str = "ephemeral") -> None:
    payload = json.dumps(
        {"response_type": response_type, "text": text},
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        response_url,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    urllib.request.urlopen(req, timeout=8).read()


def _post_slack_api(method: str, payload: dict[str, object]) -> dict[str, object]:
    if not SLACK_TWIN_BOT_TOKEN:
        raise RuntimeError("Slack bot token is not configured.")
    req = urllib.request.Request(
        f"https://slack.com/api/{method}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {SLACK_TWIN_BOT_TOKEN}",
            "Content-Type": "application/json; charset=utf-8",
        },
    )
    response = urllib.request.urlopen(req, timeout=8)
    body = response.read().decode("utf-8")
    parsed = json.loads(body) if body else {}
    if not parsed.get("ok"):
        raise RuntimeError(f"Slack API {method} failed: {parsed.get('error', 'unknown_error')}")
    return parsed


def _post_slack_message(channel_id: str, text: str, *, thread_ts: str | None = None) -> None:
    payload: dict[str, object] = {"channel": channel_id, "text": text}
    if thread_ts:
        payload["thread_ts"] = thread_ts
    _post_slack_api("chat.postMessage", payload)


def _safe_post_slack_response(
    response_url: str, text: str, *, response_type: str = "ephemeral"
) -> bool:
    try:
        _post_slack_response(response_url, text, response_type=response_type)
        return True
    except Exception as exc:  # pragma: no cover - exception type depends on network stack
        _logger.warning("Failed to post Slack /twin response: %s", exc)
        return False


def _safe_post_slack_message(
    channel_id: str, text: str, *, thread_ts: str | None = None
) -> bool:
    try:
        _post_slack_message(channel_id, text, thread_ts=thread_ts)
        return True
    except Exception as exc:  # pragma: no cover - exception type depends on network stack
        _logger.warning("Failed to post Slack twin DM response: %s", exc)
        return False


def _slack_twin_link_instructions() -> str:
    return (
        "请先登录 twin 网页端账号，生成 Slack 绑定码，然后在 Slack 输入 "
        "`/twin bind 你的绑定码` 完成绑定。"
    )


def _normalize_slack_twin_question(text: str) -> str:
    words = text.split()
    while words and words[0].startswith("<@") and words[0].endswith(">"):
        words.pop(0)
    return " ".join(words).strip()


def _handle_slack_twin_bind_text(*, user_id: str, text: str) -> str | None:
    normalized_text = _normalize_slack_twin_question(text)
    words = normalized_text.split()
    if not words or words[0].lower() != "bind":
        return None
    if len(words) < 2:
        return "用法：`/twin bind 你的绑定码`"
    link = slack_link_store.consume_code(words[1], slack_user_id=user_id)
    if link is None:
        return "绑定码无效或已过期。请回到 twin 网页端重新生成 Slack 绑定码。"
    if link.visitor_profile != "lab_member":
        return "这个账号还不是课题组成员，需要邀请码升级为课题组成员后才能使用 Slack /twin。"
    return (
        "绑定成功。以后可以直接输入 `/twin 你的问题`，"
        f"或者直接给 twin 发私信。已绑定账号：{link.email}"
    )


def _resolve_slack_twin_identity(user_id: str) -> tuple[str, str | None, str | None]:
    visitor_profile = SLACK_TWIN_VISITOR_PROFILE or "lab_member"
    user_email = None
    if user_id in SLACK_TWIN_ALLOWED_USER_IDS:
        return visitor_profile, user_email, None
    linked_account = slack_link_store.get_link_for_slack_user(user_id)
    if linked_account is None:
        return visitor_profile, user_email, _slack_twin_link_instructions()
    if linked_account.visitor_profile != "lab_member":
        return (
            visitor_profile,
            user_email,
            "已绑定账号不是课题组成员。需要邀请码升级为课题组成员后才能使用 Slack /twin。",
        )
    return linked_account.visitor_profile, linked_account.email, None


def _format_slack_twin_answer(response: ChatResponse, *, question: str | None = None) -> str:
    lines: list[str] = []
    normalized_question = (question or "").strip()
    if normalized_question:
        lines.append(f"你问：{normalized_question}")
    lines.append(response.answer.strip())
    if response.answer_basis:
        basis = "；".join(item.title for item in response.answer_basis[:2])
        if basis:
            lines.append(f"\n依据：{basis}")
    if response.used_model:
        lines.append(f"\n模型：`{response.used_model}`")
    return "\n".join(line for line in lines if line)


async def _answer_slack_twin_question(
    *,
    question: str,
    user_id: str,
    user_name: str | None,
    user_email: str | None = None,
    visitor_profile: str = "lab_member",
    course_context: str = "Slack /twin",
    delivery_callback,
) -> None:
    try:
        chat_request = ChatRequest(
            student_name=user_name or user_id,
            student_email=user_email,
            question=question,
            course_context=course_context,
            visitor_profile=visitor_profile,
            conversation_id=f"slack-{user_id}-{uuid4().hex}",
            deep_thinking=False,
            deep_thinking_explicit=False,
            web_search=False,
        )
        response = await asyncio.wait_for(
            service.answer(chat_request),
            timeout=SLACK_TWIN_RESPONSE_TIMEOUT_SECONDS,
        )
        await asyncio.to_thread(
            delivery_callback,
            _format_slack_twin_answer(response, question=question),
        )
    except Exception as exc:
        await asyncio.to_thread(
            delivery_callback,
            f"抱歉，twin 这次没有完成回答：{exc}",
        )


async def _answer_slack_twin_command(
    *,
    response_url: str,
    question: str,
    user_id: str,
    user_name: str | None,
    user_email: str | None = None,
    visitor_profile: str = "lab_member",
) -> None:
    def deliver(text: str) -> bool:
        return _safe_post_slack_response(response_url, text, response_type="ephemeral")

    await _answer_slack_twin_question(
        question=question,
        user_id=user_id,
        user_name=user_name,
        user_email=user_email,
        visitor_profile=visitor_profile,
        course_context="Slack /twin",
        delivery_callback=deliver,
    )


async def _answer_slack_twin_dm(
    *,
    channel_id: str,
    question: str,
    user_id: str,
    user_name: str | None,
    user_email: str | None = None,
    visitor_profile: str = "lab_member",
    thread_ts: str | None = None,
    course_context: str = "Slack DM",
) -> None:
    def deliver(text: str) -> bool:
        return _safe_post_slack_message(channel_id, text, thread_ts=thread_ts)

    await _answer_slack_twin_question(
        question=question,
        user_id=user_id,
        user_name=user_name,
        user_email=user_email,
        visitor_profile=visitor_profile,
        course_context=course_context,
        delivery_callback=deliver,
    )


def frontend_asset(filename: str) -> FileResponse:
    return FileResponse(web_dir / filename, headers=NO_STORE_HEADERS)


def require_admin_session(request: Request) -> dict:
    return service.require_admin_session(request.cookies.get(ADMIN_COOKIE_NAME))


llm_app.mount("/static", StaticFiles(directory=web_dir), name="static")


@llm_app.get("/", include_in_schema=False)
async def home() -> FileResponse:
    return FileResponse(web_dir / "index.html", headers=NO_STORE_HEADERS)


@llm_app.get("/styles.css", include_in_schema=False)
@llm_app.get("/styles.4217.css", include_in_schema=False)
async def styles() -> FileResponse:
    return frontend_asset("styles.css")


@llm_app.get("/home", include_in_schema=False)
@llm_app.get("/home/", include_in_schema=False)
async def homepage_redirect() -> RedirectResponse:
    target = settings.homepage_public_url or "https://shuhaozhangtony.github.io/"
    return RedirectResponse(url=target, status_code=302)


@llm_app.get("/app.js", include_in_schema=False)
@llm_app.get("/app.4217.js", include_in_schema=False)
@llm_app.get("/app.4218.js", include_in_schema=False)
async def app_js() -> FileResponse:
    return frontend_asset("app.js")


@llm_app.get("/auth/session", response_model=AdminSessionResponse)
async def auth_session(request: Request) -> AdminSessionResponse:
    return service.get_admin_session(request.cookies.get(ADMIN_COOKIE_NAME))


@llm_app.get("/auth/user/session", response_model=UserSessionResponse)
async def user_auth_session(request: Request) -> UserSessionResponse:
    return service.get_user_session(request.cookies.get(USER_COOKIE_NAME))


@llm_app.get("/slack/twin-link/status", response_model=SlackTwinLinkStatusResponse)
async def slack_twin_link_status(request: Request) -> SlackTwinLinkStatusResponse:
    session = service.get_user_session(request.cookies.get(USER_COOKIE_NAME))
    if not session.is_authenticated or session.account is None:
        return SlackTwinLinkStatusResponse(
            is_authenticated=False,
            is_lab_member=False,
            can_link=False,
            linked=False,
            message="需要先登录用户账号。",
        )
    return _slack_link_status_for_account(session.account)


@llm_app.post("/slack/twin-link/code", response_model=SlackTwinLinkCodeResponse)
async def create_slack_twin_link_code(request: Request) -> SlackTwinLinkCodeResponse:
    account = _require_user_account(request)
    is_lab_member = account.visitor_profile == "lab_member"
    if not is_lab_member:
        return SlackTwinLinkCodeResponse(
            is_authenticated=True,
            is_lab_member=False,
            can_link=False,
            message="需要邀请码升级为课题组成员后才能绑定 Slack /twin。",
        )
    code = slack_link_store.create_code(
        user_id=account.user_id,
        email=account.email,
        visitor_profile=account.visitor_profile,
        ttl_seconds=SLACK_TWIN_BIND_CODE_TTL_SECONDS,
    )
    return SlackTwinLinkCodeResponse(
        is_authenticated=True,
        is_lab_member=True,
        can_link=True,
        code=code.code,
        expires_at=code.expires_at,
        message="绑定码已生成，请在 Slack 输入 /twin bind 你的绑定码。",
    )


@llm_app.get("/admin/services", response_model=ServiceControlResponse)
async def get_managed_services(
    _: dict = Depends(require_admin_session),
) -> ServiceControlResponse:
    return service.get_managed_services()


@llm_app.post("/admin/services/{action}", response_model=ServiceControlResponse)
async def control_managed_services(
    action: str,
    _: dict = Depends(require_admin_session),
) -> ServiceControlResponse:
    try:
        return service.control_managed_services(action)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@llm_app.post("/auth/admin/login", response_model=AdminSessionResponse)
async def admin_login(payload: AdminLoginRequest, response: Response) -> AdminSessionResponse:
    result = service.login_admin(payload)
    set_admin_session_cookie(response, result.session_token, settings)
    return result.session


@llm_app.post("/auth/admin/logout", response_model=AdminSessionResponse)
async def admin_logout(response: Response) -> AdminSessionResponse:
    clear_admin_session_cookie(response)
    return service.logout_admin()


@llm_app.post("/auth/user/register", response_model=UserSessionResponse)
async def user_register(payload: UserRegisterRequest, response: Response) -> UserSessionResponse:
    result = service.register_user(payload)
    set_user_session_cookie(response, result.session_token, settings)
    return result.session


@llm_app.post("/auth/user/login", response_model=UserSessionResponse)
async def user_login(payload: UserLoginRequest, response: Response) -> UserSessionResponse:
    result = service.login_user(payload)
    set_user_session_cookie(response, result.session_token, settings)
    return result.session


@llm_app.post("/auth/user/logout", response_model=UserSessionResponse)
async def user_logout(response: Response) -> UserSessionResponse:
    clear_user_session_cookie(response)
    return service.logout_user()


@llm_app.get("/health")
async def health() -> dict[str, object]:
    if not service.is_initialized():
        return {
            "status": "starting",
            "app_version": __version__,
            "message": "Service is initializing in background.",
            "model": settings.model_name or "detecting...",
            "owner_name": settings.owner_name,
            "owner_role": settings.owner_role,
            "homepage_public_url": settings.homepage_public_url,
            "stack_version_sage": "unknown",
            "stack_version_neuromem": "unknown",
            "stack_version_vllm_hust": "unknown",
            "stack_version_sagevdb": "unknown",
            "stack_version_sage_anns": "unknown",
            "sage_runtime": "FlowNetEnvironment",
        }
    return service.health()


@llm_app.get("/stack/versions")
async def stack_versions() -> dict[str, str]:
    return build_stack_versions_payload()


@llm_app.get("/stack/hardware")
async def stack_hardware() -> dict[str, str]:
    return build_hardware_payload()


@llm_app.post("/presence/heartbeat", response_model=OnlinePresenceHeartbeatResponse)
async def record_presence_heartbeat(
    request: OnlinePresenceHeartbeatRequest,
) -> OnlinePresenceHeartbeatResponse:
    return service.record_online_presence(request)


@llm_app.get("/lucky-question")
async def lucky_question(
    visitor_profile: str = Query(default="general_visitor"),
    recent: str = Query(default="", description="Comma-separated recent questions to avoid"),
    onboarding_step: str = Query(default="", description="Current onboarding step label for context"),
) -> dict[str, str]:
    """Ask the LLM to generate a contextual question for the
    "I'm feeling lucky" button.  Returns ``{}`` on failure so the
    frontend can fall back to the static question bank."""
    if not service.is_initialized():
        return {}
    recent_questions = [q.strip() for q in recent.split(",") if q.strip()] if recent else None
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(
                service.generate_lucky_question,
                visitor_profile=visitor_profile,
                recent_questions=recent_questions,
                onboarding_step=onboarding_step,
            ),
            timeout=8.0,
        )
    except asyncio.TimeoutError:
        return {}
    return result if isinstance(result, dict) else {}


@llm_app.get("/availability", response_model=AvailabilitySchedule)
async def get_availability(
    _: dict = Depends(require_admin_session),
) -> AvailabilitySchedule:
    return service.get_availability_schedule()


@llm_app.put("/availability", response_model=AvailabilitySchedule)
async def update_availability(
    request: AvailabilitySchedule,
    _: dict = Depends(require_admin_session),
) -> AvailabilitySchedule:
    return service.update_availability_schedule(request)


@llm_app.get("/availability/previous-week", response_model=AvailabilitySchedule)
async def get_previous_week_availability_template(
    week_of: date | None = Query(default=None),
    _: dict = Depends(require_admin_session),
) -> AvailabilitySchedule:
    return service.get_previous_week_availability_template(week_of)


@llm_app.get("/chat/workflow-events", include_in_schema=False)
async def chat_workflow_events(
    request_id: str = Query(min_length=1, max_length=128),
) -> StreamingResponse:
    return StreamingResponse(
        workflow_event_broker.stream(request_id),
        media_type="text/event-stream",
        headers={
            **NO_STORE_HEADERS,
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@llm_app.post("/slack/commands/twin", include_in_schema=False)
async def slack_twin_command(
    raw_request: Request,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    raw_body = await raw_request.body()
    _verify_slack_signature(raw_body, raw_request)

    form = {
        key: values[-1] if values else ""
        for key, values in urllib.parse.parse_qs(raw_body.decode("utf-8")).items()
    }
    user_id = form.get("user_id", "").strip()
    question = form.get("text", "").strip()
    response_url = form.get("response_url", "").strip()
    if not question:
        return JSONResponse(
            {
                "response_type": "ephemeral",
                "text": "用法：`/twin 你的问题`",
            }
        )
    if not response_url:
        raise HTTPException(status_code=400, detail="Slack request missing response_url.")

    bind_reply = _handle_slack_twin_bind_text(user_id=user_id, text=question)
    if bind_reply is not None:
        return JSONResponse({"response_type": "ephemeral", "text": bind_reply})

    visitor_profile, user_email, denial_message = _resolve_slack_twin_identity(user_id)
    if denial_message is not None:
        return JSONResponse({"response_type": "ephemeral", "text": denial_message})

    background_tasks.add_task(
        _answer_slack_twin_command,
        response_url=response_url,
        question=question,
        user_id=user_id or "slack-user",
        user_name=form.get("user_name") or user_id or None,
        user_email=user_email,
        visitor_profile=visitor_profile,
    )
    question_preview = question if len(question) <= 80 else f"{question[:77]}..."
    return JSONResponse(
        {
            "response_type": "ephemeral",
            "text": f"收到，我正在问 twin。\n你问：{question_preview}\n答案会稍后发回这里。",
        }
    )


@llm_app.post("/slack/events", include_in_schema=False)
async def slack_events(
    raw_request: Request,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    raw_body = await raw_request.body()
    _verify_slack_signature(raw_body, raw_request)
    try:
        payload = json.loads(raw_body.decode("utf-8") or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid Slack event payload.") from exc

    if payload.get("type") == "url_verification":
        return JSONResponse({"challenge": payload.get("challenge", "")})

    if raw_request.headers.get("x-slack-retry-num"):
        return JSONResponse({"ok": True})
    if payload.get("type") != "event_callback":
        return JSONResponse({"ok": True})

    event = payload.get("event")
    if not isinstance(event, dict):
        return JSONResponse({"ok": True})
    event_type = str(event.get("type") or "").strip()
    if event_type not in {"message", "app_mention"}:
        return JSONResponse({"ok": True})
    if event.get("subtype") or event.get("bot_id"):
        return JSONResponse({"ok": True})

    channel_type = str(event.get("channel_type") or "").strip()
    is_direct_message = channel_type == "im"
    is_public_mention = event_type == "app_mention"
    if not is_direct_message and not is_public_mention:
        return JSONResponse({"ok": True})

    user_id = str(event.get("user") or "").strip()
    channel_id = str(event.get("channel") or "").strip()
    question = _normalize_slack_twin_question(str(event.get("text") or ""))
    thread_ts = str(event.get("thread_ts") or "").strip() or None
    if is_public_mention and thread_ts is None:
        thread_ts = str(event.get("ts") or "").strip() or None
    if not user_id or not channel_id:
        return JSONResponse({"ok": True})
    if not question:
        usage_text = "用法：`@twin 你的问题`、`/twin 你的问题`，或者直接给 twin 发私信。"
        background_tasks.add_task(_safe_post_slack_message, channel_id, usage_text, thread_ts=thread_ts)
        return JSONResponse({"ok": True})

    bind_reply = _handle_slack_twin_bind_text(user_id=user_id, text=question)
    if bind_reply is not None:
        background_tasks.add_task(_safe_post_slack_message, channel_id, bind_reply, thread_ts=thread_ts)
        return JSONResponse({"ok": True})

    visitor_profile, user_email, denial_message = _resolve_slack_twin_identity(user_id)
    if denial_message is not None:
        background_tasks.add_task(_safe_post_slack_message, channel_id, denial_message, thread_ts=thread_ts)
        return JSONResponse({"ok": True})

    background_tasks.add_task(
        _answer_slack_twin_dm,
        channel_id=channel_id,
        question=question,
        user_id=user_id,
        user_name=str(event.get("username") or user_id or "").strip() or None,
        user_email=user_email,
        visitor_profile=visitor_profile,
        thread_ts=thread_ts,
        course_context="Slack @twin" if is_public_mention else "Slack DM",
    )
    return JSONResponse({"ok": True})


@llm_app.on_event("startup")
async def startup_event() -> None:
    if settings.warm_service_on_startup:
        instance = await asyncio.to_thread(service.ensure_initialized)
        await asyncio.to_thread(instance.warm_fixed_prefix_cache)


@llm_app.on_event("shutdown")
async def shutdown_event() -> None:
    if service.is_initialized():
        await service.aclose()


@llm_app.post("/chat", response_model=ChatResponse)
async def chat(
    raw_request: Request,
    request_id: str | None = Query(default=None, min_length=1, max_length=128),
) -> ChatResponse:
    payload = await _parse_chat_request(raw_request)
    payload = payload.model_copy(
        update={
            "visitor_profile": _resolve_effective_chat_visitor_profile(
                raw_request,
                payload.visitor_profile,
            )
        }
    )
    admin_session_token = raw_request.cookies.get(ADMIN_COOKIE_NAME)
    timeout_seconds = CHAT_REQUEST_TIMEOUT_SECONDS

    if request_id is None:
        try:
            return await asyncio.wait_for(
                service.answer(payload, admin_session_token=admin_session_token),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            raise HTTPException(
                status_code=504,
                detail=(f"后端在 {int(timeout_seconds)} 秒内未完成响应，请稍后重试。"),
            ) from exc

    # When ``request_id`` is supplied the chat workflow streams trace events
    # over the workflow-events SSE channel. With
    # ``DIGITAL_TWIN_POST_ANSWER_BACKGROUND`` enabled the service returns the
    # rendered ``ChatResponse`` immediately after ``response_render`` and runs
    # the four post-answer side-effects (memory_persist, profile,
    # follow_up_plan, usefulness_score) on a background task. We defer
    # ``publish_complete`` until that background task finishes so the SSE
    # consumer still sees the post-answer trace steps before the stream
    # closes.
    def _on_post_answer_complete() -> None:
        workflow_event_broker.publish_complete(request_id)

    answer_chunk_callback = None
    if STREAM_CHAT_ANSWER:
        # Chat Latency Optimizations Task 5: only attach the streaming
        # callback when the feature flag is on. The service then asks
        # the LLM client for a streaming completion and forwards each
        # chunk to the SSE broker so the browser can paint tokens as
        # they arrive.
        def _on_answer_chunk(delta: str) -> None:
            workflow_event_broker.publish_answer_chunk(request_id, delta)

        answer_chunk_callback = _on_answer_chunk

    try:
        response = await asyncio.wait_for(
            service.answer(
                payload,
                admin_session_token=admin_session_token,
                trace_callback=lambda step: workflow_event_broker.publish_step(request_id, step),
                on_post_answer_complete=_on_post_answer_complete,
                answer_chunk_callback=answer_chunk_callback,
            ),
            timeout=timeout_seconds,
        )
    except asyncio.TimeoutError as exc:
        message = f"后端在 {int(timeout_seconds)} 秒内未完成响应，请稍后重试。"
        workflow_event_broker.publish_error(request_id, message)
        raise HTTPException(status_code=504, detail=message) from exc
    except Exception as exc:
        workflow_event_broker.publish_error(request_id, str(exc))
        raise

    if STREAM_CHAT_ANSWER:
        # Surface the final structured ChatResponse to the SSE channel so
        # the streaming UI can swap the progressively-painted text for the
        # rendered fields (answer_basis, follow_up_actions, etc.) without
        # re-fetching anything.
        try:
            workflow_event_broker.publish_answer_done(request_id, response.model_dump(mode="json"))
        except Exception:  # pragma: no cover - defensive
            pass

    return response


@llm_app.post("/chat/feedback", response_model=ChatFeedbackResponse)
async def submit_chat_feedback(request: ChatFeedbackRequest) -> ChatFeedbackResponse:
    return service.submit_chat_feedback(request)


@llm_app.post("/context/compress")
async def compress_context(raw_request: Request) -> JSONResponse:
    """Manually trigger context compression for a conversation."""
    user_session = service.get_user_session(raw_request.cookies.get(USER_COOKIE_NAME))
    if not user_session.is_authenticated:
        raise HTTPException(status_code=401, detail="请先登录后再压缩对话上下文。")
    try:
        payload = await raw_request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="无效的 JSON 请求体") from None

    conversation_id = str(payload.get("conversation_id", "") or "").strip()
    if not conversation_id:
        raise HTTPException(status_code=422, detail="conversation_id 不能为空")

    result = service.compress_conversation_context(conversation_id)
    return JSONResponse(content=result)


@llm_app.get("/chat/conversations", response_model=ConversationHistoryListResponse)
async def list_chat_conversations(
    request: Request,
    student_email: str | None = Query(default=None, max_length=256),
    limit: int = Query(default=30, ge=1, le=100),
) -> ConversationHistoryListResponse:
    user_session = service.get_user_session(request.cookies.get(USER_COOKIE_NAME))
    resolved_email = resolve_authenticated_history_email(
        is_authenticated=user_session.is_authenticated,
        account_email=(user_session.account.email if user_session.account else None),
        requested_email=student_email,
    )
    return service.list_chat_conversations(student_email=resolved_email, limit=limit)


@llm_app.get(
    "/chat/conversations/{conversation_id}",
    response_model=ConversationTranscriptResponse,
)
async def get_chat_conversation(
    conversation_id: str,
    request: Request,
    student_email: str | None = Query(default=None, max_length=256),
) -> ConversationTranscriptResponse:
    user_session = service.get_user_session(request.cookies.get(USER_COOKIE_NAME))
    resolved_email = resolve_authenticated_history_email(
        is_authenticated=user_session.is_authenticated,
        account_email=(user_session.account.email if user_session.account else None),
        requested_email=student_email,
    )
    return service.get_chat_conversation(
        conversation_id=conversation_id, student_email=resolved_email
    )


@llm_app.post("/suggestions", response_model=AnonymousSuggestionRecord)
async def submit_anonymous_suggestion(
    request: AnonymousSuggestionCreate, raw_request: Request
) -> AnonymousSuggestionRecord:
    return service.submit_anonymous_suggestion(
        request,
        admin_session_token=raw_request.cookies.get(ADMIN_COOKIE_NAME),
    )


@llm_app.get("/suggestions", response_model=list[AnonymousSuggestionRecord])
async def list_anonymous_suggestions(
    raw_request: Request,
    limit: int = Query(default=50, ge=1, le=100),
) -> list[AnonymousSuggestionRecord]:
    return service.list_anonymous_suggestions(
        limit=limit,
        admin_session_token=raw_request.cookies.get(ADMIN_COOKIE_NAME),
    )


@llm_app.post("/knowledge", response_model=KnowledgeDocumentRecord)
async def create_knowledge_document(
    request: KnowledgeDocumentCreate,
    _: dict = Depends(require_admin_session),
) -> KnowledgeDocumentRecord:
    return service.add_knowledge(request)


@llm_app.post("/knowledge/{document_id}/review", response_model=KnowledgeDocumentActionResponse)
async def review_knowledge_document(
    document_id: str,
    request: KnowledgeDocumentReviewRequest,
    _: dict = Depends(require_admin_session),
) -> KnowledgeDocumentActionResponse:
    return service.review_knowledge_document(document_id, request)


@llm_app.delete("/knowledge/{document_id}", response_model=KnowledgeDocumentActionResponse)
async def delete_knowledge_document(
    document_id: str,
    _: dict = Depends(require_admin_session),
) -> KnowledgeDocumentActionResponse:
    return service.delete_knowledge_document(document_id)


@llm_app.get("/knowledge", response_model=list[KnowledgeDocumentRecord])
async def list_knowledge_documents(
    _: dict = Depends(require_admin_session),
) -> list[KnowledgeDocumentRecord]:
    return service.list_knowledge()


@llm_app.get("/knowledge/reviews/summary", response_model=KnowledgeDocumentReviewSummary)
async def get_knowledge_review_summary(
    limit: int = Query(default=20, ge=1, le=100),
    _: dict = Depends(require_admin_session),
) -> KnowledgeDocumentReviewSummary:
    return service.list_knowledge_review_summary(limit=limit)


@llm_app.get("/knowledge/search", response_model=KnowledgeSearchResponse)
async def search_knowledge_documents(
    query: str = Query(min_length=1, max_length=256),
    visitor_profile: str | None = Query(
        default=None,
        pattern="^(hust_undergraduate|paper_writing_student|lab_member|general_visitor)$",
    ),
    admin_session: dict = Depends(require_admin_session),
) -> KnowledgeSearchResponse:
    return service.search_knowledge(
        query,
        visitor_profile=visitor_profile,
        admin_role=str(admin_session.get("role") or "super_admin"),
    )


@llm_app.get("/memory/profiles", response_model=MemoryProfileListResponse)
async def list_memory_profiles(
    category: str | None = Query(default=None, max_length=64),
    student_query: str | None = Query(default=None, max_length=128),
    limit: int = Query(default=50, ge=1, le=200),
    _: dict = Depends(require_admin_session),
) -> MemoryProfileListResponse:
    return service.list_memory_profiles(category=category, student_query=student_query, limit=limit)


@llm_app.get("/analytics/questions", response_model=QuestionAnalyticsReportResponse)
async def get_question_analytics_report(
    days: int = Query(default=7, ge=1, le=90),
    _: dict = Depends(require_admin_session),
) -> QuestionAnalyticsReportResponse:
    return service.get_question_analytics_report(days=days)


@llm_app.get("/operations/overview", response_model=OperationsOverviewResponse)
async def get_operations_overview(
    days: int = Query(default=7, ge=1, le=90),
    _: dict = Depends(require_admin_session),
) -> OperationsOverviewResponse:
    return service.get_operations_overview(days=days)


@llm_app.get("/operations/workbench", response_model=OperationsWorkbenchResponse)
async def get_operations_workbench(
    days: int = Query(default=7, ge=1, le=90),
    limit: int = Query(default=10, ge=1, le=50),
    _: dict = Depends(require_admin_session),
) -> OperationsWorkbenchResponse:
    return service.get_operations_workbench(days=days, limit=limit)


@llm_app.get("/workflow/replay", response_model=WorkflowReplayReportResponse)
async def get_workflow_replay_report(
    _: dict = Depends(require_admin_session),
) -> WorkflowReplayReportResponse:
    return service.get_workflow_replay_report()


@llm_app.patch("/operations/tasks/{task_key}", response_model=OperationsTaskStateRecord)
async def update_operations_task_state(
    task_key: str,
    request: OperationsTaskStateUpdateRequest,
    _: dict = Depends(require_admin_session),
) -> OperationsTaskStateRecord:
    return service.update_operations_task_state(task_key, request)


@llm_app.get(
    "/analytics/questions/gap-drafts",
    response_model=list[KnowledgeGapDraftRecordResponse],
)
async def list_knowledge_gap_drafts(
    _: dict = Depends(require_admin_session),
) -> list[KnowledgeGapDraftRecordResponse]:
    return service.list_knowledge_gap_drafts()


@llm_app.get("/memory/artifact-drafts", response_model=list[ArtifactMemoryDraftRecordResponse])
async def list_artifact_memory_drafts(
    _: dict = Depends(require_admin_session),
) -> list[ArtifactMemoryDraftRecordResponse]:
    return service.list_artifact_memory_drafts()


@llm_app.post(
    "/memory/artifact-drafts/{draft_id}/accept",
    response_model=ArtifactMemoryDraftRecordResponse,
)
async def accept_artifact_memory_draft(
    draft_id: str,
    _: dict = Depends(require_admin_session),
) -> ArtifactMemoryDraftRecordResponse:
    return service.accept_artifact_memory_draft(draft_id)


@llm_app.post(
    "/memory/artifact-drafts/{draft_id}/reject",
    response_model=ArtifactMemoryDraftRecordResponse,
)
async def reject_artifact_memory_draft(
    draft_id: str,
    _: dict = Depends(require_admin_session),
) -> ArtifactMemoryDraftRecordResponse:
    return service.reject_artifact_memory_draft(draft_id)


@llm_app.post("/analytics/questions/gap-drafts", response_model=KnowledgeGapDraftRecordResponse)
async def create_knowledge_gap_draft(
    request: KnowledgeGapDraftCreateRequest,
    _: dict = Depends(require_admin_session),
) -> KnowledgeGapDraftRecordResponse:
    return service.create_knowledge_gap_draft(request)


@llm_app.post(
    "/analytics/questions/gap-drafts/{draft_id}/publish",
    response_model=KnowledgeGapDraftRecordResponse,
)
async def publish_knowledge_gap_draft(
    draft_id: str,
    _: dict = Depends(require_admin_session),
) -> KnowledgeGapDraftRecordResponse:
    return service.publish_knowledge_gap_draft(draft_id)


@llm_app.get("/escalations", response_model=list[EscalationRecord])
async def list_escalations(
    status: str | None = Query(default=None, max_length=32),
    route: str | None = Query(default=None, max_length=32),
    _: dict = Depends(require_admin_session),
) -> list[EscalationRecord]:
    return service.list_escalations(status=status, route=route)


@llm_app.post("/escalations/{escalation_id}/resolve", response_model=EscalationRecord)
async def resolve_escalation(
    escalation_id: str,
    request: EscalationDecisionRequest,
    _: dict = Depends(require_admin_session),
) -> EscalationRecord:
    return service.resolve_escalation(escalation_id, request)


@llm_app.get("/follow-ups", response_model=list[FollowUpQueueRecord])
async def list_follow_ups(
    status: str | None = Query(default=None, max_length=32),
    action_type: str | None = Query(default=None, max_length=64),
    _: dict = Depends(require_admin_session),
) -> list[FollowUpQueueRecord]:
    return service.list_follow_up_actions(status=status, action_type=action_type)


@llm_app.post("/follow-ups/dispatch", response_model=FollowUpDispatchResponse)
async def dispatch_follow_ups(
    _: dict = Depends(require_admin_session),
) -> FollowUpDispatchResponse:
    return service.dispatch_due_follow_ups()


@llm_app.post("/bookings", response_model=BookingResponse)
async def create_booking(request: BookingRequest) -> BookingResponse:
    return service.book_meeting(request)


@llm_app.get("/bookings", response_model=list[BookingRecord])
async def list_bookings(
    status: str | None = Query(default=None, max_length=32),
    _: dict = Depends(require_admin_session),
) -> list[BookingRecord]:
    return service.list_bookings(status=status)


@llm_app.post("/bookings/{booking_id}/confirm", response_model=BookingResponse)
async def confirm_booking(
    booking_id: str,
    _: dict = Depends(require_admin_session),
) -> BookingResponse:
    return service.confirm_booking(booking_id)


@llm_app.post("/bookings/{booking_id}/reject", response_model=BookingResponse)
async def reject_booking(
    booking_id: str,
    request: BookingDecisionRequest,
    _: dict = Depends(require_admin_session),
) -> BookingResponse:
    return service.reject_booking(booking_id, request)


@llm_app.get("/changelog")
async def get_changelog() -> list[dict[str, object]]:
    """Return version changelog entries from data/changelog.json."""
    changelog_file = settings.changelog_path
    if not changelog_file.is_file():
        return []
    try:
        raw = json.loads(changelog_file.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            return []
        return raw  # type: ignore[return-value]
    except Exception:
        return []


@llm_app.get("/capabilities")
async def get_capabilities(
    _: dict = Depends(require_admin_session),
) -> list[CapabilityPluginStatus]:
    """Return loaded capability plugin statuses for the operations console."""
    registry = CapabilityPluginRegistry(
        plugin_dir=settings.capability_plugin_dir,
        current_version=__version__,
    )
    registry.load()
    return registry.statuses


app = create_edge_app(mount_llm=True, llm_prefix="/", llm_app=llm_app)
configure_local_cors(app)
app.mount("/static", StaticFiles(directory=web_dir), name="static")
