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
  - `sage-faculty-twin-vllm-engine.service` (`--with-vllm-engine`)
  - `sage-faculty-twin-vllm-openai-proxy.service` (`--with-vllm-proxy`)
  - `sage-faculty-twin-site.service` (`--with-site-proxy`)
  - `sage-faculty-twin-tunnel.service` (`--with-tunnel`)
- The default managed stack is:
  - `sage-faculty-twin-app.service` (always enabled)
- `tools/run_app_server.sh` seeds writable HuggingFace cache variables and
  defaults `HF_ENDPOINT` to `https://hf-mirror.com` for non-interactive
  `systemd --user` launches.
- `tools/run_vllm_openai_proxy.sh` fails fast when
  `VLLM_PROXY_HOST:VLLM_PROXY_PORT` is already occupied.
- `tools/run_vllm_engine.sh` is a thin compatibility wrapper. It loads the
  Faculty Twin `.env`, maps the historical `VLLM_ENGINE_*` variables, and then
  delegates to `deps/vllm-hust-dev-hub/scripts/run_vllm_hust_engine.sh`
  (falling back to `/home/shuhao/vllm-hust-dev-hub` only when the submodule is
  absent). This keeps the host -> Docker -> conda -> vLLM-HUST launch path in
  dev-hub instead of maintaining a drifting copy in Faculty Twin.
- The vLLM-HUST runtime dependencies are pinned through repository submodules:
  `deps/vllm-hust-dev-hub`, `deps/vllm-hust`, and `deps/vllm-ascend-hust`.

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

## Current operational shape on train05

- `sage-faculty-twin-app.service` is managed by `systemd --user`.
- `sage-faculty-twin-site.service` is managed by `systemd --user`.
- `sage-faculty-twin-vllm-openai-proxy.service` stays disabled by default on
  this host because port `18001` is already occupied by a direct `vllm-hust`
  process.
- Public Cloudflare ingress is currently handled by the shared host-level user
  service `sage-public-cloudflared.service`, which reuses the existing named
  tunnel config under `sage-faculty-twin/.runtime/cloudflared/`.

## Verification commands

```bash
export XDG_RUNTIME_DIR=/run/user/22629
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/22629/bus

systemctl --user status sage-faculty-twin-app.service
systemctl --user status sage-faculty-twin-site.service
systemctl --user status sage-public-cloudflared.service

curl http://127.0.0.1:55601/health
curl https://shuhao.sage.org.ai/
curl https://openai.sage.org.ai/v1/models
```
