The `sage-faculty-twin` application uses a hybrid configuration system combining **pydantic-settings** for structured, type-safe application settings and **environment variables** (loaded from `.env` files or shell scripts) for runtime and infrastructure-level configuration.

### 1. Core Approach: Pydantic Settings
The primary configuration logic resides in `src/sage_faculty_twin/config.py`. It defines an `AppSettings` class inheriting from `pydantic_settings.BaseSettings`.

- **Environment Prefix**: All settings are prefixed with `DIGITAL_TWIN_` (e.g., `DIGITAL_TWIN_OWNER_NAME` maps to `owner_name`).
- **File Loading**: It automatically loads from `.env` in the repo root and a secondary path (`../SAGE/.env`), allowing for layered environment-specific overrides.
- **Type Safety & Validation**: Fields use Pydantic `Field` definitions with defaults, types, and constraints (e.g., `ge`, `le` for numeric ranges).
- **Singleton Instance**: A global `settings = AppSettings()` instance is created at module load time, making configuration accessible throughout the application via `from sage_faculty_twin.config import settings`.

### 2. Environment Variable Layering
Configuration values are resolved in the following order of precedence:
1. **Explicit Environment Variables**: Set in the shell or systemd service files.
2. **`.env` Files**: Loaded by `pydantic-settings` if present.
3. **Defaults**: Defined in the `AppSettings` class.

Key files involved:
- `.env.example`: Template for required environment variables.
- `tools/run_app_server.sh`: Shell script that explicitly loads `.env` before starting the Uvicorn server, ensuring env vars are available to both the shell and the Python process.
- `deploy/systemd/user/*.service`: Systemd unit files that inject specific environment variables (e.g., `APP_PORT`, `DIGITAL_TWIN_HOMEPAGE_PUBLIC_URL`) directly into the service context.

### 3. Runtime Environment Bootstrap
The `src/sage_faculty_twin/runtime_env.py` module handles low-level runtime configuration, including:
- **PYTHONPATH Management**: Dynamically prepends paths for local development dependencies (e.g., `../SAGE/src`, `../sageVDB`).
- **Dependency Validation**: Checks for compiled extensions (like `sagevdb`'s `.so` files) and auto-links them if missing.
- **Hardware/Backend Flags**: Sets environment variables like `TORCH_DEVICE_BACKEND_AUTOLOAD=0` to control backend behavior.

### 4. Configuration Categories
- **LLM & Model**: `DIGITAL_TWIN_LLM_BASE_URL`, `DIGITAL_TWIN_API_KEY`, `DIGITAL_TWIN_MODEL_NAME`.
- **Storage Paths**: `DIGITAL_TWIN_KNOWLEDGE_BASE_DIR`, `DIGITAL_TWIN_CONVERSATION_MEMORY_DIR`.
- **Feature Flags**: `DIGITAL_TWIN_WEB_SEARCH_ENABLED`, `DIGITAL_TWIN_STREAM_CHAT_ANSWER`.
- **Admin & Security**: `DIGITAL_TWIN_ADMIN_USERNAME`, `DIGITAL_TWIN_ADMIN_SESSION_SECRET`.
- **Infrastructure**: `VLLM_PROXY_HOST`, `VLLM_ENGINE_TP_SIZE` (for vLLM engine tuning).

### 5. Developer Conventions
- **Add New Config**: Add a field to `AppSettings` in `config.py` with a default value and appropriate type/constraints. Use the `DIGITAL_TWIN_` prefix for env var mapping.
- **Sensitive Data**: Never commit real secrets to `.env`. Use `.env.example` as a template and rely on environment injection in production (systemd/CI).
- **Runtime Overrides**: For non-pydantic settings (e.g., `CHAT_REQUEST_TIMEOUT_SECONDS` in `api.py`), use `os.environ.get()` with sensible defaults. These are often legacy or performance-tuning knobs not yet migrated to the central config.