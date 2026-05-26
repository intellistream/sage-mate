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

The repository includes a repo-local Nginx launcher so you can serve the app and an optional
homepage route without writing into system-wide `/etc/nginx`.

```bash
HOMEPAGE_UPSTREAM_HOST=homepage.example.edu \
HOMEPAGE_UPSTREAM_SCHEME=https \
./tools/run_local_site.sh
```

Relevant variables:

- `APP_PORT`: upstream app port, default `55601`
- `SITE_PORT`: local proxy port, default `8088`
- `HOMEPAGE_UPSTREAM_HOST`: hostname used for `/home/` proxying
- `HOMEPAGE_UPSTREAM_SCHEME`: upstream scheme for `/home/`, default `https`

If you do not want to proxy a homepage route yet, leave the homepage link hidden by keeping
`DIGITAL_TWIN_HOMEPAGE_PUBLIC_URL` empty.

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

To show a public homepage button in the web UI, set:

```bash
export DIGITAL_TWIN_HOMEPAGE_PUBLIC_URL=https://faculty.example.edu/
```

If the variable is empty, the top-bar homepage link stays hidden.