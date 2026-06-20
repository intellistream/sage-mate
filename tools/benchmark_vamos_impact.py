#!/usr/bin/env python3
"""Benchmark A/B performance impact for my-twin deployments.

This script compares two chat endpoints (baseline vs VAMOS-enabled) on the
same request set and reports latency/throughput/truncation deltas.

Example:
  python tools/benchmark_vamos_impact.py \
    --baseline-url http://127.0.0.1:55601/chat \
    --vamos-url http://127.0.0.1:8010/chat \
    --requests-per-level 24 --concurrency-levels 1,4,8
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError, as_completed
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_QUESTIONS = [
    "我现在想把一个推理系统小课题做成可汇报成果，请给我一个两周执行计划。",
    "如果我手里只有初步实验数据，向老师请教前该如何组织问题更高效？",
    "我准备预约讨论论文进展，能给我一个会前材料清单和优先级吗？",
    "我在做系统优化实验，结果波动较大，下一步应该先做哪些排查？",
    "如果要把实验工作整理成组会汇报，建议怎么分成三部分结构？",
    "我想在下次交流前补齐方法对比，应该优先补哪些对照实验？",
]


@dataclass
class RequestResult:
    ok: bool
    latency_ms: float
    answer_chars: int
    truncated: bool
    error: str | None = None


@dataclass
class VariantStats:
    label: str
    url: str
    total_requests: int
    success_count: int
    success_rate: float
    wall_time_s: float
    throughput_rps: float
    mean_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    mean_answer_chars: float
    truncation_rate: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark VAMOS impact on my-twin chat performance")
    parser.add_argument("--baseline-url", required=True, help="Baseline /chat endpoint URL")
    parser.add_argument("--vamos-url", required=True, help="VAMOS-enabled /chat endpoint URL")
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--requests-per-level", type=int, default=24)
    parser.add_argument("--concurrency-levels", default="1,4,8")
    parser.add_argument("--course-context", default="科研指导")
    parser.add_argument("--student-name", default="VAMOS Benchmark User")
    parser.add_argument("--student-email", default="vamos-benchmark@example.com")
    parser.add_argument("--conversation-prefix", default="vamos-bench")
    parser.add_argument(
        "--skip-preflight",
        action="store_true",
        help="Skip endpoint health/chat preflight checks before running benchmark.",
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Run preflight checks only and exit without running benchmark workload.",
    )
    parser.add_argument(
        "--question-file",
        type=Path,
        default=None,
        help="Optional JSON file containing a list of benchmark questions.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output JSON path. Defaults to .benchmarks/vamos-impact-<timestamp>.json",
    )
    return parser.parse_args()


def load_questions(path: Path | None) -> list[str]:
    if path is None:
        return list(DEFAULT_QUESTIONS)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not payload:
        raise ValueError("question file must be a non-empty JSON list")
    questions = [str(item).strip() for item in payload if str(item).strip()]
    if not questions:
        raise ValueError("question file has no valid non-empty questions")
    return questions


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    low = int(pos)
    high = min(low + 1, len(ordered) - 1)
    if low == high:
        return ordered[low]
    weight = pos - low
    return ordered[low] * (1.0 - weight) + ordered[high] * weight


def looks_truncated(answer: str) -> bool:
    text = answer.strip()
    if not text:
        return True
    if "[回答因长度限制被截断]" in text:
        return True
    terminal_chars = ("。", "！", "？", ".", "!", "?", "）", ")", "】", "]")
    return not text.endswith(terminal_chars)


def post_chat(
    *,
    url: str,
    timeout_seconds: int,
    payload: dict[str, Any],
) -> RequestResult:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8", errors="replace")
            data = json.loads(raw)
            answer = str(data.get("answer") or "")
        latency_ms = (time.perf_counter() - started) * 1000.0
        return RequestResult(
            ok=True,
            latency_ms=latency_ms,
            answer_chars=len(answer),
            truncated=looks_truncated(answer),
        )
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
        latency_ms = (time.perf_counter() - started) * 1000.0
        return RequestResult(
            ok=False,
            latency_ms=latency_ms,
            answer_chars=0,
            truncated=True,
            error=str(exc),
        )


def _health_url_from_chat_url(chat_url: str) -> str:
    parts = urllib.parse.urlsplit(chat_url)
    path = parts.path
    if path.endswith("/chat"):
        path = path[: -len("/chat")] + "/health"
    else:
        path = path.rstrip("/") + "/health"
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, path, "", ""))


def run_preflight(
    *,
    label: str,
    chat_url: str,
    timeout_seconds: int,
    student_name: str,
    student_email: str,
    course_context: str,
    conversation_prefix: str,
) -> tuple[bool, str]:
    health_url = _health_url_from_chat_url(chat_url)
    health_note = ""

    health_request = urllib.request.Request(health_url, method="GET")
    try:
        with urllib.request.urlopen(health_request, timeout=max(5, min(timeout_seconds, 20))) as response:
            raw = response.read().decode("utf-8", errors="replace")
            payload = json.loads(raw)
        health_status = str(payload.get("status") or "").strip().lower()
        if health_status != "ok":
            health_note = f"health={health_status or 'unknown'}"
    except Exception as exc:
        return False, f"{label} health check failed: {exc}"

    probe_payload = {
        "student_name": student_name,
        "student_email": student_email,
        "course_context": course_context,
        "visitor_profile": "general_visitor",
        "deep_thinking": False,
        "deep_thinking_explicit": True,
        "conversation_id": f"{conversation_prefix}-{label}-preflight",
        "question": "请用一句话确认服务可用。",
    }
    probe_result = post_chat(
        url=chat_url,
        timeout_seconds=max(10, min(timeout_seconds, 45)),
        payload=probe_payload,
    )
    if not probe_result.ok:
        return False, f"{label} chat probe failed: {probe_result.error or 'unknown error'}"

    suffix = f" ({health_note})" if health_note else ""
    return True, (
        f"{label} preflight ok: latency={probe_result.latency_ms:.2f}ms "
        f"answer_chars={probe_result.answer_chars}{suffix}"
    )


def run_variant(
    *,
    label: str,
    url: str,
    concurrency: int,
    requests_per_level: int,
    timeout_seconds: int,
    questions: list[str],
    student_name: str,
    student_email: str,
    course_context: str,
    conversation_prefix: str,
) -> VariantStats:
    def build_payload(index: int) -> dict[str, Any]:
        question = questions[index % len(questions)]
        return {
            "student_name": student_name,
            "student_email": student_email,
            "course_context": course_context,
            "visitor_profile": "general_visitor",
            "deep_thinking": False,
            "deep_thinking_explicit": True,
            "conversation_id": f"{conversation_prefix}-{label}-{concurrency}-{index}",
            "question": question,
        }

    started = time.perf_counter()
    results: list[RequestResult] = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(
                post_chat,
                url=url,
                timeout_seconds=timeout_seconds,
                payload=build_payload(i),
            )
            for i in range(requests_per_level)
        ]
        done_futures = set()
        try:
            for future in as_completed(futures, timeout=max(1, timeout_seconds + 30)):
                results.append(future.result())
                done_futures.add(future)
        except FuturesTimeoutError:
            # Mark unfinished requests explicitly as timeout failures so the run
            # can still produce summary metrics under degraded endpoints.
            pass

        for future in futures:
            if future in done_futures:
                continue
            future.cancel()
            results.append(
                RequestResult(
                    ok=False,
                    latency_ms=float(timeout_seconds * 1000),
                    answer_chars=0,
                    truncated=True,
                    error="benchmark-timeout",
                )
            )
    wall_time_s = time.perf_counter() - started

    success = [item for item in results if item.ok]
    latencies = [item.latency_ms for item in success]
    mean_latency = statistics.fmean(latencies) if latencies else 0.0
    mean_chars = statistics.fmean([item.answer_chars for item in success]) if success else 0.0
    trunc_rate = (
        statistics.fmean([1.0 if item.truncated else 0.0 for item in success]) if success else 1.0
    )

    return VariantStats(
        label=f"{label}-c{concurrency}",
        url=url,
        total_requests=len(results),
        success_count=len(success),
        success_rate=(len(success) / len(results)) if results else 0.0,
        wall_time_s=wall_time_s,
        throughput_rps=(len(success) / wall_time_s) if wall_time_s > 0 else 0.0,
        mean_latency_ms=mean_latency,
        p50_latency_ms=percentile(latencies, 0.50),
        p95_latency_ms=percentile(latencies, 0.95),
        mean_answer_chars=mean_chars,
        truncation_rate=trunc_rate,
    )


def summarize_delta(baseline: VariantStats, vamos: VariantStats) -> dict[str, float]:
    def rel(new: float, old: float) -> float:
        if old == 0:
            return 0.0
        return (new - old) / old

    return {
        "latency_p50_delta_pct": rel(vamos.p50_latency_ms, baseline.p50_latency_ms) * 100.0,
        "latency_p95_delta_pct": rel(vamos.p95_latency_ms, baseline.p95_latency_ms) * 100.0,
        "throughput_delta_pct": rel(vamos.throughput_rps, baseline.throughput_rps) * 100.0,
        "success_rate_delta_pct": (vamos.success_rate - baseline.success_rate) * 100.0,
        "truncation_rate_delta_pct": (vamos.truncation_rate - baseline.truncation_rate) * 100.0,
        "answer_chars_delta_pct": rel(vamos.mean_answer_chars, baseline.mean_answer_chars) * 100.0,
    }


def default_output_path() -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    root = Path(__file__).resolve().parents[1]
    out_dir = root / ".benchmarks"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"vamos-impact-{stamp}.json"


def print_summary(baseline: VariantStats, vamos: VariantStats, delta: dict[str, float]) -> None:
    print(
        "label\tsuccess\tp50_ms\tp95_ms\trps\tavg_chars\ttrunc_rate"
    )
    for item in (baseline, vamos):
        print(
            f"{item.label}\t"
            f"{item.success_count}/{item.total_requests} ({item.success_rate:.3f})\t"
            f"{item.p50_latency_ms:.2f}\t"
            f"{item.p95_latency_ms:.2f}\t"
            f"{item.throughput_rps:.2f}\t"
            f"{item.mean_answer_chars:.2f}\t"
            f"{item.truncation_rate:.3f}"
        )

    print("\nDelta (VAMOS vs baseline)")
    print(
        f"p50: {delta['latency_p50_delta_pct']:+.2f}% | "
        f"p95: {delta['latency_p95_delta_pct']:+.2f}% | "
        f"RPS: {delta['throughput_delta_pct']:+.2f}% | "
        f"success: {delta['success_rate_delta_pct']:+.2f}pp | "
        f"truncation: {delta['truncation_rate_delta_pct']:+.2f}pp | "
        f"answer_chars: {delta['answer_chars_delta_pct']:+.2f}%"
    )


def main() -> int:
    args = parse_args()
    questions = load_questions(args.question_file)
    concurrency_levels = [int(part.strip()) for part in args.concurrency_levels.split(",") if part.strip()]
    if not concurrency_levels:
        raise ValueError("concurrency levels must not be empty")

    if not args.skip_preflight:
        print("Running preflight checks...")
        baseline_ok, baseline_msg = run_preflight(
            label="baseline",
            chat_url=args.baseline_url,
            timeout_seconds=args.timeout_seconds,
            student_name=args.student_name,
            student_email=args.student_email,
            course_context=args.course_context,
            conversation_prefix=args.conversation_prefix,
        )
        print(f"- {baseline_msg}")

        vamos_ok, vamos_msg = run_preflight(
            label="vamos",
            chat_url=args.vamos_url,
            timeout_seconds=args.timeout_seconds,
            student_name=args.student_name,
            student_email=args.student_email,
            course_context=args.course_context,
            conversation_prefix=args.conversation_prefix,
        )
        print(f"- {vamos_msg}")

        if not (baseline_ok and vamos_ok):
            print("Preflight failed. Benchmark aborted.")
            return 2

    if args.preflight_only:
        print("Preflight-only mode: benchmark skipped.")
        return 0

    runs: list[dict[str, Any]] = []
    for concurrency in concurrency_levels:
        baseline_stats = run_variant(
            label="baseline",
            url=args.baseline_url,
            concurrency=concurrency,
            requests_per_level=args.requests_per_level,
            timeout_seconds=args.timeout_seconds,
            questions=questions,
            student_name=args.student_name,
            student_email=args.student_email,
            course_context=args.course_context,
            conversation_prefix=args.conversation_prefix,
        )
        vamos_stats = run_variant(
            label="vamos",
            url=args.vamos_url,
            concurrency=concurrency,
            requests_per_level=args.requests_per_level,
            timeout_seconds=args.timeout_seconds,
            questions=questions,
            student_name=args.student_name,
            student_email=args.student_email,
            course_context=args.course_context,
            conversation_prefix=args.conversation_prefix,
        )
        delta = summarize_delta(baseline_stats, vamos_stats)
        print(f"\n=== Concurrency {concurrency} ===")
        print_summary(baseline_stats, vamos_stats, delta)
        runs.append(
            {
                "concurrency": concurrency,
                "baseline": asdict(baseline_stats),
                "vamos": asdict(vamos_stats),
                "delta": delta,
            }
        )

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "baseline_url": args.baseline_url,
        "vamos_url": args.vamos_url,
        "requests_per_level": args.requests_per_level,
        "concurrency_levels": concurrency_levels,
        "question_count": len(questions),
        "runs": runs,
    }
    out_path = args.output or default_output_path()
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nReport written to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
