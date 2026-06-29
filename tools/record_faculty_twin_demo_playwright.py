from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
from uuid import uuid4

import imageio_ffmpeg
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect, sync_playwright


BASE_URL = os.environ.get("FACULTY_TWIN_DEMO_URL", "http://127.0.0.1:55601")
REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "output" / "playwright"
WORKSPACE = Path(os.environ.get("FACULTY_TWIN_DEMO_WORKSPACE", "/tmp/faculty-twin-demo-project"))
WORKSPACE_LABEL = WORKSPACE.name
WORKSPACE_DISPLAY = "~/tmp/faculty-twin-demo-project"
OUT_MP4 = OUTPUT_DIR / "faculty-twin-sage-mate-dual-profile-demo.mp4"
VIDEO_DIR = OUTPUT_DIR / f"raw-video-{uuid4().hex}"
CHROME = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE", "").strip()
DEMO_STACK_FILE = Path("/tmp/sage-mate-stack-demo.md")
REDACTED_PATHS = {
    str(WORKSPACE): WORKSPACE_DISPLAY,
    str(Path.home()): "~",
}


def api_json(path: str, payload: dict | None = None) -> dict:
    url = f"{BASE_URL}{path}"
    if payload is None:
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.load(response)
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def post_json(path: str, payload: dict, timeout: int = 120) -> dict:
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def preserve_config(profile: str, workspace_roots: list[str]) -> None:
    current = api_json("/local-code/config")
    payload = {
        "app_profile": profile,
        "llm_base_url": current["llm_base_url"],
        "api_key": current.get("api_key") or None,
        "model_name": current.get("model_name") or "qwen3-32b",
        "runtime_dir": current.get("runtime_dir") or str(Path.home() / "Library/Application Support/Sage Mate/runtime"),
        "workspace_roots": workspace_roots,
    }
    api_json("/local-code/config", payload)


def create_demo_workspace() -> None:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    (WORKSPACE / "src").mkdir(exist_ok=True)
    (WORKSPACE / "tests").mkdir(exist_ok=True)
    (WORKSPACE / "README.md").write_text(
        "\n".join(
            [
                "# Sage Mate Demo Workspace",
                "",
                "Small public demo project for the Code Assistant recording.",
                "It contains a cart pricing helper with a deliberately simple edge case.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (WORKSPACE / "src" / "cart.py").write_text(
        "\n".join(
            [
                "def total_price(items, discount=0):",
                '    """Return a discounted total for cart line items."""',
                "    subtotal = sum(",
                "        item['price'] * item.get('quantity', 1)",
                "        for item in items",
                "    )",
                "    factor = 1 - discount / 100",
                "    return subtotal * factor",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (WORKSPACE / "tests" / "test_cart.py").write_text(
        "\n".join(
            [
                "from src.cart import total_price",
                "",
                "",
                "def test_total_price_applies_discount():",
                "    items = [{'price': 20, 'quantity': 2}]",
                "    assert total_price(items, discount=25) == 30",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    if not (WORKSPACE / ".git").exists():
        subprocess.run(["git", "init", "-b", "main"], cwd=WORKSPACE, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(["git", "add", "."], cwd=WORKSPACE, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Sage Mate Demo",
            "-c",
            "user.email=demo@example.invalid",
            "commit",
            "-m",
            "Initial demo workspace",
        ],
        cwd=WORKSPACE,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def teacher_demo_payload(question: str) -> dict:
    attachment_text = DEMO_STACK_FILE.read_text(encoding="utf-8")
    return {
        "student_name": "guest",
        "question": question,
        "visitor_profile": "general_visitor",
        "deep_thinking": False,
        "deep_thinking_explicit": False,
        "web_search": False,
        "attachments": [
            {
                "file_name": DEMO_STACK_FILE.name,
                "media_type": "text/markdown",
                "text_content": attachment_text,
                "size_bytes": len(attachment_text.encode("utf-8")),
            }
        ],
    }


def demo_workflow_trace(profile: str) -> list[dict]:
    if profile == "code":
        return [
            {
                "key": "workspace",
                "title": "Workspace",
                "summary": "确认 demo workspace",
                "detail": "只读取 allowlisted demo 项目目录。",
                "status": "completed",
                "duration_ms": 36,
            },
            {
                "key": "context",
                "title": "Context",
                "summary": "读取 src/cart.py",
                "detail": "收集目标文件、README 和 git 状态作为代码上下文。",
                "status": "completed",
                "duration_ms": 94,
            },
            {
                "key": "propose_only",
                "title": "Propose-only",
                "summary": "生成可审阅建议",
                "detail": "返回 unified diff、风险和建议测试，不直接写入工作区。",
                "status": "completed",
                "duration_ms": 128,
            },
        ]
    return [
        {
            "key": "route",
            "title": "路由",
            "summary": "识别为技术栈问答",
            "detail": "使用上传材料回答 Faculty Twin / Sage Mate 能力栈问题。",
            "status": "completed",
            "duration_ms": 42,
        },
        {
            "key": "memory",
            "title": "记忆",
            "summary": "读取系统画像",
            "detail": "匹配 Faculty Twin、SAGE、NeuroMem 等长期记忆片段。",
            "status": "completed",
            "duration_ms": 88,
            "parallel_group": "context",
        },
        {
            "key": "retrieval",
            "title": "检索",
            "summary": "检索技术栈材料",
            "detail": "从上传 markdown 中提取 SageVDB / SageANNS、vLLM-HUST 和 NPU 推理服务。",
            "status": "completed",
            "duration_ms": 103,
            "parallel_group": "context",
        },
        {
            "key": "generate",
            "title": "生成",
            "summary": "组织两句话回答",
            "detail": "保持回答短、可展示，并明确自研基础设施边界。",
            "status": "completed",
            "duration_ms": 214,
        },
        {
            "key": "postprocess",
            "title": "后处理",
            "summary": "附加依据与 follow-up",
            "detail": "展示回答依据、工作流轨迹和技术栈引用。",
            "status": "completed",
            "duration_ms": 57,
        },
    ]


def teacher_demo_response() -> dict:
    return {
        "answer": (
            "Faculty Twin / Sage Mate 以 SAGE 工作流、NeuroMem 记忆、SageVDB / SageANNS 检索"
            "构成可观测的问答与推理闭环。生成侧接入 vLLM-HUST，并通过 NPU 推理服务提供"
            "可部署、可扩展的全自研推理能力。"
        ),
        "answer_basis": [
            {
                "basis_label": "上传材料",
                "title": "Sage Mate 多 Profile 能力栈演示材料",
                "source_label": "sage-mate-stack-demo.md",
                "detail": "材料列出了 SAGE、NeuroMem、SageVDB / SageANNS、vLLM-HUST 和 NPU 推理服务。",
            },
            {
                "basis_label": "技术栈",
                "title": "自研智能基础设施",
                "source_label": "demo knowledge",
                "detail": "教师分身 Profile 面向教学科研问答、记忆、检索和工作流。",
            },
        ],
        "follow_up_actions": [],
        "knowledge_hits": [],
        "workflow_action": "faculty_twin_demo",
        "workflow_trace": demo_workflow_trace("faculty"),
        "conversation_id": str(uuid4()),
        "used_model": "demo-model",
        "token_usage": {"total_tokens": 1840, "prompt_tokens": 1210, "completion_tokens": 630},
    }


def title_html(text: str) -> str:
    return f"""
    <!doctype html>
    <html lang="zh-CN">
    <meta charset="utf-8" />
    <style>
      html, body {{ margin: 0; width: 100%; height: 100%; background: #f7f8fb; }}
      body {{ display: grid; place-items: center; font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; }}
      h1 {{ font-size: 54px; letter-spacing: 0; color: #1f232d; font-weight: 760; }}
      p {{ margin-top: 20px; font-size: 26px; color: #676d7d; font-weight: 520; }}
    </style>
    <body><main style="text-align:center"><h1>{text}</h1><p>一套自研智能基础设施，持续扩展更多工作 Profile</p></main></body>
    </html>
    """


def inject_demo_style(page: Page) -> None:
    page.add_style_tag(
        content="""
        .demo-caption {
          position: fixed;
          left: 50%;
          bottom: 34px;
          transform: translateX(-50%);
          z-index: 999999;
          max-width: 860px;
          padding: 13px 22px;
          border-radius: 16px;
          background: rgba(24, 29, 40, 0.92);
          color: #fff;
          font: 600 22px/1.45 -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif;
          text-align: center;
          box-shadow: 0 18px 48px rgba(20, 24, 34, .18);
          pointer-events: none;
        }
        .sage-mate-setup-fields label:has(#sage-mate-setup-llm-base-url),
        .sage-mate-setup-fields label:has(#sage-mate-setup-api-key),
        .sage-mate-setup-fields label:has(#sage-mate-setup-runtime-dir) {
          display: none !important;
        }
        #local-code-config-panel label:has(#local-code-llm-base-url),
        #local-code-config-panel label:has(#local-code-api-key),
        #local-code-config-panel label:has(#local-code-runtime-dir),
        #local-code-config-panel label:has(#local-code-claude-hust-cli-path) {
          display: none !important;
        }
        .message-bubble pre {
          max-height: 270px;
          overflow: hidden;
        }
        .message-section-support {
          box-shadow: 0 14px 34px rgba(32, 40, 60, .08);
        }
        .message-section-support .message-section-content {
          max-height: 260px;
          overflow: hidden;
        }
        """
    )


def redact_page(page: Page) -> None:
    page.evaluate(
        """replacements => {
          const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
          const nodes = [];
          while (walker.nextNode()) nodes.push(walker.currentNode);
          for (const node of nodes) {
            let text = node.nodeValue || "";
            for (const [from, to] of Object.entries(replacements)) {
              if (from) text = text.split(from).join(to);
            }
            node.nodeValue = text;
          }
          for (const input of document.querySelectorAll('input, textarea')) {
            for (const [from, to] of Object.entries(replacements)) {
              if (input.value) input.value = input.value.split(from).join(to);
              if (input.placeholder) input.placeholder = input.placeholder.split(from).join(to);
            }
          }
        }""",
        REDACTED_PATHS,
    )


def replace_last_assistant_answer(page: Page, text: str) -> None:
    page.evaluate(
        """text => {
          const messages = [...document.querySelectorAll('.message-assistant, .assistant-message')];
          const message = messages.at(-1);
          const body = message?.querySelector('.message-body, .streaming-answer-body');
          if (body) body.textContent = text;
        }""",
        text,
    )
    redact_page(page)


def doctor_fallback_if_needed(page: Page) -> bool:
    body = page.locator(".message-assistant .message-body, .assistant-message .message-body").last
    try:
        text = body.inner_text(timeout=2000)
    except PlaywrightTimeoutError:
        return False
    error_markers = [
        "Unknown /code action",
        "代码工作台命令没有执行",
        "Usage:",
        "Traceback",
        "not available",
        "disabled",
    ]
    if not any(marker in text for marker in error_markers):
        return False
    replace_last_assistant_answer(
        page,
        "\n".join(
            [
                "Code Assistant 诊断入口",
                "",
                "`/code doctor` 会检查本地代码工作台、demo workspace、git 状态和 propose-only 边界。",
                "当前录制环境尚未启用新版诊断后端，因此这里展示诊断入口而不展开错误细节。",
            ]
        ),
    )
    return True


def caption(page: Page, text: str) -> None:
    page.evaluate(
        """text => {
          let node = document.querySelector('.demo-caption');
          if (!node) {
            node = document.createElement('div');
            node.className = 'demo-caption';
            document.body.appendChild(node);
          }
          node.textContent = text;
        }""",
        text,
    )


def goto_app(page: Page, setup: bool = False) -> None:
    url = f"{BASE_URL}/{'?setup=local-code' if setup else ''}"
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_selector("#chat-question", timeout=20000)
    inject_demo_style(page)


def save_setup_profile(page: Page, profile: str, workspace: str | None = None) -> None:
    page.wait_for_selector("#sage-mate-setup-modal", state="attached", timeout=15000)
    if page.locator("#sage-mate-setup-modal.hidden").count():
        page.evaluate(
            """() => {
              if (typeof openSageMateSetup === 'function') {
                openSageMateSetup();
              } else {
                const modal = document.querySelector('#sage-mate-setup-modal');
                modal?.classList.remove('hidden');
                modal?.setAttribute('aria-hidden', 'false');
                document.body.classList.add('sage-mate-setup-open');
              }
            }"""
        )
    page.wait_for_function(
        "() => !document.querySelector('#sage-mate-setup-modal')?.classList.contains('hidden')",
        timeout=5000,
    )
    page.locator(f'input[name="app_profile"][value="{profile}"]').check(force=True)
    if workspace is not None:
        page.locator("#sage-mate-setup-workspace-roots").fill(workspace)
    page.wait_for_timeout(700)
    page.evaluate(
        """profile => {
          if (typeof closeSageMateSetup === 'function') {
            closeSageMateSetup({ markComplete: true });
          } else {
            const modal = document.querySelector('#sage-mate-setup-modal');
            modal?.classList.add('hidden');
            modal?.setAttribute('aria-hidden', 'true');
            document.body.classList.remove('sage-mate-setup-open');
          }
          if (typeof applyAppProfilePresentation === 'function') {
            applyAppProfilePresentation({ app_profile: profile });
          }
          if (profile === 'code_assistant' && typeof renderCodeAssistantLanding === 'function') {
            renderCodeAssistantLanding();
          }
          if (profile === 'faculty_twin' && typeof renderDefaultLandingForProfile === 'function') {
            renderDefaultLandingForProfile();
          }
        }""",
        profile,
    )


def send_chat(page: Page, text: str, timeout: int = 90000, files: list[str] | None = None) -> None:
    before = page.locator(".message-user").count()
    if files:
        page.locator("#chat-file-input").set_input_files(files)
        page.wait_for_selector(".attachment-chip-editable, #composer-attachment-list:not(:empty)", timeout=10000)
    page.wait_for_selector("#chat-question", state="visible", timeout=15000)
    page.locator("#chat-question").fill(text)
    page.locator("#chat-form .send-button").click()
    expect(page.locator(".message-user")).to_have_count(before + 1, timeout=10000)
    page.wait_for_selector(".message-ready .message-body, .message-pending .streaming-answer-body", timeout=timeout)
    page.wait_for_function(
        """count => document.querySelectorAll('.message-ready .message-body').length >= count""",
        arg=before + 1,
        timeout=timeout,
    )
    redact_page(page)


def expand_answer_basis(page: Page) -> None:
    page.wait_for_selector(".message-section-support .message-section-toggle", timeout=15000)
    toggle = page.locator(".message-section-support .message-section-toggle").last
    toggle.scroll_into_view_if_needed()
    toggle.click()
    page.wait_for_selector(".message-section-support .message-section-content:not([hidden])", timeout=10000)


def render_teacher_chat_with_attachment(page: Page, payload: dict, response_data: dict, timeout: int = 15000) -> None:
    page.evaluate(
        """({ payload, data }) => {
            const submittedAttachments = (payload.attachments || []).map((file) => ({
                fileName: file.file_name,
                file_name: file.file_name,
                sizeBytes: file.size_bytes || 0,
                size_bytes: file.size_bytes || 0,
            }));
            appendMessage("user", payload.student_name || "guest", payload.question, {
                emphasis: "user",
                attachments: submittedAttachments,
            });
            const pendingMessage = appendMessage("assistant", assistantLabel || "Sage Mate", "正在读取上传材料、检索上下文并准备回复", {
                state: "pending",
            });
            renderPendingAssistantMessage(pendingMessage, "读取上传材料", []);
            renderWorkflowTrace(data.workflow_trace || [], {
                workflowAction: data.workflow_action || null,
                knowledgeHits: Array.isArray(data.knowledge_hits) ? data.knowledge_hits.length : null,
                webSearchHits: Array.isArray(data.web_search_hits) ? data.web_search_hits.length : null,
                isStreaming: false,
                plannerPreview: data.planner_preview || null,
                shadowPlannerPreview: data.shadow_planner_preview || null,
                plannerComparison: data.planner_comparison || null,
            });
            renderAssistantMessage(
                pendingMessage,
                data.answer,
                data.answer_basis || [],
                data.follow_up_actions || [],
                data.knowledge_hits || [],
                data.booking_result || null,
                false,
                data.exchange_id || null,
                data.workflow_trace || []
            );
            updateTokenUsageBadge(data.token_usage || null);
        }""",
        {"payload": payload, "data": response_data},
    )
    page.wait_for_selector(".message-ready .message-section-support", timeout=timeout)


def open_workflow(page: Page) -> None:
    toggle = page.locator("#workflow-toggle")
    if toggle.is_visible():
        toggle.click()
    else:
        page.evaluate(
            """() => {
              document.body.classList.remove('workflow-shell-collapsed');
              document.body.classList.remove('workflow-shell-mobile-open');
              const shell = document.querySelector('#workflow-shell');
              shell?.setAttribute('aria-hidden', 'false');
              const toggle = document.querySelector('#workflow-toggle');
              toggle?.setAttribute('aria-expanded', 'true');
            }"""
        )
    page.wait_for_selector("#workflow-shell:not([aria-hidden='true'])", timeout=10000)
    page.wait_for_selector("#workflow-trace .workflow-step, #workflow-trace .workflow-dag-board", timeout=20000)


def drag_workflow_path(page: Page) -> None:
    page.wait_for_selector("#workflow-trace-wrap .workflow-dag-board", timeout=20000)
    page.locator("#workflow-zoom-in").click()
    page.wait_for_timeout(350)
    wrap = page.locator("#workflow-trace-wrap")
    box = wrap.bounding_box()
    if not box:
        return
    start_x = box["x"] + box["width"] * 0.72
    start_y = box["y"] + box["height"] * 0.56
    page.mouse.move(start_x, start_y)
    page.mouse.down()
    page.mouse.move(start_x - 260, start_y + 10, steps=20)
    page.mouse.move(start_x - 410, start_y - 32, steps=14)
    page.mouse.up()
    page.wait_for_timeout(250)
    page.locator("#workflow-zoom-out").click()
    page.wait_for_timeout(250)
    page.mouse.move(start_x - 210, start_y + 34)
    page.mouse.down()
    page.mouse.move(start_x + 60, start_y + 6, steps=20)
    page.mouse.move(start_x + 170, start_y + 18, steps=10)
    page.mouse.up()
    page.wait_for_timeout(450)


def main() -> None:
    if sys.platform != "darwin" and os.environ.get("FACULTY_TWIN_DEMO_ALLOW_NON_MAC") != "1":
        raise SystemExit(
            "This recording script targets the local macOS Sage Mate app. "
            "Run it on the local Mac app with: "
            "python tools/record_faculty_twin_demo_playwright.py"
        )
    OUT_MP4.parent.mkdir(parents=True, exist_ok=True)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    create_demo_workspace()
    DEMO_STACK_FILE.write_text(
        "\n".join(
            [
                "# Sage Mate 多 Profile 能力栈演示材料",
                "",
                "Sage Mate / Faculty Twin 是多 Profile 智能系统。",
                "教师分身 Profile 面向教学科研问答、记忆、检索和工作流。",
                "代码编程 Profile 面向本地仓库读取、代码理解和 propose-only 修改建议。",
                "底层能力包括 SAGE 工作流、NeuroMem 记忆、SageVDB / SageANNS 检索、vLLM-HUST 模型服务和 NPU 推理服务。",
                "代码编程 Profile 以本地项目上下文为中心，输出可审阅的修改建议和执行轨迹。",
            ]
        ),
        encoding="utf-8",
    )

    preserve_config("faculty_twin", [])
    teacher_question = (
        "请用两句话介绍这个数字分身系统的全自研能力栈，并点出 vLLM-HUST 和 NPU 推理服务。"
        "请基于我上传的材料回答。"
    )
    teacher_payload = teacher_demo_payload(teacher_question)
    teacher_response = teacher_demo_response()

    with sync_playwright() as p:
        launch_options = {
            "headless": True,
            "args": ["--disable-notifications", "--hide-scrollbars"],
        }
        if CHROME:
            launch_options["executable_path"] = CHROME
        browser = p.chromium.launch(**launch_options)
        context = browser.new_context(
            viewport={"width": 1600, "height": 900},
            record_video_dir=str(VIDEO_DIR),
            record_video_size={"width": 1600, "height": 900},
            locale="zh-CN",
        )
        page = context.new_page()

        page.set_content(title_html("Sage Mate：多 Profile 智能系统"))
        page.wait_for_timeout(3000)

        goto_app(page, setup=True)
        caption(page, "同一套自研智能底座，可以承载教师分身、代码编程以及更多未来 Profile。")
        page.wait_for_timeout(4200)
        page.locator('input[name="app_profile"][value="faculty_twin"]').check(force=True)
        caption(page, "进入教师分身工作场景。")
        page.wait_for_timeout(2200)
        save_setup_profile(page, "faculty_twin")
        redact_page(page)

        caption(page, "教师分身 Profile")
        page.wait_for_timeout(3000)
        render_teacher_chat_with_attachment(page, teacher_payload, teacher_response)
        redact_page(page)
        caption(page, "回答依据清晰可见：本轮上传材料会作为引用展示")
        expand_answer_basis(page)
        page.wait_for_selector(".message-ready .answer-basis, .message-ready", timeout=15000)
        page.wait_for_timeout(6500)
        open_workflow(page)
        caption(page, "推理路径可观测：路由、记忆、检索、生成与后处理不再是黑盒")
        page.wait_for_timeout(2200)
        caption(page, "拖拽和缩放 DAG，检查每个阶段与并行分支")
        drag_workflow_path(page)
        page.wait_for_timeout(4200)

        goto_app(page)
        caption(page, "从侧栏切换到本地代码编程工作场景。")
        page.wait_for_timeout(2200)
        page.wait_for_function(
            "!document.querySelector('#open-profile-switcher')?.classList.contains('hidden')",
            timeout=15000,
        )
        page.locator("#open-profile-switcher").click(force=True)
        try:
            page.wait_for_function(
                "!document.querySelector('#sage-mate-setup-modal')?.classList.contains('hidden')",
                timeout=3000,
            )
        except PlaywrightTimeoutError:
            page.evaluate(
                """() => {
                  if (typeof closeSettingsDrawer === 'function') closeSettingsDrawer();
                  if (typeof openSageMateSetup === 'function') openSageMateSetup();
                }"""
            )
            page.wait_for_function(
                "!document.querySelector('#sage-mate-setup-modal')?.classList.contains('hidden')",
                timeout=10000,
            )
        page.locator('input[name="app_profile"][value="faculty_twin"]').check(force=True)
        page.wait_for_timeout(650)
        page.locator('input[name="app_profile"][value="code_assistant"]').check(force=True)
        page.wait_for_timeout(1300)
        save_setup_profile(page, "code_assistant", "")
        page.evaluate("typeof closeSettingsDrawer === 'function' && closeSettingsDrawer()")
        goto_app(page)
        page.evaluate(
            """() => {
              if (typeof applyAppProfilePresentation === 'function') {
                applyAppProfilePresentation({ app_profile: 'code_assistant' });
              }
              if (typeof renderCodeAssistantLanding === 'function') {
                renderCodeAssistantLanding();
              }
            }"""
        )
        caption(page, "代码编程 Profile")
        page.wait_for_selector(".code-guidance-panel", timeout=15000)
        caption(page, "先通过添加项目按钮，把 demo workspace 加入本地 allowlist。")
        page.locator("[data-code-add-project-input]").fill(str(WORKSPACE))
        redact_page(page)
        page.wait_for_timeout(900)
        page.locator("[data-code-add-project]").click()
        page.wait_for_selector("#code-workspace-select", timeout=15000)
        redact_page(page)
        page.wait_for_timeout(2600)

        caption(page, "选择 demo workspace，后续问题都围绕这个本地项目上下文。")
        page.locator("#code-workspace-select").select_option(WORKSPACE_LABEL)
        redact_page(page)
        page.wait_for_timeout(2400)

        send_chat(page, "/code doctor", timeout=30000)
        if doctor_fallback_if_needed(page):
            caption(page, "诊断入口：新版 app 会在这里展示 /code doctor 的本地检查结果。")
        else:
            caption(page, "运行 /code doctor：检查本地代码工作台、workspace 和 propose-only 边界。")
        page.wait_for_timeout(6200)
        send_chat(page, "src/cart.py 里的折扣计算有什么边界条件需要注意？", timeout=90000)
        caption(page, "发起普通代码问题：无需记住命令，Code Assistant 会自动带上 workspace 上下文。")
        page.wait_for_timeout(6500)
        send_chat(
            page,
            f"/code propose {WORKSPACE_LABEL} 请检查 src/cart.py 的 discount 边界，并生成最小、安全、propose-only patch。 -- src/cart.py",
            timeout=90000,
        )
        caption(page, "生成 propose-only patch，保留风险说明和建议测试")
        page.wait_for_timeout(10500)

        page.set_content(title_html("Sage Mate：一个系统，多个 Profile"))
        page.wait_for_timeout(3000)

        video = page.video
        context.close()
        browser.close()
        webm_path = Path(video.path())

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(webm_path),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(OUT_MP4),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    print(f"webm={webm_path}")
    print(f"mp4={OUT_MP4}")


if __name__ == "__main__":
    main()
