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

## 2. 推荐：下载 Linux 安装器

从 GitHub Release 下载：

```bash
sage-faculty-twin-v4.4.0-linux.run
```

运行：

```bash
chmod +x sage-faculty-twin-v4.4.0-linux.run
./sage-faculty-twin-v4.4.0-linux.run
```

这个 `.run` 文件会自解压到：

```bash
~/.local/share/sage-faculty-twin-installer/sage-faculty-twin-v4.4.0
```

所以即使中途升级 NVIDIA driver 并重启，登录后也能继续安装。

### 安装模式

Linux `.run` 和 macOS `.dmg` 是同一级别的产品入口。`.run` 支持三种模式：

```bash
# 只安装 hosted Faculty Twin web 服务；本地代码能力保持关闭
./sage-faculty-twin-v4.4.0-linux.run --web-only

# 只安装本地 Sage Mate 代码编辑模式
./sage-faculty-twin-v4.4.0-linux.run --code-only

# 两者都装，但使用独立 checkout 和独立端口
./sage-faculty-twin-v4.4.0-linux.run --both
```

`--both` 不会把本地代码能力混入 hosted/web。默认隔离为：

- Web repo: `~/sage-faculty-twin`
- Code repo: `~/sage-mate-local-code`
- Web URL: `http://127.0.0.1:55601/`
- Code URL: `http://127.0.0.1:55611/?setup=local-code`

## 3. 可审计压缩包安装

如果想先查看包内容，也可以下载：

```bash
sage-faculty-twin-v4.4.0.tar.gz
```

解压后进入目录：

```bash
tar -xzf sage-faculty-twin-v4.4.0.tar.gz
cd sage-faculty-twin-v4.4.0
```

然后把 release key 放到目标机器，例如：

```bash
~/.config/sage-faculty-twin/release-secrets.key
```

桌面环境里直接双击 `install.sh`，或在终端执行：

```bash
FACULTY_TWIN_SECRETS_KEY_FILE=~/.config/sage-faculty-twin/release-secrets.key \
  ./install.sh
```

如果 release key 已经放在默认路径，也可以直接：

```bash
./install.sh
```

如果安装器找不到 release key，会先解释这个 key 用来解密私有部署密钥，
然后给用户三个选择：

1. 我已经放好 key，请重新检查；
2. 继续无密钥本地安装；
3. 退出。

选择无密钥安装时，安装器会自动加上 `--no-secrets --no-tunnel`。这条路径不会自动配置
GitHub/HF/Cloudflare/API key，只适合本地验证或后续手动配置。

如果机器安装了 `zenity`，会出现进度条和确认弹窗：

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
  ./install.sh --accelerator nvidia --model-preset qwen2.5-14b-awq
```

## 4. 服务器命令行一键安装

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

## 5. 常用参数

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

## 6. 验收

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

## 7. 安全边界

release installer 会强制：

```bash
DIGITAL_TWIN_DEPLOYMENT_MODE=hosted
DIGITAL_TWIN_APP_PROFILE=faculty_twin
DIGITAL_TWIN_CODE_WORKBENCH_ENABLED=false
DIGITAL_TWIN_CODE_WORKSPACE_ROOTS=
```

不会启用本地 Code Assistant、本地 repo 编辑、服务器目录选择或本地命令执行。

## 8. 密钥说明

GitHub release 只包含 `secrets.env.enc` 密文，不包含解密 key。

解密 key 必须通过服务器预置或 CI secret 下发；不要提交到 GitHub。

`hosted-web.sh` 和 `hosted-web-installer.sh` 都会在 clone 前尝试从同目录
`secrets.env.enc` 解密出必要的 `GITHUB_TOKEN`，并通过临时 `GIT_ASKPASS`
传给 git。token 不会出现在命令行参数或日志里。

## 9. Windows 说明

Hosted/web 形态是 Linux GPU/NPU 服务部署包，真正运行目标仍是 Linux
服务器或带 GPU 直通能力的 WSL/Linux 环境。因此当前发布的是 Linux `.run`
安装器。

Windows 产品化入口应该做成“部署助手”：

- 检测/配置 WSL 或远端 Linux SSH；
- 把 release key 安全放到目标 Linux 用户目录；
- 在目标 Linux 上运行 `.run` 安装器；
- 把最终 URL 和日志带回 Windows UI。

不要把 hosted/web 服务伪装成 Windows native app；那会绕开 NVIDIA/Ascend
驱动、systemd、vLLM 和 Cloudflare tunnel 的真实运行边界。
