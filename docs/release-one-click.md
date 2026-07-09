# Release 一键部署流程

适用目标：全新 Linux 机器上的 hosted/web Faculty Twin / Sage Mate。

## 1. 准备

机器需要：

- `git`
- `curl`
- `python3` 或项目可用 Python 环境
- 本地推理硬件二选一：
  - NVIDIA/CUDA：`nvidia-smi`
  - Ascend/NPU：`npu-smi`
- 如需公网：已安装 `cloudflared`，且当前用户有 `~/.cloudflared/cert.pem`
- 如需自动注入密钥：把解密 key 放到目标机器，例如：

```bash
/home/shuhao/.config/sage-faculty-twin/release-secrets.key
```

## 2. 推荐：双击安装器

下载这三个文件放到同一个目录：

- `hosted-web-installer.sh`
- `hosted-web.sh`
- `secrets.env.enc`（如果需要自动注入 GitHub/HF/Cloudflare/API key）

然后把 release key 放到目标机器，例如：

```bash
~/.config/sage-faculty-twin/release-secrets.key
```

桌面环境里直接双击 `hosted-web-installer.sh`。如果机器安装了 `zenity`，
会出现进度条和确认弹窗：

1. 检查机器和硬件。
2. 如 NVIDIA driver 太旧，弹窗提示升级。
3. 用户确认后调用仓库的 `tools/upgrade_nvidia_driver_for_vllm.sh --yes`。
4. 弹窗询问是否重启。
5. 重启并登录后自动继续安装。
6. 安装完成后运行 `verify-hosted-web` 并显示本地访问地址。

无桌面环境或没有 `zenity` 时，脚本自动退回终端输出。

命令行等价用法：

```bash
FACULTY_TWIN_SECRETS_KEY_FILE=~/.config/sage-faculty-twin/release-secrets.key \
  bash hosted-web-installer.sh --accelerator nvidia --model-preset qwen2.5-14b-awq
```

## 3. 服务器命令行一键安装

```bash
curl -fsSL https://github.com/intellistream/sage-faculty-twin/releases/download/v4.4.0/hosted-web.sh \
  -o /tmp/hosted-web.sh

FACULTY_TWIN_SECRETS_KEY_FILE=/home/shuhao/.config/sage-faculty-twin/release-secrets.key \
  bash /tmp/hosted-web.sh --yes
```

脚本会自动：

- clone / 更新 `intellistream/sage-faculty-twin`
- 同步 pinned submodules
- 只配置 hosted/web 模式
- 自动识别 NVIDIA 或 Ascend
- 安装依赖并启动 systemd 服务
- 配置 Cloudflare tunnel 和 `twin.sage.org.ai`
- 运行 `verify-hosted-web`

## 4. 常用参数

```bash
# 强制 NVIDIA
bash /tmp/hosted-web.sh --accelerator nvidia --yes

# 强制 Ascend
bash /tmp/hosted-web.sh --accelerator ascend --yes

# 不启公网 tunnel，只部署本机服务
bash /tmp/hosted-web.sh --no-tunnel --yes

# NVIDIA 双 A100 使用更大模型
bash /tmp/hosted-web.sh --accelerator nvidia --model-preset qwen3-next-80b-awq --yes

# 自定义域名
bash /tmp/hosted-web.sh --public-hostname twin.example.com --tunnel-name faculty-twin-prod --yes
```

## 5. 验收

```bash
cd ~/sage-faculty-twin

./manage.sh status --with-vllm-proxy --with-site-proxy --with-tunnel \
  --with-nvidia-vllm-engine

env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u http_proxy -u https_proxy -u all_proxy \
  NO_PROXY=127.0.0.1,localhost \
  ./manage.sh verify-hosted-web --public-url https://twin.sage.org.ai/

curl --noproxy '*' -fsS http://127.0.0.1:55601/healthz
curl --noproxy '*' -fsS https://twin.sage.org.ai/healthz
```

Ascend 机器验收状态命令把 `--with-nvidia-vllm-engine` 换成 `--with-vllm-engine`。

## 6. 安全边界

release installer 会强制：

```bash
DIGITAL_TWIN_DEPLOYMENT_MODE=hosted
DIGITAL_TWIN_APP_PROFILE=faculty_twin
DIGITAL_TWIN_CODE_WORKBENCH_ENABLED=false
DIGITAL_TWIN_CODE_WORKSPACE_ROOTS=
```

不会启用本地 Code Assistant、本地 repo 编辑、服务器目录选择或本地命令执行。

## 7. 密钥说明

GitHub release 只包含 `secrets.env.enc` 密文，不包含解密 key。

解密 key 必须通过服务器预置或 CI secret 下发；不要提交到 GitHub。

`hosted-web.sh` 和 `hosted-web-installer.sh` 都会在 clone 前尝试从同目录
`secrets.env.enc` 解密出必要的 `GITHUB_TOKEN`，并通过临时 `GIT_ASKPASS`
传给 git。token 不会出现在命令行参数或日志里。
