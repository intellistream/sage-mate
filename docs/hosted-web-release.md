# Hosted/Web Release Installer

This is the release-facing one-shot path for deploying Faculty Twin / Sage Mate in hosted/web mode
on fresh Linux servers. It supports NVIDIA/CUDA, Ascend/NPU, and local-only hosted/web installs.
It delegates the actual install/runtime work to the repository-maintained `quickstart.sh`,
`manage.sh`, systemd user units, and pinned submodule checkouts.

## One-Line Install

From a fresh server:

```bash
mkdir -p "$HOME"
curl -fsSL https://raw.githubusercontent.com/intellistream/sage-faculty-twin/main/release/hosted-web.sh \
  -o /tmp/hosted-web.sh
FACULTY_TWIN_SECRETS_KEY_FILE=/home/shuhao/.config/sage-faculty-twin/release-secrets.key \
  bash /tmp/hosted-web.sh --yes
```

The installer clones or fast-forwards `intellistream/sage-faculty-twin`, initializes submodules,
configures hosted/web safety defaults, installs pinned runtime dependencies for the selected
accelerator, installs systemd user units, starts the stack, configures the Cloudflare tunnel when
credentials are available, and runs `./manage.sh verify-hosted-web`.

## Accelerator Selection

`--accelerator auto` is the default:

- NVIDIA/CUDA hosts use `--with-nvidia-vllm-engine` and pinned `deps/vllm-hust`.
- Ascend/NPU hosts use `--with-vllm-engine` and pinned `deps/vllm-hust-dev-hub`,
  `deps/vllm-hust`, and `deps/vllm-ascend-hust`.
- Hosts without local inference hardware can use `--accelerator none` and point
  `DIGITAL_TWIN_LLM_BASE_URL` at an external OpenAI-compatible endpoint.

Convenience wrappers are also published:

```bash
bash /tmp/hosted-web.sh --accelerator nvidia --yes
bash /tmp/hosted-web.sh --accelerator ascend --yes
```

## Model Presets

```bash
# Auto: NVIDIA 80GB/Ascend default to Qwen3-32B, smaller NVIDIA hosts use Qwen2.5-14B AWQ.
bash /tmp/hosted-web.sh --yes

# Explicit large dual-A100 preset.
bash /tmp/hosted-web.sh --accelerator nvidia --model-preset qwen3-next-80b-awq --yes

# More conservative Qwen3 preset.
bash /tmp/hosted-web.sh --model-preset qwen3-32b --yes

# Small, faster smoke-test preset.
bash /tmp/hosted-web.sh --accelerator nvidia --model-preset qwen2.5-14b-awq --yes
```

For custom models, the served model name defaults to the exact model value so the deployment does
not create a misleading alias:

```bash
bash /tmp/hosted-web.sh \
  --accelerator nvidia \
  --model Qwen/Qwen3-32B \
  --served-model-name Qwen/Qwen3-32B \
  --tensor-parallel-size 2 \
  --yes
```

## Safety Guarantees

The installer writes these hosted/web settings before calling `quickstart.sh`:

```bash
DIGITAL_TWIN_DEPLOYMENT_MODE=hosted
DIGITAL_TWIN_APP_PROFILE=faculty_twin
DIGITAL_TWIN_CODE_WORKBENCH_ENABLED=false
DIGITAL_TWIN_CODE_WORKSPACE_ROOTS=
```

It does not enable local Code Assistant, local repo editing, server folder selection, or local
command execution. It chooses exactly one local inference path based on `--accelerator`; NVIDIA uses
`--with-nvidia-vllm-engine`, and Ascend uses `--with-vllm-engine`.

## Network And Secrets

- `HF_ENDPOINT` defaults to `https://hf-mirror.com` for faster model access from China-region
  networks. Override it if needed.
- `HF_HUB_DISABLE_XET` is honored when set, but the release installer does not force it because
  some large community quantized snapshots are Xet-backed.
- `HF_TOKEN`, `HUGGING_FACE_HUB_TOKEN`, GitHub tokens, Cloudflare tunnel tokens, and API keys are
  honored from the environment or `.env` but are never printed by the installer.
- Release secrets can be shipped as encrypted ciphertext. Put a filled plaintext copy at
  `release/secrets.env`, encrypt it, and commit/publish only `release/secrets.env.enc`:

  ```bash
  openssl enc -aes-256-cbc -pbkdf2 -salt \
    -in release/secrets.env \
    -out release/secrets.env.enc \
    -pass file:/secure/faculty-twin-secrets.key
  ```

  Deploy with the decrypt key kept outside the repository:

  ```bash
  FACULTY_TWIN_SECRETS_KEY_FILE=/secure/faculty-twin-secrets.key \
    bash /tmp/hosted-web.sh --yes
  ```

  On managed Sage servers, the expected key path is:

  ```bash
  /home/shuhao/.config/sage-faculty-twin/release-secrets.key
  ```

  The installer decrypts to a temporary `0600` file, merges values into `.env`, deletes the
  temporary file, and never prints secret values. A public release cannot safely contain both the
  ciphertext and the decrypt key; keep the key in server provisioning or CI secrets.
- Cloudflare tunnel is enabled by default for `twin.sage.org.ai`. The installer creates or reuses a
  CLI-managed named tunnel, writes a private runtime config file, routes DNS with
  `cloudflared tunnel route dns --overwrite-dns`, and verifies the public URL.
- Use `--no-tunnel` for local-only installs, or `--public-hostname HOSTNAME --tunnel-name NAME` for
  another domain/tunnel.

## Ports

- Faculty Twin app: `127.0.0.1:55601`
- Site proxy: `0.0.0.0:8088`
- NVIDIA vLLM engine: `127.0.0.1:18000`
- Ascend vLLM-HUST engine: `127.0.0.1:8000`
- OpenAI-compatible auth proxy: `127.0.0.1:18001`

NVIDIA vLLM uses `18000` by default so it does not collide with common local static servers or
older vLLM defaults on `8000`.

## Verification

After install:

```bash
cd "$HOME/sage-faculty-twin"
./manage.sh status --with-vllm-proxy --with-site-proxy --with-nvidia-vllm-engine
env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u http_proxy -u https_proxy -u all_proxy \
  NO_PROXY=127.0.0.1,localhost \
  ./manage.sh verify-hosted-web --public-url https://twin.sage.org.ai/
curl --noproxy '*' -fsS http://127.0.0.1:55601/healthz
curl --noproxy '*' -fsS https://twin.sage.org.ai/healthz
```

If a shell has `HTTP_PROXY`/`HTTPS_PROXY` set, use `--noproxy '*'` for local `curl` checks.
