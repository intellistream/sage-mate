from __future__ import annotations

import contextlib
import http.server
import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
import threading
from typing import Protocol

from .code_workbench import CodeWorkbench
from .config import AppSettings
from .models import (
    CodeAssistRequest,
    CodeContextRequest,
    CodeProposeRequest,
)


@dataclass(frozen=True, slots=True)
class CodeAgentBackendResult:
    answer: str
    context_paths: list[str]
    used_model: str
    backend: str


@dataclass(frozen=True, slots=True)
class CodeAgentDoctorResult:
    backend: str
    ok: bool
    message: str
    details: dict[str, str]


class CodeAgentBackend(Protocol):
    name: str

    def assist(self, request: CodeAssistRequest) -> CodeAgentBackendResult:
        ...

    def propose(self, request: CodeProposeRequest) -> CodeAgentBackendResult:
        ...

    def doctor(self) -> CodeAgentDoctorResult:
        ...


class ClaudeHustPrintRunner(Protocol):
    def __call__(
        self,
        prompt: str,
        cwd: Path,
        *,
        output_format: str = "text",
    ) -> str:
        ...


@dataclass(frozen=True, slots=True)
class ClaudeHustStructuredOutput:
    text: str
    inspected_files: list[str]
    tool_calls: list[str]
    proposed_diffs: list[str]
    errors: list[str]


def claude_hust_json_unavailable(error: str) -> bool:
    lowered = error.lower()
    return (
        "output-format" in lowered
        and ("json" in lowered or "invalid" in lowered or "unknown" in lowered)
    )


def parse_claude_hust_structured_output(payload: object) -> ClaudeHustStructuredOutput:
    assistant_text: list[str] = []
    inspected_files: list[str] = []
    tool_calls: list[str] = []
    proposed_diffs: list[str] = []
    errors: list[str] = []

    def add_unique(items: list[str], value: object) -> None:
        text = str(value or "").strip()
        if text and text not in items:
            items.append(text)

    def visit(node: object, *, role: str | None = None) -> None:
        if isinstance(node, list):
            for item in node:
                visit(item, role=role)
            return
        if not isinstance(node, dict):
            return

        node_role = str(node.get("role") or role or "")
        node_type = str(node.get("type") or "")
        if node_role == "assistant" and isinstance(node.get("content"), str):
            add_unique(assistant_text, node["content"])
        if node_type == "text" and isinstance(node.get("text"), str):
            add_unique(assistant_text, node["text"])
        if isinstance(node.get("result"), str):
            add_unique(assistant_text, node["result"])

        if node_type in {"tool_use", "tool_call"} or "toolUseResult" in node:
            name = str(node.get("name") or node.get("tool_name") or node.get("tool") or "tool")
            add_unique(tool_calls, name)
            tool_input = node.get("input") or node.get("arguments") or {}
            if isinstance(tool_input, dict):
                for key in ("file_path", "path", "absolute_path"):
                    if key in tool_input:
                        add_unique(inspected_files, tool_input[key])

        for key in ("file_path", "path"):
            if key in node and str(node.get("name") or "").lower() in {"read", "grep", "glob", "ls"}:
                add_unique(inspected_files, node[key])
        for key in ("unified_diff", "diff", "patch"):
            if isinstance(node.get(key), str):
                add_unique(proposed_diffs, node[key])
        if "error" in node:
            add_unique(errors, node["error"])
        if isinstance(node.get("errors"), list):
            for error in node["errors"]:
                add_unique(errors, error)

        for key, value in node.items():
            if key in {"input", "arguments"} and node_type in {"tool_use", "tool_call"}:
                continue
            visit(value, role=node_role or role)

    visit(payload)
    return ClaudeHustStructuredOutput(
        text="\n".join(assistant_text).strip(),
        inspected_files=inspected_files,
        tool_calls=tool_calls,
        proposed_diffs=proposed_diffs,
        errors=errors,
    )


def format_claude_hust_structured_output(parsed: ClaudeHustStructuredOutput) -> str:
    text = parsed.text
    if parsed.proposed_diffs and "```" not in text:
        text = f"{text}\n\n```diff\n{parsed.proposed_diffs[0].strip()}\n```".strip()
    details: list[str] = []
    if parsed.inspected_files:
        details.append("Inspected files: " + ", ".join(parsed.inspected_files[:16]))
    if parsed.tool_calls:
        details.append("Tool calls: " + ", ".join(parsed.tool_calls[:16]))
    if parsed.errors:
        details.append("Errors: " + "; ".join(parsed.errors[:8]))
    if details:
        return f"{text}\n\nClaude Hust metadata:\n" + "\n".join(details) if text else "\n".join(details)
    return text


class InternalCodeAgentBackend:
    name = "internal"

    def __init__(
        self,
        *,
        settings: AppSettings,
        workbench: CodeWorkbench,
        llm_client: object,
    ) -> None:
        self._settings = settings
        self._workbench = workbench
        self._llm_client = llm_client

    def assist(self, request: CodeAssistRequest) -> CodeAgentBackendResult:
        system_prompt, user_prompt, context_paths = self._workbench.build_assist_prompt(
            request
        )
        answer = self._llm_client.answer_question_sync(
            system_prompt,
            user_prompt,
            temperature=0.1,
            max_tokens=2048,
            enable_thinking=False,
            cache_namespace=f"code-workbench:{request.workspace_id}",
        )
        return CodeAgentBackendResult(
            answer=answer,
            context_paths=context_paths,
            used_model=self._llm_client.model_name,
            backend=self.name,
        )

    def propose(self, request: CodeProposeRequest) -> CodeAgentBackendResult:
        system_prompt, user_prompt, context_paths = self._workbench.build_propose_prompt(
            request
        )
        answer = self._llm_client.answer_question_sync(
            system_prompt,
            user_prompt,
            temperature=0.0,
            max_tokens=4096,
            enable_thinking=False,
            cache_namespace=f"code-propose:{request.workspace_id}",
        )
        return CodeAgentBackendResult(
            answer=answer,
            context_paths=context_paths,
            used_model=self._llm_client.model_name,
            backend=self.name,
        )

    def doctor(self) -> CodeAgentDoctorResult:
        return CodeAgentDoctorResult(
            backend=self.name,
            ok=True,
            message="Internal code backend is available.",
            details={
                "model": str(getattr(self._llm_client, "model_name", "")),
                "profile": self._settings.app_profile,
            },
        )


class ClaudeHustCodeAgentBackend:
    name = "claude_hust"

    def __init__(
        self,
        *,
        settings: AppSettings,
        workbench: CodeWorkbench,
        llm_client: object,
        print_runner: ClaudeHustPrintRunner | None = None,
    ) -> None:
        self._settings = settings
        self._workbench = workbench
        self._llm_client = llm_client
        self._print_runner = print_runner

    def assist(self, request: CodeAssistRequest) -> CodeAgentBackendResult:
        temp_dir = self._workbench.copy_workspace_to_temp(request.workspace_id)
        try:
            context = self._workbench.build_context(
                CodeContextRequest(
                    workspace_id=request.workspace_id,
                    paths=request.paths,
                    max_context_chars=request.max_context_chars,
                )
            )
            temp_workspace = Path(temp_dir.name) / self._workbench.workspace_root(
                request.workspace_id
            ).name
            paths = ", ".join(request.paths) if request.paths else "(auto-discover relevant files)"
            prompt = (
                "You are running as the Sage Mate code assistant through claude-hust.\n"
                "This is a temporary local copy of the selected repository. Read files and run safe "
                "inspection commands as needed, but do not claim that real user files were edited. "
                "For this request, explain, inspect, and propose only.\n\n"
                f"Task:\n{request.task}\n\n"
                f"User-selected paths:\n{paths}\n\n"
                f"Sage Mate context pack:\n{context.context}\n"
            )
            return CodeAgentBackendResult(
                answer=self._run_structured_or_text(prompt, temp_workspace),
                context_paths=context.context_paths,
                used_model=self._used_model(),
                backend=self.name,
            )
        finally:
            temp_dir.cleanup()

    def propose(self, request: CodeProposeRequest) -> CodeAgentBackendResult:
        temp_dir = self._workbench.copy_workspace_to_temp(request.workspace_id)
        try:
            _, user_prompt, context_paths = self._workbench.build_propose_prompt(request)
            temp_workspace = Path(temp_dir.name) / self._workbench.workspace_root(
                request.workspace_id
            ).name
            paths = ", ".join(request.paths) if request.paths else "(auto-discover relevant files)"
            prompt = (
                "You are running as Sage Mate's propose-only code backend through claude-hust.\n"
                "This is a temporary copy of the user's repository. Do not claim that real files were "
                "edited, saved, committed, pushed, or tested. Produce one JSON object with exactly these "
                "keys: summary, affected_files, unified_diff, risks, suggested_tests. affected_files and "
                "suggested_tests must be arrays of strings; unified_diff must be a single unified diff "
                "string. If more context is required, leave unified_diff empty and explain in risks.\n\n"
                f"Task:\n{request.task}\n\n"
                f"User-selected paths:\n{paths}\n\n"
                f"Sage Mate propose context:\n{user_prompt}\n"
            )
            return CodeAgentBackendResult(
                answer=self._run_structured_or_text(prompt, temp_workspace),
                context_paths=context_paths,
                used_model=self._used_model(),
                backend=self.name,
            )
        finally:
            temp_dir.cleanup()

    def doctor(self) -> CodeAgentDoctorResult:
        try:
            cli = self._resolve_cli()
        except RuntimeError as exc:
            return CodeAgentDoctorResult(
                backend=self.name,
                ok=False,
                message=str(exc),
                details={},
            )
        return CodeAgentDoctorResult(
            backend=self.name,
            ok=True,
            message="claude-hust CLI is available.",
            details={"cli": cli, "model": self._used_model()},
        )

    def _used_model(self) -> str:
        return self._settings.model_name or str(getattr(self._llm_client, "model_name", ""))

    def _run_structured_or_text(self, prompt: str, cwd: Path) -> str:
        try:
            raw = self._run_print(prompt, cwd, output_format="json")
        except RuntimeError as exc:
            if claude_hust_json_unavailable(str(exc)):
                return self._run_print(prompt, cwd, output_format="text")
            raise

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return self._run_print(prompt, cwd, output_format="text")

        parsed = parse_claude_hust_structured_output(payload)
        formatted = format_claude_hust_structured_output(parsed)
        if formatted:
            return formatted
        if parsed.errors:
            return "\n".join(parsed.errors)
        return self._run_print(prompt, cwd, output_format="text")

    def _run_print(self, prompt: str, cwd: Path, *, output_format: str = "text") -> str:
        if self._print_runner is not None:
            return self._print_runner(prompt, cwd, output_format=output_format)
        cli = self._resolve_cli()
        with self._env_for_subprocess() as env:
            completed = subprocess.run(
                [
                    cli,
                    "--print",
                    prompt,
                    "--output-format",
                    output_format,
                    "--no-session-persistence",
                ],
                cwd=cwd,
                text=True,
                capture_output=True,
                timeout=self._settings.claude_hust_timeout_seconds,
                check=False,
                env=env,
            )
        if completed.returncode != 0:
            stderr = (completed.stderr or completed.stdout or "claude-hust failed").strip()
            raise RuntimeError(stderr[-2000:])
        return (completed.stdout or "").strip()

    def _resolve_cli(self) -> str:
        configured = self._settings.claude_hust_cli_path.strip()
        candidates = [
            configured,
            shutil.which("claude-hust") or "",
            str(Path.home() / "Library/Application Support/Sage Mate/claude-code-hust/bin/claude-hust"),
            str(Path.home() / "claude-code-hust/bin/claude-hust"),
            str(Path.home() / "Documents/claude-code-hust/bin/claude-hust"),
        ]
        for candidate in candidates:
            path = Path(candidate).expanduser() if candidate else None
            if path and path.is_file() and os.access(path, os.X_OK):
                return str(path)
        raise RuntimeError(
            "claude_hust backend is enabled, but claude-hust was not found. "
            "Set DIGITAL_TWIN_CLAUDE_HUST_CLI_PATH to the local bin/claude-hust path."
        )

    def _env(self) -> dict[str, str]:
        env = os.environ.copy()
        configured = self._settings.claude_hust_cli_path.strip()
        if configured:
            cli_path = Path(configured).expanduser()
            support_bin = cli_path.parent.parent.parent / "bin"
            if support_bin.is_dir():
                env["PATH"] = str(support_bin) + os.pathsep + env.get("PATH", "")
        env["CC_HUST_SKIP_DOTENV"] = "1"
        env["PATH"] = f"{Path.home() / '.bun/bin'}:{env.get('PATH', '')}"
        env["API_TIMEOUT_MS"] = str(self._settings.claude_hust_timeout_seconds * 1000)
        if self._settings.llm_base_url:
            env["ANTHROPIC_BASE_URL"] = self._settings.llm_base_url
        if self._settings.api_key and self._settings.api_key != "EMPTY":
            env["ANTHROPIC_API_KEY"] = self._settings.api_key
        if self._should_proxy_openai():
            env["CLAUDE_CODE_FORCE_RECOVERY_CLI"] = "1"
            env.setdefault("ANTHROPIC_API_KEY", "sage-mate-local")
            env["ANTHROPIC_MODEL"] = "claude-sonnet-4-6"
            env["ANTHROPIC_DEFAULT_SONNET_MODEL"] = "claude-sonnet-4-6"
            env["ANTHROPIC_DEFAULT_HAIKU_MODEL"] = "claude-haiku-4-5"
            env["ANTHROPIC_DEFAULT_OPUS_MODEL"] = "claude-opus-4-7"
        elif self._settings.model_name:
            env["ANTHROPIC_MODEL"] = self._settings.model_name
        return env

    def _should_proxy_openai(self) -> bool:
        base_url = self._settings.llm_base_url.strip().rstrip("/")
        if not base_url:
            return False
        lowered = base_url.lower()
        return lowered.endswith("/v1") and "anthropic" not in lowered

    @contextlib.contextmanager
    def _env_for_subprocess(self) -> Iterable[dict[str, str]]:
        env = self._env()
        if not self._should_proxy_openai():
            yield env
            return

        proxy = self._start_anthropic_to_openai_proxy()
        try:
            host, port = proxy.server_address[:2]
            env["ANTHROPIC_BASE_URL"] = f"http://{host}:{port}"
            yield env
        finally:
            proxy.shutdown()
            proxy.server_close()

    def _start_anthropic_to_openai_proxy(self) -> http.server.ThreadingHTTPServer:
        target_url = self._settings.llm_base_url.rstrip("/") + "/chat/completions"
        api_key = self._settings.api_key

        def content_to_text(content: object) -> str:
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts: list[str] = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        parts.append(str(block.get("text", "")))
                return "\n".join(part for part in parts if part)
            return str(content or "")

        def bounded_max_tokens(value: object) -> int:
            try:
                requested = int(value)
            except (TypeError, ValueError):
                requested = 1024
            return max(64, min(requested, 1024))

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, _format: str, *_args: object) -> None:
                return

            def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
                if self.path not in {"/v1/models", "/models"}:
                    self.send_error(404)
                    return
                body = json.dumps(
                    {
                        "object": "list",
                        "data": [
                            {
                                "id": "claude-sonnet-4-6",
                                "object": "model",
                                "created": 0,
                                "owned_by": "sage-mate-proxy",
                            },
                            {
                                "id": "claude-haiku-4-5",
                                "object": "model",
                                "created": 0,
                                "owned_by": "sage-mate-proxy",
                            },
                            {
                                "id": "claude-opus-4-7",
                                "object": "model",
                                "created": 0,
                                "owned_by": "sage-mate-proxy",
                            },
                        ],
                    }
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
                if self.path not in {"/v1/messages", "/messages"}:
                    self.send_error(404)
                    return
                try:
                    length = int(self.headers.get("content-length", "0"))
                    payload = json.loads(self.rfile.read(length) or b"{}")
                    messages: list[dict[str, str]] = []
                    system = payload.get("system")
                    if system:
                        messages.append({"role": "system", "content": content_to_text(system)})
                    for message in payload.get("messages", []):
                        if not isinstance(message, dict):
                            continue
                        role = "assistant" if message.get("role") == "assistant" else "user"
                        text = content_to_text(message.get("content"))
                        if text:
                            messages.append({"role": role, "content": text})
                    if not messages:
                        messages.append({"role": "user", "content": ""})
                    upstream_payload = {
                        "model": self.server.sage_mate_upstream_model,  # type: ignore[attr-defined]
                        "messages": messages,
                        "max_tokens": bounded_max_tokens(payload.get("max_tokens", 1024)),
                        "temperature": payload.get("temperature", 0),
                        "stream": False,
                    }
                    request = urllib.request.Request(
                        target_url,
                        data=json.dumps(upstream_payload).encode("utf-8"),
                        headers={
                            "Content-Type": "application/json",
                            "User-Agent": "SageMate/1.0",
                            **(
                                {"Authorization": f"Bearer {api_key}"}
                                if api_key and api_key != "EMPTY"
                                else {}
                            ),
                        },
                        method="POST",
                    )
                    with urllib.request.urlopen(request, timeout=self.server.timeout or 120) as response:
                        upstream = json.loads(response.read() or b"{}")
                    text = (
                        upstream.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                    )
                    usage = upstream.get("usage") or {}
                    response_payload = {
                        "id": upstream.get("id", "sage-mate-proxy"),
                        "type": "message",
                        "role": "assistant",
                        "model": payload.get("model") or "claude-sonnet-4-6",
                        "content": [{"type": "text", "text": text}],
                        "stop_reason": "end_turn",
                        "stop_sequence": None,
                        "usage": {
                            "input_tokens": usage.get("prompt_tokens", 0),
                            "output_tokens": usage.get("completion_tokens", 0),
                        },
                    }
                    body = json.dumps(response_payload).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                except urllib.error.HTTPError as exc:
                    detail = exc.read().decode("utf-8", errors="replace")[-2000:]
                    body = json.dumps({"error": {"message": detail}}).encode("utf-8")
                    self.send_response(exc.code)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                except Exception as exc:
                    body = json.dumps({"error": {"message": str(exc)}}).encode("utf-8")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)

        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.timeout = min(self._settings.claude_hust_timeout_seconds, 300)
        server.sage_mate_upstream_model = self._settings.model_name or "qwen3-32b"  # type: ignore[attr-defined]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server
