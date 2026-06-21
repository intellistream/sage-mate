# Adopt rolling-maintenance workload for DeltaKV evaluation

_Source: coding plans from commit period ed17f66 → 06bcc83 — records intent at planning time; the implementation may lag or differ._

**Status:** accepted

## Context
Benchmarking DeltaKV on a same-GPU topology resulted in 4.2x worse latency due to resource contention, masking the benefits of delta transfer. The previous evaluation strategy (comparing against a sequential baseline on shared hardware) was invalid for measuring transfer efficiency.

## Decision drivers
- Eliminating GPU compute contention
- Creating a scenario where external transfer is mandatory
- Measuring continuity disruption time rather than raw throughput

## Considered options
- **Same-GPU two-server topology** _(rejected)_ — pros: Simple single-host setup; cons: Severe GPU memory and compute contention (TPOT 3.4x slower); invalidates performance comparison
- **Multi-GPU isolated topology with rolling-maintenance scenario** — pros: Eliminates contention; forces external transfer by handing off mid-generation; measures real-world continuity benefits; cons: Requires multi-GPU hardware; more complex benchmark harness

## Decision
Shift evaluation to a multi-GPU topology using a 'rolling-maintenance' workload. In this scenario, Instance A hands off a long-running request to Instance B mid-generation. This isolates the transfer mechanism from GPU contention and measures 'continuity disruption time' (DeltaKV vs. full restart) as the primary metric.

## Consequences
The same-GPU comparison is demoted to a 'degraded mode' appendix. The primary ASPLOS 2027 paper narrative shifts from protocol correctness to application-driven session continuity. New benchmark modes (`--scenario rolling-maintenance`) and checkpoint intervals are required in `online_benchmark.py`.