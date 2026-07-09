"""Tests for V3.3 capability plugin manifest system."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sage_faculty_twin.capability_plugins import (
    CapabilityPluginManifest,
    CapabilityPluginRegistry,
    build_plugin_status,
    check_compatibility,
    load_all_manifests,
    load_manifest,
    validate_plugin_steps,
)
from sage_faculty_twin.config import DEFAULT_RUNTIME_SEED_DATA_DIR
from sage_faculty_twin.workflow_steps import get_default_step_registry


# ── Fixtures ────────────────────────────────────────────────────────────────


def _write_manifest(directory: Path, name: str, data: dict) -> Path:
    path = directory / f"{name}.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.fixture()
def plugin_dir(tmp_path: Path) -> Path:
    d = tmp_path / "plugins"
    d.mkdir()
    return d


@pytest.fixture()
def sample_manifest_data() -> dict:
    return {
        "plugin_id": "test_pack",
        "name": "Test Pack",
        "description": "A test capability plugin.",
        "min_app_version": "3.0.0",
        "enabled": False,
        "steps": [
            {
                "step_id": "test_step_a",
                "description": "A test step.",
                "required_inputs": ["question"],
                "produces_outputs": ["test_output"],
                "timeout_budget_ms": 500,
                "trace_key": "plugin_test_a",
            }
        ],
        "policy_requirements": [
            {"step_id": "test_step_a", "requires_admin": False, "allowed_side_effects": []}
        ],
        "test_scenario_ids": ["test-scenario-1"],
    }


# ── Load Manifest Tests ─────────────────────────────────────────────────────


def test_load_manifest_valid(plugin_dir: Path, sample_manifest_data: dict) -> None:
    path = _write_manifest(plugin_dir, "test", sample_manifest_data)
    manifest = load_manifest(path)
    assert manifest.plugin_id == "test_pack"
    assert manifest.name == "Test Pack"
    assert len(manifest.steps) == 1
    assert manifest.steps[0].step_id == "test_step_a"


def test_load_manifest_invalid_json(plugin_dir: Path) -> None:
    path = plugin_dir / "bad.json"
    path.write_text("{invalid json", encoding="utf-8")
    with pytest.raises(Exception):
        load_manifest(path)


def test_load_manifest_missing_required_field(plugin_dir: Path) -> None:
    data = {"name": "No ID"}  # missing plugin_id
    path = _write_manifest(plugin_dir, "missing", data)
    with pytest.raises(Exception):
        load_manifest(path)


def test_load_all_manifests_skips_invalid(plugin_dir: Path, sample_manifest_data: dict) -> None:
    _write_manifest(plugin_dir, "good", sample_manifest_data)
    (plugin_dir / "bad.json").write_text("{broken", encoding="utf-8")
    manifests = load_all_manifests(plugin_dir)
    assert len(manifests) == 1
    assert manifests[0].plugin_id == "test_pack"


def test_load_all_manifests_empty_dir(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    assert load_all_manifests(empty) == []


def test_load_all_manifests_nonexistent_dir(tmp_path: Path) -> None:
    assert load_all_manifests(tmp_path / "nope") == []


# ── Compatibility Tests ─────────────────────────────────────────────────────


def test_check_compatibility_ok(sample_manifest_data: dict) -> None:
    manifest = CapabilityPluginManifest.model_validate(sample_manifest_data)
    ok, reason = check_compatibility(manifest, "3.2.0")
    assert ok is True
    assert reason is None


def test_check_compatibility_too_old(sample_manifest_data: dict) -> None:
    sample_manifest_data["min_app_version"] = "4.0.0"
    manifest = CapabilityPluginManifest.model_validate(sample_manifest_data)
    ok, reason = check_compatibility(manifest, "3.2.0")
    assert ok is False
    assert reason is not None
    assert "4.0.0" in reason


def test_check_compatibility_exact_match(sample_manifest_data: dict) -> None:
    sample_manifest_data["min_app_version"] = "3.2.0"
    manifest = CapabilityPluginManifest.model_validate(sample_manifest_data)
    ok, _ = check_compatibility(manifest, "3.2.0")
    assert ok is True


def test_check_compatibility_bad_version_string(sample_manifest_data: dict) -> None:
    manifest = CapabilityPluginManifest.model_validate(sample_manifest_data)
    ok, reason = check_compatibility(manifest, "not-a-version")
    assert ok is False
    assert reason is not None


# ── Validation Tests ────────────────────────────────────────────────────────


def test_validate_plugin_steps_no_warnings(sample_manifest_data: dict) -> None:
    manifest = CapabilityPluginManifest.model_validate(sample_manifest_data)
    warnings = validate_plugin_steps(manifest)
    assert warnings == []


def test_validate_plugin_steps_shadow_core_step(sample_manifest_data: dict) -> None:
    sample_manifest_data["steps"][0]["step_id"] = "classify_intent"
    manifest = CapabilityPluginManifest.model_validate(sample_manifest_data)
    warnings = validate_plugin_steps(manifest)
    assert any("shadows a core step" in w for w in warnings)


def test_validate_plugin_steps_duplicate_step_id(sample_manifest_data: dict) -> None:
    dup = dict(sample_manifest_data["steps"][0])
    dup["trace_key"] = "plugin_dup"
    sample_manifest_data["steps"] = [sample_manifest_data["steps"][0], dup]
    manifest = CapabilityPluginManifest.model_validate(sample_manifest_data)
    warnings = validate_plugin_steps(manifest)
    assert any("Duplicate" in w for w in warnings)


def test_validate_plugin_steps_orphan_policy(sample_manifest_data: dict) -> None:
    sample_manifest_data["policy_requirements"].append(
        {"step_id": "nonexistent_step", "requires_admin": True}
    )
    manifest = CapabilityPluginManifest.model_validate(sample_manifest_data)
    warnings = validate_plugin_steps(manifest)
    assert any("unknown step_ids" in w for w in warnings)


# ── Build Status Tests ──────────────────────────────────────────────────────


def test_build_plugin_status_compatible_disabled(sample_manifest_data: dict) -> None:
    manifest = CapabilityPluginManifest.model_validate(sample_manifest_data)
    status = build_plugin_status(manifest, "3.2.0")
    assert status.plugin_id == "test_pack"
    assert status.compatible is True
    assert status.enabled is False  # manifest.enabled is False


def test_build_plugin_status_enabled(sample_manifest_data: dict) -> None:
    sample_manifest_data["enabled"] = True
    manifest = CapabilityPluginManifest.model_validate(sample_manifest_data)
    status = build_plugin_status(manifest, "3.2.0")
    assert status.enabled is True


def test_build_plugin_status_incompatible(sample_manifest_data: dict) -> None:
    sample_manifest_data["min_app_version"] = "99.0.0"
    sample_manifest_data["enabled"] = True
    manifest = CapabilityPluginManifest.model_validate(sample_manifest_data)
    status = build_plugin_status(manifest, "3.2.0")
    assert status.compatible is False
    assert status.enabled is False
    assert status.incompatibility_reason is not None


# ── Registry Tests ──────────────────────────────────────────────────────────


def test_registry_load_and_merge(
    plugin_dir: Path, sample_manifest_data: dict
) -> None:
    sample_manifest_data["enabled"] = True
    _write_manifest(plugin_dir, "enabled_pack", sample_manifest_data)

    registry = CapabilityPluginRegistry(plugin_dir=plugin_dir, current_version="3.2.0")
    registry.load()

    assert len(registry.statuses) == 1
    assert registry.statuses[0].enabled is True

    merged = registry.merged_step_registry()
    core = get_default_step_registry()
    # Merged should have all core steps + the plugin step
    assert len(merged) == len(core) + 1
    assert "test_step_a" in merged


def test_registry_disabled_plugin_not_merged(
    plugin_dir: Path, sample_manifest_data: dict
) -> None:
    sample_manifest_data["enabled"] = False
    _write_manifest(plugin_dir, "disabled_pack", sample_manifest_data)

    registry = CapabilityPluginRegistry(plugin_dir=plugin_dir, current_version="3.2.0")
    registry.load()

    merged = registry.merged_step_registry()
    assert "test_step_a" not in merged


def test_registry_incompatible_plugin_not_merged(
    plugin_dir: Path, sample_manifest_data: dict
) -> None:
    sample_manifest_data["enabled"] = True
    sample_manifest_data["min_app_version"] = "99.0.0"
    _write_manifest(plugin_dir, "future_pack", sample_manifest_data)

    registry = CapabilityPluginRegistry(plugin_dir=plugin_dir, current_version="3.2.0")
    registry.load()

    merged = registry.merged_step_registry()
    assert "test_step_a" not in merged
    assert registry.statuses[0].compatible is False


def test_registry_empty_dir(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    registry = CapabilityPluginRegistry(plugin_dir=empty, current_version="3.2.0")
    registry.load()
    assert registry.statuses == []
    merged = registry.merged_step_registry()
    assert merged == get_default_step_registry()


# ── Real Manifest Tests ─────────────────────────────────────────────────────


def test_real_course_advising_manifest_loads() -> None:
    """The shipped course_advising.json manifest must be valid."""
    manifest_path = DEFAULT_RUNTIME_SEED_DATA_DIR / "capability_plugins/course_advising.json"
    if not manifest_path.is_file():
        pytest.skip("course_advising.json not found")
    manifest = load_manifest(manifest_path)
    assert manifest.plugin_id == "course_advising"
    assert manifest.enabled is True
    assert len(manifest.steps) == 3
    step_ids = [s.step_id for s in manifest.steps]
    assert "retrieve_courseware_index" in step_ids
    assert "draft_course_plan" in step_ids
    warnings = validate_plugin_steps(manifest)
    assert warnings == []


def test_real_paper_feedback_manifest_loads() -> None:
    """The shipped paper_feedback.json manifest must be valid."""
    manifest_path = DEFAULT_RUNTIME_SEED_DATA_DIR / "capability_plugins/paper_feedback.json"
    if not manifest_path.is_file():
        pytest.skip("paper_feedback.json not found")
    manifest = load_manifest(manifest_path)
    assert manifest.plugin_id == "paper_feedback"
    assert manifest.enabled is True
    assert len(manifest.steps) == 3
    step_ids = [s.step_id for s in manifest.steps]
    assert "retrieve_writing_rubric" in step_ids
    assert "draft_revision_notes" in step_ids
    warnings = validate_plugin_steps(manifest)
    assert warnings == []


def test_real_research_mentoring_manifest_loads() -> None:
    """The shipped research_mentoring.json manifest must be valid."""
    manifest_path = DEFAULT_RUNTIME_SEED_DATA_DIR / "capability_plugins/research_mentoring.json"
    if not manifest_path.is_file():
        pytest.skip("research_mentoring.json not found")
    manifest = load_manifest(manifest_path)
    assert manifest.plugin_id == "research_mentoring"
    assert manifest.enabled is True
    assert len(manifest.steps) == 4
    step_ids = [s.step_id for s in manifest.steps]
    assert "retrieve_research_overview" in step_ids
    assert "draft_research_plan" in step_ids
    warnings = validate_plugin_steps(manifest)
    assert warnings == []


def test_real_meeting_prep_manifest_loads() -> None:
    """The shipped meeting_prep.json manifest must be valid."""
    manifest_path = DEFAULT_RUNTIME_SEED_DATA_DIR / "capability_plugins/meeting_prep.json"
    if not manifest_path.is_file():
        pytest.skip("meeting_prep.json not found")
    manifest = load_manifest(manifest_path)
    assert manifest.plugin_id == "meeting_prep"
    assert manifest.enabled is True
    assert len(manifest.steps) == 4
    step_ids = [s.step_id for s in manifest.steps]
    assert "retrieve_team_schedule" in step_ids
    assert "draft_meeting_agenda" in step_ids
    warnings = validate_plugin_steps(manifest)
    assert warnings == []


def test_real_thesis_review_manifest_loads() -> None:
    """The shipped thesis_review.json manifest must be valid."""
    manifest_path = DEFAULT_RUNTIME_SEED_DATA_DIR / "capability_plugins/thesis_review.json"
    if not manifest_path.is_file():
        pytest.skip("thesis_review.json not found")
    manifest = load_manifest(manifest_path)
    assert manifest.plugin_id == "thesis_review"
    assert manifest.enabled is True
    assert len(manifest.steps) == 4
    step_ids = [s.step_id for s in manifest.steps]
    assert "retrieve_paper_digest" in step_ids
    assert "draft_review_comments" in step_ids
    warnings = validate_plugin_steps(manifest)
    assert warnings == []


def test_all_real_plugins_no_step_collisions() -> None:
    """All 5 real plugins must have unique step IDs across the registry."""
    from sage_faculty_twin.capability_plugins import CapabilityPluginRegistry
    from sage_faculty_twin import __version__

    registry = CapabilityPluginRegistry(
        plugin_dir=DEFAULT_RUNTIME_SEED_DATA_DIR / "capability_plugins",
        current_version=__version__,
    )
    registry.load()
    merged = registry.merged_step_registry()
    enabled = registry.enabled_manifests()
    assert len(enabled) == 5
    assert len(merged) > 18  # core steps + plugin steps
    # Collect all plugin step IDs
    plugin_step_ids = [s.step_id for m in enabled for s in m.steps]
    # None should collide with core step IDs
    from sage_faculty_twin.workflow_steps import get_default_step_registry
    core_ids = set(get_default_step_registry().keys())
    collisions = [sid for sid in plugin_step_ids if sid in core_ids]
    assert collisions == [], f"Plugin steps collide with core: {collisions}"


def test_all_real_plugins_draft_steps_have_trace_keys() -> None:
    """Every draft_write step in the real plugins must have a trace_key."""
    from sage_faculty_twin.capability_plugins import CapabilityPluginRegistry
    from sage_faculty_twin import __version__

    registry = CapabilityPluginRegistry(
        plugin_dir=DEFAULT_RUNTIME_SEED_DATA_DIR / "capability_plugins",
        current_version=__version__,
    )
    registry.load()
    for m in registry.enabled_manifests():
        for s in m.steps:
            if s.side_effect == "draft_write":
                assert s.trace_key is not None, (
                    f"{m.plugin_id}/{s.step_id}: draft_write without trace_key"
                )


# ── Changelog API Data Tests ────────────────────────────────────────────────


def test_changelog_json_is_valid() -> None:
    """data/changelog.json must be a valid JSON array of release entries."""
    changelog_path = Path("data/changelog.json")
    if not changelog_path.is_file():
        pytest.skip("data/changelog.json not found")
    raw = json.loads(changelog_path.read_text(encoding="utf-8"))
    assert isinstance(raw, list)
    assert len(raw) > 0
    for entry in raw:
        assert "version" in entry
        assert "date" in entry
        assert isinstance(entry.get("highlights", []), list)
