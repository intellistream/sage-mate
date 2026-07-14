from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYNC_SCRIPT = REPO_ROOT / "tools" / "sync_runtime_repo.sh"
HOSTED_WEB_SCRIPT = REPO_ROOT / "release" / "hosted-web.sh"


def run_git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )


def test_runtime_repo_replaces_seed_folder_and_preserves_local_only_files(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    run_git("init", "--initial-branch=main", cwd=source)
    run_git("config", "user.email", "test@example.com", cwd=source)
    run_git("config", "user.name", "Runtime Test", cwd=source)
    (source / "data").mkdir()
    (source / "data" / "canonical.json").write_text("repo", encoding="utf-8")
    run_git("add", ".", cwd=source)
    run_git("commit", "-m", "seed runtime", cwd=source)

    runtime_dir = tmp_path / "runtime-private"
    (runtime_dir / "data").mkdir(parents=True)
    (runtime_dir / "data" / "canonical.json").write_text("stale", encoding="utf-8")
    (runtime_dir / "cloudflared").mkdir()
    (runtime_dir / "cloudflared" / "token").write_text("secret", encoding="utf-8")

    result = subprocess.run(
        [
            "bash",
            str(SYNC_SCRIPT),
            "--runtime-dir",
            str(runtime_dir),
            "--repo-url",
            str(source),
            "--required",
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    assert (runtime_dir / ".git").is_dir()
    assert (runtime_dir / "data" / "canonical.json").read_text(
        encoding="utf-8"
    ) == "repo"
    assert (runtime_dir / "cloudflared" / "token").read_text(
        encoding="utf-8"
    ) == "secret"
    assert "secret" not in result.stdout
    assert list(tmp_path.glob("runtime-private.pre-repo-*"))


def test_runtime_repo_fast_forwards_clean_checkout(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    run_git("init", "--initial-branch=main", cwd=source)
    run_git("config", "user.email", "test@example.com", cwd=source)
    run_git("config", "user.name", "Runtime Test", cwd=source)
    (source / "version.txt").write_text("one", encoding="utf-8")
    run_git("add", ".", cwd=source)
    run_git("commit", "-m", "version one", cwd=source)

    runtime_dir = tmp_path / "runtime-private"
    subprocess.run(
        [
            "bash",
            str(SYNC_SCRIPT),
            "--runtime-dir",
            str(runtime_dir),
            "--repo-url",
            str(source),
            "--required",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    (runtime_dir / "local-only.json").write_text("local", encoding="utf-8")
    (source / "version.txt").write_text("two", encoding="utf-8")
    run_git("add", ".", cwd=source)
    run_git("commit", "-m", "version two", cwd=source)

    subprocess.run(
        [
            "bash",
            str(SYNC_SCRIPT),
            "--runtime-dir",
            str(runtime_dir),
            "--repo-url",
            str(source),
            "--required",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert (runtime_dir / "version.txt").read_text(encoding="utf-8") == "two"
    assert (runtime_dir / "local-only.json").read_text(encoding="utf-8") == "local"


def test_hosted_release_configures_private_runtime_before_quickstart() -> None:
    script = HOSTED_WEB_SCRIPT.read_text(encoding="utf-8")
    main_body = script.split("main() {", 1)[1]
    configure_index = main_body.index(
        'set_env_kv "$env_file" FACULTY_TWIN_RUNTIME_REPO_URL'
    )
    quickstart_index = main_body.index('./quickstart.sh "${quickstart_args[@]}"')

    assert configure_index < quickstart_index
    assert "Qixin-Gaoke/sage-faculty-twin-runtime-private.git" in script
