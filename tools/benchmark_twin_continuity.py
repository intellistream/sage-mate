#!/usr/bin/env python3
"""Benchmark twin session continuity with and without DeltaKV warm-start.

Measures:
- TTFT for turn N given turns 1..N-1 already served (with/without DeltaKV)
- Session survival time: how quickly a conversation resumes after vLLM restart
- User-visible disruption gap during simulated rolling maintenance

Usage:
    python tools/benchmark_twin_continuity.py --base-url http://127.0.0.1:8000/v1
    python tools/benchmark_twin_continuity.py --base-url http://127.0.0.1:8000/v1 --num-turns 5
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import urllib.request
import urllib.error

CONVERSATION_TURNS = [
    {
        "role": "user",
        "content": (
            "Hello! I'm a doctoral student working on my dissertation about "
            "disaggregated LLM serving architectures. Can you give me a brief "
            "overview of the key challenges in KV cache management for "
            "disaggregated prefill-decode systems?"
        ),
    },
    {
        "role": "user",
        "content": (
            "That's helpful. Now let's go deeper: what are the trade-offs "
            "between full KV transfer and incremental delta transfer when a "
            "decode worker needs to be migrated during rolling maintenance? "
            "Please compare at least three approaches."
        ),
    },
    {
        "role": "user",
        "content": (
            "Interesting. For my experimental evaluation, I'm planning to "
            "measure the continuity disruption time under different transfer "
            "strategies. What metrics would you recommend I report, and what "
            "baseline comparisons would be most convincing for an ASPLOS paper?"
        ),
    },
    {
        "role": "user",
        "content": (
            "Thank you. Finally, can you draft a 200-word abstract for my "
            "paper that frames the contribution around bounding continuity "
            "disruption time for long-session LLM serving?"
        ),
    },
]


def send_streaming_request(
    base_url: str,
    model: str,
    messages: list[dict],
    max_tokens: int,
    *,
    kv_transfer_params: dict | None = None,
    timeout_s: float = 120.0,
) -> dict:
    """Send a streaming chat completion request and measure TTFT + TPOT."""
    api_url = f"{base_url}/chat/completions"
    body: dict = {
        "model": model,
        "stream": True,
        "max_tokens": max_tokens,
        "temperature": 0.0,
        "messages": messages,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    if kv_transfer_params:
        body["kv_transfer_params"] = kv_transfer_params

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        api_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    start_time = time.perf_counter()
    first_token_time: float | None = None
    output_tokens = 0
    generated_text = ""
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8").strip()
                if not line or not line.startswith("data: "):
                    continue
                payload = line[6:]
                if payload == "[DONE]":
                    break
                try:
                    chunk = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                choices = chunk.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "")
                    if content and first_token_time is None:
                        first_token_time = time.perf_counter()
                    if content:
                        generated_text += content
                        output_tokens += 1
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "ttft_ms": 0.0,
            "tpot_ms": 0.0,
            "latency_ms": (time.perf_counter() - start_time) * 1000.0,
            "output_tokens": 0,
        }

    end_time = time.perf_counter()
    latency_ms = (end_time - start_time) * 1000.0
    ttft_ms = (first_token_time - start_time) * 1000.0 if first_token_time else latency_ms
    tpot_ms = 0.0
    if output_tokens > 1 and first_token_time:
        tpot_ms = (end_time - first_token_time) * 1000.0 / (output_tokens - 1)

    return {
        "success": True,
        "error": "",
        "ttft_ms": ttft_ms,
        "tpot_ms": tpot_ms,
        "latency_ms": latency_ms,
        "output_tokens": output_tokens,
        "generated_text_preview": generated_text[:200],
    }


def detect_model_name(base_url: str) -> str:
    """Discover the model name from the /models endpoint."""
    try:
        req = urllib.request.Request(f"{base_url}/models")
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = data.get("data", [])
            if models:
                return str(models[0].get("id", ""))
    except Exception:
        pass
    return "default"


def wait_for_server(base_url: str, timeout_s: float = 300.0) -> bool:
    """Wait until the vLLM server is ready."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            req = urllib.request.Request(f"{base_url}/models")
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(2.0)
    return False


def run_multi_turn_benchmark(
    base_url: str,
    model: str,
    num_turns: int,
    max_tokens: int,
    *,
    use_kv_hints: bool = False,
    session_key: str = "benchmark-session",
    label: str = "no-hints",
) -> list[dict]:
    """Run a multi-turn conversation and measure per-turn metrics."""
    messages: list[dict] = [
        {
            "role": "system",
            "content": (
                "You are a trusted academic digital twin. Answer clearly "
                "and concisely, providing structured responses."
            ),
        }
    ]
    results: list[dict] = []
    turns_to_run = min(num_turns, len(CONVERSATION_TURNS))

    for turn_idx in range(turns_to_run):
        user_msg = CONVERSATION_TURNS[turn_idx]
        messages.append(user_msg)

        kv_params = None
        if use_kv_hints:
            kv_params = {"logical_request_id": session_key}

        result = send_streaming_request(
            base_url, model, messages, max_tokens,
            kv_transfer_params=kv_params,
        )
        result["turn"] = turn_idx + 1
        result["label"] = label
        result["session_key"] = session_key
        result["cumulative_messages"] = len(messages)

        if result["success"]:
            messages.append({
                "role": "assistant",
                "content": result["generated_text_preview"],
            })
            print(
                f"  Turn {turn_idx + 1}: TTFT={result['ttft_ms']:.1f}ms  "
                f"TPOT={result['tpot_ms']:.1f}ms  "
                f"tokens={result['output_tokens']}  "
                f"latency={result['latency_ms']:.1f}ms"
            )
        else:
            print(f"  Turn {turn_idx + 1}: FAILED - {result['error']}")

        results.append(result)

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark twin session continuity with DeltaKV."
    )
    parser.add_argument(
        "--base-url", default="http://127.0.0.1:8000/v1",
        help="vLLM OpenAI-compatible API base URL.",
    )
    parser.add_argument(
        "--model", default="",
        help="Model name. Auto-detected from /models if empty.",
    )
    parser.add_argument(
        "--num-turns", type=int, default=4,
        help="Number of conversation turns to run.",
    )
    parser.add_argument(
        "--max-tokens", type=int, default=256,
        help="Max tokens per response.",
    )
    parser.add_argument(
        "--session-key", default="twin-benchmark-session",
        help="Session key for KV transfer hints.",
    )
    parser.add_argument(
        "--output-file", default=None,
        help="Path to write results JSON.",
    )
    args = parser.parse_args()

    model = args.model or detect_model_name(args.base_url)
    print(f"Model: {model}")
    print(f"Base URL: {args.base_url}")
    print(f"Turns: {args.num_turns}, Max tokens: {args.max_tokens}")
    print()

    if not wait_for_server(args.base_url, timeout_s=60.0):
        print("ERROR: vLLM server not ready within 60s", file=sys.stderr)
        sys.exit(1)

    print("=== Run 1: Cold (no KV hints) ===")
    cold_results = run_multi_turn_benchmark(
        args.base_url, model, args.num_turns, args.max_tokens,
        use_kv_hints=False,
        session_key=args.session_key,
        label="cold",
    )
    print()

    print("=== Run 2: Warm (with KV hints) ===")
    warm_results = run_multi_turn_benchmark(
        args.base_url, model, args.num_turns, args.max_tokens,
        use_kv_hints=True,
        session_key=args.session_key,
        label="warm",
    )
    print()

    cold_ttft = [r["ttft_ms"] for r in cold_results if r["success"]]
    warm_ttft = [r["ttft_ms"] for r in warm_results if r["success"]]
    cold_latency = [r["latency_ms"] for r in cold_results if r["success"]]
    warm_latency = [r["latency_ms"] for r in warm_results if r["success"]]

    print("=== Summary ===")
    if cold_ttft:
        print(f"Cold TTFT mean: {statistics.mean(cold_ttft):.1f}ms  "
              f"(p50={statistics.median(cold_ttft):.1f}ms)")
    if warm_ttft:
        print(f"Warm TTFT mean: {statistics.mean(warm_ttft):.1f}ms  "
              f"(p50={statistics.median(warm_ttft):.1f}ms)")
    if cold_ttft and warm_ttft:
        improvement = (
            (statistics.mean(cold_ttft) - statistics.mean(warm_ttft))
            / statistics.mean(cold_ttft) * 100.0
        )
        print(f"TTFT improvement: {improvement:+.1f}%")
    print()

    print("=== Continuity Disruption Time ===")
    if cold_ttft:
        print(f"Cold start TTFT (restart disruption): {cold_ttft[0]:.1f}ms")
    if warm_ttft:
        print(f"Warm start TTFT (DeltaKV recovery): {warm_ttft[0]:.1f}ms")
    print()

    output = {
        "model": model,
        "base_url": args.base_url,
        "num_turns": args.num_turns,
        "max_tokens": args.max_tokens,
        "session_key": args.session_key,
        "cold_results": cold_results,
        "warm_results": warm_results,
        "summary": {
            "cold_ttft_mean_ms": statistics.mean(cold_ttft) if cold_ttft else 0.0,
            "cold_ttft_p50_ms": statistics.median(cold_ttft) if cold_ttft else 0.0,
            "warm_ttft_mean_ms": statistics.mean(warm_ttft) if warm_ttft else 0.0,
            "warm_ttft_p50_ms": statistics.median(warm_ttft) if warm_ttft else 0.0,
            "cold_latency_mean_ms": statistics.mean(cold_latency) if cold_latency else 0.0,
            "warm_latency_mean_ms": statistics.mean(warm_latency) if warm_latency else 0.0,
            "continuity_disruption_time_cold_ms": cold_ttft[0] if cold_ttft else 0.0,
            "continuity_disruption_time_warm_ms": warm_ttft[0] if warm_ttft else 0.0,
        },
    }

    if args.output_file:
        with open(args.output_file, "w") as f:
            json.dump(output, f, indent=2)
        print(f"Results written to {args.output_file}")
    else:
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
