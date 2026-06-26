from pathlib import Path
import subprocess

from sage_faculty_twin.code_workbench import CodeWorkbench
from sage_faculty_twin.config import settings
from sage_faculty_twin.models import (
    CodeAssistRequest,
    CodeCommandRequest,
    CodeContextRequest,
    CodeDirectoryListRequest,
    CodeFileReadRequest,
    CodeGitDiffRequest,
    CodeGitStatusRequest,
    CodeSearchRequest,
)


def _workbench(tmp_path: Path) -> CodeWorkbench:
    workspace = tmp_path / "project-a"
    workspace.mkdir(parents=True)
    return CodeWorkbench(
        settings.model_copy(
            update={
                "deployment_mode": "local_code",
                "code_workspace_roots": str(workspace),
                "code_command_timeout_seconds": 5,
            }
        )
    )


def test_code_workbench_lists_only_local_code_explicit_workspaces(tmp_path: Path) -> None:
    workbench = _workbench(tmp_path)

    response = workbench.list_workspaces()
    workspace_ids = {workspace.workspace_id for workspace in response.workspaces}

    assert workspace_ids == {"project-a"}


def test_code_workbench_hosted_mode_exposes_no_workspaces(tmp_path: Path) -> None:
    workspace = tmp_path / "project-a"
    workspace.mkdir()
    workbench = CodeWorkbench(
        settings.model_copy(
            update={
                "deployment_mode": "hosted",
                "code_workspace_roots": str(workspace),
                "code_workbench_enabled": True,
            }
        )
    )

    response = workbench.list_workspaces()

    assert response.workspaces == []


def test_code_workbench_legacy_managed_root_ignores_symlink_escapes(tmp_path: Path) -> None:
    managed_root = tmp_path / "code-workspaces"
    managed_root.mkdir()
    (managed_root / "project-a").mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (managed_root / "outside-link").symlink_to(outside, target_is_directory=True)

    workbench = CodeWorkbench(
        settings.model_copy(
            update={
                "deployment_mode": "local_code",
                "code_workspace_root": managed_root,
            }
        )
    )

    response = workbench.list_workspaces()
    workspace_ids = {workspace.workspace_id for workspace in response.workspaces}

    assert workspace_ids == {"project-a"}


def test_code_workbench_searches_and_reads_files(tmp_path: Path) -> None:
    workbench = _workbench(tmp_path)
    workspace_root = tmp_path / "project-a"
    source = workspace_root / "src" / "demo.py"
    source.parent.mkdir()
    source.write_text("def hello():\n    return 'faculty twin'\n", encoding="utf-8")

    search_response = workbench.search(
        CodeSearchRequest(workspace_id="project-a", query="faculty twin")
    )
    read_response = workbench.read_file(
        CodeFileReadRequest(workspace_id="project-a", path="src/demo.py", max_lines=1)
    )

    assert search_response.hits[0].path == "src/demo.py"
    assert search_response.hits[0].line_number == 2
    assert read_response.content == "def hello():"
    assert read_response.truncated is True


def test_code_workbench_lists_directory_entries(tmp_path: Path) -> None:
    workbench = _workbench(tmp_path)
    workspace_root = tmp_path / "project-a"
    (workspace_root / "src").mkdir()
    (workspace_root / "README.md").write_text("# Demo\n", encoding="utf-8")

    response = workbench.list_directory(
        CodeDirectoryListRequest(workspace_id="project-a", path=".")
    )

    entries = {entry.path: entry for entry in response.entries}
    assert entries["src"].kind == "directory"
    assert entries["README.md"].kind == "file"
    assert entries["README.md"].size_bytes == 7


def test_code_workbench_blocks_path_escape_and_dangerous_commands(tmp_path: Path) -> None:
    workbench = _workbench(tmp_path)

    try:
        workbench.read_file(CodeFileReadRequest(workspace_id="project-a", path="../secret.txt"))
    except ValueError as exc:
        assert "escapes" in str(exc)
    else:
        raise AssertionError("path escape should fail")

    try:
        workbench.list_directory(
            CodeDirectoryListRequest(workspace_id="project-a", path="../")
        )
    except ValueError as exc:
        assert "escapes" in str(exc)
    else:
        raise AssertionError("directory path escape should fail")

    response = workbench.run_command(
        CodeCommandRequest(workspace_id="project-a", command="rm -rf .")
    )

    assert response.blocked is True
    assert response.exit_code == 126


def test_code_workbench_runs_read_only_allowlisted_command(tmp_path: Path) -> None:
    workbench = _workbench(tmp_path)
    (tmp_path / "project-a" / "README.md").write_text(
        "# Demo\n",
        encoding="utf-8",
    )

    response = workbench.run_command(
        CodeCommandRequest(workspace_id="project-a", command="rg Demo README.md")
    )

    assert response.blocked is False
    assert response.exit_code == 0
    assert "# Demo" in response.stdout


def test_code_workbench_reports_git_status_and_diff(tmp_path: Path) -> None:
    workbench = _workbench(tmp_path)
    workspace_root = tmp_path / "project-a"
    subprocess.run(["git", "init"], cwd=workspace_root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=workspace_root,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=workspace_root,
        check=True,
    )
    readme = workspace_root / "README.md"
    readme.write_text("# Demo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=workspace_root, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=workspace_root, check=True)
    readme.write_text("# Demo\nchanged\n", encoding="utf-8")

    status = workbench.git_status(CodeGitStatusRequest(workspace_id="project-a"))
    diff = workbench.git_diff(CodeGitDiffRequest(workspace_id="project-a", path="README.md"))

    assert status.is_git_repo is True
    assert status.clean is False
    assert "README.md" in status.porcelain
    assert "+changed" in diff.diff


def test_code_workbench_builds_context_pack(tmp_path: Path) -> None:
    workbench = _workbench(tmp_path)
    (tmp_path / "project-a" / "README.md").write_text(
        "# Demo\nContext pack\n",
        encoding="utf-8",
    )

    response = workbench.build_context(
        CodeContextRequest(workspace_id="project-a", paths=["README.md"])
    )

    assert "Workspace" in response.context
    assert "Git Status" in response.context
    assert "Context pack" in response.context
    assert response.context_paths == ["README.md"]


def test_code_workbench_builds_assist_prompt_with_file_context(tmp_path: Path) -> None:
    workbench = _workbench(tmp_path)
    (tmp_path / "project-a" / "README.md").write_text(
        "# Demo\nCodex-like helper\n",
        encoding="utf-8",
    )

    system_prompt, user_prompt, context_paths = workbench.build_assist_prompt(
        CodeAssistRequest(
            workspace_id="project-a",
            task="How should I extend this repo?",
            paths=["README.md"],
        )
    )

    assert "Codex/Copilot-like" in system_prompt
    assert "README.md" in context_paths
    assert "Git Status" in user_prompt
    assert "Codex-like helper" in user_prompt


def test_code_workbench_parses_chat_commands(tmp_path: Path) -> None:
    workbench = _workbench(tmp_path)

    search = workbench.parse_chat_command("/code search twin CodeWorkbench --glob '*.py'")
    listing = workbench.parse_chat_command("/code ls twin src")
    read = workbench.parse_chat_command("/code read twin src/app.py 10 30")
    status = workbench.parse_chat_command("/code status twin")
    diff = workbench.parse_chat_command("/code diff twin src/app.py --staged")
    context = workbench.parse_chat_command("/code context twin README.md src/app.py")
    run = workbench.parse_chat_command("/code run twin rg CodeWorkbench src")
    ask = workbench.parse_chat_command("/code ask twin explain this -- src/a.py src/b.py")
    chinese = workbench.parse_chat_command("代码 搜 twin 工作台")

    assert workbench.is_chat_command("/code workspaces") is True
    assert search.action == "search"
    assert search.query == "CodeWorkbench"
    assert search.glob == "*.py"
    assert listing.action == "list"
    assert listing.path == "src"
    assert read.start_line == 10
    assert read.max_lines == 30
    assert status.action == "status"
    assert diff.action == "diff"
    assert diff.path == "src/app.py"
    assert diff.staged is True
    assert context.action == "context"
    assert context.paths == ["README.md", "src/app.py"]
    assert run.command == "rg CodeWorkbench src"
    assert ask.action == "ask"
    assert ask.task == "explain this"
    assert ask.paths == ["src/a.py", "src/b.py"]
    assert chinese.action == "search"
    assert chinese.query == "工作台"
