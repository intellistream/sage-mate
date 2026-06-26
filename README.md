# sage-faculty-twin

面向单个教师的数字分身应用（FastAPI + SAGE + NeuroMem + OpenAI-compatible LLM）。

## 最重要的结论

- 推荐后端链路：vllm-hust + vllm-ascend-hust（Ascend）。
- 首次部署：`./quickstart.sh`（一键安装环境、依赖、systemd 服务）。
- 运行管理：`./manage.sh`（统一入口：启停、状态、日志）。
- 应用默认监听：`127.0.0.1:55601`。

## 前置条件（最小）

- Linux
- Python 3.11
- 同级目录存在：`../SAGE`、`../neuromem`、`../sageVDB`
- vLLM 推理引擎运行在 Docker 容器内（设置 `VLLM_ENGINE_CONTAINER`）
- 本机可访问 vllm-hust OpenAI 端点（默认 `127.0.0.1:8000`）

## 首次部署

```bash
./quickstart.sh                        # 安装环境、依赖、.env、systemd 服务
./quickstart.sh --with-vllm-engine     # 启用 vLLM 推理引擎服务
./quickstart.sh --start                # 安装并启动 systemd 服务
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
