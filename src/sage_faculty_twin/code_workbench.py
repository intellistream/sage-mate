from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .config import AppSettings
from .models import (
    CodeAssistRequest,
    CodeCommandRequest,
    CodeCommandResponse,
    CodeContextRequest,
    CodeContextResponse,
    CodeDirectoryEntry,
    CodeDirectoryListRequest,
    CodeDirectoryListResponse,
    CodeFileReadRequest,
    CodeFileReadResponse,
    CodeGitDiffRequest,
    CodeGitDiffResponse,
    CodeGitStatusRequest,
    CodeGitStatusResponse,
    CodeProposeRequest,
    CodeProposeResponse,
    CodeSearchHit,
    CodeSearchRequest,
    CodeSearchResponse,
    CodeWorkspaceListResponse,
    CodeWorkspaceSummary,
)


_MAX_COMMAND_OUTPUT_CHARS = 20000
_MAX_COMMAND_ERROR_CHARS = 12000
_TEXT_FILE_MAX_BYTES = 1_000_000
_SHELL_META_CHARS = set("|&;<>`$\\\n")
CODE_WORKBENCH_PROFILES = {"code_assistant", "auto_scientist"}
_ALLOWED_EXECUTABLES = {
    "bun",
    "cat",
    "find",
    "git",
    "head",
    "ls",
    "node",
    "npm",
    "pnpm",
    "pwd",
    "pytest",
    "python",
    "python3",
    "rg",
    "sed",
    "tail",
    "wc",
}
_BLOCKED_WORDS = {
    "chmod",
    "chown",
    "curl",
    "dd",
    "docker",
    "kill",
    "mkfs",
    "mount",
    "reboot",
    "rm",
    "shutdown",
    "sudo",
    "systemctl",
    "umount",
    "wget",
}
_WRITE_INTENT_WORDS = {
    "add",
    "apply",
    "checkout",
    "clean",
    "commit",
    "install",
    "merge",
    "mv",
    "pull",
    "push",
    "rebase",
    "reset",
    "restore",
    "switch",
    "touch",
}
_DEFAULT_CONTEXT_FILENAMES = (
    "README.md",
    "readme.md",
    "pyproject.toml",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "requirements.txt",
)
_DEFAULT_CONTEXT_SUFFIXES = {
    ".css",
    ".go",
    ".html",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".py",
    ".rs",
    ".ts",
    ".tsx",
}
_DEFAULT_CONTEXT_SKIP_DIRS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "vendor",
}


@dataclass(frozen=True, slots=True)
class CodeWorkspace:
    workspace_id: str
    label: str
    root: Path


@dataclass(frozen=True, slots=True)
class CodeChatCommand:
    action: str
    workspace_id: str = ""
    query: str = ""
    glob: str | None = None
    path: str = ""
    start_line: int = 1
    max_lines: int = 200
    command: str = ""
    task: str = ""
    paths: list[str] = field(default_factory=list)
    staged: bool = False


class CodeWorkbench:
    """Local-code workbench for user-installed Faculty Twin deployments."""

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._workspaces = self._discover_workspaces()

    def list_workspaces(self) -> CodeWorkspaceListResponse:
        return CodeWorkspaceListResponse(
            workspaces=[
                CodeWorkspaceSummary(
                    workspace_id=workspace.workspace_id,
                    label=workspace.label,
                    root=str(workspace.root),
                    exists=workspace.root.exists(),
                )
                for workspace in self._workspaces
            ]
        )

    def search(self, request: CodeSearchRequest) -> CodeSearchResponse:
        workspace = self._get_workspace(request.workspace_id)
        command = [
            "rg",
            "--line-number",
            "--no-heading",
            "--color",
            "never",
            "--max-count",
            str(request.max_results + 1),
        ]
        if request.glob:
            command.extend(["--glob", request.glob])
        command.append(request.query)

        completed = subprocess.run(
            command,
            cwd=workspace.root,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
        if completed.returncode not in (0, 1):
            raise ValueError((completed.stderr or "Code search failed.").strip()[:512])

        hits: list[CodeSearchHit] = []
        for line in completed.stdout.splitlines():
            if len(hits) >= request.max_results:
                break
            path, line_number, preview = self._parse_rg_line(line)
            if not path:
                continue
            hits.append(
                CodeSearchHit(
                    path=path,
                    line_number=line_number,
                    preview=preview[:1000],
                )
            )
        return CodeSearchResponse(
            workspace_id=workspace.workspace_id,
            query=request.query,
            hits=hits,
            truncated=len(completed.stdout.splitlines()) > request.max_results,
        )

    def read_file(self, request: CodeFileReadRequest) -> CodeFileReadResponse:
        workspace = self._get_workspace(request.workspace_id)
        path = self._resolve_path(workspace, request.path)
        if not path.is_file():
            raise ValueError(f"Not a readable file: {request.path}")
        if path.stat().st_size > _TEXT_FILE_MAX_BYTES:
            raise ValueError("File is too large for the code workbench preview.")

        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        start_index = request.start_line - 1
        selected = lines[start_index : start_index + request.max_lines]
        end_line = (
            request.start_line + len(selected) - 1
            if selected
            else request.start_line - 1
        )
        return CodeFileReadResponse(
            workspace_id=workspace.workspace_id,
            path=str(path.relative_to(workspace.root)),
            start_line=request.start_line,
            end_line=end_line,
            content="\n".join(selected),
            truncated=start_index + request.max_lines < len(lines),
        )

    def list_directory(self, request: CodeDirectoryListRequest) -> CodeDirectoryListResponse:
        workspace = self._get_workspace(request.workspace_id)
        path = self._resolve_path(workspace, request.path)
        if not path.is_dir():
            raise ValueError(f"Not a directory: {request.path}")

        entries: list[CodeDirectoryEntry] = []
        children = sorted(
            path.iterdir(),
            key=lambda child: (not child.is_dir(), child.name.lower()),
        )
        for child in children[: request.max_entries]:
            stat = child.lstat()
            if child.is_symlink():
                kind = "symlink"
                size_bytes = None
            elif child.is_dir():
                kind = "directory"
                size_bytes = None
            elif child.is_file():
                kind = "file"
                size_bytes = stat.st_size
            else:
                kind = "other"
                size_bytes = None
            entries.append(
                CodeDirectoryEntry(
                    path=str(child.relative_to(workspace.root)),
                    name=child.name,
                    kind=kind,
                    size_bytes=size_bytes,
                    modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                    hidden=child.name.startswith("."),
                )
            )
        return CodeDirectoryListResponse(
            workspace_id=workspace.workspace_id,
            path=str(path.relative_to(workspace.root)) or ".",
            entries=entries,
            truncated=len(children) > request.max_entries,
        )

    def git_status(self, request: CodeGitStatusRequest) -> CodeGitStatusResponse:
        workspace = self._get_workspace(request.workspace_id)
        if not (workspace.root / ".git").exists():
            return CodeGitStatusResponse(
                workspace_id=workspace.workspace_id,
                is_git_repo=False,
                message="Workspace is not a git repository.",
            )

        branch = self._run_git_text(workspace, ["rev-parse", "--abbrev-ref", "HEAD"])
        status = self._run_git_text(
            workspace,
            ["status", "--porcelain=v1", "--branch"],
            max_chars=20000,
        )
        return CodeGitStatusResponse(
            workspace_id=workspace.workspace_id,
            is_git_repo=True,
            branch=branch.strip(),
            clean=not any(line and not line.startswith("##") for line in status.splitlines()),
            porcelain=status.strip(),
            message="Git status collected.",
        )

    def git_diff(self, request: CodeGitDiffRequest) -> CodeGitDiffResponse:
        workspace = self._get_workspace(request.workspace_id)
        if not (workspace.root / ".git").exists():
            return CodeGitDiffResponse(
                workspace_id=workspace.workspace_id,
                path=request.path,
                staged=request.staged,
                message="Workspace is not a git repository.",
            )

        command = ["diff", "--no-color"]
        if request.staged:
            command.append("--staged")
        command.append("--")
        if request.path:
            path = self._resolve_path(workspace, request.path)
            command.append(str(path.relative_to(workspace.root)))
        diff = self._run_git_text(workspace, command, max_chars=request.max_chars + 1)
        truncated = len(diff) > request.max_chars
        return CodeGitDiffResponse(
            workspace_id=workspace.workspace_id,
            path=request.path,
            staged=request.staged,
            diff=diff[: request.max_chars],
            truncated=truncated,
            message="Git diff collected." if diff else "No diff.",
        )

    def build_context(self, request: CodeContextRequest) -> CodeContextResponse:
        workspace = self._get_workspace(request.workspace_id)
        blocks: list[str] = [f"# Workspace\n{workspace.label} ({workspace.root})"]
        context_paths: list[str] = []
        remaining = request.max_context_chars - len(blocks[0])
        truncated = False

        if request.include_git_status and remaining > 0:
            status = self.git_status(CodeGitStatusRequest(workspace_id=workspace.workspace_id))
            git_block = (
                "# Git Status\n"
                f"branch: {status.branch or '(unknown)'}\n"
                f"clean: {status.clean}\n"
                f"{status.porcelain or status.message}"
            )
            blocks.append(git_block[:remaining])
            truncated = truncated or len(git_block) > remaining
            remaining -= len(blocks[-1])

        paths = request.paths or self._default_context_paths(workspace)
        if not request.paths and remaining > 0:
            overview = self._workspace_overview(workspace)
            blocks.append(overview[:remaining])
            truncated = truncated or len(overview) > remaining
            remaining -= len(blocks[-1])

        for raw_path in paths:
            if remaining <= 0:
                truncated = True
                break
            file_response = self.read_file(
                CodeFileReadRequest(
                    workspace_id=workspace.workspace_id,
                    path=raw_path,
                    max_lines=800,
                )
            )
            block = f"# File: {file_response.path}\n```\n{file_response.content}\n```"
            blocks.append(block[:remaining])
            context_paths.append(file_response.path)
            truncated = truncated or file_response.truncated or len(block) > remaining
            remaining -= len(blocks[-1])

        return CodeContextResponse(
            workspace_id=workspace.workspace_id,
            context="\n\n".join(blocks),
            context_paths=context_paths,
            truncated=truncated,
        )

    def _workspace_overview(self, workspace: CodeWorkspace) -> str:
        entries = self.list_directory(
            CodeDirectoryListRequest(
                workspace_id=workspace.workspace_id,
                path=".",
                max_entries=80,
            )
        )
        lines = ["# Workspace Overview"]
        for entry in entries.entries:
            marker = "/" if entry.kind == "directory" else ""
            lines.append(f"- {entry.path}{marker} ({entry.kind})")
        if entries.truncated:
            lines.append("- ...")
        return "\n".join(lines)

    def _default_context_paths(self, workspace: CodeWorkspace) -> list[str]:
        candidates: list[str] = []
        seen_files: set[tuple[int, int]] = set()
        for filename in _DEFAULT_CONTEXT_FILENAMES:
            candidate_path = workspace.root / filename
            if candidate_path.is_file():
                stat = candidate_path.stat()
                identity = (stat.st_dev, stat.st_ino)
                if identity in seen_files:
                    continue
                candidates.append(filename)
                seen_files.add(identity)

        for path in sorted(workspace.root.rglob("*")):
            if len(candidates) >= 8:
                break
            if not path.is_file():
                continue
            stat = path.stat()
            identity = (stat.st_dev, stat.st_ino)
            if identity in seen_files:
                continue
            relative = path.relative_to(workspace.root)
            parts = set(relative.parts[:-1])
            if parts & _DEFAULT_CONTEXT_SKIP_DIRS:
                continue
            rel_text = relative.as_posix()
            if rel_text in candidates:
                continue
            if path.suffix.lower() not in _DEFAULT_CONTEXT_SUFFIXES:
                continue
            if path.stat().st_size > 120_000:
                continue
            candidates.append(rel_text)
            seen_files.add(identity)
        return candidates[:8]

    def run_command(self, request: CodeCommandRequest) -> CodeCommandResponse:
        workspace = self._get_workspace(request.workspace_id)
        started_at = time.perf_counter()
        blocked_message = self._validate_command(
            request.command,
            allow_write=request.allow_write,
        )
        if blocked_message:
            return CodeCommandResponse(
                workspace_id=workspace.workspace_id,
                command=request.command,
                exit_code=126,
                duration_ms=0,
                blocked=True,
                message=blocked_message,
            )

        timeout = request.timeout_seconds or self._settings.code_command_timeout_seconds
        try:
            completed = subprocess.run(
                shlex.split(request.command),
                cwd=workspace.root,
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
            duration_ms = int((time.perf_counter() - started_at) * 1000)
            return CodeCommandResponse(
                workspace_id=workspace.workspace_id,
                command=request.command,
                exit_code=completed.returncode,
                stdout=completed.stdout[-_MAX_COMMAND_OUTPUT_CHARS:],
                stderr=completed.stderr[-_MAX_COMMAND_ERROR_CHARS:],
                duration_ms=duration_ms,
                message="Command completed.",
            )
        except subprocess.TimeoutExpired as exc:
            duration_ms = int((time.perf_counter() - started_at) * 1000)
            stdout = exc.stdout if isinstance(exc.stdout, str) else ""
            stderr = exc.stderr if isinstance(exc.stderr, str) else ""
            return CodeCommandResponse(
                workspace_id=workspace.workspace_id,
                command=request.command,
                exit_code=124,
                stdout=stdout[-_MAX_COMMAND_OUTPUT_CHARS:],
                stderr=stderr[-_MAX_COMMAND_ERROR_CHARS:],
                duration_ms=duration_ms,
                timed_out=True,
                message=f"Command timed out after {timeout}s.",
            )

    def build_assist_prompt(
        self,
        request: CodeAssistRequest,
    ) -> tuple[str, str, list[str]]:
        workspace = self._get_workspace(request.workspace_id)
        context = self.build_context(
            CodeContextRequest(
                workspace_id=workspace.workspace_id,
                paths=request.paths,
                include_git_status=True,
                max_context_chars=request.max_context_chars,
            )
        )

        system_prompt = (
            "You are the code workbench inside SAGE Faculty Twin. Help the admin "
            "reason about local repositories with a code-agent style. Be "
            "concrete, cite file paths from the provided context, and do not claim "
            "that you edited files or executed commands unless the prompt explicitly "
            "includes such output."
        )
        user_prompt = (
            f"Workspace: {workspace.label} ({workspace.root})\n\n"
            f"Task:\n{request.task}\n\n"
            f"Context:\n{context.context or '(no files attached)'}"
        )
        return system_prompt, user_prompt, context.context_paths

    def build_propose_prompt(
        self,
        request: CodeProposeRequest,
    ) -> tuple[str, str, list[str]]:
        workspace = self._get_workspace(request.workspace_id)
        status = self.git_status(CodeGitStatusRequest(workspace_id=workspace.workspace_id))
        diff = self.git_diff(
            CodeGitDiffRequest(
                workspace_id=workspace.workspace_id,
                max_chars=min(30000, request.max_context_chars),
            )
        )
        context = self.build_context(
            CodeContextRequest(
                workspace_id=workspace.workspace_id,
                paths=request.paths,
                include_git_status=False,
                max_context_chars=request.max_context_chars,
            )
        )

        system_prompt = (
            "You are the propose-only local code workbench inside SAGE Faculty Twin. "
            "Generate reviewable code-change proposals as unified diffs, but never "
            "claim that files were edited, saved, applied, committed, or tested. "
            "Return one JSON object with exactly these keys: summary, affected_files, "
            "unified_diff, risks, suggested_tests. affected_files and suggested_tests "
            "must be arrays of strings; unified_diff must be a single string in unified "
            "diff format. If the task is unsafe or lacks enough context, explain that "
            "in risks and keep unified_diff empty."
        )
        user_prompt = (
            f"Workspace: {workspace.label} ({workspace.root})\n\n"
            f"Task:\n{request.task}\n\n"
            "# Git Status\n"
            f"branch: {status.branch or '(unknown)'}\n"
            f"clean: {status.clean}\n"
            f"{status.porcelain or status.message}\n\n"
            "# Git Diff\n"
            f"{diff.diff or diff.message or '(empty)'}\n\n"
            "# File Context\n"
            f"{context.context or '(no files attached)'}\n\n"
            "Produce only a propose-only response. Do not include instructions that "
            "would require writing files on behalf of the user."
        )
        return system_prompt, user_prompt, context.context_paths

    def workspace_root(self, workspace_id: str) -> Path:
        return self._get_workspace(workspace_id).root

    def copy_workspace_to_temp(self, workspace_id: str) -> tempfile.TemporaryDirectory[str]:
        workspace = self._get_workspace(workspace_id)
        temp_dir = tempfile.TemporaryDirectory(prefix=f"sage-mate-{workspace.workspace_id}-")
        destination = Path(temp_dir.name) / workspace.root.name

        def ignore(_dir: str, names: list[str]) -> set[str]:
            ignored = {
                ".git",
                ".hg",
                ".mypy_cache",
                ".pytest_cache",
                ".ruff_cache",
                ".venv",
                "__pycache__",
                "build",
                "dist",
                "node_modules",
                "vendor",
            }
            return {name for name in names if name in ignored}

        shutil.copytree(workspace.root, destination, ignore=ignore, symlinks=False)
        return temp_dir

    def is_chat_command(self, text: str) -> bool:
        stripped = text.strip()
        return stripped == "/code" or stripped.startswith("/code ") or stripped.startswith("代码 ")

    def parse_chat_command(self, text: str) -> CodeChatCommand:
        stripped = text.strip()
        if stripped == "/code":
            return CodeChatCommand(action="help")
        if stripped.startswith("/code "):
            body = stripped[len("/code ") :].strip()
        elif stripped.startswith("代码 "):
            body = stripped[len("代码 ") :].strip()
        else:
            raise ValueError("Not a code workbench command.")

        if not body or body in {"help", "帮助", "?"}:
            return CodeChatCommand(action="help")

        argv = shlex.split(body)
        if not argv:
            return CodeChatCommand(action="help")
        action = self._normalize_action(argv[0])
        if action == "workspaces":
            return CodeChatCommand(action=action)
        if action == "doctor":
            return CodeChatCommand(action=action)
        if action == "list":
            if len(argv) < 2:
                raise ValueError("Usage: /code ls <workspace> [path]")
            return CodeChatCommand(
                action=action,
                workspace_id=argv[1],
                path=argv[2] if len(argv) >= 3 else ".",
            )
        if action == "search":
            if len(argv) < 3:
                raise ValueError("Usage: /code search <workspace> <query> [--glob <pattern>]")
            glob = None
            terms: list[str] = []
            index = 2
            while index < len(argv):
                if argv[index] == "--glob" and index + 1 < len(argv):
                    glob = argv[index + 1]
                    index += 2
                    continue
                terms.append(argv[index])
                index += 1
            query = " ".join(terms).strip()
            if not query:
                raise ValueError("Search query is empty.")
            return CodeChatCommand(
                action=action,
                workspace_id=argv[1],
                query=query,
                glob=glob,
            )
        if action == "read":
            if len(argv) < 3:
                raise ValueError("Usage: /code read <workspace> <path> [start_line] [max_lines]")
            start_line = int(argv[3]) if len(argv) >= 4 else 1
            max_lines = int(argv[4]) if len(argv) >= 5 else 200
            return CodeChatCommand(
                action=action,
                workspace_id=argv[1],
                path=argv[2],
                start_line=start_line,
                max_lines=max_lines,
            )
        if action == "run":
            if len(argv) < 3:
                raise ValueError("Usage: /code run <workspace> <read-only command>")
            return CodeChatCommand(
                action=action,
                workspace_id=argv[1],
                command=" ".join(argv[2:]),
            )
        if action == "status":
            if len(argv) < 2:
                raise ValueError("Usage: /code status <workspace>")
            return CodeChatCommand(action=action, workspace_id=argv[1])
        if action == "diff":
            if len(argv) < 2:
                raise ValueError("Usage: /code diff <workspace> [path] [--staged]")
            staged = "--staged" in argv[2:]
            paths = [part for part in argv[2:] if part != "--staged"]
            return CodeChatCommand(
                action=action,
                workspace_id=argv[1],
                path=paths[0] if paths else "",
                staged=staged,
            )
        if action == "context":
            if len(argv) < 2:
                raise ValueError("Usage: /code context <workspace> [path] ...")
            return CodeChatCommand(action=action, workspace_id=argv[1], paths=argv[2:])
        if action == "ask":
            if len(argv) < 3:
                raise ValueError("Usage: /code ask <workspace> <task> [-- <path> ...]")
            path_separator = argv.index("--") if "--" in argv else len(argv)
            task = " ".join(argv[2:path_separator]).strip()
            paths = argv[path_separator + 1 :] if path_separator < len(argv) else []
            if not task:
                raise ValueError("Code assist task is empty.")
            return CodeChatCommand(
                action=action,
                workspace_id=argv[1],
                task=task,
                paths=paths,
            )
        if action == "propose":
            if len(argv) < 3:
                raise ValueError("Usage: /code propose <workspace> <task> [-- <path> ...]")
            path_separator = argv.index("--") if "--" in argv else len(argv)
            task = " ".join(argv[2:path_separator]).strip()
            paths = argv[path_separator + 1 :] if path_separator < len(argv) else []
            if not task:
                raise ValueError("Code propose task is empty.")
            return CodeChatCommand(
                action=action,
                workspace_id=argv[1],
                task=task,
                paths=paths,
            )
        raise ValueError(f"Unknown /code action: {argv[0]}")

    def format_chat_help(self) -> str:
        return "\n".join(
            [
                "代码工作台可用命令：",
                "`/code doctor` 检查本地代码工作台配置",
                "`/code workspaces` 列出可用仓库",
                "`/code ls <workspace> [path]` 浏览目录",
                "`/code search <workspace> <query> [--glob <pattern>]` 搜索代码",
                "`/code read <workspace> <path> [start_line] [max_lines]` 读取文件片段",
                "`/code status <workspace>` 查看 git 状态",
                "`/code diff <workspace> [path] [--staged]` 查看 git diff",
                "`/code context <workspace> [path] ...` 打包状态和文件上下文",
                "`/code run <workspace> <read-only command>` 执行受限只读命令",
                "`/code ask <workspace> <task> [-- <path> ...]` 让模型基于文件上下文分析",
                "`/code propose <workspace> <task> [-- <path> ...]` 生成 propose-only unified diff 建议",
            ]
        )

    def format_doctor_for_chat(self) -> str:
        rows: list[tuple[str, str, str]] = []

        def add(status: str, item: str, detail: str) -> None:
            rows.append((status, item, detail))

        deployment_mode = self._settings.deployment_mode
        if deployment_mode == "local_code":
            add("OK", "DIGITAL_TWIN_DEPLOYMENT_MODE", "local_code")
        else:
            add(
                "ERROR",
                "DIGITAL_TWIN_DEPLOYMENT_MODE",
                f"当前为 {deployment_mode or '(empty)'}，本地代码能力只允许 local_code。",
            )

        app_profile = self._settings.app_profile
        if app_profile in CODE_WORKBENCH_PROFILES:
            add("OK", "DIGITAL_TWIN_APP_PROFILE", app_profile)
        else:
            add(
                "ERROR",
                "DIGITAL_TWIN_APP_PROFILE",
                f"当前为 {app_profile or '(empty)'}，需要 code_assistant 或 auto_scientist。",
            )

        if self._settings.code_workbench_enabled:
            add("OK", "DIGITAL_TWIN_CODE_WORKBENCH_ENABLED", "true")
        else:
            add("ERROR", "DIGITAL_TWIN_CODE_WORKBENCH_ENABLED", "需要设置为 true。")

        configured_roots = [
            Path(part.strip()).expanduser()
            for part in self._settings.code_workspace_roots.split(",")
            if part.strip()
        ]
        discovered_workspaces = self.list_workspaces().workspaces
        if discovered_workspaces:
            workspace_labels = ", ".join(
                f"{workspace.workspace_id}={workspace.root}"
                for workspace in discovered_workspaces[:5]
            )
            suffix = " ..." if len(discovered_workspaces) > 5 else ""
            add(
                "OK",
                "workspace allowlist",
                f"{len(discovered_workspaces)} 个可用 workspace："
                f"{workspace_labels}{suffix}",
            )
        elif configured_roots:
            invalid = ", ".join(str(root) for root in configured_roots[:5])
            add("ERROR", "workspace allowlist", f"已配置但没有可用目录：{invalid}")
        else:
            add("ERROR", "workspace allowlist", "未配置 DIGITAL_TWIN_CODE_WORKSPACE_ROOTS。")

        backend = self._settings.code_agent_backend
        if backend in {"internal", "claude_hust"}:
            add("OK", "DIGITAL_TWIN_CODE_AGENT_BACKEND", backend)
        else:
            add(
                "ERROR",
                "DIGITAL_TWIN_CODE_AGENT_BACKEND",
                f"不支持的 backend：{backend or '(empty)'}",
            )

        claude_hust_path = self._settings.claude_hust_cli_path.strip()
        if claude_hust_path:
            executable_path = Path(claude_hust_path).expanduser()
            if executable_path.is_file() and os.access(executable_path, os.X_OK):
                add("OK", "DIGITAL_TWIN_CLAUDE_HUST_CLI_PATH", str(executable_path))
            elif executable_path.exists():
                add(
                    "ERROR",
                    "DIGITAL_TWIN_CLAUDE_HUST_CLI_PATH",
                    f"{executable_path} 存在但不可执行。",
                )
            else:
                add(
                    "ERROR",
                    "DIGITAL_TWIN_CLAUDE_HUST_CLI_PATH",
                    f"{executable_path} 不存在。",
                )
        elif backend == "claude_hust":
            add(
                "ERROR",
                "DIGITAL_TWIN_CLAUDE_HUST_CLI_PATH",
                "backend=claude_hust 时必须配置可执行 CLI。",
            )
        else:
            add(
                "WARN",
                "DIGITAL_TWIN_CLAUDE_HUST_CLI_PATH",
                "未配置；当前 backend=internal，不需要 Claude Hust CLI。",
            )

        llm_base_url = self._settings.llm_base_url.strip()
        if llm_base_url:
            add("OK", "DIGITAL_TWIN_LLM_BASE_URL", llm_base_url)
        else:
            add("ERROR", "DIGITAL_TWIN_LLM_BASE_URL", "未配置。")

        model_name = self._settings.model_name.strip()
        if model_name:
            add("OK", "DIGITAL_TWIN_MODEL_NAME", model_name)
        else:
            add("ERROR", "DIGITAL_TWIN_MODEL_NAME", "未配置。")

        has_error = any(status == "ERROR" for status, _, _ in rows)
        has_warn = any(status == "WARN" for status, _, _ in rows)
        summary = "ERROR" if has_error else "WARN" if has_warn else "OK"
        lines = [
            "代码工作台诊断报告",
            f"总体状态：{summary}",
            "",
        ]
        lines.extend(f"[{status}] {item}：{detail}" for status, item, detail in rows)
        lines.extend(
            [
                "",
                "安全边界：`/code doctor` 只在 local_code + code_assistant/auto_scientist + "
                "code_workbench_enabled 下由聊天入口处理；hosted/web 模式不会暴露"
                "本地代码 workspace 或 agent 能力。",
            ]
        )
        return "\n".join(lines)

    def format_workspaces_for_chat(self) -> str:
        response = self.list_workspaces()
        if not response.workspaces:
            return (
                "还没有配置可用代码 workspace。\n\n"
                "请打开 Sage Mate 设置，在 Workspace Folders 里添加一个本地项目目录，"
                "保存后再运行 `/code workspaces`。\n\n"
                "演示时可以使用安全示例目录："
                "`~/tmp/faculty-twin-demo-project`"
            )
        lines = ["可用代码 workspace："]
        for workspace in response.workspaces:
            state = "存在" if workspace.exists else "不存在"
            lines.append(
                f"- `{workspace.workspace_id}`：{workspace.label}，{workspace.root}（{state}）"
            )
        return "\n".join(lines)

    def format_search_for_chat(self, response: CodeSearchResponse) -> str:
        if not response.hits:
            return f"`{response.workspace_id}` 中没有搜到 `{response.query}`。"
        lines = [f"`{response.workspace_id}` 搜索 `{response.query}`："]
        for hit in response.hits[:20]:
            lines.append(f"- `{hit.path}:{hit.line_number}` {hit.preview}")
        if response.truncated:
            lines.append("结果已截断，可缩小 query 或加 `--glob`。")
        return "\n".join(lines)

    def format_file_for_chat(self, response: CodeFileReadResponse) -> str:
        suffix = "（已截断）" if response.truncated else ""
        return (
            f"`{response.path}:{response.start_line}-{response.end_line}`{suffix}\n\n"
            f"```text\n{response.content}\n```"
        )

    def format_directory_for_chat(self, response: CodeDirectoryListResponse) -> str:
        if not response.entries:
            return f"`{response.workspace_id}/{response.path}` 是空目录。"
        lines = [f"`{response.workspace_id}/{response.path}`："]
        for entry in response.entries[:80]:
            marker = "/" if entry.kind == "directory" else "@" if entry.kind == "symlink" else ""
            size = f" {entry.size_bytes}B" if entry.size_bytes is not None else ""
            lines.append(f"- `{entry.path}{marker}` {entry.kind}{size}")
        if response.truncated:
            lines.append("目录结果已截断。")
        return "\n".join(lines)

    def format_git_status_for_chat(self, response: CodeGitStatusResponse) -> str:
        if not response.is_git_repo:
            return response.message
        state = "clean" if response.clean else "dirty"
        body = response.porcelain or "(no changes)"
        return (
            f"`{response.workspace_id}` git status: {state}, branch `{response.branch}`\n\n"
            f"```text\n{body}\n```"
        )

    def format_git_diff_for_chat(self, response: CodeGitDiffResponse) -> str:
        suffix = "（已截断）" if response.truncated else ""
        scope = response.path or "workspace"
        return (
            f"`{response.workspace_id}` diff `{scope}`{suffix}: {response.message}\n\n"
            f"```diff\n{response.diff or '(empty)'}\n```"
        )

    def format_context_for_chat(self, response: CodeContextResponse) -> str:
        suffix = "（已截断）" if response.truncated else ""
        paths = ", ".join(response.context_paths) if response.context_paths else "no files"
        return f"上下文包 {suffix}，文件：{paths}\n\n```text\n{response.context}\n```"

    def format_command_for_chat(self, response: CodeCommandResponse) -> str:
        status = "blocked" if response.blocked else "timeout" if response.timed_out else "done"
        parts = [
            f"`{response.command}` -> {status}, exit={response.exit_code}, {response.duration_ms}ms"
        ]
        if response.message:
            parts.append(response.message)
        if response.stdout:
            parts.append(f"stdout:\n```text\n{response.stdout}\n```")
        if response.stderr:
            parts.append(f"stderr:\n```text\n{response.stderr}\n```")
        return "\n\n".join(parts)

    def format_propose_for_chat(self, response: CodeProposeResponse) -> str:
        affected = ", ".join(f"`{path}`" for path in response.affected_files) or "(none)"
        tests = "\n".join(f"- `{test}`" for test in response.suggested_tests) or "- (none)"
        diff = response.unified_diff or "(empty)"
        context_note = (
            "\n\n上下文：" + "、".join(f"`{path}`" for path in response.context_paths)
            if response.context_paths
            else ""
        )
        return (
            "## 摘要\n"
            f"{response.summary or '(no summary)'}\n\n"
            "## 受影响文件\n"
            f"{affected}\n\n"
            "## Unified Diff 建议\n"
            f"```diff\n{diff}\n```\n\n"
            "## 风险说明\n"
            f"{response.risks or '(none)'}\n\n"
            "## 建议运行的测试\n"
            f"{tests}"
            f"{context_note}"
        )

    def _discover_workspaces(self) -> list[CodeWorkspace]:
        if self._settings.deployment_mode != "local_code":
            return []
        if self._settings.app_profile not in CODE_WORKBENCH_PROFILES:
            return []
        if not self._settings.code_workbench_enabled:
            return []
        explicit_roots = self._discover_explicit_workspaces()
        if explicit_roots:
            return explicit_roots

        managed_root = self._settings.code_workspace_root.expanduser().resolve()
        if not managed_root.is_dir():
            return []

        workspaces: list[CodeWorkspace] = []
        seen_ids: set[str] = set()
        for child in sorted(managed_root.iterdir(), key=lambda path: path.name.lower()):
            if child.name.startswith(".") or not child.is_dir():
                continue
            resolved = child.resolve()
            try:
                resolved.relative_to(managed_root)
            except ValueError:
                continue
            workspace_id = self._workspace_id_from_name(child.name, seen_ids)
            seen_ids.add(workspace_id)
            workspaces.append(
                CodeWorkspace(workspace_id=workspace_id, label=child.name, root=resolved)
            )
        return workspaces

    def _discover_explicit_workspaces(self) -> list[CodeWorkspace]:
        roots = [
            Path(part.strip()).expanduser()
            for part in self._settings.code_workspace_roots.split(",")
            if part.strip()
        ]
        workspaces: list[CodeWorkspace] = []
        seen_ids: set[str] = set()
        seen_roots: set[Path] = set()
        for root in roots:
            resolved = root.resolve()
            if resolved in seen_roots or not resolved.is_dir():
                continue
            seen_roots.add(resolved)
            workspace_id = self._workspace_id_from_name(resolved.name, seen_ids)
            seen_ids.add(workspace_id)
            workspaces.append(
                CodeWorkspace(workspace_id=workspace_id, label=resolved.name, root=resolved)
            )
        return workspaces

    def _get_workspace(self, workspace_id: str) -> CodeWorkspace:
        for workspace in self._workspaces:
            if workspace.workspace_id == workspace_id:
                if not workspace.root.exists():
                    raise ValueError(f"Workspace does not exist: {workspace_id}")
                return workspace
        raise ValueError(f"Unknown code workspace: {workspace_id}")

    def _resolve_path(self, workspace: CodeWorkspace, raw_path: str) -> Path:
        candidate = Path(raw_path)
        if candidate.is_absolute():
            resolved = candidate.resolve()
        else:
            resolved = (workspace.root / candidate).resolve()
        try:
            resolved.relative_to(workspace.root)
        except ValueError as exc:
            raise ValueError("Path escapes the selected workspace.") from exc
        return resolved

    def _parse_rg_line(self, line: str) -> tuple[str, int, str]:
        parts = line.split(":", 2)
        if len(parts) != 3:
            return "", 0, ""
        path, line_number_text, preview = parts
        try:
            line_number = int(line_number_text)
        except ValueError:
            return "", 0, ""
        return path, line_number, preview.strip()

    def _normalize_action(self, action: str) -> str:
        aliases = {
            "workspace": "workspaces",
            "workspaces": "workspaces",
            "doctor": "doctor",
            "诊断": "doctor",
            "检查": "doctor",
            "repos": "workspaces",
            "projects": "workspaces",
            "ls": "list",
            "list": "list",
            "tree": "list",
            "dir": "list",
            "search": "search",
            "grep": "search",
            "rg": "search",
            "read": "read",
            "cat": "read",
            "file": "read",
            "run": "run",
            "exec": "run",
            "status": "status",
            "st": "status",
            "diff": "diff",
            "context": "context",
            "ctx": "context",
            "ask": "ask",
            "assist": "ask",
            "propose": "propose",
            "proposal": "propose",
            "patch": "propose",
            "问": "ask",
            "建议": "propose",
            "搜": "search",
            "读": "read",
            "跑": "run",
            "列": "list",
            "看": "list",
            "状态": "status",
            "变更": "diff",
            "上下文": "context",
        }
        return aliases.get(action.lower(), action.lower())

    def _workspace_id_from_name(self, name: str, seen_ids: set[str]) -> str:
        slug_chars = [
            char.lower() if char.isalnum() or char in {"-", "_", "."} else "-"
            for char in name.strip()
        ]
        slug = "".join(slug_chars).strip("-.") or "workspace"
        candidate = slug[:64]
        index = 2
        while candidate in seen_ids:
            suffix = f"-{index}"
            candidate = f"{slug[:64 - len(suffix)]}{suffix}"
            index += 1
        return candidate

    def _validate_command(self, command: str, *, allow_write: bool) -> str:
        if any(char in command for char in _SHELL_META_CHARS):
            return "Shell metacharacters are disabled in the code workbench."
        try:
            argv = shlex.split(command)
        except ValueError as exc:
            return f"Cannot parse command: {exc}"
        if not argv:
            return "Command is empty."

        executable = Path(argv[0]).name
        if executable not in _ALLOWED_EXECUTABLES:
            return f"Command executable is not allowlisted: {executable}"

        words = {Path(part).name.lower() for part in argv}
        if words & _BLOCKED_WORDS:
            return "This command includes a blocked system or destructive operation."
        if not allow_write and words & _WRITE_INTENT_WORDS:
            return (
                "This command looks write-capable; set allow_write only for "
                "intentional admin actions."
            )
        if (
            executable == "git"
            and len(argv) > 1
            and argv[1] in _WRITE_INTENT_WORDS
            and not allow_write
        ):
            return "Write-capable git commands require allow_write."
        return ""

    def _run_git_text(
        self,
        workspace: CodeWorkspace,
        git_args: list[str],
        *,
        max_chars: int = 12000,
    ) -> str:
        completed = subprocess.run(
            ["git", *git_args],
            cwd=workspace.root,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
        if completed.returncode != 0:
            raise ValueError((completed.stderr or "Git command failed.").strip()[:512])
        return completed.stdout[:max_chars]
