#!/usr/bin/env bash
set -euo pipefail

container_id="4843b7f5948daf4c861dda284a2d7afa2b91985c67c30230b05de025c809582c"

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