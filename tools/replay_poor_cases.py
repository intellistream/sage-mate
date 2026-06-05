"""Offline replay of the 39 poor-answer cases recorded in
docs/student-questions-poor-answers.md.

For each fixture this script runs the current chat workflow in-process
(against the live vLLM backend) and prints BEFORE/AFTER deltas. A markdown
report is emitted to docs/student-questions-replay-report.md.

Usage:
    cd /home/shuhao/sage-faculty-twin
    PYTHONPATH=src:/home/shuhao/SAGE/src:/home/shuhao/sageVDB:/home/shuhao/neuromem \
        /home/shuhao/miniforge3/envs/sagellm/bin/python3 tools/replay_poor_cases.py
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

# Apply the torch_npu / HF cache shim before importing anything that may
# transitively load transformers (only matters when the FAISS+bge backend is
# selected, but it is a no-op otherwise).
import _setup_hf_cache  # noqa: E402, F401

from sage_faculty_twin.config import AppSettings  # noqa: E402
from sage_faculty_twin.models import ChatRequest, InteractionIntent  # noqa: E402
from sage_faculty_twin.service import DigitalTwinService  # noqa: E402

POOR_DOC = ROOT / "docs" / "student-questions-poor-answers.md"
REPORT_DOC = ROOT / "docs" / "student-questions-replay-report.md"


@dataclass
class Fixture:
    student_name: str
    case_index: int  # per-student
    timestamp: str
    domain: str
    workflow_before: str
    course_context: str
    kb_hits_before: int
    failure_modes: str
    question: str
    answer_before: str

    # Replay output
    workflow_after: str = ""
    answer_after: str = ""
    kb_hits_after: int = 0
    error: str = ""
    verdict: str = ""

    # ordering
    global_index: int = 0
    conversation_id: str = field(default_factory=lambda: f"replay-{uuid.uuid4().hex[:12]}")


_HEADER_RE = re.compile(
    r"^### (?P<idx>\d+)\.\s*\[(?P<ts>[^\]]+)\]\s*\*(?P<domain>[^/]+)\s*/\s*(?P<wf>[^*]+)\*"
    r"\s*课程:(?P<course>[^\s]+)\s*KB:(?P<kb>\d+)"
)
_STUDENT_HEADER_RE = re.compile(r"^##\s+(?P<name>[^(\s]+)\s*\(问题不佳:")


def parse_fixtures(md_path: Path) -> list[Fixture]:
    text = md_path.read_text(encoding="utf-8")
    fixtures: list[Fixture] = []
    current_student: str | None = None
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m_student = _STUDENT_HEADER_RE.match(line)
        if m_student:
            current_student = m_student.group("name").strip()
            i += 1
            continue
        m = _HEADER_RE.match(line)
        if m and current_student:
            idx = int(m.group("idx"))
            ts = m.group("ts").strip()
            domain = m.group("domain").strip()
            wf_before = m.group("wf").strip()
            course = m.group("course").strip()
            kb_before = int(m.group("kb"))
            # next line: failure modes
            failure_modes = ""
            j = i + 1
            while j < len(lines) and not lines[j].startswith("**问题不佳的原因**"):
                j += 1
            if j < len(lines):
                failure_modes = lines[j].split(":", 1)[-1].strip()
            # then **学生提问:** then quoted block of one or more lines
            while j < len(lines) and not lines[j].startswith("**学生提问"):
                j += 1
            j += 1
            question_lines: list[str] = []
            while j < len(lines) and lines[j].startswith(">"):
                question_lines.append(lines[j].lstrip("> ").rstrip())
                j += 1
            question = "\n".join(question_lines).strip()
            # then **Twin 回答:**
            while j < len(lines) and not lines[j].startswith("**Twin 回答"):
                j += 1
            j += 1
            answer_lines: list[str] = []
            while j < len(lines) and (lines[j].startswith(">") or lines[j].strip() == "" and j + 1 < len(lines) and lines[j + 1].startswith(">")):
                if lines[j].startswith(">"):
                    answer_lines.append(lines[j].lstrip("> ").rstrip())
                j += 1
            answer = "\n".join(answer_lines).strip()
            fixtures.append(
                Fixture(
                    student_name=current_student,
                    case_index=idx,
                    timestamp=ts,
                    domain=domain,
                    workflow_before=wf_before,
                    course_context=course,
                    kb_hits_before=kb_before,
                    failure_modes=failure_modes,
                    question=question,
                    answer_before=answer,
                )
            )
            i = j
            continue
        i += 1
    for n, fx in enumerate(fixtures):
        fx.global_index = n + 1
    return fixtures


def assign_conversation_ids(fixtures: list[Fixture]) -> None:
    """Group consecutive same-student same-course cases into one conversation
    so multi-turn follow-ups (e.g. '具体内容') can resolve via session context.
    """
    last_key = None
    last_conv = None
    for fx in fixtures:
        key = (fx.student_name, fx.course_context)
        if key != last_key:
            last_conv = f"replay-{uuid.uuid4().hex[:12]}"
            last_key = key
        fx.conversation_id = last_conv


def _classify_verdict(fx: Fixture) -> str:
    if fx.error:
        return "error"
    before_short = len(fx.answer_before) < 80
    after_short = len(fx.answer_after) < 80
    was_followup = fx.workflow_before == "ask_follow_up"
    is_followup = fx.workflow_after == "ask_follow_up"
    kb_gain = fx.kb_hits_after > fx.kb_hits_before
    has_placeholder_before = "[" in fx.answer_before and "]" in fx.answer_before
    has_placeholder_after = "[" in fx.answer_after and "]" in fx.answer_after
    became_review = fx.workflow_after in {"review_queue", "human_handoff"}
    was_review = fx.workflow_before in {"review_queue", "human_handoff"}

    improvements = 0
    regressions = 0
    if was_followup and not is_followup:
        improvements += 1
    if not was_followup and is_followup:
        regressions += 1
    if before_short and not after_short:
        improvements += 1
    if not before_short and after_short:
        regressions += 1
    if kb_gain:
        improvements += 1
    if has_placeholder_before and not has_placeholder_after:
        improvements += 1
    if not has_placeholder_before and has_placeholder_after:
        regressions += 1
    if was_review and not became_review:
        improvements += 1
    if not was_review and became_review:
        regressions += 1
    if improvements > regressions:
        return "improved"
    if regressions > improvements:
        return "regressed"
    return "unchanged"


def _install_mock_llm(service: DigitalTwinService) -> None:
    """Patch the service's LLM client so the replay can exercise the
    deterministic guardrails (Tasks 2/4/5/8) and the deferred-clarification
    routing (Task 3) without needing the live Qwen3-32B endpoint.

    The mock classifier returns the **baseline** behaviour the analysis
    diagnosed: ``ask_followup`` with a generic clarification message. The
    deterministic post-processor in ``_normalize_interaction_intent`` is
    expected to demote that on cases that match research/advising/identity
    anchors. The mock answerer returns a templated string so we can still
    assert end-to-end shape (workflow_action, knowledge_hits) without LLM
    cost.
    """
    client = service._llm_client  # noqa: SLF001

    def _mock_classify_intent_sync(question, course_context, recent_session_context=None):  # noqa: ARG001
        return InteractionIntent(
            action="ask_followup",
            domain="general",
            decision_mode="direct_answer",
            needs_clarification=True,
            clarification_message="请问您具体需要了解什么?",
            confidence=0.4,
        )

    def _mock_answer_question_sync(system_prompt, user_prompt, **kwargs):  # noqa: ARG001
        # Echo the first 200 chars of the retrieved-context user prompt so
        # we can verify retrieval surfaced material into the prompt.
        snippet = user_prompt.replace("\n", " ")
        if len(snippet) > 240:
            snippet = snippet[:240] + "..."
        return f"[MOCK-LLM回复] 根据检索到的上下文: {snippet}"

    client.classify_interaction_intent_sync = _mock_classify_intent_sync  # type: ignore[assignment]
    client.answer_question_sync = _mock_answer_question_sync  # type: ignore[assignment]


async def run_replay(fixtures: list[Fixture], settings: AppSettings, *, max_cases: int | None = None, mock_llm: bool = False) -> None:
    service = DigitalTwinService(settings)
    if mock_llm:
        _install_mock_llm(service)
        print("[MOCK-LLM] classify_interaction_intent_sync + answer_question_sync patched")
    try:
        cases = fixtures if max_cases is None else fixtures[:max_cases]
        for n, fx in enumerate(cases, start=1):
            t0 = time.perf_counter()
            req = ChatRequest(
                student_name=fx.student_name,
                question=fx.question,
                course_context=fx.course_context,
                conversation_id=fx.conversation_id,
                deep_thinking=False,
            )
            try:
                resp = await service.answer_in_process(req)
                fx.answer_after = resp.answer
                fx.workflow_after = resp.workflow_action
                fx.kb_hits_after = len(resp.knowledge_hits)
            except Exception as exc:  # noqa: BLE001
                fx.error = f"{type(exc).__name__}: {exc}"
            fx.verdict = _classify_verdict(fx)
            dt = time.perf_counter() - t0
            print(
                f"[{n:>2}/{len(cases)}] {fx.student_name} #{fx.case_index} "
                f"verdict={fx.verdict:9s} wf:{fx.workflow_before}→{fx.workflow_after} "
                f"kb:{fx.kb_hits_before}→{fx.kb_hits_after} t={dt:.1f}s",
                flush=True,
            )
    finally:
        await service.aclose()


def write_report(fixtures: list[Fixture], path: Path) -> None:
    counts: dict[str, int] = {"improved": 0, "unchanged": 0, "regressed": 0, "error": 0}
    for fx in fixtures:
        counts[fx.verdict] = counts.get(fx.verdict, 0) + 1
    total = len(fixtures)
    out: list[str] = []
    out.append("# my-twin 回答效果不佳问题清单 — Replay 报告")
    out.append("")
    out.append(f"> Replayed at: {time.strftime('%Y-%m-%d %H:%M:%S')}  ")
    out.append(f"> Total cases: **{total}**  ")
    imp = counts.get("improved", 0)
    unc = counts.get("unchanged", 0)
    reg = counts.get("regressed", 0)
    err = counts.get("error", 0)
    out.append(f"> Improved: **{imp}** | Unchanged: **{unc}** | Regressed: **{reg}** | Error: **{err}**")
    out.append("")
    out.append("## TL;DR")
    out.append("")
    out.append(f"- 改善 {imp}/{total} 条 ({imp / total * 100 if total else 0:.0f}%)")
    out.append(f"- 仍待优化 {unc + reg + err}/{total} (unchanged + regressed + error)")
    out.append("")
    out.append("## 详细对照")
    out.append("")
    out.append("| # | 学生 | 课程 | wf BEFORE→AFTER | kb BEFORE→AFTER | verdict | 问题 (摘要) |")
    out.append("|---|------|------|------------------|------------------|---------|--------------|")
    for fx in fixtures:
        q_brief = fx.question.replace("\n", " ").replace("|", "\\|")
        if len(q_brief) > 60:
            q_brief = q_brief[:57] + "..."
        out.append(
            f"| {fx.global_index} | {fx.student_name} | {fx.course_context} | "
            f"{fx.workflow_before}→{fx.workflow_after} | {fx.kb_hits_before}→{fx.kb_hits_after} | "
            f"{fx.verdict} | {q_brief} |"
        )
    out.append("")
    out.append("## 完整答案 (前后对比)")
    out.append("")
    for fx in fixtures:
        out.append(f"### {fx.global_index}. {fx.student_name} — {fx.course_context} *(verdict: {fx.verdict})*")
        out.append("")
        out.append(f"**问题:** {fx.question}")
        out.append("")
        out.append(f"**BEFORE [{fx.workflow_before} / kb={fx.kb_hits_before}]:**")
        out.append("")
        out.append("> " + fx.answer_before.replace("\n", "\n> "))
        out.append("")
        out.append(f"**AFTER [{fx.workflow_after} / kb={fx.kb_hits_after}]:**")
        out.append("")
        if fx.error:
            out.append(f"> ERROR: {fx.error}")
        else:
            out.append("> " + (fx.answer_after or "(empty)").replace("\n", "\n> "))
        out.append("")
        out.append("---")
        out.append("")
    path.write_text("\n".join(out), encoding="utf-8")
    print(f"\nReport written to {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-cases", type=int, default=None,
                        help="Run only the first N cases (smoke test)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse fixtures only, no LLM call")
    parser.add_argument("--mock-llm", action="store_true",
                        help="Patch LLM client with deterministic stubs to verify guardrails without the live model")
    parser.add_argument("--out", type=Path, default=REPORT_DOC)
    parser.add_argument("--json-out", type=Path, default=None,
                        help="Optional JSON dump of all fixtures + replay results")
    args = parser.parse_args()

    fixtures = parse_fixtures(POOR_DOC)
    print(f"Parsed {len(fixtures)} fixtures from {POOR_DOC.name}")
    assign_conversation_ids(fixtures)
    if args.dry_run:
        for fx in fixtures:
            print(f"  [{fx.global_index:>2}] {fx.student_name:<6} #{fx.case_index:<2} "
                  f"wf={fx.workflow_before:<14} kb={fx.kb_hits_before} "
                  f"course={fx.course_context} | Q={fx.question[:60]!r}")
        return 0

    settings = AppSettings()
    asyncio.run(run_replay(fixtures, settings, max_cases=args.max_cases, mock_llm=args.mock_llm))
    write_report(fixtures, args.out)
    if args.json_out is not None:
        args.json_out.write_text(
            json.dumps([asdict(fx) for fx in fixtures], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"JSON dump: {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
