# Faculty Twin Hosted/Web Installer

This release bundle installs the hosted/web Faculty Twin service on a fresh
Linux machine.

## Install

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
./install.sh --accelerator nvidia
./install.sh --accelerator ascend
./install.sh --no-tunnel
./install.sh --model-preset qwen2.5-14b-awq
./install.sh --model-preset qwen3-next-80b-awq
```

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
