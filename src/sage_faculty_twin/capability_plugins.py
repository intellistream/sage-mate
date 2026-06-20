"""Capability plugin manifest schema and registry.

V3.3 introduces manifest-driven capability plugins. Each plugin declares
a set of workflow steps, policy requirements, minimum app version, and
trace renderer metadata. The registry loads JSON manifests from
``data/capability_plugins/`` and merges them into the step registry.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from .workflow_steps import WorkflowStepDefinition, get_default_step_registry

logger = logging.getLogger(__name__)


class CapabilityPolicyRequirement(BaseModel):
    """Declares which policy rules a plugin step must satisfy."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(min_length=1, max_length=64)
    requires_admin: bool = False
    requires_owner_review: bool = False
    allowed_side_effects: list[str] = Field(default_factory=list)


class CapabilityPluginManifest(BaseModel):
    """Structured manifest for an optional capability plugin pack.

    Each manifest declares:
    - A unique plugin_id (used for enable/disable)
    - Human-readable name and description
    - Minimum app version required
    - Workflow step definitions to register
    - Policy requirements per step
    - Test scenario IDs that must pass before enabling
    """

    model_config = ConfigDict(extra="forbid")

    plugin_id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    description: str = Field(default="", max_length=512)
    min_app_version: str = Field(default="3.0.0", max_length=32)
    steps: list[WorkflowStepDefinition] = Field(default_factory=list)
    policy_requirements: list[CapabilityPolicyRequirement] = Field(
        default_factory=list
    )
    test_scenario_ids: list[str] = Field(default_factory=list)
    enabled: bool = False


class CapabilityPluginStatus(BaseModel):
    """Runtime status of a loaded capability plugin."""

    model_config = ConfigDict(extra="forbid")

    plugin_id: str
    name: str
    description: str
    enabled: bool
    step_count: int
    step_ids: list[str]
    policy_warnings: list[str]
    compatible: bool
    incompatibility_reason: str | None = None


def load_manifest(path: Path) -> CapabilityPluginManifest:
    """Load and validate a plugin manifest from a JSON file."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    return CapabilityPluginManifest.model_validate(raw)


def load_all_manifests(
    plugin_dir: Path,
) -> list[CapabilityPluginManifest]:
    """Load all ``*.json`` manifests from *plugin_dir*."""
    if not plugin_dir.is_dir():
        return []
    manifests: list[CapabilityPluginManifest] = []
    for p in sorted(plugin_dir.glob("*.json")):
        try:
            manifests.append(load_manifest(p))
        except Exception as exc:
            logger.warning("Skipping invalid plugin manifest %s: %s", p, exc)
    return manifests


def check_compatibility(
    manifest: CapabilityPluginManifest,
    current_version: str,
) -> tuple[bool, str | None]:
    """Check whether a plugin is compatible with the running app version.

    Uses simple tuple-based semver comparison (major.minor.patch).
    """
    try:
        req = tuple(int(x) for x in manifest.min_app_version.split(".")[:3])
        cur = tuple(int(x) for x in current_version.split(".")[:3])
    except (ValueError, IndexError):
        return False, f"Cannot parse version: required={manifest.min_app_version}, current={current_version}"
    if cur < req:
        return (
            False,
            f"Requires app >= {manifest.min_app_version}, running {current_version}",
        )
    return True, None


def validate_plugin_steps(
    manifest: CapabilityPluginManifest,
    core_step_ids: set[str] | None = None,
) -> list[str]:
    """Validate plugin steps against core registry.

    Returns a list of warnings (empty = no issues).
    """
    warnings: list[str] = []
    if core_step_ids is None:
        core_step_ids = set(get_default_step_registry().keys())

    seen: set[str] = set()
    for step in manifest.steps:
        if step.step_id in core_step_ids:
            warnings.append(
                f"Step '{step.step_id}' shadows a core step; plugin step will override."
            )
        if step.step_id in seen:
            warnings.append(
                f"Duplicate step_id '{step.step_id}' in plugin '{manifest.plugin_id}'."
            )
        seen.add(step.step_id)

    # Check policy requirements reference valid step IDs
    policy_step_ids = {pr.step_id for pr in manifest.policy_requirements}
    plugin_step_ids = {s.step_id for s in manifest.steps}
    orphan = policy_step_ids - plugin_step_ids
    if orphan:
        warnings.append(
            f"Policy requirements reference unknown step_ids: {sorted(orphan)}"
        )
    return warnings


def build_plugin_status(
    manifest: CapabilityPluginManifest,
    current_version: str,
    core_step_ids: set[str] | None = None,
) -> CapabilityPluginStatus:
    """Build a runtime status report for a plugin manifest."""
    compatible, reason = check_compatibility(manifest, current_version)
    warnings = validate_plugin_steps(manifest, core_step_ids)
    return CapabilityPluginStatus(
        plugin_id=manifest.plugin_id,
        name=manifest.name,
        description=manifest.description,
        enabled=manifest.enabled and compatible,
        step_count=len(manifest.steps),
        step_ids=[s.step_id for s in manifest.steps],
        policy_warnings=warnings,
        compatible=compatible,
        incompatibility_reason=reason,
    )


class CapabilityPluginRegistry:
    """Loads, validates, and merges capability plugins into the step registry."""

    def __init__(
        self,
        plugin_dir: Path,
        current_version: str,
    ) -> None:
        self._plugin_dir = plugin_dir
        self._current_version = current_version
        self._manifests: list[CapabilityPluginManifest] = []
        self._statuses: list[CapabilityPluginStatus] = []

    def load(self) -> None:
        """Load all manifests and compute their status."""
        self._manifests = load_all_manifests(self._plugin_dir)
        core_ids = set(get_default_step_registry().keys())
        self._statuses = [
            build_plugin_status(m, self._current_version, core_ids)
            for m in self._manifests
        ]

    @property
    def manifests(self) -> list[CapabilityPluginManifest]:
        return list(self._manifests)

    @property
    def statuses(self) -> list[CapabilityPluginStatus]:
        return list(self._statuses)

    def enabled_manifests(self) -> list[CapabilityPluginManifest]:
        """Return only manifests whose plugins are enabled and compatible."""
        enabled_ids = {s.plugin_id for s in self._statuses if s.enabled}
        return [m for m in self._manifests if m.plugin_id in enabled_ids]

    def merged_step_registry(
        self,
    ) -> dict[str, WorkflowStepDefinition]:
        """Return the core step registry merged with enabled plugin steps."""
        registry = get_default_step_registry()
        for manifest in self.enabled_manifests():
            for step in manifest.steps:
                registry[step.step_id] = step.model_copy(deep=True)
        return registry
