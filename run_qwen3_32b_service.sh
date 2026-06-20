#!/usr/bin/env bash
# run_qwen3_32b_service.sh — Start or stop the Qwen3-32B vllm-hust service inside Docker.
#
# Usage:
#   ./run_qwen3_32b_service.sh           # start the service
#   ./run_qwen3_32b_service.sh --stop    # gracefully stop the service

set -euo pipefail

container_id="4843b7f5948daf4c861dda284a2d7afa2b91985c67c30230b05de025c809582c"

if [[ "${1:-}" == "--stop" ]]; then
  if [[ "$(sudo -n docker inspect -f '{{.State.Running}}' "$container_id" 2>/dev/null || true)" != "true" ]]; then
    exit 0
  fi

  sudo -n docker exec -i "$container_id" python3 - <<'PY'
import os
import signal
import time

TARGET = "/workspace/shuhao-miniconda3/envs/vllm-hust-dev/bin/vllm-hust serve /data/shared-models/Qwen3-32B"


def iter_processes():
  for entry in os.listdir("/proc"):
    if not entry.isdigit():
      continue
    pid = int(entry)
    try:
      with open(f"/proc/{pid}/comm", "r", encoding="utf-8") as fh:
        comm = fh.read().strip()
      with open(f"/proc/{pid}/cmdline", "rb") as fh:
        raw = fh.read().replace(b"\x00", b" ").decode("utf-8", errors="ignore").strip()
    except OSError:
      continue
    yield pid, comm, raw


def find_pids():
  matches = []
  for pid, comm, cmdline in iter_processes():
    if comm.startswith("python") and TARGET in cmdline:
      matches.append(pid)
      continue
    if comm.startswith("VLLM::EngineCor"):
      matches.append(pid)
  return sorted(set(matches))


def alive(pids):
  remaining = []
  for pid in pids:
    try:
      os.kill(pid, 0)
    except OSError:
      continue
    remaining.append(pid)
  return remaining


pids = find_pids()
if not pids:
  raise SystemExit(0)

for pid in pids:
  try:
    os.kill(pid, signal.SIGTERM)
  except OSError:
    pass

deadline = time.time() + 10
remaining = pids
while time.time() < deadline:
  remaining = alive(find_pids())
  if not remaining:
    raise SystemExit(0)
  time.sleep(1)

for pid in remaining:
  try:
    os.kill(pid, signal.SIGKILL)
  except OSError:
    pass
PY
  exit 0
fi

exec sudo -n docker exec -i "$container_id" /bin/bash -lc "export ASCEND_RT_VISIBLE_DEVICES=4,5 ASCEND_VISIBLE_DEVICES=4,5 HCCL_OP_EXPANSION_MODE=AIV PYTORCH_NPU_ALLOC_CONF=expandable_segments:True; export HOME=/tmp/vllm-hust-qwen3-32b-home XDG_CACHE_HOME=/tmp/vllm-hust-qwen3-32b-home/.cache XDG_CONFIG_HOME=/tmp/vllm-hust-qwen3-32b-home/.config VLLM_CACHE_ROOT=/tmp/vllm-hust-qwen3-32b-home/.cache/vllm VLLM_CONFIG_ROOT=/tmp/vllm-hust-qwen3-32b-home/.config/vllm PIP_CACHE_DIR=/tmp/vllm-hust-qwen3-32b-home/.cache/pip; mkdir -p \"\$HOME\" \"\$XDG_CACHE_HOME\" \"\$XDG_CONFIG_HOME\" \"\$VLLM_CACHE_ROOT\" \"\$VLLM_CONFIG_ROOT\" \"\$PIP_CACHE_DIR\"; exec /workspace/shuhao-miniconda3/envs/vllm-hust-dev/bin/vllm-hust serve /data/shared-models/Qwen3-32B --served-model-name Qwen3-32B --host 0.0.0.0 --port 18000 --tensor-parallel-size 2 --max-model-len 32768 --gpu-memory-utilization 0.92 --enable-chunked-prefill --max-num-batched-tokens 2048 --enable-auto-tool-choice --tool-call-parser hermes --reasoning-config '{\"reasoning_parser\":\"qwen3\"}' --additional-config '{\"ascend_compilation_config\":{}}' --compilation-config '{\"cudagraph_mode\":\"FULL_DECODE_ONLY\",\"cudagraph_capture_sizes\":[1,2,4,8,16,32]}'"
#!/usr/bin/env bash
set -euo pipefail

exec sudo -n docker exec -i 4843b7f5948daf4c861dda284a2d7afa2b91985c67c30230b05de025c809582c /bin/bash -lc "export ASCEND_RT_VISIBLE_DEVICES=4,5 ASCEND_VISIBLE_DEVICES=4,5 HCCL_OP_EXPANSION_MODE=AIV PYTORCH_NPU_ALLOC_CONF=expandable_segments:True; export HOME=/tmp/vllm-hust-qwen3-32b-home XDG_CACHE_HOME=/tmp/vllm-hust-qwen3-32b-home/.cache XDG_CONFIG_HOME=/tmp/vllm-hust-qwen3-32b-home/.config VLLM_CACHE_ROOT=/tmp/vllm-hust-qwen3-32b-home/.cache/vllm VLLM_CONFIG_ROOT=/tmp/vllm-hust-qwen3-32b-home/.config/vllm PIP_CACHE_DIR=/tmp/vllm-hust-qwen3-32b-home/.cache/pip; mkdir -p \"\$HOME\" \"\$XDG_CACHE_HOME\" \"\$XDG_CONFIG_HOME\" \"\$VLLM_CACHE_ROOT\" \"\$VLLM_CONFIG_ROOT\" \"\$PIP_CACHE_DIR\"; exec /workspace/shuhao-miniconda3/envs/vllm-hust-dev/bin/vllm-hust serve /data/shared-models/Qwen3-32B --served-model-name Qwen3-32B --host 0.0.0.0 --port 18000 --tensor-parallel-size 2 --max-model-len 32768 --gpu-memory-utilization 0.92 --enable-chunked-prefill --max-num-batched-tokens 2048 --enable-auto-tool-choice --tool-call-parser hermes --reasoning-config '{\"reasoning_parser\":\"qwen3\"}' --additional-config '{\"ascend_compilation_config\":{}}' --compilation-config '{\"cudagraph_mode\":\"FULL_DECODE_ONLY\",\"cudagraph_capture_sizes\":[1,2,4,8,16,32]}'"