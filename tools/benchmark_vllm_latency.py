"""Quick latency benchmark for the Qwen3-32B vllm service.

Measures:
- TTFT (time to first token, streaming)
- TPOT (time per output token, after the first)
- Total wall-clock for a fixed-length completion

Runs 3 warm-up calls then 5 measured calls, prints aggregates.
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.request

DEFAULT_PROMPTS = [
    # Short prompt, ~50 tokens, asks for a fixed-length numeric answer.
    {
        "system": "You are a concise math tutor. Answer in exactly 3 sentences.",
        "user": "Explain why the floating-point representation of 0.1 + 0.2 is not exactly 0.3.",
    },
    # Mid-length prompt, ~250 tokens
    {
        "system": "You are a research advisor.",
        "user": (
            "Briefly review this thesis topic: 'When a request enters an LLM "
            "inference system, partial KV reuse or full recompute may sometimes "
            "be faster than blanket full reuse. The system schedules dynamically "
            "according to IO state and request load.' Identify the strongest "
            "and weakest aspects of this framing in 5 bullet points."
        ),
    },
]


def measure_one(host: str, model: str, prompts: dict, max_tokens: int) -> dict:
    body = {
        "model": model,
        "stream": True,
        "max_tokens": max_tokens,
        "temperature": 0.0,
        "messages": [
            {"role": "system", "content": prompts["system"]},
            {"role": "user", "content": prompts["user"]},
        ],
        # Disable thinking for Qwen3 to keep results comparable across runs.
        "chat_template_kwargs": {"enable_thinking": False},
    }
    payload = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{host}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": "Bearer noop"},
        method="POST",
    )

    t0 = time.perf_counter()
    ttft: float | None = None
    n_tokens = 0
    last_t = t0
    inter_token_deltas: list[float] = []

    with urllib.request.urlopen(req, timeout=300) as resp:
        for raw_line in resp:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line.startswith("data:"):
                continue
            payload_str = line[5:].strip()
            if payload_str == "[DONE]":
                break
            try:
                obj = json.loads(payload_str)
            except json.JSONDecodeError:
                continue
            choices = obj.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta") or {}
            content_chunk = delta.get("content")
            if not content_chunk:
                continue
            now = time.perf_counter()
            if ttft is None:
                ttft = now - t0
                last_t = now
            else:
                inter_token_deltas.append(now - last_t)
                last_t = now
            n_tokens += 1

    total = time.perf_counter() - t0
    tpot = statistics.mean(inter_token_deltas) if inter_token_deltas else float("nan")
    return {
        "ttft_s": ttft,
        "tpot_ms": tpot * 1000.0 if tpot == tpot else float("nan"),
        "n_tokens": n_tokens,
        "total_s": total,
        "throughput_tok_s": n_tokens / total if total > 0 else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="http://127.0.0.1:18000")
    parser.add_argument("--model", default="Qwen3-32B")
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--label", default="baseline")
    args = parser.parse_args()

    print(f"[{args.label}] target={args.host} model={args.model} max_tokens={args.max_tokens}")
    for prompt in DEFAULT_PROMPTS:
        label = prompt["user"][:40].replace("\n", " ") + "..."
        print(f"\n>>> prompt: {label}")
        for _ in range(args.warmup):
            measure_one(args.host, args.model, prompt, args.max_tokens)
        ttfts = []
        tpots = []
        ns = []
        tots = []
        for i in range(args.runs):
            r = measure_one(args.host, args.model, prompt, args.max_tokens)
            ttfts.append(r["ttft_s"])
            tpots.append(r["tpot_ms"])
            ns.append(r["n_tokens"])
            tots.append(r["total_s"])
            print(
                f"  run {i + 1}: ttft={r['ttft_s']:.3f}s "
                f"tpot={r['tpot_ms']:.1f}ms n={r['n_tokens']} "
                f"total={r['total_s']:.2f}s tps={r['throughput_tok_s']:.2f}"
            )
        print(
            f"  median: ttft={statistics.median(ttfts):.3f}s "
            f"tpot={statistics.median(tpots):.1f}ms "
            f"total={statistics.median(tots):.2f}s "
            f"throughput={statistics.median([n / t for n, t in zip(ns, tots)]):.2f} tok/s"
        )


if __name__ == "__main__":
    main()
