# Code Assistant 与 claude-code-hust 集成审计

审计日期：2026-06-28

审计范围：

- `src/sage_faculty_twin/config.py`
- `src/sage_faculty_twin/service.py`
- `src/sage_faculty_twin/code_workbench.py`
- `src/sage_faculty_twin/api.py`
- `src/sage_faculty_twin/web/app.js`
- `src/sage_faculty_twin/web/index.html`
- `tools/install_local_code_mode.sh`
- `docs/local-code-mode.md`

本文只描述当前实现现状、边界和风险，不包含业务代码修改。

## 1. 当前支持的功能

### 配置与模式

当前配置层已经把本地代码能力放在三个开关之后：

- `DIGITAL_TWIN_DEPLOYMENT_MODE=local_code`
- `DIGITAL_TWIN_APP_PROFILE=code_assistant`
- `DIGITAL_TWIN_CODE_WORKBENCH_ENABLED=true`

对应字段定义在 `AppSettings`：

- `app_profile`: `faculty_twin` 或 `code_assistant`
- `deployment_mode`: `hosted` 或 `local_code`
- `code_workbench_enabled`: 是否启用代码工作台
- `code_workspace_roots`: local_code 模式下显式 allowlist 的本地仓库根目录
- `code_agent_backend`: `internal` 或 `claude_hust`
- `claude_hust_cli_path`: 用户本机 `claude-hust` CLI 路径
- `claude_hust_timeout_seconds`: 外部 CLI 调用超时

### Code Workbench HTTP API

`api.py` 暴露了以下代码工作台端点：

- `GET /code/workspaces`: 列出 allowlisted workspace
- `POST /code/search`: 使用 `rg` 搜索代码
- `POST /code/file`: 读取文件片段
- `POST /code/list`: 列目录
- `POST /code/git/status`: 读取 git status
- `POST /code/git/diff`: 读取 git diff
- `POST /code/context`: 打包 workspace、git 状态和文件上下文
- `POST /code/run`: 执行受限命令
- `POST /code/assist`: 代码问答
- `POST /code/propose`: propose-only 修改建议

`/local-code/config` 只允许本机访问，用于读取和保存 local_code 配置。

### Chat 内 `/code` 命令

`DigitalTwinService.answer()` 会在普通聊天流程前拦截 `/code` 或 `代码 ` 前缀。当前命令包括：

- `/code workspaces`
- `/code ls <workspace> [path]`
- `/code search <workspace> <query> [--glob <pattern>]`
- `/code read <workspace> <path> [start_line] [max_lines]`
- `/code status <workspace>`
- `/code diff <workspace> [path] [--staged]`
- `/code context <workspace> [path] ...`
- `/code run <workspace> <read-only command>`
- `/code ask <workspace> <task> [-- <path> ...]`
- `/code propose <workspace> <task> [-- <path> ...]`

前端在 Code Assistant profile 下会把普通自然语言输入自动包装为：

```text
/code ask <selected-workspace> <question>
```

需要 patch 建议时，前端模板显式生成 `/code propose ...`。

### Workspace 与文件边界

`CodeWorkbench` 的 workspace 发现逻辑是：

1. 非 `local_code` 直接返回空 workspace。
2. 非 `code_assistant` 直接返回空 workspace。
3. `code_workbench_enabled=false` 直接返回空 workspace。
4. 优先使用 `code_workspace_roots` 中的显式 allowlist。
5. 如无显式 roots，回退到 legacy managed root `code_workspace_root` 下的子目录。

文件路径通过 `_resolve_path()` 解析，并要求最终路径 `relative_to(workspace.root)` 成功，否则拒绝路径逃逸。

### 受限命令执行

`/code run` 和 `POST /code/run` 当前通过 `shlex.split()` 执行，不走 shell，并有以下限制：

- 禁用 shell metacharacters：`|&;<>`、反引号、`$`、反斜杠、换行等。
- 可执行文件 allowlist：`bun`, `cat`, `find`, `git`, `head`, `ls`, `node`, `npm`, `pnpm`, `pwd`, `pytest`, `python`, `python3`, `rg`, `sed`, `tail`, `wc`。
- 阻断危险词：`chmod`, `chown`, `curl`, `dd`, `docker`, `kill`, `mkfs`, `mount`, `reboot`, `rm`, `shutdown`, `sudo`, `systemctl`, `umount`, `wget`。
- 默认 `allow_write=false`，遇到 `add`, `apply`, `checkout`, `clean`, `commit`, `install`, `merge`, `mv`, `pull`, `push`, `rebase`, `reset`, `restore`, `switch`, `touch` 等写意图词会拒绝。

注意：HTTP 模型里存在 `allow_write` 字段，但前端 `/code run` 命令没有暴露设置该字段的入口。

### 前端本地配置与 Code Assistant UI

前端已有两层本地设置入口：

- 首次设置 modal：选择 `Faculty Twin` 或 `Code Assistant`，配置 LLM、API key、model、runtime folder、workspace roots。
- 设置 drawer 中的完整本地配置：额外支持选择 `Sage Mate internal` 或 `Claude Code Hust CLI`，并配置 CLI path。

Code Assistant 首页支持：

- 添加本地项目路径到 workspace allowlist。
- 选择当前 workspace。
- 展示可用 `/code` 命令。
- 提供解释项目、检查 bug、补测试、生成 patch 的快捷模板。
- 明确标识“本地模式”和“propose-only”。

### 安装脚本

`tools/install_local_code_mode.sh` 支持：

- 选择 `--profile faculty_twin|code_assistant`
- 配置 workspace allowlist、runtime dir、LLM endpoint、API key、model
- `--code-backend auto|internal|claude_hust`
- `--claude-hust-repo`
- `--claude-hust-dir`
- `--skip-claude-hust`

默认 profile 是 `code_assistant`，默认 backend 是 `auto`。macOS DMG 会随包携带
`claude-code-hust` 和 Bun；当 profile 为 `code_assistant` 且未跳过 claude-hust 时，脚本会优先使用包内同步出的
`claude-code-hust` 或显式传入的 `--claude-hust-dir`，成功后写入：

- `DIGITAL_TWIN_CODE_AGENT_BACKEND=claude_hust`
- `DIGITAL_TWIN_CLAUDE_HUST_CLI_PATH=<...>/bin/claude-hust`

如果安装失败且用户没有强制 `--code-backend claude_hust`，则降级到 `internal`。

## 2. claude_hust backend 的调用链

### 用户入口

claude_hust backend 当前只参与两个模型型代码能力：

- `/code ask` 或 `POST /code/assist`
- `/code propose` 或 `POST /code/propose`

浏览、搜索、读取文件、git status、git diff、context、受限 run 仍由 Sage Mate 内置 `CodeWorkbench` 执行。

### HTTP 调用链

以 `POST /code/propose` 为例：

1. `api.py` 的 `propose_code_change()` 接收 `CodeProposeRequest`。
2. FastAPI dependency `require_code_access()` 先检查当前是否为 local Code Assistant；否则直接返回 403。
3. `service.propose_code_change(payload)` 进入 `DigitalTwinService`。
4. `_require_code_workbench_enabled()` 再次检查：
   - `deployment_mode == "local_code"`
   - `code_workbench_enabled == true`
   - `app_profile == "code_assistant"`
5. `DigitalTwinService._code_agent_backend()` 选择 `InternalCodeAgentBackend` 或 `ClaudeHustCodeAgentBackend`。
6. `CodeWorkbench.copy_workspace_to_temp()` 把 allowlisted workspace 复制到临时目录，忽略 `.git`, cache, venv, build, dist, `node_modules`, `vendor` 等目录。
7. `CodeWorkbench.build_propose_prompt()` 在真实 workspace 上读取 git status、git diff 和选择的文件上下文。
8. 组合 prompt，强调：
   - 当前是临时副本。
   - 不要声称真实文件被 edited/saved/committed/pushed/tested。
   - 只输出 JSON：`summary`, `affected_files`, `unified_diff`, `risks`, `suggested_tests`。
9. `ClaudeHustCodeAgentBackend._run_print(prompt, temp_workspace)` 调用本地 CLI，优先使用 JSON 输出并保留 text fallback：

```text
claude-hust --print <prompt> --output-format json --no-session-persistence
claude-hust --print <prompt> --output-format text --no-session-persistence
```

10. subprocess 的 `cwd` 是临时 workspace。
11. 调用完成后清理临时目录。
12. `_strip_thinking_blocks()` 删除 `<think>...</think>`。
13. `_parse_code_proposal()` 尝试把输出解析为结构化 proposal；失败时以 raw text 作为 summary，diff 为空。
14. 返回 `CodeProposeResponse`，并附带 workflow trace。

`POST /code/assist` 的链路类似，但调用 `ClaudeHustCodeAgentBackend.assist()`，输出自由文本 answer，不要求 JSON diff。

### Chat 调用链

以自然语言 Code Assistant 输入为例：

1. `web/app.js` 的 `normalizeCodeAssistantQuestion()` 在 Code Assistant profile 下把普通问题改写为 `/code ask <workspace> <question>`。
2. `/chat` 进入 `DigitalTwinService.answer()`。
3. `answer()` 在普通 workflow 前检测 `_code_workbench_available()` 和 `is_chat_command()`。
4. `_answer_code_workbench_command()` 解析命令。
5. `ask` 调用 `assist_with_code()`；`propose` 调用 `propose_code_change()`。
6. 后续 backend 分支与 HTTP API 相同。

### claude-hust 环境变量与兼容代理

`_claude_hust_env()` 会为 CLI 设置：

- `CC_HUST_SKIP_DOTENV=1`
- `PATH` 前置 `~/.bun/bin`
- `API_TIMEOUT_MS=<claude_hust_timeout_seconds * 1000>`
- `ANTHROPIC_BASE_URL=<settings.llm_base_url>`
- `ANTHROPIC_API_KEY=<settings.api_key>`，如果 API key 非 `EMPTY`
- 如果 base URL 看起来是普通 OpenAI-compatible `/v1` 且不含 `anthropic`：
  - `CLAUDE_CODE_FORCE_RECOVERY_CLI=1`
  - `ANTHROPIC_MODEL=claude-sonnet-4-6`
  - `ANTHROPIC_DEFAULT_*` 使用伪 Claude model names

当 `_should_proxy_openai_for_claude_hust()` 为真时，Sage Mate 启动一个只监听 `127.0.0.1:0` 的短生命周期 `ThreadingHTTPServer`，把 Anthropic `/v1/messages` 请求转换为上游 OpenAI `/chat/completions` 请求。上游模型使用 `settings.model_name`，为空则默认 `qwen3-32b`。

## 3. Internal backend 与 claude_hust backend 的差异

### Internal backend

Internal backend 是 Sage Mate 内置 harness：

- 不启动外部 agent。
- 不复制 workspace 到临时目录。
- 由 `CodeWorkbench` 构建 prompt。
- 直接通过 `VllmChatClient.answer_question_sync()` 调用配置的 OpenAI-compatible LLM。
- `ask` 使用 temperature `0.1`、`max_tokens=2048`、`enable_thinking=False`。
- `propose` 使用 temperature `0.0`、`max_tokens=4096`、`enable_thinking=False`。
- 模型只能看到 Sage Mate 组装的 context pack，不能自主用工具继续探索 repo。
- `propose` 要求 JSON，再解析为 `CodeProposeResponse`。

### claude_hust backend

claude_hust backend 是本机外部 CLI adapter：

- 需要本机存在 `claude-hust` 可执行文件，来源可为配置路径、`PATH`、`~/claude-code-hust/bin/claude-hust`、`~/Documents/claude-code-hust/bin/claude-hust`。
- 在临时 copy 的 workspace 中运行 CLI，降低真实 repo 被写入的风险。
- CLI 可按自身能力读取临时副本、执行自己的工具流程。
- Sage Mate 仍负责 workspace allowlist、路径解析、provider 环境变量、上下文构建、trace、结果解析与 UI 呈现。
- 对 OpenAI-compatible `/v1` endpoint 会启动本机 Anthropic-to-OpenAI 兼容代理。
- `used_model` 返回 `settings.model_name` 或 `self._llm_client.model_name`，不一定等同于 claude-hust 内部看到的伪 Anthropic model name。

### 关键差异总结

| 维度 | internal | claude_hust |
| --- | --- | --- |
| 执行形态 | Python 内置 LLM prompt harness | 本机 `claude-hust` 子进程 |
| Workspace | 只读取真实 allowlisted repo 的 selected/context 文件 | 复制真实 repo 到临时目录，在临时副本中运行 |
| 工具探索 | 无 agent 工具探索，只看 context pack | 由 claude-hust 在临时副本内探索 |
| Provider | 直接走 `VllmChatClient` | 通过 Anthropic env；必要时经本机兼容代理转 OpenAI |
| 输出控制 | prompt 要求 JSON/diff；解析失败 fallback | 同样要求 JSON/diff，但外部 agent 输出更不确定 |
| 安全边界 | Sage Mate 直接控制读取范围 | Sage Mate 控制真实 repo 边界；临时副本内 CLI 能力更宽 |
| 依赖 | 无额外依赖 | 依赖 Bun、`claude-code-hust` checkout、CLI 可执行性 |

## 4. hosted/web 模式必须禁用的能力

hosted/web 模式应保持多用户服务边界，必须禁用以下能力：

- 本地 workspace allowlist 配置与展示。
- 读取、搜索、列目录、打包用户本地 repo 上下文。
- git status 和 git diff。
- `/code run` 或任何服务器侧命令执行。
- `/code ask` 和 `/code propose` 对用户仓库的分析。
- 安装、调用或探测 `claude-code-hust` / `claude-hust`。
- 从 hosted server 启动 Anthropic-to-OpenAI 本地兼容代理来服务代码 agent。
- 在 hosted UI 暴露 local code setup、workspace 添加、Code Backend 选择、CLI path 配置。
- 把用户 repo 上传、clone、缓存或复制到 hosted server。
- 任何 apply patch、commit、push、package install、docker、system service 操作。

当前实现中，核心禁用机制有三层：

1. `require_code_access()` 在非 `local_code + code_workbench_enabled + code_assistant` 时直接返回 403，不走 admin fallback。
2. `CodeWorkbench._discover_workspaces()` 在非 `local_code`、非 `code_assistant`、或 workbench disabled 时返回空。
3. `DigitalTwinService._code_workbench_available()` 要求 `local_code + code_workbench_enabled + code_assistant`。
4. `api.py` 中 `/local-code/config` 要求本机访问且 `deployment_mode == local_code`。

## 5. local_code 模式应该允许的能力

local_code 模式下应该允许的能力是“用户本机、用户显式授权目录、以读和 propose-only 为主”的能力：

- 用户在本机配置 LLM endpoint、API key、model、runtime dir。
- 用户显式添加 workspace roots，保存为 `DIGITAL_TWIN_CODE_WORKSPACE_ROOTS`。
- 列出 allowlisted workspaces。
- 在 allowlisted workspace 内列目录、搜索、读取文本文件片段。
- 读取 git status 和 git diff。
- 构建有限大小的 context pack。
- 运行受限、默认只读的 inspection command。
- 使用 internal backend 做代码问答和 propose-only diff。
- 使用 claude_hust backend 在临时 workspace 副本中做代码问答和 propose-only diff。
- 允许用户显式配置远程 LLM endpoint 做推理，但默认安装必须指向本机 endpoint，且不应让 hosted Sage Mate server 接触 repo。
- 前端允许 Code Assistant profile 的自然语言问题自动转换为 `/code ask`。
- 前端允许用户显式触发 `/code propose` 并审阅 diff、风险和建议测试。

local_code 模式仍不应该默认允许：

- 对真实 repo 自动写文件。
- 自动 apply patch。
- 自动 commit、push、pull、rebase、checkout、install。
- 后台长期运行 agent session 或持久化 claude-hust session。
- 读取 allowlist 外路径。
- 在未确认情况下把大范围私有源码发送给远程模型。

## 6. 当前缺口和风险

### 6.1 hosted code API 在 dependency 层直接拒绝

`require_code_access()` 已在非 local Code Assistant 时直接返回 403，不再允许 hosted admin fallback 进入 service 层。Service 层仍保留 `_require_code_workbench_enabled()` 作为二次防线。

剩余建议：

- 为 hosted 下所有 `/code/*` 端点增加回归测试，避免未来误把 admin diagnostics 接回代码能力。
- 保持 `/local-code/config` 只允许本机访问且只在 `local_code` 模式可用。

### 6.2 `/code run` 的 allowlist 仍包含可能写入的工具

命令校验阻断了常见写意图词和 shell metacharacters，但 allowlist 中包含 `python`, `python3`, `node`, `npm`, `pnpm`, `bun`, `pytest` 等工具。即使 `allow_write=false`，这些工具仍可能通过参数触发写文件、生成缓存、执行项目脚本或网络行为。

当前部分风险由以下机制降低：

- 不走 shell。
- 阻断 `install`、`rm`、`curl`、`wget`、`sudo` 等词。
- 命令 cwd 限制在 workspace。
- 有超时和输出截断。

残余风险：

- `python -c ...` 这类形式没有被专门阻断。
- `node -e ...` 这类形式没有被专门阻断。
- `pytest` 可能写 `.pytest_cache`、生成测试产物，或执行测试中的副作用。
- `npm run <script>` 可能绕过词表表达写入或网络动作。

建议：

- local_code MVP 如强调只读，可把 `/code run` 进一步拆成明确 read-only command profiles。
- 禁止 `python -c`、`node -e`、`npm run`、`pnpm run`、`bun run`，除非有显式确认。
- 对 run 命令加入审计日志和 UI 明确提示。

### 6.3 HTTP `allow_write` 字段存在但缺少确认流

`CodeCommandRequest` 暴露 `allow_write: bool = False`。虽然前端聊天命令不设置它，但任何能调用本地 HTTP API 且通过 code access 的客户端都可以提交 `allow_write=true`。

风险：

- 在 local_code 下，这可能允许 `git add`、`git checkout`、`touch` 等写意图命令通过第一层校验。
- blocked words 仍会阻止一些危险命令，但不是完整 sandbox。

建议：

- 在没有完整 confirmation/apply 流之前，API 层忽略或拒绝 `allow_write=true`。
- 或增加单独配置开关，如 `DIGITAL_TWIN_CODE_ALLOW_WRITE_COMMANDS=false`，默认关闭。

### 6.4 claude_hust 在临时副本内仍是高能力外部 agent

当前设计把 claude-hust 放在临时 workspace 副本中运行，这是正确的主要边界。但 claude-hust 子进程本身仍继承较完整环境变量，并可能执行自身工具链。

风险：

- 子进程继承 `os.environ.copy()`，可能看到不相关环境变量。
- 临时副本可降低真实 repo 写入风险，但不能限制网络访问、进程启动、home 目录读取等外部 agent 行为，具体取决于 `claude-code-hust` 自身实现。
- 如果 workspace 中有 symlink，`copytree(..., symlinks=False)` 会解引用 symlink；指向 workspace 外的大文件或敏感文件时，可能被复制进临时目录。

建议：

- 为 claude-hust subprocess 使用最小环境变量白名单，而不是继承全部环境。
- 在复制 workspace 前显式处理 symlink：跳过 symlink 或只复制指向 workspace 内的 symlink。
- 文档和 UI 明确 claude_hust 是本机高能力 agent，只应在用户信任的 repo 和机器上启用。

### 6.5 claude_hust 输出结构不稳定

`_parse_code_proposal()` 会尽力解析 JSON；解析失败时把 raw text 放到 summary，`unified_diff` 为空。这个 fallback 安全但可能导致用户以为没有 patch，或丢失 agent 生成的非 JSON diff。

建议：

- 在 response 中显式标记 `proposal_parse_status` 或在 risks 中写入“未解析为结构化 JSON”。
- 对 claude_hust backend 增加 fixture 测试，覆盖 fenced JSON、纯 JSON、带思考块、非 JSON 输出。

### 6.6 context_paths 已由 backend adapter 返回

internal backend 与 claude_hust backend 都应返回 `CodeWorkbench.build_*_prompt()` 或 `build_context()` 实际选择的 `context_paths`。这样 UI trace 能显示模型实际看到的默认文件，审计和调试时也更容易还原上下文。

剩余建议：

- 对自动发现文件的 ask/propose 场景增加 fixture，避免后续回归为只返回 `request.paths`。

### 6.7 local setup modal 不暴露 Code Backend

首次 setup modal 只配置 profile、LLM、API key、model、runtime、workspace roots；完整设置 drawer 才暴露 `Code Backend` 与 `Claude Hust CLI Path`。

影响：

- 首次安装脚本可以写入 claude_hust backend。
- 但用户如果从 UI 首次设置进入，不容易立即发现 claude_hust backend 选择项，必须进入完整设置。

建议：

- 如果产品目标是让 Code Assistant 优先使用 claude_hust，可在 setup modal 中显示当前 backend 状态，或提供“高级设置”链接。

### 6.8 安装脚本不应默认 clone claude-code-hust

`install_local_code_mode.sh` 在 `code_assistant` + backend `auto` 下应使用 DMG 内置或用户显式提供的
`claude-code-hust`。只有开发者显式传入 `--claude-hust-repo` 时才允许 clone。

风险：

- 默认安装路径不能依赖 GitHub 可达性，也不能在用户机器上临时下载代码依赖。
- 显式 `--claude-hust-repo` 仍会执行网络下载，应只用于开发/内部调试。
- `docs/local-code-mode.md` 已记录 claude-code-hust 来源与许可边界敏感性；需要确保分发和安装提示足够明确。

建议：

- 在安装脚本输出中增加明确提示：将安装第三方/外部本地 agent，且只适用于本机研究用途。
- 对 `--code-backend auto` 是否自动安装 claude_hust 做产品决策确认；更保守的默认是 internal，用户显式选择 claude_hust 后再安装。

### 6.9 API key 在 local config response 中返回明文

`_local_code_config_response()` 在 API key 已设置且非 `EMPTY` 时返回 `api_key` 明文，前端虽然只用 placeholder 并清空输入框，但响应体仍包含密钥。

风险：

- 本地模式接口限制为 localhost，但浏览器 devtools、日志代理或本机其他进程仍可能读取响应。
- 这与常见 secret handling 习惯不一致。

建议：

- `LocalCodeConfigResponse.api_key` 始终返回空字符串，仅保留 `api_key_set`。
- 保存时留空表示保留，输入新值才覆盖。

### 6.10 缺少端到端安全测试矩阵

当前代码已经有多处边界检查，但这类功能需要防回归测试覆盖：

- hosted 下 `/code/*` 全部拒绝。
- hosted 下 `/local-code/config` 拒绝。
- local_code 但 `faculty_twin` 下 code tools 拒绝。
- local_code + code_assistant 但 workbench disabled 时拒绝。
- workspace path escape 拒绝。
- symlink escape 行为明确。
- `/code run` shell metacharacters、blocked words、write-intent words 拒绝。
- claude_hust CLI missing 时返回可理解错误。
- claude_hust 使用临时目录 cwd，不写真实 repo。

## 总体结论

当前集成已经形成清晰的双层架构：

- Sage Mate 保持外层产品、配置、workspace allowlist、API/UI、workflow trace 和安全边界。
- `claude-code-hust` 仅作为 local_code + code_assistant 下可选的本机 CLI backend，用于 `/code ask` 和 `/code propose`。

实现方向与 `docs/local-code-mode.md` 描述基本一致：hosted 模式不应处理用户仓库；local_code 模式允许用户本机显式授权目录内的读、检索、上下文构建和 propose-only 分析。主要需要补强的是 hosted 端点拒绝语义、`/code run` 写能力边界、claude_hust subprocess 环境最小化、symlink 处理、API key 响应脱敏，以及围绕这些边界的回归测试。

## Parallel Integration Notes

后续并行合并时，以下文件属于高冲突区，应尽量减少跨线程重复编辑，并在合并前优先做局部 diff review：

- `src/sage_faculty_twin/service.py`
- `src/sage_faculty_twin/models.py`
- `src/sage_faculty_twin/api.py`
- `src/sage_faculty_twin/web/app.js`
- `src/sage_faculty_twin/code_workbench.py`

建议合并顺序：

1. audit/doc
2. `/code doctor`
3. backend adapter
4. UI
5. session API
6. structured output
7. demo script

`/code doctor` 应由 doctor 线程实现；UI 和 demo 线程只调用它，不再重复实现。

hosted/web 永远不显示 profile switcher / code tools / local repo entry。
