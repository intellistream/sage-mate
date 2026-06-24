from __future__ import annotations

from tools.segment_reuse_experiment import (
    BODY_MARKER_BEGIN,
    TrialConfig,
    _build_messages,
)


def _system_text(config: TrialConfig) -> tuple[str, dict]:
    messages, extras = _build_messages(config, model="demo-model", request_id=1)
    return messages[0]["content"], extras


def test_experiment_baseline_uses_envelope_before_body_without_hints() -> None:
    system_text, extras = _system_text(
        TrialConfig(
            variant="baseline_e_b",
            body_tokens=512,
            envelope_tokens=32,
            concurrency=1,
            repeated_mode="cold",
        )
    )

    assert system_text.index("ENVELOPE") < system_text.index(BODY_MARKER_BEGIN)
    assert extras == {}


def test_experiment_native_prefix_uses_body_before_envelope_and_cache_salt() -> None:
    system_text, extras = _system_text(
        TrialConfig(
            variant="native_b_e",
            body_tokens=512,
            envelope_tokens=32,
            concurrency=1,
            repeated_mode="hot",
        )
    )

    assert system_text.index(BODY_MARKER_BEGIN) < system_text.index("ENVELOPE")
    assert extras["cache_salt"].startswith("native-prefix:demo-model:512:32")
    assert "extra_key" not in extras


def test_experiment_segment_hint_keeps_envelope_before_body_and_sends_extra_key() -> None:
    system_text, extras = _system_text(
        TrialConfig(
            variant="segment_hint_e_b",
            body_tokens=512,
            envelope_tokens=32,
            concurrency=1,
            repeated_mode="hot",
        )
    )

    assert system_text.index("ENVELOPE") < system_text.index(BODY_MARKER_BEGIN)
    assert "cache_salt" not in extras
    assert extras["extra_key"].startswith("sage-faculty-twin:experiment:lab_member:")
    assert "||segreuse:v1;" in extras["extra_key"]
    assert "leading_tokens=;" in extras["extra_key"]
