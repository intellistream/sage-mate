"""Smoke-test twin segment-reuse/prefix-cache runtime behavior.

This is intentionally a small online regression probe, not a benchmark suite.
It sends a fixed set of representative questions through /chat, then repeats
them with fresh conversation ids. The output separates app-level timing from
vLLM prefix-cache metrics so we can spot obvious wiring bugs or regressions.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

from benchmark_vllm_latency import _load_env, _metric_delta, _read_prefix_metrics


CASES: tuple[tuple[str, str, str], ...] = (
    (
        "route",
        "我想了解的是：这个课题组的研究路线和一般企业 R&D 有什么区别？请用三点说明。",
        "general_visitor",
    ),
    (
        "kv",
        "我想研究的问题是：在长上下文 LLM 服务中，如何通过 KV 缓存分段复用来减少首次响应延迟？",
        "general_visitor",
    ),
    (
        "lab",
        "作为 lab member，我想把 segment-reuse 接到 twin 的 skills 机制里，哪些风险和指标最关键？",
        "lab_member",
    ),
)


def _post_chat(
    app_url: str,
    label: str,
    question: str,
    visitor_profile: str,
    *,
    batch_id: str,
    stable_questions: bool,
) -> dict[str, Any]:
    effective_question = question
    if not stable_questions:
        effective_question = (
            f"{question}\n\n"
            f"本次线上性能 smoke 批次编号：{batch_id}-{label}。"
            "请只把它当作测试编号，不要解释这个编号。"
        )
    body = {
        "student_name": "segment reuse smoke",
        "question": effective_question,
        "visitor_profile": visitor_profile,
        "conversation_id": f"seg-smoke-{label}-{uuid.uuid4().hex[:10]}",
        "deep_thinking": False,
    }
    request = urllib.request.Request(
        app_url.rstrip("/") + "/chat",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=180) as response:
        payload = json.loads(response.read().decode("utf-8", errors="replace"))
    elapsed_s = time.perf_counter() - started
    steps = {
        step.get("key"): step.get("duration_ms")
        for step in payload.get("workflow_trace") or []
        if isinstance(step, dict)
    }
    summaries = {
        step.get("key"): step.get("summary")
        for step in payload.get("workflow_trace") or []
        if isinstance(step, dict)
    }
    return {
        "label": label,
        "visitor_profile": visitor_profile,
        "elapsed_s": elapsed_s,
        "answer_len": len(payload.get("answer") or ""),
        "knowledge_ms": steps.get("knowledge_retrieve"),
        "llm_ms": steps.get("llm_answer"),
        "memory_ms": steps.get("memory_retrieve"),
        "knowledge_summary": summaries.get("knowledge_retrieve"),
    }


def _median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--app-url", default="http://127.0.0.1:55601")
    parser.add_argument("--metrics-url", default=None)
    parser.add_argument("--strict", action="store_true", help="fail on conservative smoke thresholds")
    parser.add_argument(
        "--stable-questions",
        action="store_true",
        help="send exact canonical questions instead of adding a unique batch suffix",
    )
    parser.add_argument("--max-first-median-s", type=float, default=12.0)
    parser.add_argument("--max-repeat-median-s", type=float, default=6.0)
    parser.add_argument("--min-prefix-hit-rate", type=float, default=0.10)
    args = parser.parse_args()

    env = _load_env(args.repo_root)
    metrics_url = args.metrics_url or env.get("DIGITAL_TWIN_VLLM_METRICS_URL") or ""
    api_key = env.get("DIGITAL_TWIN_API_KEY") or ""

    before = _read_prefix_metrics(metrics_url, api_key=api_key) if metrics_url else {}
    first: list[dict[str, Any]] = []
    repeat: list[dict[str, Any]] = []
    batch_id = uuid.uuid4().hex[:8]

    for label, question, visitor_profile in CASES:
        first.append(
            _post_chat(
                args.app_url,
                label,
                question,
                visitor_profile,
                batch_id=f"{batch_id}-first",
                stable_questions=args.stable_questions,
            )
        )
    for label, question, visitor_profile in CASES:
        repeat.append(
            _post_chat(
                args.app_url,
                label,
                question,
                visitor_profile,
                batch_id=f"{batch_id}-repeat",
                stable_questions=args.stable_questions,
            )
        )

    after = _read_prefix_metrics(metrics_url, api_key=api_key) if metrics_url else {}
    delta = _metric_delta(before, after) if before and after else {}

    first_median = _median([item["elapsed_s"] for item in first])
    repeat_median = _median([item["elapsed_s"] for item in repeat])
    queries = float(delta.get("prefix_cache_queries", 0.0))
    hits = float(delta.get("prefix_cache_hits", 0.0))
    hit_rate = hits / queries if queries > 0 else 0.0

    report = {
        "app_url": args.app_url,
        "batch_id": batch_id,
        "stable_questions": args.stable_questions,
        "first": first,
        "repeat": repeat,
        "summary": {
            "first_median_s": first_median,
            "repeat_median_s": repeat_median,
            "prefix_cache_delta": delta,
            "prefix_cache_hit_rate": hit_rate,
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.strict:
        failures: list[str] = []
        if first_median > args.max_first_median_s:
            failures.append(
                f"first median {first_median:.3f}s exceeds {args.max_first_median_s:.3f}s"
            )
        if repeat_median > args.max_repeat_median_s:
            failures.append(
                f"repeat median {repeat_median:.3f}s exceeds {args.max_repeat_median_s:.3f}s"
            )
        if queries > 0 and hit_rate < args.min_prefix_hit_rate:
            failures.append(
                f"prefix hit rate {hit_rate:.3f} below {args.min_prefix_hit_rate:.3f}"
            )
        if failures:
            raise SystemExit("Smoke regression: " + "; ".join(failures))


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code}: {detail[:800]}") from exc
