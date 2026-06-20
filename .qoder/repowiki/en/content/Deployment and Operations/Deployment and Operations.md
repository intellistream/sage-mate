# Deployment and Operations

<cite>
**Referenced Files in This Document**
- [deployment.md](file://docs/deployment.md)
- [systemd-runtime-notes.md](file://docs/systemd-runtime-notes.md)
- [sage-faculty-twin-app.service](file://deploy/systemd/user/sage-faculty-twin-app.service)
- [sage-faculty-twin-site.service](file://deploy/systemd/user/sage-faculty-twin-site.service)
- [sage-faculty-twin-tunnel.service](file://deploy/systemd/user/sage-faculty-twin-tunnel.service)
- [sage-faculty-twin-vllm-engine.service](file://deploy/systemd/user/sage-faculty-twin-vllm-engine.service)
- [sage-faculty-twin-vllm-openai-proxy.service](file://deploy/systemd/user/sage-faculty-twin-vllm-openai-proxy.service)
- [manage.sh](file://manage.sh)
- [quickstart.sh](file://quickstart.sh)
- [runtime_env.sh](file://tools/lib/runtime_env.sh)
- [run_vllm_engine.sh](file://tools/run_vllm_engine.sh)
- [run_app_server.sh](file://tools/run_app_server.sh)
- [run_local_proxy.sh](file://tools/run_local_proxy.sh)
- [reload_local_proxy.sh](file://tools/reload_local_proxy.sh)
- [run_named_tunnel.sh](file://tools/run_named_tunnel.sh)
- [run_vllm_openai_proxy.sh](file://tools/run_vllm_openai_proxy.sh)
- [nginx-local.conf](file://tools/nginx-local.conf)
- [cloudflared-config.example.yml](file://tools/cloudflared-config.example.yml)
- [ci.yml](file://.github/workflows/ci.yml)
</cite>

## Update Summary
**Changes Made**
- Updated to reflect the streamlined deployment process with consolidated scripts
- Documented the enhanced CI/CD workflow with --no-siblings flag for faster sibling repository handling
- Updated service management workflow to reflect the consolidated approach replacing previous multi-script system
- Enhanced deployment documentation to show improved service installation and management procedures

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Monitoring and Logging](#monitoring-and-logging)
9. [Maintenance Procedures](#maintenance-procedures)
10. [Scaling Considerations](#scaling-considerations)
11. [Backup and Disaster Recovery](#backup-and-disaster-recovery)
12. [Troubleshooting Guide](#troubleshooting-guide)
13. [Conclusion](#conclusion)

## Introduction
This document provides comprehensive deployment and operations guidance for the Sage Faculty Twin system. It covers systemd user service configuration, service management scripts, production deployment procedures, monitoring/logging, maintenance, scaling, backup, and disaster recovery. The system now features a unified service management approach that consolidates all deployment operations into two primary entry points: manage.sh for runtime operations and quickstart.sh for installation and setup. Recent enhancements include improved CI/CD workflows with the --no-siblings flag for faster sibling repository handling and streamlined service management procedures.

## Project Structure
The deployment artifacts and operational scripts are organized as follows:
- Systemd user service units under deploy/systemd/user
- Management and orchestration scripts under tools and at repo root
- Unified runtime management via manage.sh and quickstart.sh
- Operational documentation under docs
- CI/CD workflows under .github/workflows

```mermaid
graph TB
subgraph "Systemd User Units"
APP["sage-faculty-twin-app.service"]
SITE["sage-faculty-twin-site.service"]
TUN["sage-faculty-twin-tunnel.service"]
ENGINE["sage-faculty-twin-vllm-engine.service"]
VPXY["sage-faculty-twin-vllm-openai-proxy.service"]
end
subgraph "Unified Management Scripts"
MNG["manage.sh"]
QS["quickstart.sh"]
ENV["runtime_env.sh"]
end
subgraph "Runtime Launchers"
RUNAPP["run_app_server.sh"]
RUNSITE["run_local_proxy.sh"]
RUNTUN["run_named_tunnel.sh"]
RUNENGINE["run_vllm_engine.sh"]
RUNVPXY["run_vllm_openai_proxy.sh"]
RELOAD["reload_local_proxy.sh"]
NGINX["nginx-local.conf"]
CFYML["cloudflared-config.example.yml"]
end
subgraph "CI/CD Infrastructure"
CI["GitHub Actions CI"]
end
MNG --> ENV
QS --> ENV
ENV --> APP
ENV --> SITE
ENV --> TUN
ENV --> ENGINE
ENV --> VPXY
APP --> RUNAPP
SITE --> RUNSITE
TUN --> RUNTUN
ENGINE --> RUNENGINE
VPXY --> RUNVPXY
RUNSITE --> NGINX
RUNTUN --> CFYML
CI --> QS
CI --> MNG
```

**Diagram sources**
- [sage-faculty-twin-app.service](file://deploy/systemd/user/sage-faculty-twin-app.service)
- [sage-faculty-twin-site.service](file://deploy/systemd/user/sage-faculty-twin-site.service)
- [sage-faculty-twin-tunnel.service](file://deploy/systemd/user/sage-faculty-twin-tunnel.service)
- [sage-faculty-twin-vllm-engine.service](file://deploy/systemd/user/sage-faculty-twin-vllm-engine.service)
- [sage-faculty-twin-vllm-openai-proxy.service](file://deploy/systemd/user/sage-faculty-twin-vllm-openai-proxy.service)
- [manage.sh](file://manage.sh)
- [quickstart.sh](file://quickstart.sh)
- [runtime_env.sh](file://tools/lib/runtime_env.sh)
- [run_vllm_engine.sh](file://tools/run_vllm_engine.sh)
- [run_app_server.sh](file://tools/run_app_server.sh)
- [run_local_proxy.sh](file://tools/run_local_proxy.sh)
- [run_named_tunnel.sh](file://tools/run_named_tunnel.sh)
- [run_vllm_openai_proxy.sh](file://tools/run_vllm_openai_proxy.sh)
- [nginx-local.conf](file://tools/nginx-local.conf)
- [cloudflared-config.example.yml](file://tools/cloudflared-config.example.yml)
- [ci.yml](file://.github/workflows/ci.yml)

**Section sources**
- [deployment.md](file://docs/deployment.md)
- [systemd-runtime-notes.md](file://docs/systemd-runtime-notes.md)

## Core Components
- **Application server**: FastAPI app served via uvicorn, launched by run_app_server.sh and managed by the app systemd unit.
- **Local site proxy**: Nginx-based reverse proxy for local development and compatibility routes, launched by run_local_proxy.sh and managed by the site systemd unit.
- **Cloudflare tunnel**: Named tunnel managed by run_named_tunnel.sh and systemd unit; forwards traffic to the local site proxy.
- **vLLM inference engine**: Qwen3-32B model service managed by run_vllm_engine.sh and systemd unit with Ascend NPU acceleration.
- **OpenAI-compatible vLLM proxy**: Optional OpenAI-compatible proxy for model requests, launched by run_vllm_openai_proxy.sh and managed by the vllm-openai-proxy systemd unit.
- **Unified management**: manage.sh orchestrates all service actions with JSON output support; quickstart.sh bootstraps environment, installs services, and manages systemd units.
- **Runtime environment**: runtime_env.sh provides deterministic Python interpreter and PYTHONPATH resolution across all entry points.
- **Enhanced CI/CD**: GitHub Actions workflow with --no-siblings flag for optimized sibling repository handling during automated deployments.

Key operational variables and ports:
- Application server port: configurable via APP_PORT (default 55601)
- Site proxy port: configurable via SITE_PORT (default 8088)
- vLLM engine host/port: configurable via VLLM_ENGINE_HOST/VLLM_ENGINE_PORT (default 0.0.0.0:18000)
- vLLM proxy host/port: configurable via VLLM_PROXY_HOST/VLLM_PROXY_PORT (default 127.0.0.1:18001)
- Upstream base URL for vLLM proxy: VLLM_PROXY_UPSTREAM_BASE_URL (default http://127.0.0.1:18000/v1)
- Path prefix for vLLM proxy: VLLM_PROXY_PATH_PREFIX (default /v1)
- Qwen3-32B model service: Ascend NPU acceleration with tensor parallel size 4

**Section sources**
- [sage-faculty-twin-app.service](file://deploy/systemd/user/sage-faculty-twin-app.service)
- [sage-faculty-twin-site.service](file://deploy/systemd/user/sage-faculty-twin-site.service)
- [sage-faculty-twin-tunnel.service](file://deploy/systemd/user/sage-faculty-twin-tunnel.service)
- [sage-faculty-twin-vllm-engine.service](file://deploy/systemd/user/sage-faculty-twin-vllm-engine.service)
- [sage-faculty-twin-vllm-openai-proxy.service](file://deploy/systemd/user/sage-faculty-twin-vllm-openai-proxy.service)
- [run_app_server.sh](file://tools/run_app_server.sh)
- [run_local_proxy.sh](file://tools/run_local_proxy.sh)
- [run_named_tunnel.sh](file://tools/run_named_tunnel.sh)
- [run_vllm_engine.sh](file://tools/run_vllm_engine.sh)
- [run_vllm_openai_proxy.sh](file://tools/run_vllm_openai_proxy.sh)
- [nginx-local.conf](file://tools/nginx-local.conf)
- [cloudflared-config.example.yml](file://tools/cloudflared-config.example.yml)

## Architecture Overview
The deployment topology consists of unified service management with streamlined operations and enhanced CI/CD workflows:
- **Model layer**: vLLM-HUST inference engine with Ascend NPU acceleration for Qwen3-32B
- **Application layer**: FastAPI app exposing chat and related endpoints
- **Proxy layer**: Local Nginx proxy for local development and compatibility routes; optional Cloudflare tunnel for public ingress
- **Control plane**: Unified systemd user services and consolidated management scripts
- **CI/CD pipeline**: GitHub Actions workflow with optimized sibling repository handling via --no-siblings flag

```mermaid
graph TB
subgraph "External"
CF["Cloudflare Tunnel"]
VLLM["External vLLM Serving"]
end
subgraph "Host"
subgraph "Model Layer"
ENGINE["vLLM-HUST Engine<br/>Qwen3-32B (Ascend NPU)"]
RUNENG["run_vllm_engine.sh"]
ENDSUB
subgraph "Proxy Layer"
NGINX["Local Nginx (site)"]
TUNNEL["Cloudflared Tunnel"]
end
subgraph "Application Layer"
APP["FastAPI App (:55601)"]
VPXY["OpenAI-compatible vLLM Proxy (:18001)"]
end
subgraph "Control Plane"
SYS["systemd --user"]
MGMT["manage.sh / quickstart.sh"]
ENV["runtime_env.sh"]
CI["GitHub Actions CI"]
ENDSUB
end
CF --> TUNNEL
TUNNEL --> NGINX
NGINX --> APP
APP --> VPXY
ENGINE --> VPXY
RUNENG --> ENGINE
SYS --> APP
SYS --> NGINX
SYS --> TUNNEL
SYS --> VPXY
SYS --> ENGINE
MGMT --> SYS
ENV --> MGMT
ENV --> SYS
CI --> QS
CI --> MNG
```

**Diagram sources**
- [deployment.md](file://docs/deployment.md)
- [systemd-runtime-notes.md](file://docs/systemd-runtime-notes.md)
- [sage-faculty-twin-app.service](file://deploy/systemd/user/sage-faculty-twin-app.service)
- [sage-faculty-twin-site.service](file://deploy/systemd/user/sage-faculty-twin-site.service)
- [sage-faculty-twin-tunnel.service](file://deploy/systemd/user/sage-faculty-twin-tunnel.service)
- [sage-faculty-twin-vllm-engine.service](file://deploy/systemd/user/sage-faculty-twin-vllm-engine.service)
- [sage-faculty-twin-vllm-openai-proxy.service](file://deploy/systemd/user/sage-faculty-twin-vllm-openai-proxy.service)
- [run_app_server.sh](file://tools/run_app_server.sh)
- [run_local_proxy.sh](file://tools/run_local_proxy.sh)
- [run_named_tunnel.sh](file://tools/run_named_tunnel.sh)
- [run_vllm_engine.sh](file://tools/run_vllm_engine.sh)
- [run_vllm_openai_proxy.sh](file://tools/run_vllm_openai_proxy.sh)
- [nginx-local.conf](file://tools/nginx-local.conf)
- [cloudflared-config.example.yml](file://tools/cloudflared-config.example.yml)
- [ci.yml](file://.github/workflows/ci.yml)

## Detailed Component Analysis

### Application Server
- **Purpose**: Host the FastAPI application on loopback interface
- **Startup**: Managed by systemd unit; ExecStart invokes run_app_server.sh which sets environment, validates knowledge backend dependencies, and starts uvicorn
- **Ports**: Listens on 127.0.0.1:APP_PORT (default 55601)
- **Environment**: PYTHON_BIN, APP_PORT, DIGITAL_TWIN_HOMEPAGE_PUBLIC_URL, and .env-loaded variables

```mermaid
sequenceDiagram
participant U as "systemd --user"
participant SVC as "sage-faculty-twin-app.service"
participant SH as "run_app_server.sh"
participant UV as "uvicorn"
participant APP as "FastAPI App"
U->>SVC : Start
SVC->>SH : ExecStart
SH->>SH : Export repo runtime env and .env
SH->>SH : Validate knowledge backend deps
SH->>UV : Start uvicorn on 127.0.0.1 : APP_PORT
UV->>APP : Serve endpoints
```

**Diagram sources**
- [sage-faculty-twin-app.service](file://deploy/systemd/user/sage-faculty-twin-app.service)
- [run_app_server.sh](file://tools/run_app_server.sh)

**Section sources**
- [sage-faculty-twin-app.service](file://deploy/systemd/user/sage-faculty-twin-app.service)
- [run_app_server.sh](file://tools/run_app_server.sh)
- [deployment.md](file://docs/deployment.md)

### Local Site Proxy
- **Purpose**: Provide local development site and compatibility routes (/home, /home/) and proxy to the app
- **Startup**: Managed by systemd unit; ExecStart invokes run_local_proxy.sh which waits for the app and then starts Nginx using tools/nginx-local.conf
- **Ports**: Listens on SITE_PORT (default 8088); proxies to APP_PORT
- **Reload**: reload_local_proxy.sh regenerates config, validates, and reloads Nginx

```mermaid
sequenceDiagram
participant U as "systemd --user"
participant SVC as "sage-faculty-twin-site.service"
participant SH as "run_local_proxy.sh"
participant NG as "Nginx"
participant APP as "FastAPI App"
U->>SVC : Start
SVC->>SH : ExecStart
SH->>SH : Wait for http : //127.0.0.1 : APP_PORT
SH->>NG : Start with generated nginx.conf
NG->>APP : Proxy / and /home(/) to APP_PORT
```

**Diagram sources**
- [sage-faculty-twin-site.service](file://deploy/systemd/user/sage-faculty-twin-site.service)
- [run_local_proxy.sh](file://tools/run_local_proxy.sh)
- [reload_local_proxy.sh](file://tools/reload_local_proxy.sh)
- [nginx-local.conf](file://tools/nginx-local.conf)

**Section sources**
- [sage-faculty-twin-site.service](file://deploy/systemd/user/sage-faculty-twin-site.service)
- [run_local_proxy.sh](file://tools/run_local_proxy.sh)
- [reload_local_proxy.sh](file://tools/reload_local_proxy.sh)
- [nginx-local.conf](file://tools/nginx-local.conf)
- [deployment.md](file://docs/deployment.md)

### Cloudflare Tunnel
- **Purpose**: Provide public ingress via Cloudflare Tunnel to the local site proxy
- **Startup**: Managed by systemd unit; ExecStart invokes run_named_tunnel.sh which waits for the local site proxy and then runs cloudflared with credentials and config
- **Configuration**: Requires a Cloudflare tunnel config YAML with hostname and service mapping to 127.0.0.1:8088

```mermaid
sequenceDiagram
participant U as "systemd --user"
participant SVC as "sage-faculty-twin-tunnel.service"
participant SH as "run_named_tunnel.sh"
participant CF as "cloudflared"
participant SITE as "Local Site Proxy"
U->>SVC : Start
SVC->>SH : ExecStart
SH->>SH : Wait for http : //127.0.0.1 : 8088
SH->>CF : Run tunnel with config.yml
CF->>SITE : Forward traffic to 127.0.0.1 : 8088
```

**Diagram sources**
- [sage-faculty-twin-tunnel.service](file://deploy/systemd/user/sage-faculty-twin-tunnel.service)
- [run_named_tunnel.sh](file://tools/run_named_tunnel.sh)
- [cloudflared-config.example.yml](file://tools/cloudflared-config.example.yml)

**Section sources**
- [sage-faculty-twin-tunnel.service](file://deploy/systemd/user/sage-faculty-twin-tunnel.service)
- [run_named_tunnel.sh](file://tools/run_named_tunnel.sh)
- [cloudflared-config.example.yml](file://tools/cloudflared-config.example.yml)
- [deployment.md](file://docs/deployment.md)

### vLLM Inference Engine
- **Purpose**: Provide Qwen3-32B model inference service with Ascend NPU acceleration
- **Startup**: Managed by systemd unit; ExecStart invokes run_vllm_engine.sh which loads .env configuration and launches vllm-hust serve
- **Configuration**: All tunable parameters read from .env (model_path, served_model_name, host, port, tp_size, max_model_len, gpu_mem_util, api_key)
- **Hardware**: Ascend NPU acceleration with configurable device selection via ASCEND_RT_VISIBLE_DEVICES

```mermaid
sequenceDiagram
participant U as "systemd --user"
participant SVC as "sage-faculty-twin-vllm-engine.service"
participant SH as "run_vllm_engine.sh"
participant VLLM as "vllm-hust"
participant MODEL as "Qwen3-32B"
U->>SVC : Start
SVC->>SH : ExecStart
SH->>SH : Load .env configuration
SH->>SH : Set ASCEND_RT_VISIBLE_DEVICES if specified
SH->>VLLM : Launch vllm-hust serve with Qwen3-32B
VLLM->>MODEL : Initialize model with tensor parallel size 4
Note over VLLM,MODEL : GPU memory utilization 0.85<br/>Graph mode enabled<br/>Max model length 32768
```

**Diagram sources**
- [sage-faculty-twin-vllm-engine.service](file://deploy/systemd/user/sage-faculty-twin-vllm-engine.service)
- [run_vllm_engine.sh](file://tools/run_vllm_engine.sh)

**Section sources**
- [sage-faculty-twin-vllm-engine.service](file://deploy/systemd/user/sage-faculty-twin-vllm-engine.service)
- [run_vllm_engine.sh](file://tools/run_vllm_engine.sh)
- [deployment.md](file://docs/deployment.md)

### OpenAI-Compatible vLLM Proxy
- **Purpose**: Provide an OpenAI-compatible interface for model requests, optionally forwarding to a local vLLM instance
- **Startup**: Managed by systemd unit; ExecStart invokes run_vllm_openai_proxy.sh which checks port availability, validates uvicorn presence, and starts either the internal proxy app or a key proxy
- **Ports**: Listens on VLLM_PROXY_HOST:VLLM_PROXY_PORT (default 127.0.0.1:18001)
- **Upstream**: VLLM_PROXY_UPSTREAM_BASE_URL (default http://127.0.0.1:18000/v1), path prefix VLLM_PROXY_PATH_PREFIX (default /v1)

```mermaid
sequenceDiagram
participant U as "systemd --user"
participant SVC as "sage-faculty-twin-vllm-openai-proxy.service"
participant SH as "run_vllm_openai_proxy.sh"
participant UV as "uvicorn"
participant VP as "vLLM/OpenAI-compatible Endpoint"
U->>SVC : Start
SVC->>SH : ExecStart
SH->>SH : Check port availability
SH->>UV : Start internal proxy app or key proxy
UV->>VP : Proxy OpenAI-compatible requests
```

**Diagram sources**
- [sage-faculty-twin-vllm-openai-proxy.service](file://deploy/systemd/user/sage-faculty-twin-vllm-openai-proxy.service)
- [run_vllm_openai_proxy.sh](file://tools/run_vllm_openai_proxy.sh)

**Section sources**
- [sage-faculty-twin-vllm-openai-proxy.service](file://deploy/systemd/user/sage-faculty-twin-vllm-openai-proxy.service)
- [run_vllm_openai_proxy.sh](file://tools/run_vllm_openai_proxy.sh)
- [deployment.md](file://docs/deployment.md)

### Unified Management Workflow
- **manage.sh**: Single entry point for all runtime operations including status, start, stop, restart, and logs with JSON output support
- **quickstart.sh**: Complete installation and setup script handling environment bootstrap, dependency installation, systemd unit rendering, and service management
- **runtime_env.sh**: Provides deterministic Python interpreter and PYTHONPATH resolution across all entry points
- **Service registry**: Centralized service management with optional components (engine, proxy, site, tunnel)
- **Enhanced CI/CD**: GitHub Actions workflow with --no-siblings flag for optimized sibling repository handling

```mermaid
flowchart TD
Start([Start]) --> QS["quickstart.sh"]
QS --> DEPS["Install deps and .env"]
QS --> RENDER["Render systemd units with __REPO_ROOT__ and __PYTHON_BIN__"]
RENDER --> ENABLE["Enable selected units"]
ENABLE --> ACTION{"--start?"}
ACTION --> |Yes| START["systemctl --user restart units"]
ACTION --> |No| DONE([Done])
MNG["manage.sh"] --> ACTION2{"Action"}
ACTION2 --> STATUS["status"]
ACTION2 --> START2["start/stop/restart"]
ACTION2 --> LOGS["logs"]
START2 --> APPLY["systemctl --user apply"]
STATUS --> JSON["JSON output support"]
LOGS --> JOURNAL["journalctl --user follow"]
ALL["Service Registry"] --> APP["Application Service"]
ALL --> SITE["Site Proxy Service"]
ALL --> TUN["Tunnel Service"]
ALL --> ENGINE["Engine Service"]
ALL --> VPXY["VLLM Proxy Service"]
CI["GitHub Actions CI"] --> QS
CI --> MNG
```

**Diagram sources**
- [quickstart.sh](file://quickstart.sh)
- [manage.sh](file://manage.sh)
- [runtime_env.sh](file://tools/lib/runtime_env.sh)
- [ci.yml](file://.github/workflows/ci.yml)

**Section sources**
- [manage.sh](file://manage.sh)
- [quickstart.sh](file://quickstart.sh)
- [runtime_env.sh](file://tools/lib/runtime_env.sh)
- [systemd-runtime-notes.md](file://docs/systemd-runtime-notes.md)

## Dependency Analysis
- **Startup ordering**:
  - app.service starts first
  - site.service requires app.service and starts after
  - tunnel.service requires site.service and starts after
  - vllm-engine.service is independent and optional
  - vllm-openai-proxy.service is independent and optional
- **Inter-process dependencies**:
  - site.proxy depends on app.port readiness
  - tunnel depends on site.port readiness
  - vllm-openai-proxy may depend on vllm-engine or external vLLM depending on configuration
  - Model service operates independently with its own vLLM-HUST process
- **Environment propagation**:
  - .env is exported into process environment before launching uvicorn in run_app_server.sh
  - Variables like DIGITAL_TWIN_STREAM_CHAT_ANSWER, DIGITAL_TWIN_CHAT_REQUEST_TIMEOUT_SECONDS, and others are read at module import time
  - runtime_env.sh ensures consistent PYTHON_BIN and PYTHONPATH across all scripts

```mermaid
graph LR
APP["app.service"] --> SITE["site.service"]
SITE --> TUN["tunnel.service"]
APP -. optional .-> VPXY["vllm-openai-proxy.service"]
APP -. optional .-> ENGINE["vllm-engine.service"]
RUNTIME["runtime_env.sh"] --> APP
RUNTIME --> SITE
RUNTIME --> TUN
RUNTIME --> ENGINE
RUNTIME --> VPXY
```

**Diagram sources**
- [sage-faculty-twin-app.service](file://deploy/systemd/user/sage-faculty-twin-app.service)
- [sage-faculty-twin-site.service](file://deploy/systemd/user/sage-faculty-twin-site.service)
- [sage-faculty-twin-tunnel.service](file://deploy/systemd/user/sage-faculty-twin-tunnel.service)
- [sage-faculty-twin-vllm-engine.service](file://deploy/systemd/user/sage-faculty-twin-vllm-engine.service)
- [sage-faculty-twin-vllm-openai-proxy.service](file://deploy/systemd/user/sage-faculty-twin-vllm-openai-proxy.service)
- [runtime_env.sh](file://tools/lib/runtime_env.sh)

**Section sources**
- [deployment.md](file://docs/deployment.md)
- [systemd-runtime-notes.md](file://docs/systemd-runtime-notes.md)

## Performance Considerations
- **Streaming and chunked transfer**:
  - Ensure the upstream OpenAI-compatible endpoint emits Transfer-Encoding: chunked for per-token streaming
  - Verify streaming end-to-end with a curl command against the upstream endpoint
- **Proxy tuning**:
  - Increase client_max_body_size and timeouts in the host Nginx to match application limits and avoid early truncation
  - Disable proxy buffering for streaming endpoints
- **Request timeouts**:
  - Tune DIGITAL_TWIN_CHAT_REQUEST_TIMEOUT_SECONDS and DIGITAL_TWIN_LLM_TIMEOUT_SECONDS to stay comfortably below Cloudflare's edge timeout
- **SSE keepalive**:
  - Configure DIGITAL_TWIN_CHAT_SSE_KEEPALIVE_SECONDS to maintain long-lived streams
- **Model service optimization**:
  - Qwen3-32B service uses tensor parallel size 4 with optimized cuDNN graph modes for better performance
  - GPU memory utilization set to 0.85 for efficient resource usage
  - Ascend NPU acceleration provides hardware-specific optimizations with configurable device selection

**Section sources**
- [deployment.md](file://docs/deployment.md)
- [run_vllm_engine.sh](file://tools/run_vllm_engine.sh)

## Monitoring and Logging
- **Health checks**:
  - Use curl to probe health endpoints on the app and public ingress
  - Monitor vLLM engine health via its HTTP API
- **Logs**:
  - Nginx error and access logs are configured under .runtime/nginx
  - systemd user journal for service states and errors
  - journalctl integration for centralized log viewing
- **Observability**:
  - Monitor CPU, memory, and disk usage of the app and proxy
  - Track Cloudflare tunnel connectivity and latency
  - Monitor Ascend NPU utilization for model service

**Section sources**
- [systemd-runtime-notes.md](file://docs/systemd-runtime-notes.md)
- [nginx-local.conf](file://tools/nginx-local.conf)
- [run_vllm_engine.sh](file://tools/run_vllm_engine.sh)

## Maintenance Procedures
- **Service lifecycle**:
  - Use manage.sh status/start/stop/restart to control services with JSON output support
  - Use quickstart.sh --start to start services after initial install
  - Use manage.sh start --with-model for foreground model engine startup
- **Configuration updates**:
  - Update .env and reload the site proxy using reload_local_proxy.sh or restart the site service
  - Update model service configuration through .env variables for vllm-engine
- **Environment management**:
  - runtime_env.sh provides deterministic Python interpreter resolution
  - The installer persists the chosen Python interpreter to avoid drift across reinstalls
  - Ensure XDG_RUNTIME_DIR and DBUS_SESSION_BUS_ADDRESS are set for user systemd operations
- **Model service maintenance**:
  - Use manage.sh start --with-model for graceful model service startup
  - Monitor vLLM engine logs via journalctl integration
  - Update model weights through vllm engine configuration
- **CI/CD maintenance**:
  - Use --no-siblings flag in CI/CD pipelines for faster sibling repository handling
  - GitHub Actions workflow automatically handles service management and deployment

**Section sources**
- [manage.sh](file://manage.sh)
- [quickstart.sh](file://quickstart.sh)
- [runtime_env.sh](file://tools/lib/runtime_env.sh)
- [systemd-runtime-notes.md](file://docs/systemd-runtime-notes.md)
- [run_vllm_engine.sh](file://tools/run_vllm_engine.sh)
- [ci.yml](file://.github/workflows/ci.yml)

## Scaling Considerations
- **Horizontal scaling**:
  - Run multiple instances of the app server behind a load balancer; ensure sticky sessions if required by SSE/long-lived connections
  - Scale model service by adjusting tensor parallel size and container resources
- **Vertical scaling**:
  - Increase worker processes in uvicorn for CPU-bound workloads; adjust Nginx worker_processes accordingly
  - Optimize model service with higher tensor parallel size for multi-NPU setups
- **Model scaling**:
  - Scale vLLM horizontally or vertically depending on throughput and latency targets; ensure the proxy configuration matches the new topology
  - Use vllm engine resource limits to control model service resource allocation
- **Caching**:
  - Leverage Nginx caching for static assets; tune cache sizes and TTLs
  - Implement model caching strategies for frequently accessed models

## Backup and Disaster Recovery
- **Data protection**:
  - Back up the repository, .env, and runtime directories (e.g., .runtime/nginx, .runtime/cloudflared)
  - Backup vLLM engine model data and configuration
- **Recovery**:
  - Restore repository and runtime artifacts; re-run quickstart.sh to re-install services and dependencies
  - Recreate vLLM engine with backed-up model data and configuration
- **Offsite storage**:
  - Store backups in secure, offsite locations with checksum verification
  - Maintain separate backups for application data and model artifacts

## Troubleshooting Guide
- **Services not starting**:
  - Check systemd user status for each unit; verify ExecStart paths and environment variables
  - Verify vLLM-HUST binary is available in PATH for model service management
- **Port conflicts**:
  - The vLLM proxy script checks for port availability and exits with a clear message if the port is already in use
  - Model service uses port 18000; ensure it's available or configure alternative port
- **Missing Python runtime**:
  - runtime_env.sh resolves a working Python interpreter and persists it; ensure the environment is set for user systemd
- **Streaming not working**:
  - Verify upstream endpoint emits Transfer-Encoding: chunked; confirm DIGITAL_TWIN_STREAM_CHAT_ANSWER is set appropriately
- **Proxy timeouts and 413 errors**:
  - Adjust client_max_body_size and proxy timeouts in the host Nginx configuration to match application limits
- **Model service issues**:
  - Check vLLM engine logs via journalctl integration for initialization errors
  - Verify Ascend NPU drivers and device accessibility
  - Monitor GPU memory utilization and adjust model parameters if needed
- **Unified workflow problems**:
  - Use manage.sh status --all for coordinated service status checking
  - Verify service dependencies and startup order in unified workflow
- **CI/CD issues**:
  - Use --no-siblings flag to skip sibling repository cloning in CI environments
  - Check GitHub Actions workflow logs for deployment failures
  - Verify service management commands execute successfully in automated pipelines

**Section sources**
- [systemd-runtime-notes.md](file://docs/systemd-runtime-notes.md)
- [run_vllm_openai_proxy.sh](file://tools/run_vllm_openai_proxy.sh)
- [runtime_env.sh](file://tools/lib/runtime_env.sh)
- [deployment.md](file://docs/deployment.md)
- [run_vllm_engine.sh](file://tools/run_vllm_engine.sh)
- [ci.yml](file://.github/workflows/ci.yml)

## Conclusion
The Sage Faculty Twin deployment relies on a unified service management approach that consolidates all deployment operations into two primary entry points: manage.sh for runtime operations and quickstart.sh for installation and setup. The system maintains clean separation of concerns: the application server, local site proxy, optional vLLM proxy, Cloudflare tunnel, and vLLM-HUST inference engine, all orchestrated via systemd user services and consolidated management scripts. Recent enhancements include improved CI/CD workflows with the --no-siblings flag for optimized sibling repository handling, eliminating the previous multi-script deployment approach that reduced complexity while providing more consistent service installation across different environments. Following the documented procedures ensures reliable operation, observability, and maintainability. For production environments, carefully tune proxy settings, monitor streaming behavior, establish robust backup and recovery procedures, and leverage the unified workflow for simplified service management. The enhanced CI/CD infrastructure with --no-siblings flag provides faster and more reliable automated deployments, particularly beneficial for continuous integration and deployment scenarios.