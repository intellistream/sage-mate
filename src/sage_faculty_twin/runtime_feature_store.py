from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock

from .config import AppSettings
from .models import RuntimeFeatureFlagsResponse


class RuntimeFeatureFlagStore:
    def __init__(self, settings: AppSettings) -> None:
        self._path = settings.runtime_feature_flags_path
        self._default_shadow_planner_enabled = settings.shadow_planner_enabled
        self._lock = Lock()

    def get(self) -> RuntimeFeatureFlagsResponse:
        with self._lock:
            return self._read_unlocked()

    def update_shadow_planner(self, enabled: bool) -> RuntimeFeatureFlagsResponse:
        with self._lock:
            state = RuntimeFeatureFlagsResponse(
                shadow_planner_enabled=enabled,
                updated_at=datetime.now(UTC),
            )
            self._persist_unlocked(state)
            return state

    def _read_unlocked(self) -> RuntimeFeatureFlagsResponse:
        if not self._path.exists():
            return RuntimeFeatureFlagsResponse(
                shadow_planner_enabled=self._default_shadow_planner_enabled,
            )
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
            return RuntimeFeatureFlagsResponse.model_validate(payload)
        except (OSError, ValueError, TypeError):
            return RuntimeFeatureFlagsResponse(
                shadow_planner_enabled=self._default_shadow_planner_enabled,
            )

    def _persist_unlocked(self, state: RuntimeFeatureFlagsResponse) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = Path(f"{self._path}.tmp")
        temporary_path.write_text(
            json.dumps(state.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary_path.replace(self._path)
