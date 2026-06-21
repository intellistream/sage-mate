## Overview

The `sage-faculty-twin` application uses Python's built-in `logging` module exclusively for all log output. There is no third-party logging framework (e.g., `loguru`, `structlog`) and no centralized logging configuration or initialization.

## Approach

### Framework
- **Python standard library `logging`** — every module that needs logging imports `logging` and creates a module-level logger via `logging.getLogger(__name__)`.

### Logger Initialization Pattern
Every source file follows the same pattern:
```python
import logging
logger = logging.getLogger(__name__)
```

This pattern appears consistently across all modules:
- `src/sage_faculty_twin/service.py` — `_logger = logging.getLogger(__name__)`
- `src/sage_faculty_twin/llm_client.py` — `logger = logging.getLogger(__name__)`
- `src/sage_faculty_twin/capability_plugins.py` — `logger = logging.getLogger(__name__)`
- `src/sage_faculty_twin/skill_router.py` — `logger = logging.getLogger(__name__)`
- `src/sage_faculty_twin/skill_runner.py` — `logger = logging.getLogger(__name__)`
- `src/sage_faculty_twin/skill_tools.py` — `logger = logging.getLogger(__name__)`

### Log Levels Used
The codebase uses these log levels:
- **`logger.info()`** — operational events (model auto-detection, workflow progress, skill routing decisions)
- **`logger.debug()`** — fine-grained tracing (skill disabled status, internal decision branches)
- **`logger.warning()`** — recoverable errors (failed model detection, invalid plugin manifests, LLM call failures)
- **`logger.exception()`** — error paths with stack traces (async task failures, unexpected exceptions)

No `logger.error()` or `logger.critical()` calls were found; errors are logged via `exception()` to include tracebacks.

### Configuration
There is **no explicit logging configuration** anywhere in the codebase:
- No `logging.basicConfig()` call
- No `logging.config.dictConfig()` usage
- No `LOG_LEVEL` environment variable or config setting in `AppSettings`
- No custom handlers, formatters, or filters

Logging behavior is entirely controlled by the runtime environment (uvicorn/FastAPI defaults) and any external configuration applied at deployment time.

### Output Routing
Log output flows through uvicorn's default handler when the application runs via:
```bash
python -m uvicorn sage_faculty_twin.api:app --host 127.0.0.1 --port 55601
```

Uvicorn captures `logging` output and routes it to stdout/stderr with its own formatting. The application itself does not configure file-based logging or structured JSON output.

## Key Files

| File | Role |
|------|------|
| `src/sage_faculty_twin/service.py` | Main service logic; uses `_logger` for workflow-level logging |
| `src/sage_faculty_twin/llm_client.py` | LLM client; logs model detection, cache hits, request metrics |
| `src/sage_faculty_twin/capability_plugins.py` | Plugin registry; logs manifest validation warnings |
| `src/sage_faculty_twin/skill_router.py` | Skill routing; debug/info logs for routing decisions |
| `src/sage_faculty_twin/skill_runner.py` | Skill execution; warning logs for LLM call failures |
| `tools/run_app_server.sh` | Server startup script; no logging configuration |

## Conventions for Developers

1. **Always use `logging.getLogger(__name__)`** — never create loggers with hardcoded names or use `print()` for operational messages.

2. **Prefer parameterized messages** — use `logger.info("Model detected: %s", name)` instead of f-strings to avoid unnecessary string construction when the log level is disabled.

3. **Use `logger.exception()` for caught exceptions** — this automatically includes the stack trace. Do not use `logger.error()` followed by manual traceback formatting.

4. **No centralized log level control** — if you need to adjust verbosity, set the `LOGLEVEL` environment variable before starting uvicorn, or configure uvicorn's `--log-level` flag.

5. **No structured logging** — log messages are plain text strings. If structured fields are needed for downstream analysis, they must be manually embedded in the message string.

6. **Avoid `print()` in application code** — `print()` is used only in CLI tools (`tools/`) and knowledge import scripts, not in the core service modules.

## Limitations

- No log rotation or file-based persistence configured
- No structured/JSON log format for machine parsing
- No correlation IDs or request tracing across async boundaries
- Log level must be controlled externally (uvicorn flags or environment variables)
