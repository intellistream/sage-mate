---
kind: design
name: Optimize AgentKV miss-path via cache-capturing baseline
source: session
category: adr
---

# Optimize AgentKV miss-path via cache-capturing baseline

_Source: coding plans from commit period ed17f66 → 06bcc83 — records intent at planning time; the implementation may lag or differ._

**Status:** accepted

## Context
AgentKV's hit-conditioned TTFT showed gains (1.115x), but the end-to-end stream benchmark was negative (0.962x). The 'miss' path incurred a 372.3ms penalty compared to the 276.7ms baseline because it performed separate prefix and suffix prefill passes, losing kernel batching and incurring double device synchronization overhead.

## Decision drivers
- Eliminating the 'double-forward' penalty on cache misses
- Ensuring miss-cost equals baseline cost
- Shifting the break-even point for caching to favor end-to-end speedup

## Considered options
- **Separate prefix/suffix prefill on miss** _(rejected)_ — pros: Explicitly builds cache for future hits; cons: Non-sub-additive compute cost; two kernel launch sequences; 35% slower than baseline
- **Cache-capturing baseline (full prompt prefill)** — pros: Miss cost equals baseline cost; captures `past_key_values` for free during normal execution; cons: None identified; preserves hit savings without penalizing misses

## Decision
Replace the separate prefix/suffix prefill on a miss with a 'cache-capturing' baseline approach. On a miss, the system runs the full prompt normally (like the baseline) but captures the resulting `past_key_values`. This ensures the miss path is not slower than the baseline, allowing the hit savings to drive net positive speedup.

## Consequences
The stream benchmark is expected to turn positive (>1.0x). The paper narrative reframes around diagnosing and closing this 'reuse gap' via latency decomposition. A dynamic admission policy is also introduced to further optimize caching decisions based on prefix/suffix ratios.