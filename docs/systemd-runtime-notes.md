# systemd Runtime Notes

This note records the 2026-06-07 runtime cleanup on `train05` and the repo-side
changes that came out of it.

## What changed in the repository

- `tools/install_user_services.sh` now prefers a Python interpreter that can
  import `uvicorn` instead of blindly falling back to `/usr/bin/python3`.
- The chosen interpreter is persisted in
  `~/.config/systemd/user/.sage-faculty-twin-python-bin` so a later reinstall
  does not accidentally rewrite the rendered units to a broken interpreter.
- `manage.sh` and `tools/install_user_services.sh` now treat
  `sage-faculty-twin-vllm-openai-proxy.service` as optional. The default managed
  stack is:
  - `sage-faculty-twin-app.service`
  - `sage-faculty-twin-site.service`
  - `sage-faculty-twin-tunnel.service`
- To include the OpenAI proxy explicitly, use `--with-vllm-proxy`.
- `tools/run_app_server.sh` now seeds writable HuggingFace cache variables and
  defaults `HF_ENDPOINT` to `https://hf-mirror.com` for non-interactive
  `systemd --user` launches.
- `tools/run_vllm_openai_proxy.sh` now fails fast when
  `VLLM_PROXY_HOST:VLLM_PROXY_PORT` is already occupied.

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