# my-twin 回答效果不佳问题清单 — Replay 报告

## 方法论

本报告由 [tools/replay_poor_cases.py](file:///home/shuhao/sage-faculty-twin/tools/replay_poor_cases.py) 自动生成, 数据源是 [docs/student-questions-poor-answers.md](file:///home/shuhao/sage-faculty-twin/docs/student-questions-poor-answers.md) 中记录的 39 条历史不佳回答。

本轮使用 **mock-LLM 模式** (Qwen3-32B 离线时的回退方案), 用以验证以下确定性流水线改动是否生效:

| Task | 验证方式 |
|------|----------|
| Task 2 (确定性 guardrail) | mock 分类器始终返回 `ask_followup`, 期望被 `_normalize_interaction_intent` 在命中研究/指导/学术 anchor 时 demote 成 `answer` |
| Task 3 (始终跑 KB 检索 + 推迟 clarification) | 即使是 ask_followup, retrieval 也应被执行, kb_hits 应 > 0 |
| Task 4 (短 follow-up 查询扩展) | 用同一 conversation_id 串起同一学生连续问题, 检验 `具体内容/已有的/kvpr这篇` 等短 follow-up 能否检索到相关文档 |
| Task 5 (身份地板 + persona 占位符规则) | `你是谁/学术背景/招生` 等问题应 force-include `主页资料｜张书豪` 等档 |
| Task 6 (新摄入 README + 自建 FAQ) | 12 篇新文档应在 retrieval 中被命中 |
| Task 8 (profile-doc 评分 floor) | research/general topic 短查询时, profile-tagged 文档不应被 0 分淘汰 |

**Verdict 规则**: improved/unchanged/regressed 由多维启发式打分得出 — workflow 从 ask_follow_up 转为 answer (+1), 答案不再过短 (+1), kb_hits 提升 (+1), 不再含 `[占位符]` (+1), 不再进入 review_queue/human_handoff (+1); 反向各 −1。

**Mock-LLM 模式的局限**: 由于 mock 分类器始终返回 ask_followup, 本报告测的是 **底层确定性管线** 的健壮性。要进一步看到 LLM 在新提示下能不能直接回答, 需要重启 Qwen3-32B 服务 (`./manage.sh start --with-vllm-engine`), 然后跑 `python tools/replay_poor_cases.py` (不带 `--mock-llm`)。

> Replayed at: 2026-06-04 23:56:12  
> Total cases: **39**  
> Improved: **38** | Unchanged: **0** | Regressed: **1** | Error: **0**

## TL;DR

- 改善 38/39 条 (97%)
- 仍待优化 1/39 (unchanged + regressed + error)

## 详细对照

| # | 学生 | 课程 | wf BEFORE→AFTER | kb BEFORE→AFTER | verdict | 问题 (摘要) |
|---|------|------|------------------|------------------|---------|--------------|
| 1 | 曹哲 | 科研指导 | ask_follow_up→ask_follow_up | 0→3 | improved | 我已经整理了十篇文献，然后进行汇报，汇报的内容应该包括什么 |
| 2 | 曹哲 | 科研指导 | ask_follow_up→ask_follow_up | 0→3 | improved | 我该怎么围绕我的课题整理文献 |
| 3 | 曹哲 | 科研指导 | ask_follow_up→ask_follow_up | 0→3 | improved | 我的研究思路是：当请求进入时，可能面临就算存在kv可复用时，重计算也比复用kv更快的情况。 在不同负载和硬件条件下... |
| 4 | 曹哲 | 科研指导 | ask_follow_up→answer | 0→3 | improved | 研究目标是降低TTFT，希望得到怎么整理相关文献的建议 |
| 5 | 曹哲 | 初次来访 | ask_follow_up→ask_follow_up | 0→3 | improved | 你能帮我看论文吗 |
| 6 | 曹哲 | 初次来访 | ask_follow_up→ask_follow_up | 0→3 | improved | 已有的 |
| 7 | 曹哲 | 初次来访 | ask_follow_up→ask_follow_up | 0→3 | improved | 我想看让你帮忙看看已有的论文 |
| 8 | 曹哲 | 初次来访 | ask_follow_up→ask_follow_up | 0→3 | improved | kvpr这篇 |
| 9 | 曹哲 | 初次来访 | ask_follow_up→ask_follow_up | 0→3 | improved | 具体内容 |
| 10 | 曹哲 | 初次来访 | ask_follow_up→answer | 0→3 | improved | 都不是，你这个系统可以做什么 |
| 11 | 曹哲 | 初次来访 | ask_follow_up→answer | 0→3 | improved | 主题是：汇报整理的文献 |
| 12 | 曹哲 | 初次来访 | ask_follow_up→ask_follow_up | 0→3 | improved | 需要关于如何整理文献的具体建议 |
| 13 | 曹哲 | 初次来访 | ask_follow_up→ask_follow_up | 0→3 | improved | 都需要，都讲讲吧 |
| 14 | 曹哲 | 初次来访 | ask_follow_up→answer | 0→3 | improved | 我是老师手底下的研究生 |
| 15 | 曹哲 | 初次来访 | ask_follow_up→answer | 0→2 | improved | 我想确认我应该围绕什么问题阅读文献。我现在的研究课题是：当请求进入推理系统时，可能不复用或者部分复用会比全复用更好 |
| 16 | 曹哲 | 初次来访 | ask_follow_up→answer | 0→1 | improved | 什么叫具体背景信息，你举个例子 |
| 17 | 曹哲 | 初次来访 | ask_follow_up→answer | 0→2 | improved | 你会联系上下文吗 |
| 18 | 曹哲 | 初次来访 | ask_follow_up→answer | 0→3 | improved | 是的 |
| 19 | 曹哲 | 初次来访 | ask_follow_up→answer | 0→3 | improved | 我是想了解你是否能理解并使用之前的对话内容来回答问题 |
| 20 | 曹哲 | 初次来访 | ask_follow_up→answer | 0→2 | improved | 我的研究选题的问题定义是：当请求进入时，部分复用甚至不复用可能比全复用更好。这个问题定义有什么问题吗 |
| 21 | 曹哲 | 初次来访 | ask_follow_up→ask_follow_up | 0→1 | improved | 大模型推理时，为了加快推理速度，对于能复用kv的请求往往直接复用，但有时候可能不复用会更好。我的研究选题的问题定义... |
| 22 | 曹哲 | 初次来访 | ask_follow_up→ask_follow_up | 0→1 | improved | 我现在就是不知道哪些文献是相关文献 |
| 23 | 曹哲 | 初次来访 | ask_follow_up→ask_follow_up | 0→3 | improved | 你觉得我刚刚的问题的主题是什么呢 |
| 24 | 曹哲 | 初次来访 | ask_follow_up→ask_follow_up | 0→3 | improved | 告诉我相关问题 |
| 25 | 王子澳 | 初次来访 | ask_follow_up→ask_follow_up | 0→3 | improved | 张老师有那些学生 |
| 26 | 王子澳 | 初次来访 | ask_follow_up→ask_follow_up | 0→3 | improved | 当前学生以及曾经指导过的学生 |
| 27 | 王子澳 | 初次来访 | ask_follow_up→answer | 0→3 | improved | 学生名单 |
| 28 | 王子澳 | 初次来访 | ask_follow_up→answer | 0→3 | improved | 张老师指导过的学生名单 |
| 29 | 王子澳 | 初次来访 | ask_follow_up→ask_follow_up | 0→3 | improved | 正在指导的学生信息 |
| 30 | 王子澳 | 初次来访 | ask_follow_up→ask_follow_up | 0→3 | improved | 正在指导的学生的个人信息 |
| 31 | 王子澳 | 初次来访 | ask_follow_up→answer | 0→3 | improved | 学生的名字 |
| 32 | 王子澳 | 初次来访 | ask_follow_up→ask_follow_up | 0→3 | improved | 张睿诚的姓名 |
| 33 | 王子澳 | 初次来访 | answer→ask_follow_up | 3→3 | regressed | sage是什么 |
| 34 | 阮弘毅 | 科研指导 | ask_follow_up→ask_follow_up | 0→3 | improved | 你是谁 |
| 35 | 阮弘毅 | 科研指导 | ask_follow_up→ask_follow_up | 0→3 | improved | 你的身份 |
| 36 | 阮弘毅 | 科研指导 | ask_follow_up→answer | 0→3 | improved | 你的身份背景 |
| 37 | 阮弘毅 | 科研指导 | advise_only→ask_follow_up | 1→3 | improved | 你的学术背景 |
| 38 | 王明琪 | 初次来访 | ask_follow_up→ask_follow_up | 0→3 | improved | 在吗 |
| 39 | 王明琪 | 初次来访 | review_queue→ask_follow_up | 0→3 | improved | 当前我的论文定位为一个面向 continuation-anchored LLM serving 的 request... |

## 完整答案 (前后对比)

### 1. 曹哲 — 科研指导 *(verdict: improved)*

**问题:** 我已经整理了十篇文献，然后进行汇报，汇报的内容应该包括什么

**BEFORE [ask_follow_up / kb=0]:**

> 您能否提供更多关于汇报目的和听众的信息？这将帮助我给出更具体的建议。

**AFTER [ask_follow_up / kb=3]:**

> 请问您具体需要了解什么?
> 
> 我大致检索到这些相关材料，可一起说明你想聚焦哪一块：
> - 课件正文｜大模型推理基础设施课程材料｜第 14 讲 课程总结与汇报（第1部分）
> - 课程附件正文｜数据库实验课｜数据库系统原理实践报告模板2026春季mysql环境版（第1部分）
> - 课件正文｜大模型推理基础设施课程材料｜Tutorial 13 课程总结与汇报

---

### 2. 曹哲 — 科研指导 *(verdict: improved)*

**问题:** 我该怎么围绕我的课题整理文献

**BEFORE [ask_follow_up / kb=0]:**

> 您能否提供一些关于您的课题的具体信息？这将帮助我给出更具体的建议。

**AFTER [ask_follow_up / kb=3]:**

> 请问您具体需要了解什么?
> 
> 我大致检索到这些相关材料，可一起说明你想聚焦哪一块：
> - 课件正文｜大模型推理基础设施课程材料｜第 14 讲 课程总结与汇报（第1部分）
> - 课件正文｜研究生论文写作课程材料｜第 8 讲 研究生毕业论文中常见的问题（第2部分）
> - 课件正文｜大模型推理基础设施课程材料｜Tutorial 13 课程总结与汇报

---

### 3. 曹哲 — 科研指导 *(verdict: improved)*

**问题:** 我的研究思路是：当请求进入时，可能面临就算存在kv可复用时，重计算也比复用kv更快的情况。
在不同负载和硬件条件下，动态根据IO状态及请求状态对复用情况进行调度。

**BEFORE [ask_follow_up / kb=0]:**

> 您能否详细说明一下您的研究目标以及希望得到的具体建议或资源？

**AFTER [ask_follow_up / kb=3]:**

> 请问您具体需要了解什么?
> 
> 我大致检索到这些相关材料，可一起说明你想聚焦哪一块：
> - 主页附件正文｜2026 cccf domestic inference engine survey（第3部分）
> - Current Research | 2026 CCF-Ant Proposal (VAMOS)
> - 研究总览｜二、状态感知执行优化与软硬件协同设计

---

### 4. 曹哲 — 科研指导 *(verdict: improved)*

**问题:** 研究目标是降低TTFT，希望得到怎么整理相关文献的建议

**BEFORE [ask_follow_up / kb=0]:**

> 您能否提供更具体的关于降低TTFT的研究方向或领域？这将帮助我给出更有针对性的建议。

**AFTER [answer / kb=3]:**

> [MOCK-LLM回复] 根据检索到的上下文: Student name: 曹哲 Course context: 科研指导. Current weekly meeting availability: - 2026-05-25: 14:00-18:00 - 2026-05-26: 14:00-18:00 - 2026-05-27: 16:00-18:00 - 2026-05-28: 14:00-18:00 - 2026-05-29: 14:00-18:00 Immediate session context (same co...

---

### 5. 曹哲 — 初次来访 *(verdict: improved)*

**问题:** 你能帮我看论文吗

**BEFORE [ask_follow_up / kb=0]:**

> 您是想讨论已有的论文，还是需要帮助撰写新的论文呢？

**AFTER [ask_follow_up / kb=3]:**

> 请问您具体需要了解什么?
> 
> 我大致检索到这些相关材料，可一起说明你想聚焦哪一块：
> - 课件正文｜研究生论文写作课程材料｜第 5 讲 多维视角看论文写作（第3部分）
> - 课件正文｜研究生论文写作课程材料｜第 6 讲 培养写作能力的若干建议（第3部分）
> - 课件正文｜大模型推理基础设施课程材料｜第 10 讲 论文比较方法（第1部分）

---

### 6. 曹哲 — 初次来访 *(verdict: improved)*

**问题:** 已有的

**BEFORE [ask_follow_up / kb=0]:**

> 您是指想要了解我已有的哪些信息或资源吗？请提供更多的细节。

**AFTER [ask_follow_up / kb=3]:**

> 请问您具体需要了解什么?
> 
> 我大致检索到这些相关材料，可一起说明你想聚焦哪一块：
> - 课件正文｜研究生论文写作课程材料｜第 5 讲 多维视角看论文写作（第3部分）
> - 课件正文｜研究生论文写作课程材料｜第 6 讲 培养写作能力的若干建议（第3部分）
> - 课件正文｜研究生论文写作课程材料｜第 8 讲 研究生毕业论文中常见的问题（第2部分）

---

### 7. 曹哲 — 初次来访 *(verdict: improved)*

**问题:** 我想看让你帮忙看看已有的论文

**BEFORE [ask_follow_up / kb=0]:**

> 您是想要了解具体的哪篇论文，还是希望我帮您浏览所有已发表的论文并提供一些指导或建议？

**AFTER [ask_follow_up / kb=3]:**

> 请问您具体需要了解什么?
> 
> 我大致检索到这些相关材料，可一起说明你想聚焦哪一块：
> - 课件正文｜研究生论文写作课程材料｜第 5 讲 多维视角看论文写作（第1部分）
> - 课件正文｜研究生论文写作课程材料｜第 6 讲 培养写作能力的若干建议（第2部分）
> - 课件正文｜研究生论文写作课程材料｜第 8 讲 研究生毕业论文中常见的问题（第1部分）

---

### 8. 曹哲 — 初次来访 *(verdict: improved)*

**问题:** kvpr这篇

**BEFORE [ask_follow_up / kb=0]:**

> 您是想了解关于kvpr这篇论文的具体内容还是其他相关信息？

**AFTER [ask_follow_up / kb=3]:**

> 请问您具体需要了解什么?
> 
> 我大致检索到这些相关材料，可一起说明你想聚焦哪一块：
> - 课件正文｜研究生论文写作课程材料｜第 5 讲 多维视角看论文写作（第1部分）
> - 课件正文｜研究生论文写作课程材料｜第 8 讲 研究生毕业论文中常见的问题（第1部分）
> - 课件正文｜研究生论文写作课程材料｜第 6 讲 培养写作能力的若干建议（第2部分）

---

### 9. 曹哲 — 初次来访 *(verdict: improved)*

**问题:** 具体内容

**BEFORE [ask_follow_up / kb=0]:**

> 请问您想了解关于初次来访的具体内容是什么？是关于预约会议、教学材料还是其他方面的问题？

**AFTER [ask_follow_up / kb=3]:**

> 请问您具体需要了解什么?
> 
> 我大致检索到这些相关材料，可一起说明你想聚焦哪一块：
> - 课件正文｜研究生论文写作课程材料｜第 8 讲 研究生毕业论文中常见的问题（第1部分）
> - 课件正文｜研究生论文写作课程材料｜第 5 讲 多维视角看论文写作（第3部分）
> - 课件正文｜研究生论文写作课程材料｜第 6 讲 培养写作能力的若干建议（第2部分）

---

### 10. 曹哲 — 初次来访 *(verdict: improved)*

**问题:** 都不是，你这个系统可以做什么

**BEFORE [ask_follow_up / kb=0]:**

> 请问您具体想了解系统的哪些功能呢？

**AFTER [answer / kb=3]:**

> [MOCK-LLM回复] 根据检索到的上下文: Student name: 曹哲 Course context: 初次来访. Current weekly meeting availability: - 2026-05-25: 14:00-18:00 - 2026-05-26: 14:00-18:00 - 2026-05-27: 16:00-18:00 - 2026-05-28: 14:00-18:00 - 2026-05-29: 14:00-18:00 Immediate session context (same co...

---

### 11. 曹哲 — 初次来访 *(verdict: improved)*

**问题:** 主题是：汇报整理的文献

**BEFORE [ask_follow_up / kb=0]:**

> 请问您需要关于如何整理文献的具体建议，还是预约时间来汇报已经整理好的文献？

**AFTER [answer / kb=3]:**

> [MOCK-LLM回复] 根据检索到的上下文: Student name: 曹哲 Course context: 初次来访. Current weekly meeting availability: - 2026-05-25: 14:00-18:00 - 2026-05-26: 14:00-18:00 - 2026-05-27: 16:00-18:00 - 2026-05-28: 14:00-18:00 - 2026-05-29: 14:00-18:00 Immediate session context (same co...

---

### 12. 曹哲 — 初次来访 *(verdict: improved)*

**问题:** 需要关于如何整理文献的具体建议

**BEFORE [ask_follow_up / kb=0]:**

> 您是需要关于整理文献的一般性建议，还是针对特定研究或课程的建议？

**AFTER [ask_follow_up / kb=3]:**

> 请问您具体需要了解什么?
> 
> 我大致检索到这些相关材料，可一起说明你想聚焦哪一块：
> - 课件正文｜研究生论文写作课程材料｜第 6 讲 培养写作能力的若干建议（第2部分）
> - 课程附件正文｜数据库实验课｜数据库系统原理实践报告模板2026春季mysql环境版（第1部分）
> - 课件正文｜大模型推理基础设施课程材料｜第 14 讲 课程总结与汇报（第1部分）

---

### 13. 曹哲 — 初次来访 *(verdict: improved)*

**问题:** 都需要，都讲讲吧

**BEFORE [ask_follow_up / kb=0]:**

> 您能具体说明一下需要了解的内容吗？比如是关于研究方向、教学材料还是其他方面的问题。

**AFTER [ask_follow_up / kb=3]:**

> 请问您具体需要了解什么?
> 
> 我大致检索到这些相关材料，可一起说明你想聚焦哪一块：
> - 课件正文｜研究生论文写作课程材料｜第 6 讲 培养写作能力的若干建议（第2部分）
> - 课件正文｜大模型推理基础设施课程材料｜第 14 讲 课程总结与汇报（第1部分）
> - 课件正文｜研究生论文写作课程材料｜第 8 讲 研究生毕业论文中常见的问题（第2部分）

---

### 14. 曹哲 — 初次来访 *(verdict: improved)*

**问题:** 我是老师手底下的研究生

**BEFORE [ask_follow_up / kb=0]:**

> 请问您需要关于研究指导的哪方面的帮助？

**AFTER [answer / kb=3]:**

> [MOCK-LLM回复] 根据检索到的上下文: Student name: 曹哲 Course context: 初次来访. Current weekly meeting availability: - 2026-05-25: 14:00-18:00 - 2026-05-26: 14:00-18:00 - 2026-05-27: 16:00-18:00 - 2026-05-28: 14:00-18:00 - 2026-05-29: 14:00-18:00 Immediate session context (same co...

---

### 15. 曹哲 — 初次来访 *(verdict: improved)*

**问题:** 我想确认我应该围绕什么问题阅读文献。我现在的研究课题是：当请求进入推理系统时，可能不复用或者部分复用会比全复用更好

**BEFORE [ask_follow_up / kb=0]:**

> 您能否提供一些关于您的研究课题的具体背景信息或目标？这将有助于给出更准确的建议。

**AFTER [answer / kb=2]:**

> [MOCK-LLM回复] 根据检索到的上下文: Student name: 曹哲 Course context: 初次来访. Current weekly meeting availability: - 2026-05-25: 14:00-18:00 - 2026-05-26: 14:00-18:00 - 2026-05-27: 16:00-18:00 - 2026-05-28: 14:00-18:00 - 2026-05-29: 14:00-18:00 Immediate session context (same co...

---

### 16. 曹哲 — 初次来访 *(verdict: improved)*

**问题:** 什么叫具体背景信息，你举个例子

**BEFORE [ask_follow_up / kb=0]:**

> 您是指在什么情境下需要具体背景信息呢？例如，是关于研究项目、课程学习还是其他方面的问题。

**AFTER [answer / kb=1]:**

> [MOCK-LLM回复] 根据检索到的上下文: Student name: 曹哲 Course context: 初次来访. Current weekly meeting availability: - 2026-05-25: 14:00-18:00 - 2026-05-26: 14:00-18:00 - 2026-05-27: 16:00-18:00 - 2026-05-28: 14:00-18:00 - 2026-05-29: 14:00-18:00 Immediate session context (same co...

---

### 17. 曹哲 — 初次来访 *(verdict: improved)*

**问题:** 你会联系上下文吗

**BEFORE [ask_follow_up / kb=0]:**

> 您是想了解我是否能理解并使用之前的对话内容来回答问题吗？

**AFTER [answer / kb=2]:**

> [MOCK-LLM回复] 根据检索到的上下文: Student name: 曹哲 Course context: 初次来访. Current weekly meeting availability: - 2026-05-25: 14:00-18:00 - 2026-05-26: 14:00-18:00 - 2026-05-27: 16:00-18:00 - 2026-05-28: 14:00-18:00 - 2026-05-29: 14:00-18:00 Immediate session context (same co...

---

### 18. 曹哲 — 初次来访 *(verdict: improved)*

**问题:** 是的

**BEFORE [ask_follow_up / kb=0]:**

> 请问您具体需要什么帮助或信息？

**AFTER [answer / kb=3]:**

> [MOCK-LLM回复] 根据检索到的上下文: Student name: 曹哲 Course context: 初次来访. Current weekly meeting availability: - 2026-05-25: 14:00-18:00 - 2026-05-26: 14:00-18:00 - 2026-05-27: 16:00-18:00 - 2026-05-28: 14:00-18:00 - 2026-05-29: 14:00-18:00 Immediate session context (same co...

---

### 19. 曹哲 — 初次来访 *(verdict: improved)*

**问题:** 我是想了解你是否能理解并使用之前的对话内容来回答问题

**BEFORE [ask_follow_up / kb=0]:**

> 您是指希望我能够基于我们之前的对话内容来回答您的问题吗？请提供一些具体的例子或进一步的信息。

**AFTER [answer / kb=3]:**

> [MOCK-LLM回复] 根据检索到的上下文: Student name: 曹哲 Course context: 初次来访. Current weekly meeting availability: - 2026-05-25: 14:00-18:00 - 2026-05-26: 14:00-18:00 - 2026-05-27: 16:00-18:00 - 2026-05-28: 14:00-18:00 - 2026-05-29: 14:00-18:00 Immediate session context (same co...

---

### 20. 曹哲 — 初次来访 *(verdict: improved)*

**问题:** 我的研究选题的问题定义是：当请求进入时，部分复用甚至不复用可能比全复用更好。这个问题定义有什么问题吗

**BEFORE [ask_follow_up / kb=0]:**

> 您能否提供一些背景信息或具体例子来帮助我更好地理解您的研究选题？

**AFTER [answer / kb=2]:**

> [MOCK-LLM回复] 根据检索到的上下文: Student name: 曹哲 Course context: 初次来访. Current weekly meeting availability: - 2026-05-25: 14:00-18:00 - 2026-05-26: 14:00-18:00 - 2026-05-27: 16:00-18:00 - 2026-05-28: 14:00-18:00 - 2026-05-29: 14:00-18:00 Immediate session context (same co...

---

### 21. 曹哲 — 初次来访 *(verdict: improved)*

**问题:** 大模型推理时，为了加快推理速度，对于能复用kv的请求往往直接复用，但有时候可能不复用会更好。我的研究选题的问题定义是：当请求进入时，部分复用甚至不复用可能比全复用更好。这个问题定义有什么问题吗

**BEFORE [ask_follow_up / kb=0]:**

> 您能否提供一些背景信息或具体例子来说明为什么部分复用或不复用KV可能在某些情况下优于全复用？这将有助于更准确地评估您的研究问题。

**AFTER [ask_follow_up / kb=1]:**

> 请问您具体需要了解什么?
> 
> 我大致检索到这些相关材料，可一起说明你想聚焦哪一块：
> - 研究总览｜研究主线

---

### 22. 曹哲 — 初次来访 *(verdict: improved)*

**问题:** 我现在就是不知道哪些文献是相关文献

**BEFORE [ask_follow_up / kb=0]:**

> 您能提供一下具体的研究主题或领域吗？这样我可以更好地帮助您找到相关的文献。

**AFTER [ask_follow_up / kb=1]:**

> 请问您具体需要了解什么?
> 
> 我大致检索到这些相关材料，可一起说明你想聚焦哪一块：
> - 研究总览｜研究主线

---

### 23. 曹哲 — 初次来访 *(verdict: improved)*

**问题:** 你觉得我刚刚的问题的主题是什么呢

**BEFORE [ask_follow_up / kb=0]:**

> 请您提供一些关于您问题的具体信息，这样我可以更好地帮助您。

**AFTER [ask_follow_up / kb=3]:**

> 请问您具体需要了解什么?
> 
> 我大致检索到这些相关材料，可一起说明你想聚焦哪一块：
> - 课件正文｜大模型推理基础设施课程材料｜第 4 讲 请求调度（第1部分）
> - 课件正文｜大模型推理基础设施课程材料｜第 3 讲 请求生命周期（第1部分）
> - 课件正文｜大模型推理基础设施课程材料｜第 13 讲 课程项目工作坊（第1部分）

---

### 24. 曹哲 — 初次来访 *(verdict: improved)*

**问题:** 告诉我相关问题

**BEFORE [ask_follow_up / kb=0]:**

> 请问您具体指的是哪方面的问题？

**AFTER [ask_follow_up / kb=3]:**

> 请问您具体需要了解什么?
> 
> 我大致检索到这些相关材料，可一起说明你想聚焦哪一块：
> - 课件正文｜研究生论文写作课程材料｜第 8 讲 研究生毕业论文中常见的问题（第1部分）
> - 课件正文｜大模型推理基础设施课程材料｜第 14 讲 课程总结与汇报（第1部分）
> - 课件正文｜研究生论文写作课程材料｜第 6 讲 培养写作能力的若干建议（第2部分）

---

### 25. 王子澳 — 初次来访 *(verdict: improved)*

**问题:** 张老师有那些学生

**BEFORE [ask_follow_up / kb=0]:**

> 您是想了解张老师的当前学生还是曾经指导过的学生？

**AFTER [ask_follow_up / kb=3]:**

> 请问您具体需要了解什么?
> 
> 我大致检索到这些相关材料，可一起说明你想聚焦哪一块：
> - 荣誉附件正文｜数据库老师获奖证书
> - 课件正文｜研究生论文写作课程材料｜第 7 讲 发表高水平论文（第2部分）
> - 课件正文｜研究生论文写作课程材料｜第 6 讲 培养写作能力的若干建议（第1部分）

---

### 26. 王子澳 — 初次来访 *(verdict: improved)*

**问题:** 当前学生以及曾经指导过的学生

**BEFORE [ask_follow_up / kb=0]:**

> 您是想了解当前学生的相关信息，还是希望获取曾经指导过的学生的名单？

**AFTER [ask_follow_up / kb=3]:**

> 请问您具体需要了解什么?
> 
> 我大致检索到这些相关材料，可一起说明你想聚焦哪一块：
> - 课件正文｜研究生论文写作课程材料｜第 7 讲 发表高水平论文（第2部分）
> - 课件正文｜研究生论文写作课程材料｜第 6 讲 培养写作能力的若干建议（第1部分）
> - 荣誉附件正文｜数据库老师获奖证书

---

### 27. 王子澳 — 初次来访 *(verdict: improved)*

**问题:** 学生名单

**BEFORE [ask_follow_up / kb=0]:**

> 您需要学生名单的具体信息是什么？例如，是关于课程的学生名单还是其他活动的学生名单？

**AFTER [answer / kb=3]:**

> [MOCK-LLM回复] 根据检索到的上下文: Student name: 王子澳 Course context: 初次来访. Current weekly meeting availability: - 2026-05-25: 14:00-18:00 - 2026-05-26: 14:00-18:00 - 2026-05-27: 16:00-18:00 - 2026-05-28: 14:00-18:00 - 2026-05-29: 14:00-18:00 Immediate session context (same c...

---

### 28. 王子澳 — 初次来访 *(verdict: improved)*

**问题:** 张老师指导过的学生名单

**BEFORE [ask_follow_up / kb=0]:**

> 您需要了解张老师指导过的具体哪方面信息？例如，他们的毕业论文题目或目前的职业发展情况。

**AFTER [answer / kb=3]:**

> [MOCK-LLM回复] 根据检索到的上下文: Student name: 王子澳 Course context: 初次来访. Current weekly meeting availability: - 2026-05-25: 14:00-18:00 - 2026-05-26: 14:00-18:00 - 2026-05-27: 16:00-18:00 - 2026-05-28: 14:00-18:00 - 2026-05-29: 14:00-18:00 Immediate session context (same c...

---

### 29. 王子澳 — 初次来访 *(verdict: improved)*

**问题:** 正在指导的学生信息

**BEFORE [ask_follow_up / kb=0]:**

> 您是想了解正在指导的学生的个人信息，还是想要知道如何更好地指导他们？

**AFTER [ask_follow_up / kb=3]:**

> 请问您具体需要了解什么?
> 
> 我大致检索到这些相关材料，可一起说明你想聚焦哪一块：
> - 荣誉附件正文｜数据库老师获奖证书
> - 课件正文｜研究生论文写作课程材料｜第 8 讲 研究生毕业论文中常见的问题（第1部分）
> - 课件正文｜研究生论文写作课程材料｜第 6 讲 培养写作能力的若干建议（第2部分）

---

### 30. 王子澳 — 初次来访 *(verdict: improved)*

**问题:** 正在指导的学生的个人信息

**BEFORE [ask_follow_up / kb=0]:**

> 您需要了解学生的哪些具体信息？

**AFTER [ask_follow_up / kb=3]:**

> 请问您具体需要了解什么?
> 
> 我大致检索到这些相关材料，可一起说明你想聚焦哪一块：
> - 荣誉附件正文｜数据库老师获奖证书
> - 课件正文｜研究生论文写作课程材料｜第 8 讲 研究生毕业论文中常见的问题（第1部分）
> - 课件正文｜研究生论文写作课程材料｜第 6 讲 培养写作能力的若干建议（第2部分）

---

### 31. 王子澳 — 初次来访 *(verdict: improved)*

**问题:** 学生的名字

**BEFORE [ask_follow_up / kb=0]:**

> 请问您需要了解哪位学生的姓名？

**AFTER [answer / kb=3]:**

> [MOCK-LLM回复] 根据检索到的上下文: Student name: 王子澳 Course context: 初次来访. Current weekly meeting availability: - 2026-05-25: 14:00-18:00 - 2026-05-26: 14:00-18:00 - 2026-05-27: 16:00-18:00 - 2026-05-28: 14:00-18:00 - 2026-05-29: 14:00-18:00 Immediate session context (same c...

---

### 32. 王子澳 — 初次来访 *(verdict: improved)*

**问题:** 张睿诚的姓名

**BEFORE [ask_follow_up / kb=0]:**

> 您想了解张睿诚的哪些信息？

**AFTER [ask_follow_up / kb=3]:**

> 请问您具体需要了解什么?
> 
> 我大致检索到这些相关材料，可一起说明你想聚焦哪一块：
> - 课件正文｜大模型推理基础设施课程材料｜实验 5 指标观测与最小复现实验
> - 课件正文｜大模型推理基础设施课程材料｜实验 2 请求生命周期观察
> - 课件正文｜研究生论文写作课程材料｜第 6 讲 培养写作能力的若干建议（第2部分）

---

### 33. 王子澳 — 初次来访 *(verdict: regressed)*

**问题:** sage是什么

**BEFORE [answer / kb=3]:**

> 您好，王子澳同学。SAGE是指一篇名为"SAGE: A Dataflow-Native Framework for Modular, Controllable, and Transparent LLM-Augmented Reasoning"的论文，该研究聚焦于大模型推理、检索增强与记忆系统。这项工作发表在ICML国际会议上。如果您对这篇论文或相关技术有兴趣，可以告诉我具体的问题或需要讨论的内容，我们可以进一步探讨。

**AFTER [ask_follow_up / kb=3]:**

> 请问您具体需要了解什么?
> 
> 我大致检索到这些相关材料，可一起说明你想聚焦哪一块：
> - 论文提炼｜SAGE: A Dataflow-Native Framework for Modular, Controllable, and Transparent LLM-Augmented Reasoning
> - 论文提炼｜GRACE: Alleviating Reconstruction Cost in Dynamic Graph Processing Systems
> - 论文提炼｜Low-Latency Video Conferencing via Optimized Packet Routing and Reordering

---

### 34. 阮弘毅 — 科研指导 *(verdict: improved)*

**问题:** 你是谁

**BEFORE [ask_follow_up / kb=0]:**

> 您是想了解我的身份还是有关科研指导的具体问题？

**AFTER [ask_follow_up / kb=3]:**

> 请问您具体需要了解什么?
> 
> 我大致检索到这些相关材料，可一起说明你想聚焦哪一块：
> - 课件正文｜研究生论文写作课程材料｜第 7 讲 发表高水平论文（第1部分）
> - 课件正文｜大模型推理基础设施课程材料｜第 7 讲 推理系统架构（第1部分）
> - 课件正文｜大模型推理基础设施课程材料｜实验 1 最小运行与代码地图（第1部分）

---

### 35. 阮弘毅 — 科研指导 *(verdict: improved)*

**问题:** 你的身份

**BEFORE [ask_follow_up / kb=0]:**

> 您是想了解我的身份背景，还是有关科研指导的具体问题？

**AFTER [ask_follow_up / kb=3]:**

> 请问您具体需要了解什么?
> 
> 我大致检索到这些相关材料，可一起说明你想聚焦哪一块：
> - 课件正文｜研究生论文写作课程材料｜第 8 讲 研究生毕业论文中常见的问题（第1部分）
> - 课件正文｜研究生论文写作课程材料｜第 6 讲 培养写作能力的若干建议（第2部分）
> - 课件正文｜大模型推理基础设施课程材料｜实验 3 调度与连续批处理实验

---

### 36. 阮弘毅 — 科研指导 *(verdict: improved)*

**问题:** 你的身份背景

**BEFORE [ask_follow_up / kb=0]:**

> 您是想了解我的学术背景还是其他方面的信息？

**AFTER [answer / kb=3]:**

> [MOCK-LLM回复] 根据检索到的上下文: Student name: 阮弘毅 Course context: 科研指导. Current weekly meeting availability: - 2026-05-25: 14:00-18:00 - 2026-05-26: 14:00-18:00 - 2026-05-27: 16:00-18:00 - 2026-05-28: 14:00-18:00 - 2026-05-29: 14:00-18:00 Immediate session context (same c...

---

### 37. 阮弘毅 — 科研指导 *(verdict: improved)*

**问题:** 你的学术背景

**BEFORE [advise_only / kb=1]:**

> 阮弘毅同学，关于我的学术背景，我可以提供一个简要的概述。我在科研领域专注于[具体研究方向]，并且已经发表了几篇相关的学术论文。如果您对特定的研究项目或论文感兴趣，可以告诉我，我可以提供更详细的摘要或链接给您。
> 
> 在我们进一步讨论之前，请确保您已经准备好了会议议程、当前遇到的阻碍以及任何相关的草稿或材料。这样可以帮助我们更有效地进行讨论。如果您有任何具体的问题或需要进一步的信息，请随时告知。

**AFTER [ask_follow_up / kb=3]:**

> 请问您具体需要了解什么?
> 
> 我大致检索到这些相关材料，可一起说明你想聚焦哪一块：
> - 课件正文｜研究生论文写作课程材料｜第 6 讲 培养写作能力的若干建议（第2部分）
> - 课件正文｜研究生论文写作课程材料｜第 8 讲 研究生毕业论文中常见的问题（第1部分）
> - 课件正文｜研究生论文写作课程材料｜第 5 讲 多维视角看论文写作（第1部分）

---

### 38. 王明琪 — 初次来访 *(verdict: improved)*

**问题:** 在吗

**BEFORE [ask_follow_up / kb=0]:**

> 您好！请问您有什么具体的问题或需要帮助的地方吗？

**AFTER [ask_follow_up / kb=3]:**

> 请问您具体需要了解什么?
> 
> 我大致检索到这些相关材料，可一起说明你想聚焦哪一块：
> - 课件正文｜研究生论文写作课程材料｜第 5 讲 多维视角看论文写作（第3部分）
> - 课件正文｜研究生论文写作课程材料｜第 6 讲 培养写作能力的若干建议（第2部分）
> - 课件正文｜研究生论文写作课程材料｜第 7 讲 发表高水平论文（第2部分）

---

### 39. 王明琪 — 初次来访 *(verdict: improved)*

**问题:** 当前我的论文定位为一个面向 continuation-anchored LLM serving 的 request dispatch benchmark，核心目标是系统性评测不同请求调度策略在 locality-load tradeoff 下的行为，而不是单纯提出一个新调度算法。希望确认这一定位是否足够明确、是否符合顶会论文的叙事方式。

**BEFORE [review_queue / kb=0]:**

> 这个请求需要人工审核后才能给出正式结论，我先不替老师做决定。
> 已加入待审核队列：49e31b1d-37b3-46ae-ac71-7ed27899bf70
> 原因：这类请求需要老师审核后才能正式答复。

**AFTER [ask_follow_up / kb=3]:**

> 请问您具体需要了解什么?
> 
> 我大致检索到这些相关材料，可一起说明你想聚焦哪一块：
> - 主页附件正文｜2026 cccf domestic inference engine survey（第2部分）
> - 课件正文｜大模型推理基础设施课程材料｜第 4 讲 请求调度（第2部分）
> - Current Research | 2026 CCF-Ant Proposal (VAMOS)

---
