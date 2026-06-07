from __future__ import annotations

import os
import socket
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALL_SCRIPT = REPO_ROOT / "tools" / "install_user_services.sh"
PROXY_SCRIPT = REPO_ROOT / "tools" / "run_vllm_openai_proxy.sh"


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _make_fake_python(path: Path, *, has_uvicorn: bool) -> Path:
    exit_code = "0" if has_uvicorn else "1"
    _write_executable(
        path,
        "#!/usr/bin/env bash\n"
        f"exit {exit_code}\n",
    )
    return path


def _make_fake_systemctl(path: Path) -> Path:
    _write_executable(
        path,
        "#!/usr/bin/env bash\n"
        "printf '%s\n' \"$*\" >>\"$SYSTEMCTL_LOG\"\n"
        "exit 0\n",
    )
    return path


def test_install_user_services_prefers_valid_existing_unit_over_stale_state(
    tmp_path: Path,
) -> None:
    fake_bin_dir = tmp_path / "bin"
    fake_bin_dir.mkdir()
    fake_systemctl = _make_fake_systemctl(fake_bin_dir / "systemctl")
    good_python = _make_fake_python(tmp_path / "good-python", has_uvicorn=True)
    bad_python = _make_fake_python(tmp_path / "bad-python", has_uvicorn=False)

    xdg_config_home = tmp_path / "xdg"
    target_dir = xdg_config_home / "systemd" / "user"
    target_dir.mkdir(parents=True)
    (target_dir / "sage-faculty-twin-app.service").write_text(
        "[Service]\nEnvironment=PYTHON_BIN=" + str(good_python) + "\n",
        encoding="utf-8",
    )
    (target_dir / ".sage-faculty-twin-python-bin").write_text(
        str(bad_python) + "\n",
        encoding="utf-8",
    )

    env = os.environ.copy()
    env.update(
        {
            "HOME": str(tmp_path / "home"),
            "XDG_CONFIG_HOME": str(xdg_config_home),
            "PATH": f"{fake_bin_dir}:{env['PATH']}",
            "SYSTEMCTL_LOG": str(tmp_path / "systemctl.log"),
        }
    )

    subprocess.run(["bash", str(INSTALL_SCRIPT)], check=True, cwd=REPO_ROOT, env=env)

    rendered_unit = (target_dir / "sage-faculty-twin-app.service").read_text(encoding="utf-8")
    remembered_python = (target_dir / ".sage-faculty-twin-python-bin").read_text(
        encoding="utf-8"
    ).strip()

    assert f"Environment=PYTHON_BIN={good_python}" in rendered_unit
    assert remembered_python == str(good_python)
    assert fake_systemctl.exists()


def test_install_user_services_only_enables_proxy_with_explicit_flag(tmp_path: Path) -> None:
    fake_bin_dir = tmp_path / "bin"
    fake_bin_dir.mkdir()
    _make_fake_systemctl(fake_bin_dir / "systemctl")
    good_python = _make_fake_python(tmp_path / "good-python", has_uvicorn=True)
    systemctl_log = tmp_path / "systemctl.log"

    env = os.environ.copy()
    env.update(
        {
            "HOME": str(tmp_path / "home"),
            "XDG_CONFIG_HOME": str(tmp_path / "xdg"),
            "PATH": f"{fake_bin_dir}:{env['PATH']}",
            "PYTHON_BIN": str(good_python),
            "SYSTEMCTL_LOG": str(systemctl_log),
        }
    )

    subprocess.run(["bash", str(INSTALL_SCRIPT)], check=True, cwd=REPO_ROOT, env=env)
    default_log = systemctl_log.read_text(encoding="utf-8")
    assert "enable sage-faculty-twin-app.service sage-faculty-twin-site.service sage-faculty-twin-tunnel.service" in default_log
    assert "sage-faculty-twin-vllm-openai-proxy.service" not in default_log

    systemctl_log.write_text("", encoding="utf-8")
    subprocess.run(
        ["bash", str(INSTALL_SCRIPT), "--with-vllm-proxy"],
        check=True,
        cwd=REPO_ROOT,
        env=env,
    )
    proxy_log = systemctl_log.read_text(encoding="utf-8")
    assert "sage-faculty-twin-vllm-openai-proxy.service" in proxy_log


def test_run_vllm_openai_proxy_fails_fast_when_port_is_occupied(tmp_path: Path) -> None:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    occupied_port = listener.getsockname()[1]

    env = os.environ.copy()
    env.update(
        {
            "PYTHON_BIN": sys.executable,
            "VLLM_PROXY_HOST": "127.0.0.1",
            "VLLM_PROXY_PORT": str(occupied_port),
        }
    )

    try:
        result = subprocess.run(
            ["bash", str(PROXY_SCRIPT)],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        listener.close()

    assert result.returncode == 1
    assert "already in use" in result.stderr
    assert "VLLM_PROXY_PORT" in result.stderr