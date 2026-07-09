# Faculty Twin Hosted/Web Installer

This release bundle installs the hosted/web Faculty Twin service on a fresh
Linux machine.

## Recommended Linux Install

Download the `.run` installer from GitHub Release:

```bash
chmod +x sage-faculty-twin-v4.4.0-linux.run
./sage-faculty-twin-v4.4.0-linux.run
```

The `.run` installer extracts this bundle to:

```bash
~/.local/share/sage-faculty-twin-installer/sage-faculty-twin-v4.4.0
```

That persistent location lets the installer resume after a driver-upgrade reboot.

## Install Modes

The installer supports three product modes:

```bash
# Hosted Faculty Twin web service. Local code tools are disabled.
./sage-faculty-twin-v4.4.0-linux.run --web-only

# Local Sage Mate code-editing app only.
./sage-faculty-twin-v4.4.0-linux.run --code-only

# Both, installed into separate checkouts and ports.
./sage-faculty-twin-v4.4.0-linux.run --both
```

`--both` uses separate directories so hosted/web safety settings do not mix with
local code-editing settings:

- Web repo: `~/sage-faculty-twin`
- Code repo: `~/sage-mate-local-code`
- Web URL: `http://127.0.0.1:55601/`
- Code URL: `http://127.0.0.1:55611/?setup=local-code`

## Tarball Install

Put the release key on the target machine:

```bash
mkdir -p ~/.config/sage-faculty-twin
chmod 700 ~/.config/sage-faculty-twin
# place release-secrets.key at:
# ~/.config/sage-faculty-twin/release-secrets.key
```

Then run:

```bash
FACULTY_TWIN_SECRETS_KEY_FILE=~/.config/sage-faculty-twin/release-secrets.key \
  ./install.sh
```

On a desktop Linux session with `zenity`, `install.sh` shows progress dialogs.
Without a desktop session, it prints progress in the terminal.

If the release key is already at the default path, you can simply run:

```bash
./install.sh
```

If the key is missing, the installer explains what it is used for and offers:

- check again after placing the key;
- continue a local install without encrypted secrets;
- exit.

Continuing without encrypted secrets disables automatic Cloudflare tunnel setup
and requires you to configure any private GitHub, Hugging Face, Cloudflare, or
app keys separately.

## What The Installer Does

- Checks NVIDIA or Ascend hardware.
- Explains whether encrypted release secrets will be used.
- If the NVIDIA driver is too old, asks before upgrading it with the repository
  driver helper.
- Asks before rebooting when a driver upgrade requires it.
- Resumes automatically after login.
- Clones or updates `intellistream/sage-faculty-twin`.
- Applies hosted/web safety settings.
- Installs pinned dependencies and submodules.
- Starts systemd user services.
- Runs hosted/web verification.
- During first model startup, prints progress for vLLM readiness, Hugging Face
  cache size, and GPU memory so long downloads do not look frozen.

## Hosted/Web Safety

The installer forces:

```bash
DIGITAL_TWIN_DEPLOYMENT_MODE=hosted
DIGITAL_TWIN_APP_PROFILE=faculty_twin
DIGITAL_TWIN_CODE_WORKBENCH_ENABLED=false
DIGITAL_TWIN_CODE_WORKSPACE_ROOTS=
```

It does not enable local Code Assistant, local repository editing, server folder
selection, or local command execution.

## Common Options

```bash
./install.sh --web-only
./install.sh --code-only
./install.sh --both
./install.sh --accelerator nvidia
./install.sh --accelerator ascend
./install.sh --no-tunnel
./install.sh --model-preset qwen3-32b-awq
./install.sh --model-preset qwen2.5-14b-awq
./install.sh --model-preset qwen3-next-80b-awq
```

On NVIDIA hosts with large GPUs, `auto` uses a practical Qwen3 32B AWQ model by
default. Its served model name is the actual model id: `Qwen/Qwen3-32B-AWQ`.

Large presets such as `qwen3-next-80b-awq` can spend a long time on first start
downloading model shards and warming up vLLM. For NVIDIA hosted/web installs,
the installer pre-downloads this model with a single Hugging Face cache process
before starting vLLM, then starts vLLM in offline-cache mode to avoid multi-worker
mirror rate limits. Set `FACULTY_TWIN_PREDOWNLOAD_MODEL=0` to skip that behavior.
If the mirror cannot complete the 80B pre-download, the installer falls back to
`Qwen/Qwen3-32B-AWQ` by default so first install can still complete; set
`FACULTY_TWIN_ALLOW_MODEL_FALLBACK=0` to make that condition fatal instead.
Unless `HF_ENDPOINT` is explicitly set, this fallback uses the official
Hugging Face endpoint to avoid mirror API rate limits.
Set `FACULTY_TWIN_VERIFY_TIMEOUT_SECONDS` if a very slow network needs an even
longer first-start window.

## Logs

Installer logs are written to:

```bash
~/.local/state/sage-faculty-twin-installer/install.log
```

## URLs

After installation:

- Local app: `http://127.0.0.1:55601/`
- Local site proxy: `http://127.0.0.1:8088/`

If Cloudflare tunnel credentials are available and `--with-tunnel` is used, the
installer also verifies the configured public hostname.

## Windows

Hosted/web runs on Linux GPU/NPU hosts. A Windows package should act as a
deployment assistant for WSL or a remote Linux server, then invoke the Linux
`.run` installer there. It should not pretend that the hosted/web service runs
as a native Windows app.
