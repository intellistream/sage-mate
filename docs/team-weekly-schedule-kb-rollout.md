# 周工作安排知识注入：验证与生效指南

这份文档给 twin maintenance team 使用，说明团队周工作安排知识已经注入到本地知识库后，如何验证、如何让索引生效，以及后续如何维护。

## 背景

当前环境已经向 `sage-faculty-twin` 的知识库注入 6 份团队周工作安排文档，目标是让数字分身能够回答以下类型的问题：

- 团队固定会议有哪些
- 老师每周一上午的安排是什么
- 学生什么时候可以预约讨论
- 某一角色在特定工作日通常做什么

这些知识文件当前位于运行时知识目录 `data/knowledge_base/`。注意，这个目录属于运行时数据边界，适合作为部署环境中的本地状态，不应作为通用源码改动提交。

## 已注入文档

以下 6 份文档与 [tools/ingest_weekly_schedules.py](sage-faculty-twin/tools/ingest_weekly_schedules.py) 中的映射一致：

| 文件 | 知识库标题 | source_name |
|------|-----------|-------------|
| `pi-weekly-schedule.md` | 团队管理｜项目负责人周工作安排 | `team-schedule/pi-weekly-schedule` |
| `engineer-weekly-schedule.md` | 团队管理｜工程师周工作安排 | `team-schedule/engineer-weekly-schedule` |
| `project-assistant-weekly-schedule.md` | 团队管理｜项目助理周工作安排 | `team-schedule/project-assistant-weekly-schedule` |
| `part-time-assistant-weekly-schedule.md` | 团队管理｜兼职助理周工作安排 | `team-schedule/part-time-assistant-weekly-schedule` |
| `academic-student-weekly-schedule.md` | 团队管理｜学术路线学生周工作安排 | `team-schedule/academic-student-weekly-schedule` |
| `engineering-student-weekly-schedule.md` | 团队管理｜工程路线学生周工作安排 | `team-schedule/engineering-student-weekly-schedule` |

## 关键日程摘要

下面这些信息适合用来做功能验收：

- 每周一 09:00–09:30：周工作安排会，参与角色包括 PI、工程师、项目助理、兼职助理
- 每周三 08:30–09:30：大课题双周会
- 每周三 10:00–11:00：大项目双周会
- 每周三 14:00–17:00：学术路线学生 1:1 开放预约时段
- 每周五上午：阅读分享会，学术路线同学进行文献分享

## 验证步骤

### 1. 确认文件已写入

在部署环境执行：

```bash
cd /home/shuhao/sage-faculty-twin
grep -rl "team-schedule/" data/knowledge_base/ | wc -l
```

预期输出是 `6`。

### 2. 检查标题、长度与标签

```bash
cd /home/shuhao/sage-faculty-twin
for f in $(grep -rl "team-schedule/" data/knowledge_base/); do
  echo "--- $(python3 -c "import json; print(json.load(open('$f'))['title'])")"
  python3 -c "import json; d=json.load(open('$f')); print(f'  chars={len(d[\"content\"])}, tags={d[\"tags\"]}')"
done
```

这里重点确认三件事：

- 标题与上表一致
- `content` 不是空字符串
- `tags` 中至少包含 `schedule`、`weekly-routine` 等检索标签

### 3. 让索引生效

[tools/ingest_weekly_schedules.py](sage-faculty-twin/tools/ingest_weekly_schedules.py) 在缺少 `sentence-transformers` 时会直接写 JSON 文件，并提示索引在下次服务启动时重建。因此知识写入磁盘后，还需要让知识索引重新加载。

推荐方式：

```bash
cd /home/shuhao/sage-faculty-twin
./manage.sh restart
```

如果不希望重启服务，也可以在完整依赖环境下手动初始化知识库：

```bash
cd /home/shuhao/sage-faculty-twin
PYTHONPATH=src:/home/shuhao/SAGE/src:/home/shuhao/sageVDB:/home/shuhao/neuromem \
  python -c "
from sage_faculty_twin.config import AppSettings
from sage_faculty_twin.knowledge_base import LocalKnowledgeStore
store = LocalKnowledgeStore(AppSettings())
print(f'Loaded {len(store.list_documents())} documents, indexes rebuilt.')
"
```

如果命令可以正常构造 `LocalKnowledgeStore` 并输出文档数量，说明本地知识文档已被重新扫描和加载。

## 功能验证

完成索引重建后，建议直接对 twin 发起以下问题做验收：

### 问题 1

```text
我每周一上午的安排是什么？
```

预期回答要点：

- 09:00–09:30 周工作安排会
- 会后会审阅周报、PR 状态、课题进展等

### 问题 2

```text
学生什么时候可以约我讨论？
```

预期回答要点：

- 每周三下午 14:00–17:00
- 学术路线学生开放预约
- 每人约 30 分钟

### 问题 3

```text
工程师周一要做什么？
```

预期回答要点：

- 09:00 参加周工作安排会
- 会后分拣 PR、跟进工程事项、参加相关例会

### 问题 4

```text
团队有哪些固定的会议？
```

预期回答要点：

- 周一晨会
- 周三上午的双周会
- 周三下午学生 1:1
- 周五上午阅读分享会

## 后续维护

如果周工作安排有变更，先更新源文件，再重新执行摄入脚本并重建索引：

```bash
cd /home/shuhao/sage-faculty-twin
python tools/ingest_weekly_schedules.py
./manage.sh restart
```

源文件目录：

```text
/home/shuhao/private-materials/课题组管理/周工作安排/
```

这个摄入脚本会按 `source_name` 做 upsert，已存在的文档会复用原有 `document_id` 更新内容，不会重复堆积脏数据。

## 备注

- [docs/runtime-data.md](sage-faculty-twin/docs/runtime-data.md) 已明确 `data/knowledge_base/` 属于运行时目录，维护时请把它当部署态数据处理。
- 如果生产环境和开发环境依赖不一致，优先使用 `./manage.sh restart` 触发服务侧重建，而不是手工在瘦环境里导入 Python 模块。