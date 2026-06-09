# sage-faculty-twin: 完成 venv 迁移并重启服务

## 背景

之前 `run_app_server.sh` 通过 PYTHONPATH 硬编码拼接 4-5 个源码树（SAGE、neuromem、sageVDB 等），并通过复杂逻辑猜测 Python 解释器路径。这在 Docker 容器、后台进程、conda 环境切换等场景下反复出问题。

**已完成的改造：**
- 新增 `tools/bootstrap_venv.sh` — 创建项目专属 `.venv/`，以 editable 模式安装所有依赖
- 重写 `tools/run_app_server.sh` — 仅使用 `.venv/bin/python`，不再有 PYTHONPATH、解释器猜测
- 简化 `tools/install_user_services.sh` — 去掉了 `resolve_python_bin()` 等复杂逻辑
- 更新 systemd 服务模板 — 移除了 `Environment=PYTHON_BIN=__PYTHON_BIN__`
- 知识库已新增 6 篇论文写作经验文档（data/knowledge_base/ 中已存在）

## 宿主机上需要做的事

### 1. Bootstrap venv（约 2 分钟）

```bash
cd /home/shuhao/sage-faculty-twin
bash tools/bootstrap_venv.sh
```

如果自动发现的 Python 不对，可以手动指定：
```bash
PYTHON_BASE=/home/shuhao/miniconda3/envs/vllm-hust-dev/bin/python bash tools/bootstrap_venv.sh
```

验证：
```bash
.venv/bin/python -c 'from sage_faculty_twin.api import app; print("OK")'
```

### 2. 重装 systemd 服务（如果之前用 systemd 管理）

```bash
bash tools/install_user_services.sh --start
```

或者手动 restart：
```bash
bash manage.sh restart
```

### 3. 如果不用 systemd，直接启动

```bash
bash tools/run_app_server.sh
```

服务默认监听 `127.0.0.1:55601`。

### 4. 验证论文写作知识

服务启动后，测试以下问题看是否能正确召回知识库中的论文写作材料：

```bash
curl -s http://127.0.0.1:55601/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "写英文系统论文时，修改意见该怎么处理？", "session_id": "test-paper-1"}' | python -m json.tool
```

```bash
curl -s http://127.0.0.1:55601/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "论文标题怎么设计比较好？有什么原则？", "session_id": "test-paper-2"}' | python -m json.tool
```

```bash
curl -s http://127.0.0.1:55601/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "怎么发表高水平论文？需要注意什么？", "session_id": "test-paper-3"}' | python -m json.tool
```

---

## 已知问题 & 注意事项

### HF_HOME 权限

宿主机上 `HF_HOME` 环境变量可能指向 `/data/shared-models/.cache/huggingface-shuhao`（当前用户无写权限）。新的 `run_app_server.sh` 已强制覆盖为 `$HOME/.cache/hf-models`。

但如果宿主机 shell profile（`.bashrc` 等）设了 `export HF_HOME=...`，Python 可能在 import 链路的 module-level code 中早于脚本覆盖就读到了旧值。最彻底的解决方案：

1. **推荐**：在宿主机的 `.bashrc` 中不设 `HF_HOME`，或者设为有写权限的路径
2. **备选**：在 `run_app_server.sh` 最开头加 `unset HF_HOME` 然后再设新值

### sentence-transformers 版本

bootstrap 中 `pip install bm25s sentence-transformers faiss-cpu` 可能装到最新版（5.x），但 neuromem 的 pyproject.toml 声明了 `sentence-transformers<4.0.0`。运行时实际兼容没问题，但如果需要严格版本匹配：

```bash
.venv/bin/pip install 'sentence-transformers>=3.1,<4.0' 'transformers>=4.52,<4.54'
```

### 新增的论文写作知识文档

已通过 `tools/ingest_paper_writing_knowledge.py` 脚本注入 6 篇文档：
1. 英文系统论文修改准则（Paper Revision Lessons）
2. 中文综述写作经验（CCCF Chinese Survey Revision Lessons）
3. 第5讲：多维视角看论文写作
4. 第6讲：培养写作能力的若干建议
5. 第7讲：发表高水平论文
6. 第8讲：学术论文写作方法论（Beamer 版）

这些文档已经存在于 `data/knowledge_base/` 目录中，服务启动后应当自动被索引。

---

## 文件变更清单

| 文件 | 动作 |
|------|------|
| `tools/bootstrap_venv.sh` | **新增** — 创建 .venv |
| `tools/run_app_server.sh` | **重写** — 仅用 .venv/bin/python |
| `tools/install_user_services.sh` | **重写** — 简化，去掉解释器探测 |
| `tools/ingest_paper_writing_knowledge.py` | **新增** — 论文写作知识注入脚本 |
| `deploy/systemd/user/sage-faculty-twin-app.service` | **修改** — 移除 PYTHON_BIN |
| `.gitignore` | **修改** — 添加 `.venv/` 和 `.python-bin` |
| `.python-bin` | **可删除** — 旧方案遗留，已无用 |
| `data/knowledge_base/*.json` | **新增 6 篇** — 论文写作知识 |
