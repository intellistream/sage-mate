import asyncio
import json
import threading
from collections.abc import AsyncIterator
from datetime import date
from pathlib import Path

from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi import Query
from fastapi import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from sage.edge.app import create_app as create_edge_app

from .auth import ADMIN_COOKIE_NAME
from .auth import clear_admin_session_cookie
from .auth import clear_user_session_cookie
from .auth import set_admin_session_cookie
from .auth import set_user_session_cookie
from .auth import USER_COOKIE_NAME
from .config import settings
from .models import (
    AdminLoginRequest,
    AdminSessionResponse,
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
    FollowUpDispatchResponse,
    FollowUpQueueRecord,
    KnowledgeGapDraftCreateRequest,
    KnowledgeGapDraftRecordResponse,
    KnowledgeDocumentCreate,
    KnowledgeDocumentRecord,
    KnowledgeSearchResponse,
    MemoryProfileListResponse,
    QuestionAnalyticsReportResponse,
    ServiceControlResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserSessionResponse,
)
from .service import DigitalTwinService


def configure_local_cors(target_app: FastAPI) -> None:
    target_app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


llm_app = FastAPI(title="SAGE Faculty Twin", version="0.1.0")
configure_local_cors(llm_app)
service = DigitalTwinService(settings)
web_dir = Path(__file__).with_name("web")
homepage_dir = settings.homepage_dir.resolve()
NO_STORE_HEADERS = {"Cache-Control": "no-store, no-cache, must-revalidate"}


class WorkflowEventBroker:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._streams: dict[str, tuple[asyncio.AbstractEventLoop, asyncio.Queue[dict[str, object] | None]]] = {}

    async def stream(self, request_id: str) -> AsyncIterator[str]:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[dict[str, object] | None] = asyncio.Queue()
        with self._lock:
            self._streams[request_id] = (loop, queue)

        try:
            while True:
                payload = await queue.get()
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


def frontend_asset(filename: str) -> FileResponse:
    return FileResponse(web_dir / filename, headers=NO_STORE_HEADERS)


def homepage_asset(asset_path: str = "index.html") -> FileResponse:
    candidate = (homepage_dir / asset_path).resolve()
    try:
        candidate.relative_to(homepage_dir)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Not Found") from exc

    if candidate.is_dir():
        candidate = candidate / "index.html"

    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="Not Found")

    return FileResponse(candidate, headers=NO_STORE_HEADERS)


def require_admin_session(request: Request) -> dict:
    return service.require_admin_session(request.cookies.get(ADMIN_COOKIE_NAME))

llm_app.mount("/static", StaticFiles(directory=web_dir), name="static")


@llm_app.get("/", include_in_schema=False)
async def home() -> FileResponse:
    return FileResponse(web_dir / "index.html", headers=NO_STORE_HEADERS)


@llm_app.get("/styles.css", include_in_schema=False)
async def styles() -> FileResponse:
    return frontend_asset("styles.css")


@llm_app.get("/home", include_in_schema=False)
@llm_app.get("/home/", include_in_schema=False)
async def homepage_index() -> FileResponse:
    return homepage_asset()


@llm_app.get("/home/{asset_path:path}", include_in_schema=False)
async def homepage_files(asset_path: str) -> FileResponse:
    return homepage_asset(asset_path)


@llm_app.get("/app.js", include_in_schema=False)
async def app_js() -> FileResponse:
    return frontend_asset("app.js")


@llm_app.get("/auth/session", response_model=AdminSessionResponse)
async def auth_session(request: Request) -> AdminSessionResponse:
    return service.get_admin_session(request.cookies.get(ADMIN_COOKIE_NAME))


@llm_app.get("/auth/user/session", response_model=UserSessionResponse)
async def user_auth_session(request: Request) -> UserSessionResponse:
    return service.get_user_session(request.cookies.get(USER_COOKIE_NAME))


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
async def health() -> dict[str, str]:
    due_follow_ups = service._follow_up_store.list_due_actions()
    return {
        "status": "ok",
        "owner_name": service._settings.owner_name,
        "owner_role": service._settings.owner_role,
        "homepage_public_url": service._settings.homepage_public_url,
        "model_name": service._settings.model_name,
        "sage_runtime": service._describe_sage_runtime(),
        "knowledge_backend": service._knowledge_store.backend_name(),
        "knowledge_embedding_backend": service._knowledge_store.embedding_backend_name(),
        "knowledge_documents": str(service._knowledge_store.count_documents()),
        "conversation_memory_backend": service._conversation_store.backend_name(),
        "conversation_memory_records": str(service._conversation_store.count_records()),
        "conversation_memory_profiles": str(service._conversation_store.count_profiles()),
        "conversation_feedback_records": str(service._analytics_store.count_feedback()),
        "knowledge_gap_drafts": str(service._knowledge_gap_draft_store.count_drafts()),
        "escalation_queue_records": str(service._escalation_store.count_records()),
        "follow_up_queue_records": str(service._follow_up_store.count_actions()),
        "follow_up_dispatch_sent": "0",
        "follow_up_dispatch_due": str(len(due_follow_ups)),
        "chat_pipeline_stages": "12",
        "admin_pipeline_stages": "4",
    }


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


@llm_app.on_event("shutdown")
async def shutdown_event() -> None:
    await service.aclose()


@llm_app.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    raw_request: Request,
    request_id: str | None = Query(default=None, min_length=1, max_length=128),
) -> ChatResponse:
    if request_id is None:
        return await service.answer(
            payload,
            admin_session_token=raw_request.cookies.get(ADMIN_COOKIE_NAME),
        )

    try:
        response = await service.answer(
            payload,
            admin_session_token=raw_request.cookies.get(ADMIN_COOKIE_NAME),
            trace_callback=lambda step: workflow_event_broker.publish_step(request_id, step),
        )
    except Exception as exc:
        workflow_event_broker.publish_error(request_id, str(exc))
        raise

    workflow_event_broker.publish_complete(request_id)
    return response


@llm_app.post("/chat/feedback", response_model=ChatFeedbackResponse)
async def submit_chat_feedback(request: ChatFeedbackRequest) -> ChatFeedbackResponse:
    return service.submit_chat_feedback(request)


@llm_app.post("/knowledge", response_model=KnowledgeDocumentRecord)
async def create_knowledge_document(
    request: KnowledgeDocumentCreate,
    _: dict = Depends(require_admin_session),
) -> KnowledgeDocumentRecord:
    return service.add_knowledge(request)


@llm_app.get("/knowledge", response_model=list[KnowledgeDocumentRecord])
async def list_knowledge_documents(
    _: dict = Depends(require_admin_session),
) -> list[KnowledgeDocumentRecord]:
    return service.list_knowledge()


@llm_app.get("/knowledge/search", response_model=KnowledgeSearchResponse)
async def search_knowledge_documents(
    query: str = Query(min_length=1, max_length=256),
    _: dict = Depends(require_admin_session),
) -> KnowledgeSearchResponse:
    return service.search_knowledge(query)


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


@llm_app.get("/analytics/questions/gap-drafts", response_model=list[KnowledgeGapDraftRecordResponse])
async def list_knowledge_gap_drafts(
    _: dict = Depends(require_admin_session),
) -> list[KnowledgeGapDraftRecordResponse]:
    return service.list_knowledge_gap_drafts()


@llm_app.post("/analytics/questions/gap-drafts", response_model=KnowledgeGapDraftRecordResponse)
async def create_knowledge_gap_draft(
    request: KnowledgeGapDraftCreateRequest,
    _: dict = Depends(require_admin_session),
) -> KnowledgeGapDraftRecordResponse:
    return service.create_knowledge_gap_draft(request)


@llm_app.post("/analytics/questions/gap-drafts/{draft_id}/publish", response_model=KnowledgeGapDraftRecordResponse)
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


app = create_edge_app(mount_llm=True, llm_prefix="/", llm_app=llm_app)
configure_local_cors(app)
app.mount("/static", StaticFiles(directory=web_dir), name="static")
