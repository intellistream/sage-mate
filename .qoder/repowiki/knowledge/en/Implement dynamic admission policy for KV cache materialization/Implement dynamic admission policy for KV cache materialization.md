---
kind: design
name: Implement dynamic admission policy for KV cache materialization
source: session
category: adr
---

# Implement dynamic admission policy for KV cache materialization

_Source: coding plans from commit period 0272566 → 8dd53dd — records intent at planning time; the implementation may lag or differ._

**Status:** accepted

## Context
The existing static admission threshold (admission_baseline_floor_ms = 300.0) fails to account for varying workload characteristics, leading to suboptimal caching decisions. A static floor cannot distinguish between scenarios where caching is beneficial (long prefix, high hit probability) and those where it is wasteful (short prefix, low hit probability, or high device contention).

## Decision drivers
- Optimization of cache hit/miss trade-offs
- Adaptability to varying prefix/suffix ratios
- Responsiveness to device load conditions

## Considered options
- **Dynamic admission policy** — pros: Decides materialization based on prefix/suffix ratio, observed hit probability, and current device load; prevents caching when it is unlikely to pay off.; cons: Adds complexity to the admission logic; requires maintaining state for hit probability and load metrics.
- **Static admission threshold** _(rejected)_ — pros: Simple to implement and debug; no runtime overhead for decision making.; cons: Inflexible; leads to cache pollution or missed opportunities depending on the fixed value; currently results in poor end-to-end performance.

## Decision
Replace the static admission_baseline_floor_ms with a dynamic admission model in src/agent_kv_system/residency/admission.py. The new policy evaluates prefix length vs suffix length ratio, observed hit probability for the prefix class, and current device load before materializing cache entries.

## Consequences
The system will selectively cache only when the expected benefit outweighs the cost, improving overall efficiency. This requires new configuration parameters in src/agent_kv_system/config.py and adds a dependency on runtime metrics for load and hit rates.