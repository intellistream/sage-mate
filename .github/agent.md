# Agent Runtime Notes (my-twin)

## Why restarts looked like failures

These incidents were mostly "false restart failures" rather than a crashed app process.

1. Service reported `active (running)` but probes used overly short timeout.
- Several checks used `curl -m 2` immediately after restart.
- During startup warm-up (imports, store initialization, first health aggregation), 2s is often too short.
- Result: repeated timeout/connection-refused during warm-up, then recovery later.

2. Health endpoint can be expensive right after restart.
- `/health` aggregates multiple runtime sources.
- It now also includes LLM metrics pulls and store statistics.
- Under load or cold start, first health call may be much slower than steady-state.

3. vLLM prefix metrics naming mismatch caused misleading zero values.
- vLLM exposed `vllm:prefix_cache_*_total` counters.
- The parser previously expected non-`_total` names.
- This did not break restart, but created "system looks wrong" symptoms (`prefix hit=0`) that looked like restart instability.

4. Manual systemd inspection from shell could fail without user bus env.
- When `XDG_RUNTIME_DIR` / `DBUS_SESSION_BUS_ADDRESS` are missing, `systemctl --user` checks may fail.
- This can look like service failure even while unit is running.

## Operational guidance

1. After restart, probe with a longer timeout and bounded retries.
- Example: `for i in $(seq 1 40); do curl -sS -m 20 http://127.0.0.1:55601/health && break || true; done`

2. Distinguish states explicitly.
- `connection refused`: process/socket not yet up.
- `timeout`: process up but request path still warming or blocked.

3. Validate app and site independently.
- App: `http://127.0.0.1:55601/health`
- Site proxy: `http://127.0.0.1:8088/`

4. Use user-systemd checks with explicit runtime bus env in non-login shells.
- `export XDG_RUNTIME_DIR=/run/user/$(id -u)`
- `export DBUS_SESSION_BUS_ADDRESS=unix:path=$XDG_RUNTIME_DIR/bus`

5. SQLite persistence policy for machine portability.
- For this project, sqlite state under `data/conversation_memory/*.sqlite3` is treated as portable runtime baseline.
- When shipping environment/migration updates, include the relevant sqlite files in commits so another machine can restore history/state directly.
- If sqlite changes are intentionally local-only experiments, call that out explicitly before excluding them.

## Mobile UI validation notes

1. Mobile viewport check was executed at 390x844.
- Topbar actions (`历史对话` / `设置` / `状态`) render without overlap.
- `设置` drawer and `状态` drawer can both be opened on mobile layout.

2. Outside-click close behavior verified.
- With settings drawer open, tapping a blank area outside the drawer closes it.
- Status drawer already supports outside-click close with the same interaction expectation.

## Python environment notes

1. Broken `.venv` can be present even when the repo appears to have a local environment.
- In this repo, `.venv/bin/python3.11` was a symlink to `/usr/bin/python3.11`.
- On this host, `/usr/bin/python3.11` did not exist, so `.venv/bin/python`, `.venv/bin/uvicorn`, and other console scripts failed even though the `.venv` directory was present.
- If `.venv` points at a missing interpreter, treat it as stale and remove or rebuild it instead of assuming the environment is usable.

2. `sagellm` is the reliable Python 3.11 execution path on this machine.
- The working interpreter is `/home/shuhao/miniforge3/envs/sagellm/bin/python`.
- It provides Python 3.11 plus the packages needed for `my-twin` regression checks.
- When running tests manually, prefer invoking that interpreter directly with the repo `PYTHONPATH` instead of relying on `conda activate`.

3. `conda` entrypoints under `miniforge3/bin` can be stale even if the env itself still works.
- On this host, `/home/shuhao/miniforge3/bin/conda` still referenced `/workspace/miniforge3/bin/python` in its shebang.
- That made `conda env list` fail, but did not mean `/home/shuhao/miniforge3/envs/sagellm/` was broken.
- If `conda` wrapper scripts fail, inspect the target environment's `bin/python` directly before concluding the environment is unavailable.
