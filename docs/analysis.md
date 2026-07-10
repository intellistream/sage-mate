# vLLM-HUST Qwen3-32B 性能分析报告

> **机器:** train05 (Ascend 910B3 × 8)  
> **采集时间:** 2026-06-04 18:40 CST  
> **服务运行时长:** ~17h (since 01:07 today)

---

## 1. 当前部署配置

```bash
# systemd service: sage-mate-vllm-qwen3-32b.service
vllm-hust serve /data/shared-models/Qwen3-32B \
  --served-model-name Qwen3-32B \
  --host 0.0.0.0 \
  --port 18000 \
  --tensor-parallel-size 2 \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.85 \
  --enforce-eager
```

| 项目 | 值 |
|------|------|
| 模型 | Qwen3-32B (BF16, 未量化) |
| 使用NPU | NPU 2 (PCIe 0000:81:00.0, NUMA 96-119) + NPU 5 (PCIe 0000:02:00.0, NUMA 0-23) |
| NPU互联 | HCCS, 7 lanes × 224 Gbps = 1568 Gbps 全双工 |
| HBM使用率 | 86% (每卡 ~56936/65536 MB) |
| 运行方式 | Docker容器内 (`docker exec -i <container>`) |
| vLLM版本 | 0.17.2.post2.dev1197+g2206f1f7b (开发版) |
| Prefix Cache | 已启用, block_size=128, sha256 |
| Graph Mode | **禁用** (`--enforce-eager`) |

---

## 2. 实测性能数据

### 2.1 快速基准测试 (单请求, 无并发)

| 场景 | Prompt | Completion | TTFB | Total | 吞吐 |
|------|--------|------------|------|-------|------|
| 极短回复 (enable_thinking=false) | 24 tokens | 3 tokens | 0.478s | 0.478s | 6.3 tok/s |
| 长回复 (enable_thinking=true, 含CoT) | 23 tokens | 521 tokens | ~0.25s | **68s** | **7.7 tok/s** |

### 2.2 Prometheus指标统计 (服务启动以来, 111个完成请求)

| 指标 | 值 | 说明 |
|------|------|------|
| 平均TTFB | 0.254s (30.49s / 120 req) | 72.5%请求 < 0.25s |
| 平均TPOT | 0.158s/token (17.58s / 111 req) | 约6.3 tokens/s |
| Inter-token latency (P50) | ~0.15s | 大部分在0.1-0.2s之间 |
| Avg generation throughput | **1.7 tokens/s** (idle时日志) | 低并发下更低 |
| Prefix cache命中率 | **0%** (0/43325 tokens) | 完全未命中! |
| 请求结束原因 | stop: 25, **length: 86** | 77%请求触达max_tokens |
| E2E延迟P50 | ~35s | |
| E2E延迟P90 | ~60s | |
| E2E延迟P99 | ~120s | |

### 2.3 关键发现

1. **生成速度仅 6-8 tokens/s** — 32B模型TP2在910B3上的表现远低于预期 (理论应能达到15-25 tok/s)
2. **Prefix cache 0%命中** — 尽管已启用, 但完全没有缓存复用
3. **77%请求因max_tokens截断** — Qwen3的thinking模式生成大量CoT token, 实际有效输出被压缩

---

## 3. 性能瓶颈分析

### 3.1 🔴 `--enforce-eager` 禁用了图模式 (最大嫌疑)

**影响:** 每一次forward pass都走动态dispatch, 无法利用昇腾的ACL Graph编译优化。

- Eager模式下, 每个算子单独下发到NPU, 存在大量Host-Device同步开销
- Graph模式允许将多个算子fusion、消除中间Tensor分配、减少kernel launch overhead
- 对于decode阶段(每次只生成1个token), kernel launch overhead占比极高
- **预估性能损失: 2-4x**

**为什么当初设了`--enforce-eager`?**
- 可能是为了避免graph编译错误或兼容性问题 (开发版vLLM常见)
- 需要团队验证移除后是否可正常运行

**建议操作:**
```bash
# 尝试移除 --enforce-eager
vllm-hust serve /data/shared-models/Qwen3-32B \
  --served-model-name Qwen3-32B \
  --host 0.0.0.0 --port 18000 \
  --tensor-parallel-size 2 \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.85
  # 不加 --enforce-eager
```

### 3.2 🔴 跨NUMA节点TP通信

**影响:** NPU 2 (NUMA node 1, CPU 96-119) 和 NPU 5 (NUMA node 0, CPU 0-23) 位于不同NUMA节点。

- 每次all-reduce (TP=2每个decoder layer至少2次) 都需要跨NUMA hop
- HCCS带宽1568 Gbps应足够, 但**延迟**受NUMA拓扑影响
- 32B模型TP2时, 每次all-reduce的数据量 = hidden_size × 2 bytes ≈ 5120 × 2 = 10KB (decode) / 更大 (prefill)
- 跨NUMA增加的延迟主要影响decode (因为是latency-bound)

**建议操作:**
```bash
# 优先选择同NUMA节点的NPU对
# NPU 2+3 (NUMA 96-119) 或 NPU 4+5 (NUMA 0-23) 或 NPU 6+7 (NUMA 48-71)
# 当前NPU 4正在跑量化任务, NPU 6空闲
# 建议等NPU 4量化完成后, 迁移到NPU 4+5 (同NUMA)
export ASCEND_RT_VISIBLE_DEVICES=4,5  # 同NUMA node 0
```

### 3.3 🟡 Prefix Cache 0%命中

**影响:** 每次请求都重新计算完整的prompt KV cache, 浪费prefill算力。

- sage-mate的system prompt是固定的 (~几千tokens), 应该可以缓存复用
- 0%命中可能的原因:
  1. Docker容器内内存管理问题
  2. 每次请求的token化结果不一致 (不同的chat template或添加的内容)
  3. block_size=128 太大, 短prompt无法对齐cache block
  4. vLLM开发版的prefix cache实现有bug

**建议操作:**
- 检查vLLM日志, 确认prefix cache初始化是否成功
- 确保system prompt完全相同 (逐字节一致), 包括结尾的空格/换行
- 考虑降低block_size: `--block-size 16`

### 3.4 🟡 BF16未量化 (64GB模型, 两卡各32GB)

**影响:** 模型权重占用大量HBM, 留给KV cache的空间有限。

- Qwen3-32B FP16/BF16: ~64GB 权重
- TP2: 每卡 ~32GB 权重 + 框架overhead
- 65536MB × 0.85 = 55705MB 可用, 减去32GB权重 ≈ 23GB KV cache
- max_model_len=32768, KV cache需求: 32768 × 64层 × 2(KV) × 5120维 × 2bytes / TP2 ≈ 单请求20GB
- 这意味着**几乎只能同时服务1个长请求**!

**建议操作:**
```bash
# 选项A: 使用W8A8量化模型 (已有 /root/models/Qwen3-8B-w8a8 先例)
# 等Qwen3-32B的W8A8量化完成后替换
# NPU 4上正在跑的 qwen2.5-14B_w4a4.py 量化脚本可能就是在做类似工作

# 选项B: 降低max_model_len以释放KV cache空间给并发
--max-model-len 16384  # 或 8192 (视实际对话长度而定)
```

### 3.5 🟡 Docker容器层开销

**影响:** 通过`docker exec -i <container> bash -lc "..."` 运行vLLM, 增加了:
- IPC开销 (container namespace crossing)
- 可能的CPU调度/cgroup限制
- 文件系统IO额外层

**建议操作:**
- 条件允许时, 迁移到host直接运行 (或至少用`docker run --privileged --network host`)

### 3.6 🟢 HCCS互联状态正常

- 两张卡HCCS均为OK, 无error/retry
- 7 lanes全部在线, link speed 224 Gbps
- 互联本身不是瓶颈

---

## 4. 为什么体感"特别慢"? — 叠加因素

实际用户感知的延迟 ≈ `应用pipeline延迟 + TTFB + 生成时间`

| 阶段 | 耗时 | 说明 |
|------|------|------|
| 应用前处理 (intent detection等) | ~1-3s | 已优化为用同模型 |
| TTFB (第一个token) | ~0.25-0.5s | 正常 |
| Thinking生成 | **30-50s** | Qwen3深度思考模式生成几百个thinking tokens |
| 实际回答生成 | 10-20s | 有效回答通常100-300 tokens |
| **总计** | **40-70s** | |

**结论:** 主要延迟来自:
1. 生成速度慢 (6-8 tok/s vs 预期15-25 tok/s) — `--enforce-eager` + 跨NUMA
2. Qwen3 thinking模式生成大量CoT tokens (占总输出的60-80%)

---

## 5. 优先级排序的优化建议

| 优先级 | 操作 | 预期收益 | 风险 |
|--------|------|----------|------|
| P0 | 移除 `--enforce-eager` | **2-4x吞吐提升** | 可能遇到graph编译错误, 需测试 |
| P0 | 迁移到同NUMA NPU对 (如4+5) | ~10-30%延迟降低 | 需等NPU 4量化任务完成 |
| P1 | 使用W8A8量化模型 | ~1.5-2x吞吐 + 更多KV cache空间 | 需要做量化+精度验证 |
| P1 | 降低 `--max-model-len` 到 8192 或 16384 | 更多并发空间 | 限制长对话 |
| P2 | 调试prefix cache不命中问题 | prefill时间减少50%+ (对重复prompt) | 需要分析日志 |
| P2 | 应用层限制thinking token数量 | 减少无效生成 | 可能影响回答质量 |
| P3 | 迁移出Docker, host直接运行 | ~5-10% | 需要环境迁移 |

---

## 6. 验证步骤

### 快速验证脚本

```bash
# 1. 基准测试 (当前配置)
time curl -s -X POST http://127.0.0.1:18000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen3-32B","messages":[{"role":"user","content":"What is 2+2?"}],"max_tokens":50,"temperature":0,"chat_template_kwargs":{"enable_thinking":false}}' \
  | jq '.usage'

# 2. 检查 /metrics 端点
curl -s http://127.0.0.1:18000/metrics | grep -E "(time_to_first_token_seconds_sum|time_per_output_token_seconds_sum|request_success_total|prefix_cache_hits_total)"

# 3. 监控NPU利用率 (运行请求时)
watch -n1 'npu-smi info -t usages -i 2; npu-smi info -t usages -i 5'
```

### 移除 `--enforce-eager` 后的对比

> **2026-06-20 更新:** vLLM engine 配置已纳入仓库管理 (`deploy/systemd/user/sage-mate-vllm-engine.service` + `tools/run_vllm_engine.sh`)。
> 部署时默认启用 graph mode (不使用 `--enforce-eager`)，TP=4。
>
> 使用 managed service 部署:
> ```bash
> ./manage.sh install --with-vllm-engine --start
> journalctl --user -u sage-mate-vllm-engine.service -f
> ```
>
> 如需清理旧的 system-level 服务:
> ```bash
> sudo systemctl stop sage-mate-vllm-qwen3-32b.service
> sudo systemctl disable sage-mate-vllm-qwen3-32b.service
> ```

以下是旧的手动移除 `--enforce-eager` 步骤（已废弃）:

```bash
sudo systemctl daemon-reload
sudo systemctl restart sage-mate-vllm-qwen3-32b.service
# 等待模型加载完成 (约3-5分钟)
journalctl -u sage-mate-vllm-qwen3-32b.service -f
# 看到 "Application startup complete" 后重新跑基准
```

---

## 7. 附录: NPU卡使用全景

| NPU | HBM (MB) | 占用者 | NUMA |
|-----|-----------|--------|------|
| 0 | 43335/65536 | Qwen3-8B-w8a8 (别人手动启动, 非systemd) | 144-167 |
| 1 | 57344/65536 | 某VLLMEngineCor (非我们) | 144-167 |
| 2 | 56936/65536 | **我们的Qwen3-32B TP worker** | 96-119 |
| 3 | 56884/65536 | 某VLLMEngineCor (非我们) | 96-119 |
| 4 | 24924/65536 | 量化脚本 (Qwen2.5-14B w4a4) | 0-23 |
| 5 | 56936/65536 | **我们的Qwen3-32B TP worker** | 0-23 |
| 6 | 3628/65536 | 几乎空闲 | 48-71 |
| 7 | 56773/65536 | 某VLLMEngineCor (非我们) | 48-71 |

**我们仅使用NPU 2+5, 不应再增加占用。**
