The `sage-faculty-twin` repository uses a Python-centric dependency management strategy anchored by `pyproject.toml` and `setuptools`. It relies on standard PyPI for public packages and a "sibling checkout" pattern for internal/private libraries.

### 1. Core System: `pyproject.toml`
- **Build Backend**: Uses `setuptools` with `wheel`.
- **Dependency Declaration**: All third-party libraries are declared in the `[project.dependencies]` section of `pyproject.toml`. 
- **Versioning**: Dependencies use flexible version constraints (e.g., `fastapi>=0.115.0,<1.0.0`) to ensure compatibility while allowing minor updates.
- **Optional Dependencies**: Features like vector database support (`vdb`, `vdb-anns`) and development tools (`dev`) are grouped into optional extras, installed via `pip install -e .[vdb-anns]` or `.[dev]`.

### 2. Private/Internal Library Strategy: Sibling Checkouts
The project depends heavily on internal IntelliStream libraries (`isage`, `isage-neuromem`, `isage-vdb`, `isage-anns`). These are managed via:
- **Sibling Repositories**: The `quickstart.sh` script automatically clones required sibling repositories (`SAGE`, `neuromem`, `sageVDB`) into the parent directory if they are missing.
- **PYTHONPATH Injection**: Instead of vendoring or using a private PyPI index, the application injects these sibling source directories into `PYTHONPATH` at runtime (e.g., `$PWD/../SAGE/src`).
- **Editable Installs**: For development and some deployment paths, these siblings are installed as editable packages (`pip install -e`) or imported directly via path manipulation.
- **Auto-Installation Fallback**: The `tools/run_app_server.sh` script includes logic to check for importability of `sagevdb` and `sage_anns`. If missing, it attempts to auto-install them from PyPI (`isage-vdb`, `isage-anns`), providing a fallback for environments where sibling checkouts are not present.

### 3. Installation and Bootstrap
- **Idempotent Bootstrap**: `quickstart.sh` is the primary entry point for setting up dependencies. It:
  1. Clones sibling repos.
  2. Upgrades `pip`.
  3. Installs the main package in editable mode with extras (`pip install -e .[vdb-anns]`).
  4. Optionally installs `vllm-hust` from a sibling checkout.
- **Development Setup**: Contributors are instructed to use `python -m pip install -e .[dev]` to install local dependencies and testing tools.

### 4. Key Files
- `pyproject.toml`: Central manifest for all public dependencies and project metadata.
- `quickstart.sh`: Automation script for cloning siblings and installing Python packages.
- `tools/run_app_server.sh`: Runtime script that validates and auto-installs specific knowledge backend dependencies.
- `CONTRIBUTING.md`: Documents the expected development environment setup.

### 5. Rules for Developers
- **Do not commit `.env` or runtime data**: Dependency configuration is handled via code and scripts, not environment-specific files in version control.
- **Use `PYTHONPATH` for local development**: When working with sibling checkouts, ensure `PYTHONPATH` includes the `src` directories of `SAGE`, `neuromem`, and `sageVDB`.
- **Prefer `pip install -e .`**: For local changes, use editable installs to ensure the running application reflects source code modifications immediately.
- **No `requirements.txt`**: The project does not use `requirements.txt`; all dependency resolution is handled by `pyproject.toml` and `pip`.