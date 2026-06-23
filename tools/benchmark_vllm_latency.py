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
import os
import re
import statistics
import time
import urllib.error
import urllib.request
from pathlib import Path

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



def _load_env(repo_root: Path) -> dict[str, str]:
    env = dict(os.environ)
    path = repo_root / ".env"
    if not path.exists():
        return env
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env.setdefault(key.strip(), value.strip())
    return env


def _derive_metrics_url(host: str) -> str:
    return re.sub(r"/v1/?$", "", host.rstrip("/")) + "/metrics"


def _read_prefix_metrics(metrics_url: str) -> dict[str, float]:
    selected = {
        "prefix_cache_queries": 0.0,
        "prefix_cache_hits": 0.0,
        "prefix_cache_block_queries": 0.0,
        "prefix_cache_block_hits": 0.0,
        "prefix_cache_blocks_cached": 0.0,
        "vllm:num_requests_running": 0.0,
        "vllm:num_requests_waiting": 0.0,
        "vllm:kv_cache_usage_perc": 0.0,
    }
    metric_aliases = {
        "vllm:prefix_cache_queries": "prefix_cache_queries",
        "vllm:prefix_cache_queries_total": "prefix_cache_queries",
        "vllm:prefix_cache_hits": "prefix_cache_hits",
        "vllm:prefix_cache_hits_total": "prefix_cache_hits",
        "vllm:prefix_cache_block_queries": "prefix_cache_block_queries",
        "vllm:prefix_cache_block_queries_total": "prefix_cache_block_queries",
        "vllm:prefix_cache_block_hits": "prefix_cache_block_hits",
        "vllm:prefix_cache_block_hits_total": "prefix_cache_block_hits",
        "vllm:prefix_cache_blocks_cached": "prefix_cache_blocks_cached",
        "vllm:prefix_cache_blocks_cached_total": "prefix_cache_blocks_cached",
    }
    try:
        with urllib.request.urlopen(metrics_url, timeout=2.0) as resp:
            text = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        return selected

    for raw in text.splitlines():
        if not raw or raw.startswith("#"):
            continue
        name = raw.split("{", 1)[0].split(" ", 1)[0]
        key = metric_aliases.get(name, name)
        if key not in selected:
            continue
        try:
            selected[key] += float(raw.rsplit(" ", 1)[-1])
        except ValueError:
            continue
    return selected


def _metric_delta(before: dict[str, float], after: dict[str, float]) -> dict[str, float]:
    return {key: after.get(key, 0.0) - before.get(key, 0.0) for key in after}


def measure_one(
    host: str,
    model: str,
    prompts: dict,
    max_tokens: int,
    *,
    api_key: str,
    cache_salt: str | None = None,
) -> dict:
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
    if cache_salt:
        body["cache_salt"] = cache_salt
    payload = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{host.rstrip('/')}/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
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
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--host", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--label", default="baseline")
    parser.add_argument("--cache-salt", default=None)
    parser.add_argument("--metrics", action="store_true")
    args = parser.parse_args()

    env = _load_env(args.repo_root)
    host = (args.host or env.get("DIGITAL_TWIN_LLM_BASE_URL") or "http://127.0.0.1:8000/v1").rstrip("/")
    model = args.model or env.get("DIGITAL_TWIN_MODEL_NAME") or "qwen3-32b"
    api_key = env.get("DIGITAL_TWIN_API_KEY") or "EMPTY"
    metrics_url = _derive_metrics_url(host)

    print(f"[{args.label}] target={host} model={model} max_tokens={args.max_tokens}")
    if args.cache_salt:
        print("[benchmark] cache_salt enabled (value redacted)")
    for prompt in DEFAULT_PROMPTS:
        label = prompt["user"][:40].replace("\n", " ") + "..."
        print(f"\n>>> prompt: {label}")
        for _ in range(args.warmup):
            measure_one(host, model, prompt, args.max_tokens, api_key=api_key, cache_salt=args.cache_salt)
        ttfts = []
        tpots = []
        ns = []
        tots = []
        metrics_before = _read_prefix_metrics(metrics_url) if args.metrics else {}
        for i in range(args.runs):
            r = measure_one(host, model, prompt, args.max_tokens, api_key=api_key, cache_salt=args.cache_salt)
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
        if args.metrics:
            metrics_after = _read_prefix_metrics(metrics_url)
            delta = _metric_delta(metrics_before, metrics_after)
            queries = delta["prefix_cache_queries"]
            hits = delta["prefix_cache_hits"]
            block_queries = delta["prefix_cache_block_queries"]
            block_hits = delta["prefix_cache_block_hits"]
            hit_rate = hits / queries if queries > 0 else 0.0
            block_hit_rate = block_hits / block_queries if block_queries > 0 else 0.0
            print(
                "  prefix-cache delta: "
                f"queries={queries:.0f} hits={hits:.0f} hit_rate={hit_rate:.3f} "
                f"block_queries={block_queries:.0f} block_hits={block_hits:.0f} "
                f"block_hit_rate={block_hit_rate:.3f} "
                f"cached_blocks={delta['prefix_cache_blocks_cached']:.0f}"
            )


if __name__ == "__main__":
    main()
