# Qwen3-32B vLLM-HUST Performance Tuning Log

> **Date**: 2026-06-05  
> **Platform**: train05 — 8× Ascend 910B3 (64 GB HBM each), CANN 9.0  
> **Model**: Qwen3-32B (FP16/BF16), served via vllm-hust 0.17.2 + vllm-ascend plugin  
> **Service**: `sage-faculty-twin-vllm-qwen3-32b.service` (systemd unit)  
> **Container**: Docker `4843b7f5` running on host, vllm-hust-dev env inside

---

## TL;DR

| Metric | Baseline | After P0+P2 (config-only) | After P3 (fused kernel) | Total Change |
|--------|----------|---------------------------|-------------------------|--------------|
| TTFT (short prompt) | 162 ms | 166 ms | 150 ms | -7% |
| TPOT (per token) | 33.6 ms | 33.7 ms | **32.0 ms** | **-5%** |
| Throughput (single user) | ~28 tok/s | ~28 tok/s | **~30.5 tok/s** | **+9%** |

**Verdict**: After installing `triton-ascend` + `pybind11` and patching the rejection sampler API, the
fused `qkv_rmsnorm_rope` kernel was unlocked, giving a real ~5% per-token latency improvement.
Ngram speculative decoding was also unlocked but is a **3x regression** on Ascend 910B3 — the
verification forward pass is far more expensive than sequential single-token decode under the
current NPU graph capture set. Draft-model speculation remains broken (separate AscendDraftModelProposer bug).

**Production config**: fused kernel ON, no speculative decoding.

---

## 1. Baseline Configuration

```bash
# Original launch (before tuning)
ASCEND_RT_VISIBLE_DEVICES=2,5   # Cross-NUMA (0000:81 + 0000:02)
--tensor-parallel-size 2
--max-model-len 32768
--gpu-memory-utilization 0.85
--compilation-config '{"cudagraph_mode":"FULL_DECODE_ONLY","cudagraph_capture_sizes":[1,2,4,8]}'
--additional-config '{"ascend_compilation_config":{"fuse_qknorm_rope":false}}'
```

**Baseline numbers** (5 runs, 2 warmup, `enable_thinking=false`):
- Short prompt (math): TTFT=162ms, TPOT=33.6ms, 27.6 tok/s
- Mid prompt (thesis review): TTFT=136ms, TPOT=33.6ms, 29.1 tok/s

---

## 2. Applied Optimizations (P0 + P2)

### P0b: TP NUMA pairing — cards (2,5) → (4,5)

- **Rationale**: Cards 4 (0000:01) and 5 (0000:02) are on the same PCI socket
- **Result**: No measurable difference. Ascend 910B3 inter-NPU communication uses **HCCS mesh** (not PCIe), so all chip pairs have uniform bandwidth regardless of host PCI topology.
- **Kept**: Yes (still slightly better for host-side DMA coherence)

### P0c: max-model-len 32768 → 8192

- **Rationale**: my-twin conversations never exceed ~4K tokens. Reducing frees KV cache budget.
- **Result**: No single-user latency change (expected — only affects max concurrency)
- **Kept**: Yes

### P0d: gpu-memory-utilization 0.85 → 0.92

- **Rationale**: More memory for KV cache, allows more concurrent sequences
- **Result**: No single-user latency change
- **Kept**: Yes

### P2a: `--enable-chunked-prefill --max-num-batched-tokens 2048`

- **Rationale**: Prevents long prefills from blocking short decode steps under concurrency
- **Result**: No single-user improvement; will matter under load
- **Kept**: Yes

### P2b: cudagraph_capture_sizes [1,2,4,8] → [1,2,4,8,16,32]

- **Rationale**: Pre-captures NPU graphs for larger batch sizes
- **Result**: No single-user improvement; amortizes overhead at higher concurrency
- **Kept**: Yes

### P2c: `PYTORCH_NPU_ALLOC_CONF=expandable_segments:True`

- **Rationale**: Reduces memory fragmentation, fewer re-allocations
- **Result**: No measurable latency change, improves stability
- **Kept**: Yes

---

## 3. Failed Experiments

### P2d: Remove `fuse_qknorm_rope: false` workaround

```
AttributeError: '_OpNamespace' 'vllm' object has no attribute 'qkv_rmsnorm_rope'
[ERROR] ERR03005 GRAPH internal error
```

**Root cause**: The fused `qkv_rmsnorm_rope` custom op is NOT registered in this vllm-ascend build.
The workaround (`fuse_qknorm_rope: false`) disables the fused path and uses separate RMSNorm + RoPE.
**Status**: Must keep workaround until vllm-ascend-hust implements the custom op.

### P1a: Speculative Decoding — Draft Model (Qwen3-1.7B)

```bash
--speculative-config '{"method":"draft_model","model":"/data/shared-models/Qwen3-1.7B","num_speculative_tokens":3}'
```

```
RuntimeError: 'AscendDraftModelProposer' object has no attribute 'update_stream'
```

**Root cause**: vllm-ascend's `AscendDraftModelProposer` class doesn't fully implement the draft model proposer interface.
**Status**: Blocked — requires vllm-ascend-hust code fix.

### P1a (alt): Speculative Decoding — Ngram

```bash
--speculative-config '{"method":"ngram","num_speculative_tokens":4,"prompt_lookup_max":5}'
```

- Service starts and compiles graphs successfully
- First inference request → `EngineDeadError` (engine core crash)
- **Root cause**: Speculative decoding verification loop likely hits an unimplemented NPU graph path
- **Status**: Blocked — fundamental Ascend backend limitation.

### P1a (note): Native MTP

- Qwen3-32B config: `num_nextn_predict_layers: null` → model does NOT include MTP prediction heads
- Would need `Qwen3-32B-MTP` variant (not available)
- **Status**: N/A for this model checkpoint.

### P1b: W8A8 Quantization

- No pre-quantized Qwen3-32B-W8A8 model available on disk
- Requires calibration with representative data + conversion (e.g., via `llm-compressor` or `autogptq`)
- Would theoretically halve TPOT (~17 ms/tok) by halving memory bandwidth requirement
- **Status**: Deferred — requires model preparation effort.

---

## 4. Analysis: Why 33.7 ms/tok is the Floor

The decode step for a large language model is **memory-bandwidth-bound** (reading weights once per token):

- 2× Ascend 910B3 HBM bandwidth: ~2 × 1.1 TB/s = 2.2 TB/s theoretical peak
- Qwen3-32B BF16 weights: ~64 GB total (32 GB per card with TP=2)
- Minimum decode time = 64 GB ÷ 2.2 TB/s ≈ **29 ms** (theoretical)
- Measured: 33.7 ms → **~86% bandwidth utilization** (excellent!)

The 14% gap accounts for:
- KV cache reads (~2-3 ms at sequence lengths < 1K)
- HCCS all-reduce communication (~1 ms for TP=2)
- Kernel launch overhead + graph dispatch (~0.5 ms)

**Conclusion**: This deployment is already near-optimal for FP16/BF16 on this hardware.

---

## 5. Remaining Options for TPOT Reduction

| Option | Expected TPOT | Effort | Blocked? |
|--------|:------------:|--------|----------|
| W8A8 quantization | ~17 ms | Medium (calibrate + convert model) | No, but needs prep |
| TP=4 (4 cards) | ~17 ms | Low (config change) | No, but uses 2 extra cards |
| Speculative decoding | ~20 ms effective | Low (config) | **Yes** — unlocked, but 3x slower (no graph coverage for verification) |
| MTP native | ~22 ms effective | Low (need MTP model) | **Yes** — no MTP weights |
| Fused QKNorm+RoPE | ~31 ms | None | **DONE — ~32 ms achieved** |

---

## 6. Final Configuration (Production)

```bash
#!/usr/bin/env bash
set -euo pipefail

exec sudo -n docker exec -i <container> /bin/bash -lc "
  export ASCEND_RT_VISIBLE_DEVICES=4,5
  export ASCEND_VISIBLE_DEVICES=4,5
  export HCCL_OP_EXPANSION_MODE=AIV
  export PYTORCH_NPU_ALLOC_CONF=expandable_segments:True
  ...
  exec vllm-hust serve /data/shared-models/Qwen3-32B \
    --served-model-name Qwen3-32B \
    --host 0.0.0.0 --port 18000 \
    --tensor-parallel-size 2 \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.92 \
    --enable-chunked-prefill \
    --max-num-batched-tokens 2048 \
    --additional-config '{\"ascend_compilation_config\":{}}' \
    --compilation-config '{\"cudagraph_mode\":\"FULL_DECODE_ONLY\",\"cudagraph_capture_sizes\":[1,2,4,8,16,32]}'
"
```

**Performance characteristics** (post P3 fused kernel):
- TTFT: ~120-150 ms (depends on prompt length)
- TPOT: **~32.0 ms/token** (was 33.7 ms before fused kernel)
- Throughput (single user): **~30.5 tok/s** (was ~28 tok/s)
- Max context: 8192 tokens
- Startup time: ~3 min (weight load + NPU graph + triton kernel JIT)

---

## P3: Unblocking the Fused `qkv_rmsnorm_rope` Kernel (2026-06-05)

### Root cause investigation

The original config carried `fuse_qknorm_rope: false` because the fused op crashed at graph
compile time with:

```
AttributeError: '_OpNamespace' 'vllm' object has no attribute 'qkv_rmsnorm_rope'
```

Deep dive revealed **two missing dependencies** in the container env:

1. **`triton-ascend` was not installed.** The fused op is implemented as a Triton kernel in
   `vllm_ascend/ops/triton/linearnorm/split_qkv_rmsnorm_rope.py`. Registration is gated by
   `HAS_TRITON` in `vllm_ascend/ops/__init__.py:29`. Without `triton-ascend`,
   `from vllm.triton_utils import HAS_TRITON` returned `False` and the op was never registered.
2. **`pybind11` was not installed.** Even after installing `triton-ascend`, `triton.backends`
   import failed with `ModuleNotFoundError: No module named 'pybind11'` (the `triton.backends.ascend.utils`
   submodule needs pybind11). This made `HAS_TRITON` still evaluate to `False`.

### Fix

```bash
pip install 'triton-ascend>=3.2.0' pybind11
```

The dev-hub `quickstart.sh` already reads `triton-ascend==3.2.0` from `vllm-ascend-hust/pyproject.toml`
and installs it (see `scripts/quickstart.sh:463-464`), so new environments get this automatically.
Only long-running containers from before that change need the manual install.

### Bonus: rejection_sampler API mismatch (vllm-hust 0.17.2 vs vllm-ascend plugin)

While validating speculative decoding, hit a second bug:

```
RuntimeError: Worker failed with error 'rejection_sample() got an unexpected keyword argument 'synthetic_mode''
```

The vllm-hust core's `RejectionSampler.forward` (line 177 of `vllm/v1/sample/rejection_sampler.py`)
calls `rejection_sample(synthetic_mode=...)`, but the ascend plugin's monkey-patch
(`vllm_ascend/sample/rejection_sampler.py:82`) replaced it with an older signature lacking those args.

**Fix** (committed locally to `vllm-ascend-hust/vllm_ascend/sample/rejection_sampler.py`):
```python
def rejection_sample(
    ...
    sampling_metadata: SamplingMetadata,
    synthetic_mode: bool = False,                        # <- added
    synthetic_conditional_rates: torch.Tensor | None = None,  # <- added
) -> torch.Tensor:
```

These parameters are accepted but ignored — the ascend kernel path doesn't use them.

### Speculative decoding outcome on Ascend 910B3

With all fixes in place we successfully launched ngram speculative decoding
(`--speculative-config '{"method":"ngram","num_speculative_tokens":4,"prompt_lookup_max":5}'`).
Benchmarks showed:

| Config | TPOT | Throughput |
|--------|------|------------|
| No spec decode (production) | 32.0 ms | 30.5 tok/s |
| Ngram, n=4, prompt_lookup_max=5 | **106 ms** | **9.3 tok/s** |

Ngram speculation is a **~3x regression** on this hardware. Reason: the verification forward pass
with multiple speculated tokens hits a path that isn't covered by the captured NPU graphs
(graph capture sizes `[1,2,4,8,16,32]` are all single-token decode shapes), so each verification
falls back to eager mode. Until graph capture is extended to cover variable-length
decode batches with `num_speculative_tokens>1`, speculation is not usable for single-user latency.

Draft-model speculation (`method="draft_model"`) remains broken with
`AscendDraftModelProposer object has no attribute 'update_stream'` — a separate bug in the
ascend-side proposer initialization. Not pursued further since ngram already showed speculation
is disadvantageous on this hardware.

See section 6 above for the final production launch config.
