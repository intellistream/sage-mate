# vLLM-HUST on macOS

This note records what is needed to compile and run `deps/vllm-hust` locally on
macOS, and what would be required to use Apple GPU acceleration.

## Current State

`vllm-hust` already has a macOS CPU path:

- `setup.py` forces `VLLM_TARGET_DEVICE=cpu` on Darwin when any other target is
  requested.
- Platform detection maps macOS to `CpuPlatform`.
- CMake only forwards non-CUDA/non-ROCm builds to `cmake/cpu_extension.cmake`
  when the target is exactly `cpu`; any other target returns without building a
  device extension.
- The CPU platform selects `CPU_ATTN` and `CPUWorker`, and the CPU attention
  backend calls CPU custom ops for KV cache update and attention.

So macOS can be a local vLLM-HUST runtime today, but only as a CPU runtime. It is
useful for local-only correctness and small models, not for high-throughput
assistant serving.

## Product Path

The package/install path now uses `vllm-metal-hust` for Apple GPU acceleration:

1. Keep Sage Mate local-first by default:
   - `DIGITAL_TWIN_LLM_BASE_URL=http://127.0.0.1:8000/v1`
   - `DIGITAL_TWIN_API_KEY=EMPTY`
   - no automatic hosted vLLM-HUST URL unless the user explicitly saves or
     provides one.
2. Bundle the `vLLM-HUST/vllm-metal-hust` fork as `deps/vllm-metal-hust` and as
   a macOS app resource.
3. Install the Apple GPU runtime from that bundled source into
   `~/Library/Application Support/Sage Mate/vllm-metal-hust`.
4. Install the vLLM core from pinned local `deps/vllm-hust`, not from the
   official upstream vLLM release.
5. Launch the local OpenAI-compatible endpoint with
   `tools/run_vllm_metal_engine.sh`.

This satisfies "everything local" without implying Apple GPU support is already
part of the CUDA/CPU `vllm-hust` fork.

## Apple GPU/MPS Port

Using the Apple GPU is not a packaging toggle. It needs a real platform port.
There are two possible directions:

1. Integrate the existing `vllm-metal` plugin model.
2. Build a direct PyTorch MPS backend inside `vllm-hust`.

The first direction is much more practical.

## Existing Apple Plugin

The vLLM ecosystem now has `vllm-metal`, a hardware plugin for Apple Silicon. Our
fork is `https://github.com/vLLM-HUST/vllm-metal-hust`, vendored in this repo as
`deps/vllm-metal-hust`. It is similar in spirit to `vllm-ascend`: vLLM core keeps
the engine, scheduler, tokenizer, and OpenAI-compatible API, while the plugin
supplies an Apple-specific platform, worker, and model runner.

Important details:

- `vllm-metal` uses MLX/Metal as the primary compute backend, not plain PyTorch
  MPS.
- It targets Apple Silicon with native arm64 Python.
- It expects MLX-format safetensors models, typically from `mlx-community`.
- It already has paged attention work and Apple-specific model runner logic.

For Sage Mate, this means Apple GPU support should preferably be implemented by
using the local runtime adapter for `vllm-metal-hust`, not by attempting to force
the existing CUDA/CPU `vllm-hust` fork onto MPS.

## Implemented Adapter

- `tools/install_vllm_metal_runtime.sh` installs the fork from bundled source.
  It points the plugin installer at pinned `deps/vllm-hust` through
  `VLLM_METAL_VLLM_SOURCE_DIR`.
- `tools/run_vllm_metal_engine.sh` starts the OpenAI-compatible vLLM server.
- `tools/install_local_code_mode.sh` selects `vllm_metal` automatically on Apple
  Silicon when no explicit remote endpoint is supplied.
- The macOS DMG builder bundles `vllm-metal-hust` source into the app resources.
- Source installs set `VLLM_METAL_BUILD_FROM_SOURCE=1`, avoiding a full Xcode
  Metal artifact prebuild on end-user machines. Release maintainers can still
  set `VLLM_METAL_PREBUILD_ARTIFACTS=1` on a full Xcode build Mac to ship
  prebuilt artifacts.
- Default model: `mlx-community/gemma-3-1b-it-qat-4bit`.

## Direct MPS Port Scope

If we still want to build direct PyTorch MPS support inside `vllm-hust`, the
minimum changes are:

1. Add a platform:
   - add `PlatformEnum.MPS`;
   - add `vllm/platforms/mps.py`;
   - detect `torch.backends.mps.is_available()`;
   - expose `device_type="mps"`, `device_name="mps"`, supported dtypes, and a
     non-CUDA distributed story, likely `gloo` for single-machine local serving.
2. Change build target handling:
   - stop forcing Darwin to CPU when `VLLM_TARGET_DEVICE=mps`;
   - teach CMake that `mps` is a valid non-CUDA/non-ROCm target;
   - skip CUDA, ROCm, NCCL, FlashAttention, FlashInfer, and Triton GPU kernels;
   - still build pure C++/Rust extensions that are device-independent.
3. Add an MPS worker/model runner:
   - either adapt the GPU runner to `torch.device("mps")`, or fork a smaller
     `MPSWorker`/`MPSModelRunner`;
   - disable CUDA graphs, CUDA streams, NCCL/custom all-reduce, CUDA memory
     snapshot code, and CUDA-only profiling;
   - verify KV cache allocation and block management on MPS tensors.
4. Add an MPS attention backend:
   - first prototype with PyTorch SDPA/FlexAttention if it works for paged KV
     cache and decode shapes;
   - otherwise implement Metal kernels for paged attention and KV cache update;
   - register a new backend such as `MPS_ATTN`;
   - define supported head sizes, dtypes, block sizes, sliding window behavior,
     and unsupported features explicitly.
5. Audit model features:
   - quantization paths;
   - FP8/BF16 behavior;
   - custom ops used by common layers;
   - sampling/logits processors;
   - speculative decoding;
   - multimodal encoders.
6. Add Apple Silicon CI/smoke tests:
   - import and platform detection;
   - CPU build on macOS still works;
   - `VLLM_TARGET_DEVICE=mps` build completes;
   - one tiny text model serves OpenAI-compatible completions;
   - fallback errors are clear when MPS lacks an op.

## Recommendation

Ship macOS local inference in two phases:

1. Short term: support launching local CPU `vllm-hust` for small models and keep
   remote endpoints strictly user-configured.
2. Near term: add a `vllm-metal` runtime adapter for macOS Apple Silicon. This
   gets real Apple GPU acceleration without forking a large MPS backend.
3. Medium term: only pursue a direct MPS backend if `vllm-metal` cannot satisfy
   model coverage, packaging, or API compatibility requirements. For practical
   speed before that port is complete, also consider an MLX or llama.cpp
   OpenAI-compatible local server as a fallback runtime while keeping
   vLLM-HUST as the Linux/CUDA and Linux/CPU runtime.
