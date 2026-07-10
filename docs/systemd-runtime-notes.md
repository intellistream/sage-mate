# systemd Runtime Notes

This note records the 2026-06-07 runtime cleanup on `train05` and the repo-side
changes that came out of it.

## What changed in the repository

- `quickstart.sh` is the single entry point for installation. It renders
  systemd service templates from `deploy/systemd/user/`, installs them to
  `~/.config/systemd/user/`, and enables the selected services.
- The install logic was previously in `tools/install_user_services.sh` (now
  deleted) and has been inlined into `quickstart.sh` section 6.
- `manage.sh` is the single entry point for runtime management
  (start/stop/restart/status/logs). It supports `--all` to include all
  optional services at once.
- The following services are optional and controlled by flags:
  - `sage-mate-vllm-engine.service` (`--with-vllm-engine`)
  - `sage-mate-vllm-openai-proxy.service` (`--with-vllm-proxy`)
  - `sage-mate-site.service` (`--with-site-proxy`)
  - `sage-mate-tunnel.service` (`--with-tunnel`)
- The default managed stack is:
  - `sage-mate-app.service` (always enabled)
- `tools/run_app_server.sh` seeds writable HuggingFace cache variables and
  defaults `HF_ENDPOINT` to `https://hf-mirror.com` for non-interactive
  `systemd --user` launches.
- `tools/run_vllm_openai_proxy.sh` fails fast when
  `VLLM_PROXY_HOST:VLLM_PROXY_PORT` is already occupied.
- `tools/run_vllm_engine.sh` is a thin compatibility wrapper. It loads the
  Faculty Twin `.env`, maps the historical `VLLM_ENGINE_*` variables, and then
  delegates to `deps/vllm-hust-dev-hub/scripts/run_vllm_hust_engine.sh`.
  It must not fall back to `/home/shuhao/vllm-hust*` shared checkouts. The
  engine container mounts this repository's `deps/` directory at `/workspace`,
  so `/workspace/vllm-hust`, `/workspace/vllm-ascend-hust`, and
  `/workspace/vllm-hust-dev-hub` are always the pinned Faculty Twin submodules.
- The vLLM-HUST runtime dependencies are pinned through repository submodules:
  `deps/vllm-hust-dev-hub`, `deps/vllm-hust`, `deps/vllm-ascend-hust`, and
  `deps/ascend-runtime-manager`.
- The dedicated runtime container is `faculty_twin_vllm_hust`. Do not reuse
  shared development containers such as `vllm_hust_ws_21rc` for production
  Faculty Twin service startup.

## What changed on the host

- The host needed a persistent override for `user@22629.service` because the
  user manager failed with `XDG_RUNTIME_DIR is not set`.
- The persistent host-level drop-in is:

```ini
[Service]
Environment=XDG_RUNTIME_DIR=/run/user/22629
```

- On `train05` this override lives under:
  `/etc/systemd/system/user@22629.service.d/override.conf`
- This file is host-specific and is not tracked by the repository.

## Current operational shape on 180-ascend-bench

- `sage-mate-app.service` is managed by `systemd --user`.
- `sage-mate-site.service` is managed by `systemd --user`.
- `sage-mate-vllm-engine.service` is managed by `systemd --user` and
  starts the dedicated `faculty_twin_vllm_hust` container from pinned
  submodules.
- `sage-mate-vllm-openai-proxy.service` is managed by `systemd --user`
  and proxies `127.0.0.1:18001/v1` to the vLLM-HUST engine.
- `sage-mate-tunnel.service` is managed by `systemd --user`. It runs
  `cloudflared` with a token stored under the private runtime directory:
  `$DIGITAL_TWIN_RUNTIME_DIR/cloudflared/token`.
- Public Cloudflare ingress for `twin.sage.org.ai` is handled by the named
  tunnel `sage-local-235b`, whose remote ingress points
  `twin.sage.org.ai -> http://localhost:55601`.

## Verification commands

```bash
./manage.sh status --all

curl http://127.0.0.1:55601/health
curl https://twin.sage.org.ai/health
```
