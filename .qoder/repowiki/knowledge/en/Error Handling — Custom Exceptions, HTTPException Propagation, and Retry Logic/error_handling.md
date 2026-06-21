## Overview

The `sage-faculty-twin` codebase employs a **hybrid error handling strategy** combining:
- **Custom exception classes** for domain-specific failures
- **FastAPI's `HTTPException`** for API-layer validation and request errors
- **Retry logic with exponential backoff** for transient LLM communication failures
- **Defensive try/except blocks** with structured logging for post-answer background tasks
- **Graceful degradation** where non-critical failures are captured without aborting the main workflow

---

## Key Files and Packages

| File | Role |
|------|------|
| `src/sage_faculty_twin/llm_client.py` | Defines `StreamingServerError`; implements retry logic with exponential backoff for LLM calls |
| `src/sage_faculty_twin/notifications.py` | Defines `BookingNotificationError`; wraps SMTP transport errors with contextual messages |
| `src/sage_faculty_twin/api.py` | Raises `HTTPException` (400/422/500/504) for request validation, file parsing, and timeout errors |
| `src/sage_faculty_twin/service.py` | Catches `BookingNotificationError` to degrade gracefully; uses `_logger.exception()` for post-answer stage failures |
| `src/sage_faculty_twin/knowledge_base.py` | Raises `RuntimeError` for missing optional dependencies (e.g., `sentence-transformers`) and dimension mismatches |
| `src/sage_faculty_twin/config.py` | Configures `llm_retry_attempts` (default=2) and `llm_retry_backoff_seconds` (default=1.0) |

---

## Architecture and Conventions

### 1. Custom Exception Classes

Two custom exceptions are defined, both inheriting from `RuntimeError`:

```python
# llm_client.py:53
class StreamingServerError(RuntimeError):
    """Raised when the vLLM SSE stream delivers an error event.
    
    vLLM sometimes returns HTTP 200 with an error payload embedded in
    the SSE stream. This exception carries the original error message
    and an optional HTTP-like status code so callers can react.
    """
    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.status_code = status_code

# notifications.py:10
class BookingNotificationError(RuntimeError):
    pass
```

**Design rationale**: `StreamingServerError` captures SSE-level errors that `response.raise_for_status()` cannot detect (HTTP 200 with error payload). It carries a `status_code` attribute for caller introspection.

### 2. HTTPException at the API Layer

The FastAPI layer (`api.py`) uses `HTTPException` extensively for client-facing errors:

- **400 Bad Request**: Invalid JSON body, empty attachments, unsupported file types, PDF parsing failures, UTF-8 decode errors
- **422 Unprocessable Entity**: Pydantic `ValidationError` re-raised as `RequestValidationError`
- **500 Internal Server Error**: Missing optional dependencies (e.g., `pypdf` not installed)
- **504 Gateway Timeout**: LLM inference timeout exceeded

Example pattern:
```python
# api.py:295-308
def _extract_pdf_text(content: bytes, file_name: str) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise HTTPException(status_code=500, detail="当前环境缺少 PDF 解析依赖 pypdf。") from exc

    try:
        reader = PdfReader(BytesIO(content))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"无法读取 PDF 文件：{file_name}") from exc
```

**Chaining convention**: Exceptions are always chained with `from exc` to preserve the original traceback for debugging.

### 3. Retry Logic with Exponential Backoff

The `VllmChatClient` implements retry logic for transient LLM failures:

```python
# llm_client.py:874-956
max_retries = self._settings.llm_retry_attempts  # default=2
for attempt in range(max_retries + 1):
    try:
        # ... streaming chat completion ...
        break
    except httpx.TimeoutException as exc:
        if attempt >= max_retries:
            self._record_request_error(exc)
            raise
        self._sleep_before_retry(attempt + 1)
    except Exception as exc:
        self._record_request_error(exc)
        raise
```

Backoff calculation (`llm_client.py:1909-1912`):
```python
def _sleep_before_retry(self, retry_number: int) -> None:
    delay_seconds = self._settings.llm_retry_backoff_seconds * (2 ** max(0, retry_number - 1))
    if delay_seconds > 0:
        time.sleep(delay_seconds)
```

**Scope**: Retries apply only to `httpx.TimeoutException`. All other exceptions (including `StreamingServerError`) are raised immediately without retry.

### 4. Graceful Degradation for Non-Critical Failures

Post-answer background tasks (memory persistence, follow-up planning, usefulness scoring) use broad `except Exception` blocks with logging:

```python
# service.py:7169-7177
for stage_key, stage_cls in post_answer_stages:
    try:
        stage_cls(support).execute(context)
    except Exception:  # pragma: no cover - logged for ops review
        _logger.exception(
            "post-answer stage %s failed (conversation_id=%s)",
            stage_key,
            getattr(context, "conversation_id", None),
        )
```

Similarly, email notification failures are caught and converted into a `NotificationDeliveryStatus` with `status="failed"`, allowing the booking to proceed even if the email fails:

```python
# service.py:926-939
try:
    recipient = self._email_notifier.send_booking_request_notification(booking)
except BookingNotificationError as exc:
    notification = NotificationDeliveryStatus(
        status="failed",
        summary=f"管理员提醒邮件发送失败。{exc}",
        detail="预约记录已经保存，不影响管理员后续在后台查看和处理；邮件可稍后重试。",
    )
```

### 5. Dependency Import Error Handling

Optional dependencies (e.g., `sentence-transformers`, `pypdf`) raise `RuntimeError` or `HTTPException` with installation instructions:

```python
# knowledge_base.py:45-51
try:
    from sentence_transformers import SentenceTransformer
except ImportError as exc:
    raise RuntimeError(
        "sagevdb embedding backend 'sentence-transformers' requires the sentence-transformers package. "
        "Install with: python -m pip install -e .[vdb]"
    ) from exc
```

---

## Rules Developers Should Follow

1. **Use `HTTPException` for API-layer errors**: Always raise `HTTPException` with appropriate status codes (400 for client errors, 500 for server errors, 504 for timeouts) in `api.py`. Include Chinese `detail` messages for user-facing errors.

2. **Chain exceptions with `from exc`**: Preserve the original traceback by using `raise NewException(...) from exc` when wrapping lower-level errors.

3. **Define custom exceptions for domain-specific failures**: Create subclasses of `RuntimeError` (not `Exception`) for errors that need special handling or carry additional context (e.g., `status_code`).

4. **Retry only transient errors**: Limit retries to `httpx.TimeoutException`. Do not retry on validation errors, authentication failures, or malformed responses.

5. **Log but don't crash for non-critical background tasks**: Use `except Exception` with `_logger.exception()` for post-answer stages (memory persistence, follow-up planning) so the main answer is delivered even if auxiliary tasks fail.

6. **Provide actionable error messages for missing dependencies**: Include installation commands (e.g., `pip install -e .[vdb]`) in `RuntimeError` messages for optional features.

7. **Degrade gracefully for notification failures**: Catch `BookingNotificationError` and return a `NotificationDeliveryStatus` with `status="failed"` rather than aborting the entire booking flow.

8. **Avoid bare `except:` clauses**: Always catch specific exception types (`except Exception`, `except OSError`, `except ValidationError`) to avoid masking `KeyboardInterrupt` and `SystemExit`.
