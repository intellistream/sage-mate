# Contributing

## Development Environment

- Use an existing non-venv Python environment.
- Install local dependencies with `python -m pip install -e .[dev]`.
- When working against sibling checkouts, prefer `PYTHONPATH="$PWD/src:$PWD/../SAGE/src:$PWD/../neuromem:$PWD/../sageVDB"`.

## Repository Boundaries

- Do not commit `.env`, generated runtime data, or local `.runtime/` artifacts.
- Keep personal deployment details out of `README.md` and other public entry points.
- Treat `data/persona/style_profile.md` and `data/availability/current_week.json` as templates, not production secrets.

## Validation

Run the narrowest relevant checks for your change.

```bash
PYTHONPATH=src pytest tests/
node --check src/sage_faculty_twin/web/app.js
python -m py_compile src/sage_faculty_twin/*.py
```

## Style

- Keep changes small and focused.
- Prefer root-cause fixes over UI-only or compatibility-only patches.
- Preserve the app architecture: HTTP surface in `api.py`, orchestration in `service.py`, storage and retrieval in dedicated modules.