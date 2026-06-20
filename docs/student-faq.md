# my-twin 常问问题清单 (FAQ)

> 数据基础: `docs/student-questions-summary.md` (64 条真实学生提问) + `docs/student-questions-poor-answers.md` (39 条回答不佳的 case)。
> 更新节奏: **每周一** 由 `tools/refresh_student_faq.py` 重新聚类一次, 然后人工 review。
> 维护人: Shuhao。

## 怎么用这份清单

1. **每个 FAQ 条目** = 一类高频问法 (基于真实对话聚类), 带 *代表问句*、*KB 覆盖状态*、*应对材料*、*下一步动作*。
2. **KB 覆盖状态**:
   - ✅ Covered — 知识库已有可直接被检索命中的条目, 列出 source 文档名。
   - 🟡 Partial — 命中相邻文档但缺一个直接、简短、对话化的版本; 需要补一篇 FAQ 短文。
   - ❌ Missing — 没有任何对应文档; 必须新增材料。
3. **应对材料字段** 使用 `data/knowledge_base/` 下的标准 FAQ 文档结构 (title 以 `FAQ |` 起, tags 含 `faq`)。新增材料统一走 `tools/ingest_workspace_repos.py --kind faq` 摄入。
4. 每次新增/修改 FAQ 文档后, **必须重启 app** 让 `LocalKnowledgeStore` 重建 FAISS 索引 (`bash manage.sh restart sage-faculty-twin-app`)。

---

## TL;DR · 当前 7 大常问主题

| # | 主题 | 频次 (poor-answer) | KB 覆盖 | 优先级 |
|---|------|-------------------|---------|--------|
| A | **身份与系统介绍** (你是谁 / 这个系统能做什么) | 6 | 🟡 | P0 |
| B | **实验室成员名单** (张老师指导过哪些学生) | 8 | ❌ | P0 |
| C | **文献整理方法** (怎么围绕课题整理 / 汇报文献) | 7 | 🟡 | P0 |
| D | **论文阅读 / 评论** (帮我看论文 / kvpr 这篇) | 4 | 🟡 | P1 |
| E | **研究问题定义评估** (我的选题定义有问题吗) | 3 | 🟡 | P1 |
| F | **顶会论文叙事 / 论文定位** | 1 (但被 review_queue 拦截) | ✅ | P1 |
| G | **短模糊 follow-up** (具体内容 / 已有的 / 是的) | 10 | (检索层已修, 无需新文档) | P2 |

---

## A. 身份与系统介绍

**频次**: 阮弘毅 1-4 (你是谁/你的身份/学术背景), 曹哲 10 (这个系统可以做什么), 王明琪 1 (在吗)。

**代表问句**:

- 你是谁 / 你的身份 / 你的身份背景
- 你的学术背景 / 你的研究方向
- 你这个系统可以做什么 / 在吗

**当前 KB 覆盖**: 🟡 Partial — `主页资料｜张书豪`、`研究总览｜研究主线`、`Lab System | SAGE README` 已存在并被 force-include, 但缺一篇 *面向首次来访学生的 60 秒自我介绍*。

**应对材料 (待补)**: `FAQ | 我是 my-twin (张书豪老师的数字分身)` —— 1) 我是谁 (张书豪老师的研究/教学数字分身); 2) 我能做什么 (回答研究/教学/学生指导问题、推荐先读材料、在不确定时把问题交给老师); 3) 我不能做什么 (不替老师做录取/打分/合作意向决定); 4) 你可以问的 5 个示例问题。

**下一步**:

- [ ] 写 `data/knowledge_base/faq-self-introduction.json`, 1 段 ≤ 200 字。
- [ ] 在 `persona/zhangshuhao.json` 里补 `learning_focus_summary` 和 `lab_pitch_30s` 两个字段, 让 deterministic floor 直接拿来回答。

---

## B. 实验室成员名单

**频次**: 王子澳 1-8 (8 条连续追问)。

**代表问句**:

- 张老师有那些学生 / 张老师指导过的学生名单
- 学生名单 / 学生的名字 / 张睿诚的姓名
- 正在指导的学生信息

**当前 KB 覆盖**: ❌ Missing。检索完全打不到, 因为 `data/knowledge_base/` 里没有任何"实验室成员/学生列表"文档, `data/user_accounts/` 是私有的 booking 数据。

**应对材料 (必补)**: `FAQ | 实验室成员` —— 列出 *公开可披露* 的当前学生与已毕业学生 (姓名 + 入学年份 + 研究方向 + 简短 1 行成果)。私人信息 (邮箱、手机) **不要进 KB**。

**下一步**:

- [ ] 把 `shuhaozhangtony.github.io/contents/students.md` (或新建) 用 `ingest_workspace_repos.py` 摄入。
- [ ] 在 `light_agent.py` 里加一条 deterministic guardrail: 命中 `学生名单 / 指导过 / 学生姓名` 关键词时强制 include "实验室成员" 文档; 若文档缺失则降级为 "目前可公开的成员名单尚未整理, 建议直接邮件 zhangshuhao@hust.edu.cn"。
- [ ] 把私人字段 (邮箱) 留在 `data/user_accounts/`, 不写进 KB。

---

## C. 文献整理 / 汇报方法

**频次**: 曹哲 1, 2, 3, 4, 11, 12, 22 (7 条)。

**代表问句**:

- 我整理了十篇文献, 汇报的内容应该包括什么
- 我该怎么围绕我的课题整理文献
- 我现在就是不知道哪些文献是相关文献
- 怎么整理相关文献的建议

**当前 KB 覆盖**: 🟡 Partial — *研究生论文写作课* 第 5/6/7 讲讲了 "如何写综述、相关工作", 但没有专门面向 "刚整理完一批文献准备汇报" 的一份动作清单。

**应对材料 (待补)**: `FAQ | 文献整理与汇报模板` —— 1) 汇报必带的 4 段: 问题定义 / 方法分类树 / 与本课题的差距 / 你接下来要做什么; 2) 整理文献时回答的 6 个问题 (它解决什么问题、关键 insight、实验设置、与你的课题最近的差异、能否复现、未来工作); 3) 找相关文献的 3 步法 (顶会列表过滤 → forward citation → backward citation)。

**下一步**:

- [ ] 起 `data/knowledge_base/faq-literature-survey.json`, 引用 `第 5 讲 多维视角看论文写作` 的对应章节做交叉链接。
- [ ] Persona 里加 `literature_review_protocol` 字段。

---

## D. 论文阅读 / 评论

**频次**: 曹哲 5, 7, 8, 13 (4 条)。

**代表问句**:

- 你能帮我看论文吗 / 让你帮忙看看已有的论文
- kvpr 这篇 (具体某一篇)
- 都讲讲吧 / 都需要

**当前 KB 覆盖**: 🟡 Partial — 已经有 `论文提炼｜SAGE...`、`论文提炼｜KV-Pruner...` 等文档, 但学生问 "kvpr 这篇" 时检索器需要别名映射 (kvpr ↔ KV-Pruner)。

**应对材料 (待补)**:

- 一份 `FAQ | 我能帮你怎么看论文` —— 1) 我能给的: 一段 ≤ 200 字摘要 + 与本组研究的关联; 2) 我不能给的: 详细推导验证、是否抄袭判定; 3) 怎么帮我帮你: 给 ArXiv 链接 / 论文标题 / 至少能搜到的关键词。
- 在每篇 `论文提炼｜...` 文档里追加一行 `aliases:` 字段 (kvpr / kv-pruner / KV Reuse Pruner ...), 让检索预处理时做软同义。

**下一步**:

- [ ] 改 `tools/ingest_workspace_repos.py` 让 `论文提炼｜` 类型读取 frontmatter 里的 `aliases` 字段。
- [ ] 跑一次 `python tools/refresh_student_faq.py --check-aliases` 验证 kvpr / kv-pruner / SAGE 等都能命中。

---

## E. 研究问题定义评估

**频次**: 曹哲 15, 20, 21 (3 条)。

**代表问句**:

- 我现在的研究课题是 X, 这个问题定义有什么问题吗
- 我应该围绕什么问题阅读文献
- 部分复用甚至不复用可能比全复用更好, 这个问题定义有什么问题吗

**当前 KB 覆盖**: 🟡 Partial — `第 5 讲 多维视角看论文写作` 与 `FAQ | 顶会论文叙事是什么样` 已经讲了 "好的研究问题应该是什么样", 但没有面向 *一段具体描述* 的 review checklist。

**应对材料 (待补)**: `FAQ | 怎么 review 一个研究问题定义` —— 6 条 review checklist:

1. 问题是不是 well-defined (输入/输出/可观测指标都讲清楚了吗)
2. 与已有方法对比的 baseline 是不是清楚
3. 假设是否可证伪 (有没有反例边界)
4. 评测指标是 system-level 还是 paper-level
5. 工作量是 1 个学生 6 个月可做完的吗
6. 论文叙事属于 **measurement / mechanism / system / theorem** 哪一类

**下一步**:

- [ ] 起 `data/knowledge_base/faq-research-problem-review.json`, 与 `FAQ | 顶会论文叙事是什么样` 互引。

---

## F. 顶会论文叙事 / 论文定位

**频次**: 王明琪 2 (1 条, 但被 `review_queue` 拦截)。

**代表问句**:

- 当前我的论文定位为 X, 是否符合顶会论文的叙事方式
- 你觉得这个 benchmark 题目能投顶会吗

**当前 KB 覆盖**: ✅ Covered — `FAQ | 顶会论文叙事是什么样` 已经存在并被命中。这一类不是 KB 问题, 是 escalation 策略问题——当前规则把所有 *"这个工作能不能投顶会"* 都送进 `review_queue`。

**应对材料**: 已经存在 (`FAQ | 顶会论文叙事是什么样`)。

**下一步**:

- [ ] 调整 `workflow_policies/`, 让 *自我评估类* (学生先描述自己定位再问反馈) 走 `advise_only` + 命中 FAQ 文档, 而不是直接 escalate; 真正需要老师拍板的是 *投稿决定*, 不是 *叙事评估*。

---

## G. 短模糊 follow-up

**频次**: 曹哲 6, 9, 13, 14, 16, 17, 18, 19, 23, 24 (10 条)。

**代表问句**:

- 已有的 / 具体内容 / 都需要 / 是的 / 都讲讲吧
- 你会联系上下文吗
- 什么叫具体背景信息
- 你觉得我刚刚的问题的主题是什么呢
- 我是老师手底下的研究生

**当前 KB 覆盖**: 不是 KB 缺料问题, 是 **检索 + 上下文** 问题。

- 短查询扩展 (Task 4) 已落地, replay 已确认 case 6/8/9 在 FAISS 后端下从 `ask_follow_up` 升级为 `answer`。
- 检索后端从 BM25 切换到 `faiss:BAAI/bge-small-zh-v1.5` 后, 这一类的 kb_hits 从 0 升到 3。

**应对材料**: 不需要新 FAQ 文档, 但要补一条 *deterministic 元 FAQ*: `FAQ | 我会不会联系上下文`。

**下一步**:

- [ ] 起 `data/knowledge_base/faq-context-awareness.json` ≤ 100 字: "会的——同一个 conversation_id 下我会读最近 N 轮; 跨会话则需要你简单回顾一下背景"。
- [ ] 对 `你觉得我刚刚的问题的主题是什么呢` 这种 meta-pragmatic 查询, 在 `_normalize_interaction_intent` 加一条规则: 检测到 `刚刚 / 上面 / 之前 + 问题 / 主题` 时强制走 *回顾上一轮* 分支, 而不是再去检索。

---

## 定期更新流程 (每周一)

```bash
# 1. 重新聚类最新对话
cd /home/shuhao/sage-faculty-twin
python tools/refresh_student_faq.py \
    --conversation-source data/conversation_memory/collections/conversation-memory/raw_data.json \
    --output docs/student-faq.candidates.md

# 2. diff 出新 cluster (人工 review)
diff docs/student-faq.md docs/student-faq.candidates.md | less

# 3. 对每个新 cluster, 决定:
#    a. 加进现有主题 (合并)
#    b. 新建 FAQ 文档 (写进 data/knowledge_base/)
#    c. 走 deterministic guardrail (改 light_agent.py / persona)

# 4. 落库 + 重启
python tools/ingest_workspace_repos.py --kind faq
bash manage.sh restart sage-faculty-twin-app

# 5. replay 一次确认改善
python tools/replay_poor_cases.py --mock-llm \
    --output docs/student-questions-replay-report.md
```

`tools/refresh_student_faq.py` 还没写——它需要做:

1. 读 raw conversation log。
2. 用 `bge-small-zh-v1.5` (我们已经在 KB 用同一份模型) 给每个学生提问编码, DBSCAN 聚类 (eps≈0.35, min_samples=3)。
3. 对每个 cluster 选 top-3 代表问句, 输出 `## Cluster <id>` 区块, 含:
   - representative_questions
   - hit_count (本周新增 / 累计)
   - top_3_kb_documents (用现 store 检索)
   - kb_coverage_status (✅/🟡/❌, 阈值: top-1 score ≥ 0.55 → ✅; ≥ 0.35 → 🟡; 否则 ❌)
4. 写到 `docs/student-faq.candidates.md`, 由人合并。

**我下一步要做的事**: 写 `tools/refresh_student_faq.py` (P1) + 把上述 7 个 FAQ 主题里标了 ❌/🟡 的 5 篇短文先补上 (P0)。补完后再跑一次 replay, 期望:

- 王子澳 8 条 (实验室名单类) 从 verdict=improved (但 wf 仍 ask_follow_up) → wf=answer。
- 阮弘毅 1-3 (你是谁) 从 KB=0 → KB=3。
- 曹哲 11/12 (文献整理建议) 从 wf=ask_follow_up → wf=answer。

确认要不要现在就动手写 5 篇 FAQ + `refresh_student_faq.py`？
