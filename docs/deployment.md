# Deployment Guide

This document describes the generic deployment shape for `sage-faculty-twin` after moving the
repository into the IntelliStream organization.

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