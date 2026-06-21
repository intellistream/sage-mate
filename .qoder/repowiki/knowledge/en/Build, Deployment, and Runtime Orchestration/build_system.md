The `sage-faculty-twin` project employs a **Python-native build system** combined with **systemd-based deployment** and **GitHub Actions CI**. It avoids containerization for the application layer in favor of direct host-level service management, while relying on external Docker containers for heavy inference engines (vLLM).

### Build & Packaging
- **Tooling**: Uses `setuptools` via `pyproject.toml` as the build backend. The project is packaged as an editable install (`pip install -e .`) during development and deployment.
- **Dependencies**: Core dependencies include `fastapi`, `uvicorn`, `pydantic`, and custom internal libraries (`isage`, `isage-neuromem`). Optional dependency groups (`vdb`, `vdb-anns`, `dev`) allow modular installation of vector database backends and development tools.
- **Versioning**: Semantic versioning is maintained in `pyproject.toml` (currently `4.2.4`).

### Continuous Integration (CI)
- **Platform**: GitHub Actions (`.github/workflows/ci.yml`).
- **Pipeline Stages**:
  1. **Lint**: Runs `ruff` on `src/` and `tests/` using Python 3.11.
  2. **Frontend Contract**: Validates JavaScript syntax (`node --check`) and runs Python-based frontend contract tests to ensure API/UI consistency.
  3. **Test Suite**: Executes `pytest` with specific exclusions for heavy integration tests (`test_sagevdb_knowledge_store.py`, `test_identity_eval.py`) to keep CI fast.
- **Bootstrap**: CI jobs use `quickstart.sh --no-systemd --no-siblings --yes` to standardize the environment setup before running checks.

### Deployment & Runtime Management
- **Entry Points**:
  - `quickstart.sh`: The primary installation script. It handles dependency installation, `.env` bootstrapping, and systemd unit generation/installation. It supports flags for optional components (vLLM engine, proxies, tunnels).
  - `manage.sh`: The runtime operations controller. It wraps `systemctl --user` commands to start, stop, restart, and monitor services. It supports JSON output for programmatic status checks.
- **Service Architecture**: The application is decomposed into multiple systemd user services:
  - `sage-faculty-twin-app.service`: The core FastAPI application.
  - `sage-faculty-twin-vllm-engine.service`: Manages the LLM inference engine (often Docker-backed).
  - `sage-faculty-twin-vllm-openai-proxy.service`: Auth proxy for model access.
  - `sage-faculty-twin-site.service` & `tunnel.service`: Optional networking layers for local proxying and public exposure via Cloudflare.
  - `sage-faculty-twin-wiki-sync.timer`: Periodic knowledge base synchronization.
- **Environment Resolution**: A shared library `tools/lib/runtime_env.sh` ensures deterministic Python interpreter selection and `PYTHONPATH` construction across all scripts, integrating sibling repositories (`SAGE`, `neuromem`, `sageVDB`) into the runtime path.

### Developer Conventions
- **No Makefile**: Build and operational tasks are scripted in Bash (`quickstart.sh`, `manage.sh`) rather than using `make`.
- **Systemd User Services**: Deployment targets `~/.config/systemd/user/`, allowing non-root deployment. Developers must run `systemctl --user daemon-reload` after manual unit changes.
- **Environment Variables**: Configuration is driven by `.env` files. `quickstart.sh` safely appends missing keys but never overwrites existing values, preserving local developer configurations.