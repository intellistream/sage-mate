# Segment-Reuse Exploration for Sage Faculty Twin

## Current Prompt Anatomy

The current `/chat` prompt is effectively **B|E** for the reusable parts that
matter to native prefix caching:

```text
System message:
  Response instructions
  Reusable retrieved materials (materialization scope: ...)
  Request context
    Student name
    Visitor profile
    Intent/profile/fast-answer guidance
    Availability, attachments, recent session, memory
    Residual retrieved knowledge and web context
    Question

User message:
  dynamic user prompt
```

`Response instructions` and the materializable KB excerpts are stable body-like
content. They appear before dynamic request-specific envelope fields such as
student name, visitor profile, recent session, memory, residual knowledge, and
the question. This means native prefix cache can already reuse a large fraction
of the stable prefix when the tokenized prefix is identical for enough blocks.

Segment stitch is expected to help most when business semantics require **E|B**:

```text
Dynamic envelope first
Stable reusable body later
```

In that order, native prefix cache cannot skip the body prefill because the
prefix differs before the stable body starts. Segment-reuse needs the serving
engine adapter to resolve the body span after tokenization, look up body KV,
and stitch/borrow the pinned body blocks.

## What Is Proven Today

Twin currently sends segment-reuse `extra_key` metadata when enabled. That is
only a control-plane hint. It is **not** proof of segment stitch.

The current online evidence shows:

- native vLLM prefix cache metrics increase for B|E-style stable prefixes;
- service-layer semantic/knowledge caches can make repeated `/chat` calls much
  faster and may hide model-side effects;
- current vLLM-HUST metrics do not expose segment-specific counters such as
  `segment_stitch_committed` or `segment_reused_body_tokens`.

Therefore, current twin-side measurements should be interpreted as:

```text
extra_key accepted != exact boundary resolved != stitch committed
```

## Request Classes

| Request shape | Better mechanism | Why |
| --- | --- | --- |
| Stable persona/skills/public KB first, dynamic question later | Native prefix cache | The stable body is already prefix-aligned. |
| Repeated exact or near-exact `/chat` question | Service cache + native prefix cache | App cache may dominate and hide model-side gains. |
| Dynamic routing/envelope first, long stable body later | Segment stitch | Native prefix cache cannot reuse a non-prefix body. |
| Long shared tool/skill/RAG body with per-user private envelope before it | Segment stitch with scope isolation | Reuse body KV while recomputing fresh envelope. |
| Private/admin/student-record material | Neither shared native body nor cross-user stitch | Must remain outside shared reusable body. |

## Minimal Experiment Script

Use:

```bash
source tools/lib/runtime_env.sh
export_repo_runtime_env "$PWD"
"$PYTHON_BIN" tools/segment_reuse_experiment.py \
  --body-tokens 512,2048,8192 \
  --envelope-tokens 32,128,512 \
  --concurrency 1,4,16 \
  --repeated-modes cold,hot,mixed \
  --workloads policy_first,task_first,agent_state_first \
  --requests-per-trial 4 \
  --output-json /tmp/segment-reuse-report.json \
  --output-csv /tmp/segment-reuse-report.csv
```

For quick smoke:

```bash
"$PYTHON_BIN" tools/segment_reuse_experiment.py \
  --body-tokens 512 \
  --envelope-tokens 32 \
  --concurrency 1 \
  --repeated-modes cold,hot \
  --workloads policy_first \
  --requests-per-trial 2
```

The script sends three direct OpenAI-compatible variants:

| Variant | Prompt order | Metadata |
| --- | --- | --- |
| `baseline_e_b` | E|B | no `cache_salt`, no `extra_key` |
| `native_b_e` | B|E | `cache_salt` |
| `segment_hint_e_b` | E|B | body markers + `extra_key` |

It also includes three E|B workload families:

| Workload | Dynamic envelope | Stable body |
| --- | --- | --- |
| `policy_first` | current visitor profile, permission scope, audit id, redaction rule | shared public lab handbook |
| `task_first` | this request's objective, output format, evaluation axis | shared KV/prefix/segment-reuse technical corpus |
| `agent_state_first` | current planner step, tool results, pending constraints | shared tool/skill manual |

It bypasses `/chat`, so service semantic/knowledge caches are not part of the
model-side comparison. Use `tools/smoke_segment_reuse_perf.py` separately to
measure the full app path where service cache is enabled.

## Result Table Template

| Variant | Workload | Body | Envelope | Concurrency | Mode | Median E2E | Prefix hit tokens/blocks | Stitch committed | Reused body tokens | Interpretation |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | --- |
| baseline_e_b | policy_first | 512 | 32 | 1 | cold | TBD | expected low | requires engine metric | requires engine metric | Full prefill baseline |
| native_b_e | policy_first | 512 | 32 | 1 | hot | TBD | expected high | 0/absent | 0/absent | Native prefix benefit |
| segment_hint_e_b | policy_first | 512 | 32 | 1 | hot | TBD | may be low | must be >0 to claim stitch | must be >0 to claim stitch | Control hint unless engine consumes it |

## Initial Online Observations

These quick probes bypassed `/chat` and used the direct OpenAI-compatible
endpoint with `repeated_mode=cold`, so the dynamic envelope changed between
requests.

| Variant | Workload | Body target | Prefix hit rate | Native cached tokens | Segment committed | Reused body tokens | Interpretation |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `baseline_e_b` | `policy_first` | 512 | 0.000 | 0 | 0 | 0 | Dynamic E prefix prevents native prefix reuse. |
| `native_b_e` | `policy_first` | 512 | 0.835 | 5376 | 0 | 0 | B|E exposes body to native prefix cache. |
| `segment_hint_e_b` | `policy_first` | 512 | 0.000 | 0 | 0 | 0 | `extra_key` alone does not trigger stitch. |
| `baseline_e_b` | `policy_first` | 2048 | 0.000 | 0 | 0 | 0 | Long body still recomputed when behind dynamic E. |
| `native_b_e` | `policy_first` | 2048 | 0.485 | 7680 | 0 | 0 | Native cache helps only after moving body to prefix. |
| `segment_hint_e_b` | `policy_first` | 2048 | 0.000 | 0 | 0 | 0 | No engine-side stitch metrics observed. |

This confirms that the workload shape we need does exist: dynamic envelope
first, reusable body later. It also confirms that the current serving stack is
not yet reporting segment stitch consumption. If the engine adapter later
implements stitch, the `segment_hint_e_b` rows are where
`segment_stitch_committed` and `segment_reused_body_tokens` should become
nonzero.

## Engine Adapter Hooks Needed

The serving engine adapter should expose these stages and metrics separately:

- `segment_reuse_extra_key_seen_total`
- `segment_reuse_extra_key_decoded_total`
- `segment_reuse_boundary_resolved_total`
- `segment_reuse_boundary_resolve_failed_total{reason=...}`
- `segment_reuse_registry_lookup_total`
- `segment_reuse_registry_hit_total`
- `segment_reuse_stitch_plan_ready_total`
- `segment_reuse_stitch_committed_total`
- `segment_reuse_reused_body_tokens_total`
- `segment_reuse_fresh_envelope_tokens_total`
- `segment_reuse_tokens_recomputed_total`
- `segment_reuse_pinned_body_blocks`
- `segment_reuse_hbm_bytes_pinned`
- `segment_reuse_demotion_total{reason=...}`

Demotion reasons should include at least:

- `extra_key_missing`
- `extra_key_invalid`
- `boundary_marker_missing`
- `boundary_token_mismatch`
- `body_digest_mismatch`
- `scope_mismatch`
- `registry_miss`
- `body_too_short`
- `capacity_or_eviction`
- `attention_contract_unsupported`
- `position_id_or_mask_unsafe`

## Boundary Ownership

Twin should not authorize stitch with an approximate `tokens=<max>` value. The
adapter must compute exact body boundaries after the same tokenizer and chat
template used by the serving engine. Twin can help by adding stable body markers
and body digest metadata, but the adapter should be the source of truth for:

- tokenized marker positions;
- exact `leading_tokens`;
- body token-id hash;
- chat template hash;
- model/tokenizer revision;
- scope and permission partition.

## Current Answer

The current measured benefit is very likely dominated by B|E native prefix cache
and service-layer caches. Segment stitch should become visible only when all of
these are true:

1. the prompt shape is E|B;
2. service cache is bypassed or reported separately;
3. the engine adapter consumes `extra_key`;
4. exact body boundaries are resolved after tokenization;
5. `stitch_committed` and `reused_body_tokens` are nonzero.
