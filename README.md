# sage-faculty-twin

面向单个教师的数字分身应用（FastAPI + SAGE + NeuroMem + OpenAI-compatible LLM）。

## 最重要的结论

- 推荐后端链路：vllm-hust + vllm-ascend-hust（Ascend）。
- 本仓库已提供一键启动脚本：`tools/run_full_stack_with_vllm_hust.sh`。
- 应用默认监听：`127.0.0.1:55601`。

## 前置条件（最小）

- Linux
- Python 3.11（使用现有非 venv 环境）
- 同级目录存在：`../SAGE`、`../neuromem`、`../sageVDB`
- 本机可访问 vllm-hust OpenAI 端点（默认 `127.0.0.1:18000`）

## 一键启动（推荐）

```bash
cd /home/shuhao/sage-faculty-twin
tools/run_full_stack_with_vllm_hust.sh
```

该脚本会做三件事：

1. 检查 `http://127.0.0.1:18000/v1/models` 是否可用（不可用时尝试启动 `vllm-hust serve`）。
2. 自动写入 `.env` 的关键 LLM 配置（base URL、model、stream）。
3. 启动 my-twin（`tools/run_app_server.sh`）。

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

## OpenAI 代理（可选）

如果你想让 `vllm-hust` 通过 systemd 代理对外提供带鉴权的 OpenAI-compatible API，可以启用 `sage-faculty-twin-vllm-openai-proxy.service`。

默认的 `./manage.sh install --start` 和 `./manage.sh restart` 只管理公共 app/site/tunnel 栈，不会自动启用这个代理。需要代理时显式使用：

```bash
./manage.sh install --with-vllm-proxy --start
./manage.sh restart --with-vllm-proxy
```

代理默认监听 `127.0.0.1:18001`，上游转发到 `127.0.0.1:18000/v1`。启用后，把 `.env` 里的 `DIGITAL_TWIN_API_KEY` 改成真实密钥，并将 `DIGITAL_TWIN_LLM_BASE_URL` 指向 `http://127.0.0.1:18001/v1`。

如果 `127.0.0.1:18001` 已经被独立的 `vllm-hust serve` 进程直接占用，就不要启用这个代理；否则它会因为端口冲突而反复重启。

验证方式：

```bash
curl -H 'Authorization: Bearer <your-key>' http://127.0.0.1:18001/v1/models
curl -X POST http://127.0.0.1:18001/v1/chat/completions \
  -H 'Authorization: Bearer <your-key>' \
  -H 'Content-Type: application/json' \
  -d '{"model":"Qwen3-32B","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'
```

## 常用覆盖参数（给一键脚本）

```bash
VLLM_PORT=18000 \
VLLM_MODEL=/data/shared-models/Qwen2.5-7B-Instruct \
VLLM_SERVED_MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct \
VLLM_LOG_PATH=$HOME/logs/vllm-hust-twin.log \
tools/run_full_stack_with_vllm_hust.sh
```

## 最小排障

- `No module named sage_faculty_twin`：确认通过脚本启动，避免外部 `PYTHONPATH` 覆盖。
- `/chat` 422：请求体必须至少包含 `student_name` 与 `question`。
- 页面无流式输出：确认 `.env` 中 `DIGITAL_TWIN_STREAM_CHAT_ANSWER=true`，并确认上游 LLM 支持 chunked streaming。

## 目录入口

- API：`src/sage_faculty_twin/api.py`
- 编排：`src/sage_faculty_twin/service.py`
- 启动脚本：`tools/run_app_server.sh`
- 全栈一键脚本：`tools/run_full_stack_with_vllm_hust.sh`
