# Deployment Guide

This document describes the generic deployment shape for `sage-faculty-twin` after moving the
repository into the IntelliStream organization.

For a fresh-machine bring-up, the fastest path is:

```bash
git clone https://github.com/intellistream/sage-faculty-twin.git
cd sage-faculty-twin
./quickstart.sh                  # env + deps + .env + systemd units
./quickstart.sh --with-vllm      # also pull and editable-install vllm-hust
./quickstart.sh --start          # install + start the three user services
```

`quickstart.sh` is idempotent and never overwrites an existing `.env` value—it only fills in
missing keys. See §7 below for the chunked-transfer / streaming gotcha that the latency
rollout uncovered.

## 1. Application Server

Start the FastAPI app directly:

```bash
cd /path/to/sage-faculty-twin
PYTHONPATH="$PWD/src:$PWD/../SAGE/src:$PWD/../neuromem:$PWD/../sageVDB" \
python -m uvicorn sage_faculty_twin.api:app --host 127.0.0.1 --port 55601
```

Or use the provided wrapper:

```bash
./tools/run_app_server.sh
```

## 2. Local Reverse Proxy

The repository includes a repo-local Nginx launcher so you can serve the app and keep a local
homepage compatibility route without writing into system-wide `/etc/nginx`.

```bash
./tools/run_local_site.sh
```

Relevant variables:

- `APP_PORT`: upstream app port, default `55601`
- `SITE_PORT`: local proxy port, default `8088`
- `HOMEPAGE_REDIRECT_ORIGIN`: canonical public homepage origin, default `https://home.shuhao.sage.org.ai`

`/home` and `/home/` are compatibility paths at the site-proxy layer. They now redirect to the
canonical public homepage origin, while local direct app access can still use the built-in FastAPI
homepage endpoint on `APP_PORT`.

## 3. User Services

To install persistent user services with `systemd --user`:

```bash
./manage.sh install --start
```

This renders and installs:

- `sage-faculty-twin-app.service`
- `sage-faculty-twin-site.service`
- `sage-faculty-twin-tunnel.service`

The management entry points are:

```bash
./manage.sh status
./manage.sh start
./manage.sh stop
./manage.sh restart
```

## 4. Tunnel Configuration

The repository ships a generic Cloudflare Tunnel example:

```bash
mkdir -p .runtime/cloudflared
cp tools/cloudflared-config.example.yml .runtime/cloudflared/config.yml
```

Replace the placeholder tunnel id and hostname in that file, then run:

```bash
./tools/run_named_tunnel.sh
```

## 5. Public Branding

Set the canonical public homepage URL for the web UI top-bar button with:

```bash
export DIGITAL_TWIN_HOMEPAGE_PUBLIC_URL=https://faculty.example.edu/
```

For this deployment, the canonical public homepage is `https://home.shuhao.sage.org.ai/`.

If the variable is empty, the top-bar homepage link falls back to the app-local `/home/` route.
That fallback is useful for local development, but it should not be treated as the public-facing
homepage URL.

## 6. Upstream Proxy: Body Size and Timeouts

When the deployment chain is `Cloudflare → host nginx → uvicorn`, two
proxy-side knobs commonly cause student-visible failures:

- **HTTP 413 “Request Entity Too Large”** when uploading multi-page PDFs to
  `/chat`. The application accepts up to `MAX_CHAT_ATTACHMENT_BYTES = 5 MB`,
  but stock nginx defaults to `client_max_body_size 1m`, so larger uploads
  are rejected at the proxy before reaching FastAPI.
- **HTTP 504 “Gateway time-out”** when the LLM takes longer than the proxy's
  read timeout. Cloudflare's free tier caps end-to-end requests at
  approximately **100 seconds**; uvicorn typically completes within ~60s but
  occasionally exceeds 90s under load.

### nginx (host) settings

Match or exceed the application limits in the production nginx server block,
for example in `/etc/nginx/sites-available/sage-faculty-twin`:

```nginx
http {
    # Allow chat attachments up to slightly above the 5MB application limit.
    client_max_body_size 8m;
    client_body_timeout 120s;

    # Long LLM responses can take 30-60 seconds; do not truncate them.
    proxy_read_timeout 180s;
    proxy_send_timeout 180s;
    proxy_connect_timeout 30s;
    proxy_buffering off;
}
```

The repo-local template at `tools/nginx-local.conf` already ships with these
values. After editing the production config:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Application-side timeout guard

The FastAPI `/chat` route wraps `service.answer(...)` in
`asyncio.wait_for(...)` with a default budget of **95 seconds** so that the
app returns a structured `504` with a Chinese message before Cloudflare's
edge times out. Override the budget by exporting:

```bash
export DIGITAL_TWIN_CHAT_REQUEST_TIMEOUT_SECONDS=95
```

Keep this value comfortably below Cloudflare's 100s cap. If the upstream LLM
is consistently slower than this budget, lower
`DIGITAL_TWIN_LLM_TIMEOUT_SECONDS` (default 90s) first so the model abandons
before the request budget fires.

### Cloudflare

Cloudflare's edge timeout cannot be increased on free / Pro plans. To
support long-running answers either:

1. Reduce the answer budget (smaller LLM, shorter prompts), or
2. Move long-running endpoints behind WebSocket / Server-Sent Events (the
   `/chat/workflow-events` SSE stream is already exempt from the 100s cap as
   long as bytes flow regularly), or
3. Use a Cloudflare plan that supports custom timeouts.

## 7. LLM Streaming and the chunked-transfer gotcha

Faculty-twin can stream LLM tokens to the browser per-token via SSE
(`answer_delta` / `answer_done` events) when
`DIGITAL_TWIN_STREAM_CHAT_ANSWER=true`. For this to work end-to-end the
upstream OpenAI-compatible endpoint MUST emit `Transfer-Encoding: chunked`.

Reproduction recipe to verify any candidate `LLM_BASE_URL`:

```bash
curl -N -i -H "Authorization: Bearer $KEY" \
     -H 'Content-Type: application/json' \
     --data '{"model":"<model>","stream":true,"max_tokens":50,
              "messages":[{"role":"user","content":"hi"}]}' \
     "$LLM_BASE_URL/chat/completions" | head -c 400
```

Look for these headers:

* `HTTP/1.1 200 OK`  — NOT `HTTP/1.0`
* `Content-Type: text/event-stream; charset=utf-8`
* `Transfer-Encoding: chunked`

**Common foot-gun.** A custom OpenAI router built on Python's stdlib
`http.server.BaseHTTPRequestHandler` defaults to `HTTP/1.0`, which has no
chunked transfer encoding. Such routers buffer the entire response and
flush at the end of generation, defeating per-token streaming even though
vllm itself behaves correctly. Either:

* **point `DIGITAL_TWIN_LLM_BASE_URL` directly at vllm-hust** (recommended),
  or
* fix the proxy to set `protocol_version = "HTTP/1.1"` and forward the
  upstream response with explicit `Transfer-Encoding: chunked` framing.

### .env must be in the process environment, not just the file

The streaming flag and the latency knobs (`DIGITAL_TWIN_STREAM_CHAT_ANSWER`,
`DIGITAL_TWIN_CHAT_REQUEST_TIMEOUT_SECONDS`,
`DIGITAL_TWIN_CHAT_SSE_KEEPALIVE_SECONDS`,
`DIGITAL_TWIN_CHAT_PROMPT_SOFT_CAP_CHARS`) are read at module import time
via `os.environ.get(...)`. They are *not* loaded by pydantic-settings.
`tools/run_app_server.sh` therefore exports `.env` into the process
environment immediately before launching uvicorn so these values reach the
app. If you write your own launcher, do the same — a value that lives only
inside `.env` will be invisible to those code paths.