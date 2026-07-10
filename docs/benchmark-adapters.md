# Benchmark Adapters

This repository now includes a runnable adapter draft for two external benchmark formats:

- CharacterEval-compatible generation export
- LaMP-compatible prediction export

It also now includes a repo-local memory-sensitive benchmark family:

- multi-turn memory follow-up evaluation

A repo-local faculty-specific CharacterEval-style subset is available at [tests/data/charactereval_faculty_subset.json](tests/data/charactereval_faculty_subset.json).
It now contains 24 scenarios and a per-scenario heuristic rubric scaffold.

The implementation lives in [src/sage_faculty_twin/benchmark_adapter.py](src/sage_faculty_twin/benchmark_adapter.py).

## Why an adapter draft

Neither external benchmark maps perfectly to the faculty twin out of the box:

- CharacterEval evaluates arbitrary role-playing agents across many fictional characters.
- LaMP evaluates generic personalized language tasks such as classification and generation from user profiles.

The faculty twin is narrower: one persistent academic persona, grounded knowledge, and advising or teaching workflows. So the adapter should be treated as an integration layer and experiment harness, not as a claim that the official public leaderboard numbers are directly comparable.

One additional caveat matters for this repository: the CharacterEval and LaMP adapter requests deliberately use benchmark-only `course_context` labels, and those labels skip conversation-memory retrieval and persistence inside the main service so benchmark runs do not contaminate normal chats. That means they are useful for overall answer-quality regressions, but they are not the right instrument for measuring whether NeuroMem-backed multi-turn memory actually helped.

For live benchmark runs against a real local model server, long responses can still hit the HTTP client timeout. The app now supports bounded retry/backoff at the LLM client layer via:

- `DIGITAL_TWIN_LLM_TIMEOUT_SECONDS`
- `DIGITAL_TWIN_LLM_RETRY_ATTEMPTS`
- `DIGITAL_TWIN_LLM_RETRY_BACKOFF_SECONDS`

Example for a more fault-tolerant local eval run:

```bash
export DIGITAL_TWIN_LLM_TIMEOUT_SECONDS=120
export DIGITAL_TWIN_LLM_RETRY_ATTEMPTS=2
export DIGITAL_TWIN_LLM_RETRY_BACKOFF_SECONDS=1
```

The benchmark generation commands themselves now execute the same chat workflow stages in-process instead of paying the per-turn FlowNet compile/submit overhead. That keeps the evaluation semantics aligned with the app workflow while making local benchmark runs materially cheaper. These commands are therefore suited for answer-quality and memory-quality evaluation, not for measuring production runtime overhead.

## CharacterEval

Official CharacterEval generation uses records with fields such as:

- `id`
- `role`
- `context`

and expects a `results/generation.jsonl`-style JSON list with:

- `id`
- `role`
- `context`
- `model_output`

The adapter preserves that output shape.

Run it with:

```bash
PYTHONPATH=/home/shuhao/sage-mate/src:/home/shuhao/SAGE/src:/home/shuhao/sageVDB:/home/shuhao/neuromem \
python -m sage_faculty_twin.benchmark_adapter charactereval \
  --input /path/to/test_data.jsonl \
  --output /path/to/results/generation.jsonl
```

Recommended use in this repo:

- build a faculty-specific CharacterEval-style subset
- keep the official field names
- replace arbitrary fictional role cards with a faculty twin persona card
- score multi-turn persona drift, style consistency, and character fidelity

You can run the local faculty subset directly:

```bash
PYTHONPATH=/home/shuhao/sage-mate/src:/home/shuhao/SAGE/src:/home/shuhao/sageVDB:/home/shuhao/neuromem \
python -m sage_faculty_twin.benchmark_adapter charactereval \
  --input /home/shuhao/sage-mate/tests/data/charactereval_faculty_subset.json \
  --output /tmp/charactereval-faculty-results.json
```

The local subset currently covers:

- faculty self-introduction grounding
- meeting-preparation guidance
- paper-writing course teacher voice
- research direction grounding
- lab joining expectations
- meeting policy boundaries
- publication reading guidance
- multi-turn persona consistency in light follow-up turns
- course logistics and admin boundaries
- research versus teaching disambiguation
- draft-feedback preparation
- reading-plan guidance
- collaborator-facing scope framing
- availability and non-fabrication checks
- memory and follow-up continuity

## Faculty Rubric Scaffold

The local faculty subset now includes a heuristic rubric block on every scenario. Each rubric can define:

- `must_include_all`
- `must_include_any`
- `must_not_include`
- `preferred_keywords`
- `min_chars`
- `max_chars`
- `pass_threshold`

This is intentionally a scaffold rather than a final judge. It is useful for:

- batch regression after prompt or retrieval changes
- catching obvious persona drift or boundary failures
- highlighting which scenarios still need manual review

It is not sufficient for final quality judgment on its own, because semantic equivalence and nuanced phrasing can still evade keyword-based checks.

You can score a generated CharacterEval prediction file with:

```bash
PYTHONPATH=/home/shuhao/sage-mate/src:/home/shuhao/SAGE/src:/home/shuhao/sageVDB:/home/shuhao/neuromem \
python -m sage_faculty_twin.benchmark_adapter score-charactereval-faculty \
  --scenarios /home/shuhao/sage-mate/tests/data/charactereval_faculty_subset.json \
  --predictions /tmp/charactereval-faculty-results.json \
  --output /tmp/charactereval-faculty-score-report.json
```

The generated JSON report includes:

- scenario-level pass/fail
- total score per scenario
- missing required keywords
- forbidden hits
- average score and pass rate
- average score by focus area

## LaMP

Official LaMP question files are either:

- a plain JSON list of items with fields such as `id`, `input`, `profile`, and sometimes `output`
- or a top-level envelope with `task` and `golds`

The official evaluation expects a prediction file shaped like:

```json
{
  "task": "LaMP_6",
  "golds": [
    {"id": "sample-1", "output": "..."}
  ]
}
```

The adapter writes exactly that shape.

Run it with:

```bash
PYTHONPATH=/home/shuhao/sage-mate/src:/home/shuhao/SAGE/src:/home/shuhao/sageVDB:/home/shuhao/neuromem \
python -m sage_faculty_twin.benchmark_adapter lamp \
  --questions /path/to/dev_questions.json \
  --task-name LaMP-6 \
  --output /path/to/preds.json
```

Recommended use in this repo:

- focus first on LaMP-style profile retrieval stress tests
- use the `profile` field to pressure-test memory ranking and personalization prompts
- do not treat all seven official LaMP tasks as equally meaningful for the faculty twin
- start with generation-style tasks where profile-grounded free-form output is still sensible

A repo-local LaMP-style personalization subset is available at [tests/data/lamp_personalization_subset.json](tests/data/lamp_personalization_subset.json).
It currently contains 16 scenarios for profile-grounded recommendation and next-step guidance.

You can run the local subset directly:

```bash
PYTHONPATH=/home/shuhao/sage-mate/src:/home/shuhao/SAGE/src:/home/shuhao/sageVDB:/home/shuhao/neuromem \
python -m sage_faculty_twin.benchmark_adapter lamp \
  --questions /home/shuhao/sage-mate/tests/data/lamp_personalization_subset.json \
  --task-name LaMP-Local \
  --output /tmp/lamp-local-results.json
```

The local subset currently covers:

- student onboarding under time constraints
- paper-writing support with deadline pressure
- lab-member update formatting
- limited-time reading plans
- career path advice from user-specific goals
- draft-feedback preparation
- course-question structuring
- publication topic entry points
- project-fit preparation
- project scope narrowing
- email-vs-meeting choice
- abstract compression priorities
- collaboration pre-discussion framing
- cold-start reading plans
- course-question and research disambiguation
- memory-conditioned next-step suggestions

## Local LaMP Rubric Scaffold

The local LaMP subset uses a profile-aware heuristic rubric. Each scenario can define:

- `must_include_all`
- `must_include_any`
- `must_not_include`
- `preferred_keywords`
- `profile_grounding_terms`
- `min_chars`
- `max_chars`
- `pass_threshold`

This scaffold is meant to catch obvious personalization failures such as:

- ignoring key profile facts
- answering with generic advice that could fit anyone
- drifting into unrelated topics
- fabricating next steps that conflict with the profile

You can score a generated local LaMP prediction file with:

```bash
PYTHONPATH=/home/shuhao/sage-mate/src:/home/shuhao/SAGE/src:/home/shuhao/sageVDB:/home/shuhao/neuromem \
python -m sage_faculty_twin.benchmark_adapter score-lamp-local \
  --scenarios /home/shuhao/sage-mate/tests/data/lamp_personalization_subset.json \
  --predictions /tmp/lamp-local-results.json \
  --output /tmp/lamp-local-score-report.json
```

The generated report includes:

- scenario-level pass/fail
- score by scenario
- profile-grounding hits and misses
- forbidden-topic hits
- average score and pass rate
- average score by focus area

## Memory Follow-Up Benchmark

To measure whether the faculty twin is actually reusing NeuroMem-backed conversation and profile memory, this repo now includes a dedicated local benchmark family at [tests/data/memory_followup_subset.json](tests/data/memory_followup_subset.json).

Unlike CharacterEval and LaMP adapter requests, these scenarios intentionally run through the normal application path:

- shared `conversation_id` across seed turns and evaluation turns
- normal advising or teaching `course_context`
- memory retrieval remains enabled
- response scoring checks both answer content and memory-audit fields

Each scenario contains:

- one or more `seed_turns`
- one `evaluation_turn`
- a rubric that can require:
  - answer keywords
  - memory-grounding terms
  - specific retrieved memory types such as `short_term` or `long_term`
  - minimum retrieved item count
  - `memory_used == true`

Run the local memory benchmark directly:

```bash
PYTHONPATH=/home/shuhao/sage-mate/src:/home/shuhao/SAGE/src:/home/shuhao/sageVDB:/home/shuhao/neuromem \
python -m sage_faculty_twin.benchmark_adapter memory-followup \
  --scenarios /home/shuhao/sage-mate/tests/data/memory_followup_subset.json \
  --output /tmp/memory-followup-results.json
```

Then score it with:

```bash
PYTHONPATH=/home/shuhao/sage-mate/src:/home/shuhao/SAGE/src:/home/shuhao/sageVDB:/home/shuhao/neuromem \
python -m sage_faculty_twin.benchmark_adapter score-memory-followup \
  --scenarios /home/shuhao/sage-mate/tests/data/memory_followup_subset.json \
  --predictions /tmp/memory-followup-results.json \
  --output /tmp/memory-followup-score-report.json
```

The raw prediction export now also includes a diagnostics block for debugging slow or unstable runs:

- `scenario_duration_ms` across seed turns plus the evaluation turn
- `evaluation_diagnostics.workflow_duration_ms`
- `evaluation_diagnostics.llm_answer_duration_ms`
- per-step `step_durations_ms` and `step_statuses`
- `seed_turn_diagnostics` for each warm-up turn in the scenario

The generated report includes:

- scenario-level pass/fail
- score by scenario
- whether `memory_used` was true
- retrieved memory-type coverage
- retrieved item counts
- memory-grounding hits and misses in the final answer
- average score and pass rate
- average score by focus area

## Unified Summary

Once you have both local score reports, you can merge them into one repo-level benchmark summary:

```bash
PYTHONPATH=/home/shuhao/sage-mate/src:/home/shuhao/SAGE/src:/home/shuhao/sageVDB:/home/shuhao/neuromem \
python -m sage_faculty_twin.benchmark_adapter summarize-local-benchmarks \
  --charactereval-report /tmp/charactereval-faculty-score-report.json \
  --lamp-report /tmp/lamp-local-score-report.json \
  --memory-report /tmp/memory-followup-score-report.json \
  --output /tmp/local-benchmark-summary.json \
  --lowest-k 8
```

The unified summary report includes:

- weighted overall average score
- weighted overall pass rate
- per-benchmark failure counts
- per-benchmark focus averages
- weakest scenarios across both benchmark families

This is the intended one-shot artifact for regression tracking after prompt, retrieval, or routing changes.

## Suggested rollout

1. CharacterEval-inspired local subset for persona drift and role consistency.
2. LaMP-inspired local subset for profile retrieval and memory-conditioned generation.
3. Use the memory follow-up benchmark when the change target is NeuroMem retrieval, profile consolidation, or multi-turn continuity.
4. Keep public benchmark adapters separate from the repo's own identity and workflow eval suites.

## Validation

The adapter draft is covered by:

```bash
PYTHONPATH=/home/shuhao/sage-mate/src:/home/shuhao/SAGE/src:/home/shuhao/sageVDB:/home/shuhao/neuromem \
pytest tests/test_benchmark_adapter.py -v
```