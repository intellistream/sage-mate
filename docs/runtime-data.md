# Runtime Data Boundary

Faculty Twin has three separate state boundaries. Keep them separate so
deployment work does not accidentally commit secrets or depend on shared host
checkouts.

## Code Repository

`intellistream/sage-mate` tracks application source, docs, tests, systemd
entrypoints, examples, and pinned runtime submodules under `deps/`.

The hosted vLLM-HUST runtime must use these submodules:

- `deps/vllm-hust-dev-hub`
- `deps/vllm-hust`
- `deps/vllm-ascend-hust`
- `deps/ascend-runtime-manager`

Do not point Faculty Twin production startup at shared development checkouts
such as `/home/shuhao/vllm-hust`, `/home/shuhao/vllm-ascend-hust`, or
`/home/shuhao/vllm-hust-dev-hub`.

## Private Runtime Directory

`DIGITAL_TWIN_RUNTIME_DIR` stores deployment data and secrets that should not be
committed to the code repository. On 180-ascend-bench this is:

```bash
/home/shuhao/sage-mate-runtime-private
```

Hosted Faculty Twin releases can populate this directory from a dedicated private
runtime-data repository before seeding defaults:

```bash
FACULTY_TWIN_RUNTIME_REPO_URL=https://github.com/Qixin-Gaoke/sage-faculty-twin-runtime-private.git
FACULTY_TWIN_RUNTIME_REPO_BRANCH=main
FACULTY_TWIN_RUNTIME_REPO_REQUIRED=true
```

Authentication uses `GITHUB_TOKEN` through a temporary `GIT_ASKPASS` file, so the
token is never placed in Git arguments or logs. If an older non-Git runtime folder
already exists, the installer keeps a timestamped backup, installs the private
repository as the canonical data source, and merges only files missing from the
repository. Existing local secrets and live records are therefore retained without
overwriting reviewed runtime data.

Runtime-private data includes:

- knowledge base and conversation memory
- user accounts and operational queues
- local deployment `.env` material
- Cloudflare tunnel tokens or credentials under `cloudflared/`

Cloudflare tunnel token-file mode expects:

```bash
$DIGITAL_TWIN_RUNTIME_DIR/cloudflared/token
```

The token file should be mode `0600`.

## Local Scratch State

The code repository's `.runtime/` directory is ignored and is only for local
scratch artifacts such as pid files, proxy config generated during development,
temporary audio files, or one-off experiments. It is not the canonical
production runtime directory.

## Operational Rules

- Keep `.env` local and publish only `.env.example`.
- Keep Cloudflare tokens, API keys, origin certificates, and tunnel credentials
  in the private runtime directory.
- Use `./manage.sh status --all` to inspect all services.
- Use `./manage.sh status --with-tunnel` or `./manage.sh restart --with-tunnel`
  when you only want to operate the tunnel service; explicit service flags no
  longer imply app stop/start.
- For hosted deployments, the dedicated vLLM-HUST container is
  `faculty_twin_vllm_hust`, with this repository's `deps/` mounted at
  `/workspace`.
