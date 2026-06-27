from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import urllib.request
from uuid import uuid4

import imageio_ffmpeg
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect, sync_playwright


BASE_URL = os.environ.get("FACULTY_TWIN_DEMO_URL", "http://127.0.0.1:55601")
WORKSPACE = "/Users/shuhao/tmp/faculty-twin-demo-project"
OUT_MP4 = Path.home() / "Downloads" / "faculty-twin-dual-profile-demo.mp4"
VIDEO_DIR = Path("/tmp") / f"faculty-twin-playwright-video-{uuid4().hex}"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DEMO_STACK_FILE = Path("/tmp/sage-mate-stack-demo.md")


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
        """() => {
          if (typeof closeSageMateSetup === 'function') {
            closeSageMateSetup({ markComplete: true });
          } else {
            const modal = document.querySelector('#sage-mate-setup-modal');
            modal?.classList.add('hidden');
            modal?.setAttribute('aria-hidden', 'true');
            document.body.classList.remove('sage-mate-setup-open');
          }
        }"""
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
    OUT_MP4.parent.mkdir(parents=True, exist_ok=True)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
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

    preserve_config("code_assistant", [WORKSPACE])
    teacher_question = (
        "请用两句话介绍这个数字分身系统的全自研能力栈，并点出 vLLM-HUST 和 NPU 推理服务。"
        "请基于我上传的材料回答。"
    )
    teacher_payload = teacher_demo_payload(teacher_question)
    teacher_response = post_json(f"/chat?request_id={uuid4()}", teacher_payload, timeout=120)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME,
            headless=True,
            args=["--disable-notifications", "--hide-scrollbars"],
        )
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

        caption(page, "教师分身 Profile")
        page.wait_for_timeout(3000)
        render_teacher_chat_with_attachment(page, teacher_payload, teacher_response)
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
        save_setup_profile(page, "code_assistant", WORKSPACE)
        preserve_config("code_assistant", [WORKSPACE])
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
        page.wait_for_timeout(4200)
        send_chat(page, "/code workspaces 帮我检查本地代码路径", timeout=30000)
        caption(page, "像 Codex 一样选择本地项目、理解代码、生成修改")
        page.wait_for_timeout(6000)
        send_chat(page, "/code read faculty-twin-demo-project src/cart.py 1 40", timeout=30000)
        caption(page, "围绕本地项目上下文，先理解代码再生成建议")
        page.wait_for_timeout(6000)
        send_chat(
            page,
            "/code propose faculty-twin-demo-project 请检查 src/cart.py 里有没有明显 bug，并生成最小 patch。 -- src/cart.py",
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
