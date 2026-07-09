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

## 2. 一键安装

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

## 3. 常用参数

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

## 4. 验收

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

## 5. 安全边界

release installer 会强制：

```bash
DIGITAL_TWIN_DEPLOYMENT_MODE=hosted
DIGITAL_TWIN_APP_PROFILE=faculty_twin
DIGITAL_TWIN_CODE_WORKBENCH_ENABLED=false
DIGITAL_TWIN_CODE_WORKSPACE_ROOTS=
```

不会启用本地 Code Assistant、本地 repo 编辑、服务器目录选择或本地命令执行。

## 6. 密钥说明

GitHub release 只包含 `secrets.env.enc` 密文，不包含解密 key。

解密 key 必须通过服务器预置或 CI secret 下发；不要提交到 GitHub。
