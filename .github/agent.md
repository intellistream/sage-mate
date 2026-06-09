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

5. Keep runtime data out of commits.
- Do not commit local runtime sqlite churn under `data/conversation_memory/*.sqlite3` unless migration policy explicitly requires it.
