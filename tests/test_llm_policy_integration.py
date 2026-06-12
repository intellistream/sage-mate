from __future__ import annotations

from sage_faculty_twin.config import AppSettings
from sage_faculty_twin.llm_client import VllmChatClient


def _build_settings(*, enabled: bool) -> AppSettings:
    return AppSettings(
        llm_policy_enabled=enabled,
        llm_policy_variant_kind="ablation",
        llm_policy_variant_name="adaptive-controller",
        llm_policy_execution_priority_mode="off",
        llm_policy_output_max_tokens_cap=512,
        llm_policy_output_min_tokens_floor=192,
        llm_policy_congestion_waiting_threshold=1.0,
        llm_policy_congestion_kv_usage_threshold=0.75,
        llm_policy_congestion_total_requests_threshold=8.0,
    )


def test_llm_policy_disabled_keeps_max_tokens_unchanged() -> None:
    client = VllmChatClient(_build_settings(enabled=False))
    try:
        payload = {"max_tokens": 512}
        client._apply_serving_policy_to_payload(
            payload,
            deadline_class="interactive-high",
            request_priority=90,
            target_e2e_ms=2200.0,
        )
        assert payload["max_tokens"] == 512
    finally:
        client.close()


def test_llm_policy_enabled_caps_tokens_under_overload() -> None:
    client = VllmChatClient(_build_settings(enabled=True))
    try:
        client._vllm_num_requests_running = 4.0
        client._vllm_num_requests_waiting = 2.0
        client._vllm_kv_cache_usage_perc = 0.08
        # Skip live metric polling so this test remains deterministic.
        client._vllm_metrics_last_refresh_at = 10**12

        payload = {"max_tokens": 512}
        client._apply_serving_policy_to_payload(
            payload,
            deadline_class="interactive-high",
            request_priority=90,
            target_e2e_ms=2200.0,
        )
        assert payload["max_tokens"] == 256
    finally:
        client.close()


def test_llm_policy_enabled_low_congestion_keeps_tokens_when_under_cap() -> None:
    client = VllmChatClient(_build_settings(enabled=True))
    try:
        client._vllm_num_requests_running = 1.0
        client._vllm_num_requests_waiting = 0.0
        client._vllm_kv_cache_usage_perc = 0.10
        client._vllm_metrics_last_refresh_at = 10**12

        payload = {"max_tokens": 384}
        client._apply_serving_policy_to_payload(
            payload,
            deadline_class="interactive-high",
            request_priority=90,
            target_e2e_ms=2200.0,
        )
        assert payload["max_tokens"] == 384
    finally:
        client.close()


def test_llm_policy_enabled_applies_global_output_cap_when_low_congestion() -> None:
    client = VllmChatClient(_build_settings(enabled=True))
    try:
        client._vllm_num_requests_running = 1.0
        client._vllm_num_requests_waiting = 0.0
        client._vllm_kv_cache_usage_perc = 0.10
        client._vllm_metrics_last_refresh_at = 10**12

        payload = {"max_tokens": 2048}
        client._apply_serving_policy_to_payload(
            payload,
            deadline_class="batch-standard",
            request_priority=45,
            target_e2e_ms=10000.0,
        )
        assert payload["max_tokens"] == 512
    finally:
        client.close()


def test_llm_policy_enforces_interactive_min_floor_under_overload() -> None:
    client = VllmChatClient(_build_settings(enabled=True))
    try:
        client._vllm_num_requests_running = 4.0
        client._vllm_num_requests_waiting = 2.0
        client._vllm_kv_cache_usage_perc = 0.08
        client._vllm_metrics_last_refresh_at = 10**12

        payload = {"max_tokens": 192}
        client._apply_serving_policy_to_payload(
            payload,
            deadline_class="interactive-high",
            request_priority=90,
            target_e2e_ms=2200.0,
        )
        assert payload["max_tokens"] == 192
    finally:
        client.close()