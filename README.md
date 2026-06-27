# sage-faculty-twin

面向单个教师的数字分身应用（FastAPI + SAGE + NeuroMem + OpenAI-compatible LLM）。

## 最重要的结论

- 推荐后端链路：vllm-hust + vllm-ascend-hust（Ascend）。
- 首次部署：`./quickstart.sh`（一键安装环境、依赖、systemd 服务）。
- 运行管理：`./manage.sh`（统一入口：启停、状态、日志）。
- 应用默认监听：`127.0.0.1:55601`。

## 前置条件（服务器网页部署）

- Linux
- Python 3.11
- 同级目录存在：`../SAGE`、`../neuromem`、`../sageVDB`
- vLLM 推理引擎运行在 Docker 容器内（设置 `VLLM_ENGINE_CONTAINER`）
- 本机可访问 vllm-hust OpenAI 端点（默认 `127.0.0.1:8000`）

## 本地 Sage Mate sibling 布局

本地代码编程版会把 `claude-code-hust` 作为同级依赖仓库管理，默认布局如下：

```text
parent/
  faculty-twin/
  SAGE/
  neuromem/
  sageVDB/
  claude-code-hust/   # 仅 local-mac-app / Sage Mate 代码 Profile 使用
```

`hosted-web` 服务器部署不会安装、暴露或启用 `claude-code-hust`。

## 首次部署

### 服务器网页部署（Faculty Twin hosted）

用于 `180-ascend-dev` 这类远程服务器。默认是浏览器网页形态，并且显式关闭本地代码功能：

```bash
./quickstart.sh --target hosted-web          # 默认 target；安装环境、依赖、.env、systemd 服务
./quickstart.sh --target hosted-web --start  # 安装并启动 systemd 服务
./quickstart.sh --with-vllm-engine --start   # 需要本机 vLLM 引擎服务时再启用
```

`hosted-web` 会在 `.env` 中确保：

```bash
DIGITAL_TWIN_DEPLOYMENT_MODE=hosted
DIGITAL_TWIN_APP_PROFILE=faculty_twin
DIGITAL_TWIN_CODE_WORKBENCH_ENABLED=false
DIGITAL_TWIN_CODE_WORKSPACE_ROOTS=
```

### macOS 本地 App（Sage Mate）

```text
打开 dist/sage-mate-macos.dmg，双击 Sage Mate.app
```

它会作为独立 macOS 应用启动，在应用窗口内选择 Faculty Twin 或 Code Assistant 模式，
并完成 LLM、运行时数据目录和本地仓库 allowlist 配置。`sage-studio` 已保留给 SAGE
画布/低代码流水线 UI，这个桌面助手命名为 Sage Mate。
LLM URL、API key 和模型名会优先从本机 `SAGE_MATE_PREFILL_ENV` 指向的 env 文件预填；
没有显式指定时会尝试读取 `~/vllm-hust-dev-hub/.env` 或 runtime 私有仓库中的部署 env。
代码后端默认使用内置 propose-only harness；本地安装也可以在设置里切到 sibling
`claude-code-hust` 的 `claude-hust` CLI 后端。选择 Code Assistant 模式时，
本地安装器会尝试自动 clone/install `../claude-code-hust`，并把本机 `bin/claude-hust` 路径写入 Sage Mate 配置；
服务器 hosted-web 部署不会安装或启用代码功能。

维护者构建 DMG：

```bash
./quickstart.sh --target mac-dmg
```

本机脚本化安装（不走 DMG）：

```bash
./quickstart.sh --target local-mac-app --app-profile code_assistant --workspace "$HOME/my-repo" --start
```

## 启动后验证

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:55601/
curl -s http://127.0.0.1:55601/healthz
curl -s -N http://127.0.0.1:55601/chat \
  -H 'Content-Type: application/json' \
  -d '{"student_name":"测试同学","question":"请用一句话介绍你自己"}'
```

## 关键配置（.env）

最关键只有这 4 个：

- `DIGITAL_TWIN_LLM_BASE_URL`（例如 `http://127.0.0.1:8000/v1`）
- `DIGITAL_TWIN_API_KEY`（本地直连可用 `EMPTY`；如果启用 systemd OpenAI 代理，请换成真实密钥）
- `DIGITAL_TWIN_MODEL_NAME`（例如 `qwen3-32b`）
- `DIGITAL_TWIN_STREAM_CHAT_ANSWER=true`

vLLM 推理引擎配置（用于 `--with-vllm-engine`）：

- `VLLM_ENGINE_MODEL_PATH`（模型路径，默认 `/data/shared-models/Qwen3-32B`）
- `VLLM_ENGINE_TP_SIZE`（张量并行度，默认 `4`）
- `VLLM_ENGINE_MAX_MODEL_LEN`（最大上下文长度，默认 `32768`）

联网检索（可选）建议再配 2 个：

- `TAVILY_TOKEN`（或 `DIGITAL_TWIN_TAVILY_TOKEN`）
- `DIGITAL_TWIN_WEB_SEARCH_ENABLED=true`

## 服务管理

```bash
./manage.sh status --all               # 查看所有服务状态
./manage.sh start  --all               # 启动全部
./manage.sh stop   --all               # 停止全部
./manage.sh restart --with-vllm-engine # 重启推理引擎
./manage.sh logs   app                 # 跟踪 app 日志
./manage.sh logs   engine              # 跟踪推理引擎日志
./manage.sh install --start            # 重装 systemd 服务并启动（转发到 quickstart.sh）
```

## OpenAI 代理（可选）

如果你想让 `vllm-hust` 通过 systemd 代理对外提供带鉴权的 OpenAI-compatible API，可以启用 `sage-faculty-twin-vllm-openai-proxy.service`。

```bash
./quickstart.sh --with-vllm-proxy --start
./manage.sh restart --with-vllm-proxy
```

代理默认监听 `127.0.0.1:18001`，上游转发到 `127.0.0.1:8000/v1`。启用后，把 `.env` 里的 `DIGITAL_TWIN_API_KEY` 改成真实密钥，并将 `DIGITAL_TWIN_LLM_BASE_URL` 指向 `http://127.0.0.1:18001/v1`。

## Qwen3-32B 模型服务

推理引擎始终运行在 Docker 容器内（设置 `VLLM_ENGINE_CONTAINER` 指向已运行的容器）：

```bash
./quickstart.sh --with-vllm-engine --start
./manage.sh logs engine
```

## 最小排障

- `No module named sage_faculty_twin`：确认通过脚本启动，避免外部 `PYTHONPATH` 覆盖。
- `cannot import name policy from sage.serving.integrations`：说明命中了错误的 `sage` 包，确保 `PYTHONPATH` 包含 `../SAGE/src`。
- `sagevdb` 缺少 `DatabaseConfig` 或提示 C 扩展 ABI 不匹配：运行 `./manage.sh repair-sagevdb` 一键修复。
- `/chat` 422：请求体必须至少包含 `student_name` 与 `question`。
- 页面无流式输出：确认 `.env` 中 `DIGITAL_TWIN_STREAM_CHAT_ANSWER=true`，并确认上游 LLM 支持 chunked streaming。

## 目录入口

- API：`src/sage_faculty_twin/api.py`
- 本地代码模式：`docs/local-code-mode.md`
- 编排：`src/sage_faculty_twin/service.py`
- 首次部署：`quickstart.sh`
- 服务管理：`manage.sh`
- Systemd 启动器：`tools/run_*.sh`（由 systemd `ExecStart` 调用）
