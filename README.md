# sage-faculty-twin

面向单个教师的数字分身应用（FastAPI + SAGE + NeuroMem + OpenAI-compatible LLM）。

## 最重要的结论

- 推荐后端链路：vllm-hust + vllm-ascend-hust（Ascend）。
- 首次部署：`./quickstart.sh`（一键安装环境、依赖、systemd 服务）。
- 全栈启动（含模型服务）：`bash tools/start_all_services.sh`。
- 应用默认监听：`127.0.0.1:55601`。

## 前置条件（最小）

- Linux
- Python 3.11（使用现有非 venv 环境）
- 同级目录存在：`../SAGE`、`../neuromem`、`../sageVDB`
- 本机可访问 vllm-hust OpenAI 端点（默认 `127.0.0.1:18000`）

## 首次部署

```bash
./quickstart.sh              # 安装环境、依赖、.env、systemd 服务
./quickstart.sh --with-vllm  # 同时安装 vllm-hust（editable）
./quickstart.sh --start      # 安装并启动 systemd 服务
```

## 全栈启动（含模型服务）

```bash
bash tools/start_all_services.sh                        # 默认 preset=coder
bash tools/start_all_services.sh --preset w8a8           # 使用 w8a8 preset
bash tools/start_all_services.sh --skip-model            # 跳过模型服务（已启动时）
```

该脚本会依次：

1. 启动 vLLM 模型服务（通过 vllm-hust-dev-hub launch script）。
2. 安装并启动 sage-faculty-twin app + site proxy。
3. 启动 Cloudflare tunnel。

日常开发/测试直接启动 app：

```bash
bash tools/run_app_server.sh
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

- `DIGITAL_TWIN_LLM_BASE_URL`（例如 `http://127.0.0.1:18000/v1`）
- `DIGITAL_TWIN_API_KEY`（本地直连可用 `EMPTY`；如果启用 systemd OpenAI 代理，请换成真实密钥）
- `DIGITAL_TWIN_MODEL_NAME`（例如 `meta-llama/Llama-3.1-8B-Instruct`）
- `DIGITAL_TWIN_STREAM_CHAT_ANSWER=true`

联网检索（可选）建议再配 2 个：

- `TAVILY_TOKEN`（或 `DIGITAL_TWIN_TAVILY_TOKEN`）
- `DIGITAL_TWIN_WEB_SEARCH_ENABLED=true`

## 服务管理

```bash
./manage.sh status                          # 查看所有服务状态
./manage.sh start | stop | restart          # 管理 app 服务
./manage.sh restart --with-vllm-proxy       # 含 OpenAI 代理
./manage.sh restart --with-tunnel           # 含 Cloudflare 隧道
./manage.sh install --start                 # 重装 systemd 服务并启动
```

## OpenAI 代理（可选）

如果你想让 `vllm-hust` 通过 systemd 代理对外提供带鉴权的 OpenAI-compatible API，可以启用 `sage-faculty-twin-vllm-openai-proxy.service`。

默认的 `./manage.sh restart` 只管理 app 服务，不会自动启用这个代理。需要代理时显式使用：

```bash
./manage.sh install --with-vllm-proxy --start
./manage.sh restart --with-vllm-proxy
```

代理默认监听 `127.0.0.1:18001`，上游转发到 `127.0.0.1:18000/v1`。启用后，把 `.env` 里的 `DIGITAL_TWIN_API_KEY` 改成真实密钥，并将 `DIGITAL_TWIN_LLM_BASE_URL` 指向 `http://127.0.0.1:18001/v1`。

验证方式：

```bash
curl -H 'Authorization: Bearer <your-key>' http://127.0.0.1:18001/v1/models
curl -X POST http://127.0.0.1:18001/v1/chat/completions \
  -H 'Authorization: Bearer <your-key>' \
  -H 'Content-Type: application/json' \
  -d '{"model":"Qwen3-32B","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'
```

## Qwen3-32B 模型服务（Docker 环境）

```bash
./run_qwen3_32b_service.sh            # 启动 Qwen3-32B vllm-hust 服务
./run_qwen3_32b_service.sh --stop     # 优雅停止
```

## 最小排障

- `No module named sage_faculty_twin`：确认通过脚本启动，避免外部 `PYTHONPATH` 覆盖。
- `cannot import name policy from sage.serving.integrations`：说明命中了错误的 `sage` 包，确保 `PYTHONPATH` 包含 `../SAGE/src`。
- `/chat` 422：请求体必须至少包含 `student_name` 与 `question`。
- 页面无流式输出：确认 `.env` 中 `DIGITAL_TWIN_STREAM_CHAT_ANSWER=true`，并确认上游 LLM 支持 chunked streaming。

## 目录入口

- API：`src/sage_faculty_twin/api.py`
- 编排：`src/sage_faculty_twin/service.py`
- 启动脚本：`tools/run_app_server.sh`
- 全栈启动：`tools/start_all_services.sh`
- 首次部署：`quickstart.sh`
- 服务管理：`manage.sh`
