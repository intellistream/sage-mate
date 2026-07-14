from pathlib import Path

from sage_faculty_twin.config import settings
from sage_faculty_twin.runtime_feature_store import RuntimeFeatureFlagStore


def test_runtime_feature_flags_persist_across_store_instances(tmp_path: Path) -> None:
    feature_path = tmp_path / "runtime-feature-flags.json"
    isolated_settings = settings.model_copy(
        update={
            "runtime_feature_flags_path": feature_path,
            "shadow_planner_enabled": False,
        }
    )

    store = RuntimeFeatureFlagStore(isolated_settings)
    assert store.get().shadow_planner_enabled is False

    updated = store.update_shadow_planner(True)
    assert updated.shadow_planner_enabled is True
    assert updated.updated_at is not None

    reloaded_store = RuntimeFeatureFlagStore(isolated_settings)
    assert reloaded_store.get().shadow_planner_enabled is True
    assert "shadow_planner_enabled" in feature_path.read_text(encoding="utf-8")


def test_runtime_feature_flags_fall_back_when_file_is_invalid(tmp_path: Path) -> None:
    feature_path = tmp_path / "runtime-feature-flags.json"
    feature_path.write_text("not-json", encoding="utf-8")
    isolated_settings = settings.model_copy(
        update={
            "runtime_feature_flags_path": feature_path,
            "shadow_planner_enabled": False,
        }
    )

    assert (
        RuntimeFeatureFlagStore(isolated_settings).get().shadow_planner_enabled is False
    )
