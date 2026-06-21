# Adopt cache-capturing miss path to eliminate double-forward penalty

_Source: coding plans from commit period 0272566 → 8dd53dd — records intent at planning time; the implementation may lag or differ._

**Status:** accepted

## Context
The sequential stream benchmark showed a negative end-to-end speedup (0.962x) because the miss-side cache fill (372.3ms) was significantly more expensive than the baseline (276.7ms). The root cause was identified as a 'double-forward' penalty: the miss path performed separate prefix and suffix prefills, incurring extra kernel launches, device synchronizations, and Python overhead compared to the baseline's single combined prefill.

## Decision drivers
- End-to-end latency performance
- Elimination of non-sub-additive prefill overhead
- Shifting the break-even point for caching viability

## Considered options
- **Cache-capturing miss path (full prompt prefill + capture)** — pros: Miss cost equals baseline cost (no double-forward penalty); preserves past_key_values for subsequent hits; simplifies the miss path logic.; cons: Requires refactoring the miss handler to capture state during the standard forward pass rather than building cache explicitly beforehand.
- **Separate prefix/suffix prefill with explicit cache build** _(rejected)_ — pros: Conceptually straightforward separation of concerns.; cons: Incurs ~35% overhead on misses due to separate kernel sequences and lack of batched attention across the boundary; makes end-to-end wins impossible unless hit rates are extremely high.

## Decision
Replace the two-step miss path (_prefix_cache + _reuse_ttft_ms) with a single full-prompt prefill that captures past_key_values (full_ttft_with_cache_capture). This ensures the miss penalty is no worse than the baseline, allowing the hit savings to drive positive aggregate speedup.

## Consequences
The miss path latency drops from ~372ms to ~277ms (baseline equivalent). This shifts the aggregate stream performance from negative (0.962x) to positive (~1.08x) under typical hit/miss ratios. The system now relies on the correctness of the cache capture mechanism during the standard forward pass.