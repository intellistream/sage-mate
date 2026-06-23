# KB 权限审阅清单

根据 `data/knowledge_base/*.json` 和 `src/sage_faculty_twin/knowledge_base.py` 的可见性逻辑生成。本文档只列标题、来源和路由元数据，不复制私有正文。

## 当前可见性规则

- 如果存在显式 `metadata.audience` 或 `audience:*` tag，则按该 audience 控制访问。
- 没有显式 audience 的文档，如果来源是 `private-materials:` / `workspace/`，或路径/tag 命中 proposal、roadmap、基金、LOA 等敏感信号，会被推断为 `lab_member`。
- 其他没有显式 audience 的文档会对所有人可见，表里记作 `public_by_default`，实际等价于公开。

## 数量统计

| 实际可见桶 | 数量 |
| --- | ---: |
| `public_by_default` | 484 |
| `graduate` | 69 |
| `lab_member` | 64 |
| `public` | 16 |
| `admin` | 8 |
| `undergraduate` | 5 |
| `manager` | 1 |

| 显式 audience metadata/tag | 数量 |
| --- | ---: |
| `none` | 484 |
| `graduate` | 69 |
| `lab_member` | 64 |
| `public` | 16 |
| `admin` | 8 |
| `undergraduate` | 5 |
| `manager` | 1 |

## 访问者到权限桶映射

| 请求身份/角色 | 可访问 audience | 备注 |
| --- | --- | --- |
| `general_visitor` 或未登录 | `public` + `public_by_default` | 公开访客。 |
| `hust_undergraduate` | `public`, `undergraduate` + `public_by_default` | 本科课程材料额外开放。 |
| `paper_writing_student` | `public`, `graduate` + `public_by_default` | 研究生/论文写作课程材料额外开放。 |
| `lab_member` | `public`, `undergraduate`, `graduate`, `lab_member` + `public_by_default` | 邀请码组内同学。七问法现在在这一层。 |
| `admin_role=manager` | `public`, `undergraduate`, `graduate`, `lab_member`, `manager` + `public_by_default` | 管理员角色叠加在 visitor profile 之上。 |
| `admin_role=super_admin` | 全部，包括 `admin` | 最高权限。 |

## 已按本轮确认调整

| 标题 | 当前权限 | 处理结果 |
| --- | --- | --- |
| 项目文档｜面向国产硬件极致性能优化的推理引擎（课题实施方案） | `admin` | 从 public 收紧为超管/负责人审阅。 |
| 私有材料精选｜国产算力大模型推理服务系统研究框架 | `lab_member` | 按确认改为邀请码组内同学可见。 |
| Wiki \| Ascend NPU 开发环境搭建指南 | `public` | 保持公开，但移除具体内部化硬件配置/性能建议表述。 |
| 管理资料｜课题组成员信息总表 | `manager` | 保持 manager；另有测试确认普通访客/lab_member 不可见，manager/super_admin 可见。 |
| 未显式标注但被推断为 Lab Member 的敏感来源 | `lab_member` | 52 条全部补成显式 `audience:lab_member`。 |

## 显式 Public (16)

| 来源 | 标题 | 文件 |
| --- | --- | --- |
| wiki:tutorials/ascend-npu-setup | Wiki \| Ascend NPU 开发环境搭建指南 | `c12a6884-de64-4757-a795-e30b3ba1cae7.json` |
| wiki:intro | Wiki \| Intro | `9851c5d1-cff0-4d75-b076-1148e6f1cb76.json` |
| wiki:tutorials/llm-inference-basics | Wiki \| LLM 推理入门——从 Prefill 到 Decode | `678a21ad-0b8f-42bf-870b-028707da70cb.json` |
| wiki:tutorials/prompt-engineering-guide | Wiki \| Prompt Engineering 实践指南 | `1bb0b254-2762-44b1-bd5f-eac3ffc3d19d.json` |
| wiki:achievements/sage-system-overview | Wiki \| SAGE 系统概述与里程碑 | `c5377439-3d8b-46d3-91aa-f87f1986aa5a.json` |
| wiki:resources/tools-and-frameworks | Wiki \| 常用工具与框架清单 | `57e267a1-b81d-4d86-8ce7-25d601d36e27.json` |
| wiki:resources/inference-benchmark-guide | Wiki \| 推理系统 Benchmark 指南 | `71299a3d-6073-4d78-b2c1-394e2d573ca1.json` |
| wiki:resources/recommended-reading | Wiki \| 推荐阅读与学习资源 | `17e748fa-1cc1-4f60-b8f7-aef3f2010cfd.json` |
| private-materials:publication-venue-stats | 个人资料｜发表文章 Venue 统计 | `f63449c4-feee-43f0-95b8-b856f631a4c0.json` |
| private-materials:lecture-ecnu-inference-infra | 演讲讲稿｜华东师大学术沙龙：面向国产异构算力的大模型推理基础设施 | `7758f4e5-7d4c-457f-b358-9b0d34e68166.json` |
| private-materials:curated-bio-awards-service | 私有材料精选｜张书豪公开个人简介、奖励与学术服务 | `c4c85772-3e7e-4bb9-ba8d-b0850006d5b1.json` |
| private-materials:curated-state-management-research-line | 私有材料精选｜状态管理到大模型推理基础设施研究主线 | `b09b0e0e-151a-4463-bca5-1657b6c1cdfe.json` |
| private-materials:cccf-survey-revision-lessons | 论文写作方法｜中文综述论文修改经验 | `5369f797-ac80-4a3d-8130-820b2d04c0f4.json` |
| private-materials:paper-revision-lessons | 论文写作方法｜系统论文修改与打磨经验 | `66235eb6-a046-4b6d-9c5a-206b53a206a8.json` |
| private-materials:paper-revision-lessons-zh-summary | 论文写作方法｜系统论文修改中文速查清单：避免实验比较不公平 | `f6f33d6c-f80c-420c-91b5-5fc93a534d35.json` |
| homepage:publications-list | 论文列表｜完整论文索引与PDF下载 | `a43c62a4-f6c9-4ede-83a7-a612e29b6d2c.json` |

## 显式 Lab Member (64)

| 来源 | 标题 | 文件 |
| --- | --- | --- |
| workspace/vamos/proposal | Current Research \| 2026 CCF-Ant Proposal (VAMOS) | `bf89ff15-c2a2-4d8d-a6bf-68db833a053b.json` |
| workspace/vamos | Current Research \| VAMOS README | `fb0adf8e-0aa8-4ba0-b3a2-e803bc72a14c.json` |
| workspace/vamos/roadmap | Current Research \| VAMOS Roadmap | `715c0310-e33f-4b89-86cf-53d2407d3ad3.json` |
| workspace/neuromem | Lab System \| Neuromem README | `300b3520-e356-4774-acb7-bc6c880c4e77.json` |
| workspace/SAGE | Lab System \| SAGE README | `fd0ff1b0-8849-4cf8-a2f7-c1677978f7e7.json` |
| workspace/sageVDB | Lab System \| SageVDB README | `97e6e7d7-d00c-41c1-a645-711ad8216b71.json` |
| workspace/vllm-hust | Lab System \| vLLM-HUST README | `b4737220-8e87-4a5c-ad5d-e304824a533c.json` |
| workspace/sage-tutorials | Teaching \| Sage-Tutorials Quick Start | `662163ab-6443-4b5e-abd7-8d8108e9868f.json` |
| wiki:tech-notes/continuous-batching-notes | Wiki \| Continuous Batching 技术笔记 | `982b3fc7-b03e-4750-aa74-cba2cd705715.json` |
| wiki:tech-notes/kv-cache-optimization | Wiki \| KV Cache 优化技术详解 | `895e7ecd-76e2-422d-b93f-b2b908933481.json` |
| wiki:tech-notes/npu-memory-management | Wiki \| NPU 显存管理与调度策略 | `04579934-3508-4ac6-b525-580dd7ab0db2.json` |
| wiki:industry-docs/prompt-engineering-cb-cli | Wiki \| Prompt Engineering——Codebuddy CLI 提示词设计 (完整翻译版) | `f454c728-13b9-4f2e-b732-f97b8eb322e6.json` |
| wiki:tech-notes/retrieval-augmented-generation | Wiki \| RAG 系统设计与实践 | `0a6054e2-9a1c-450e-b208-42b6acfa9778.json` |
| wiki:standards/code-review-standards | Wiki \| 代码 Review 规范 | `e2134409-a7cc-420b-992f-0df67b7788e5.json` |
| wiki:tech-notes/distributed-inference-patterns | Wiki \| 分布式推理架构模式 | `3745d0a5-8cf1-4c89-9a38-9bf7371bea6b.json` |
| private-materials:bio-awards | 个人资料｜个人简介、奖励与任职主稿 | `ff5333f4-ee45-4c30-9869-51e7194d96b3.json` |
| onboarding-handbook | 新生手册：第一个月实用指南 | `onboarding-first-month.json` |
| private-materials:curated-domestic-inference-serving-framework | 私有材料精选｜国产算力大模型推理服务系统研究框架 | `92049b10-499f-41a3-87f2-12f7abfb252d.json` |
| private-materials:how-to-think-about-research-topic | 科研指导方法｜如何确定一个好的研究课题 | `72244e9d-5835-46b3-9685-b938d1849ded.json` |
| homepage:contents/awards/基金/Award - Zhang Shuhao.pdf::part-1 | 荣誉附件正文｜Award Zhang Shuhao（第1部分） | `9710ffd6-8d4b-43c3-9401-aff6454303d2.json` |
| homepage:contents/awards/基金/Award - Zhang Shuhao.pdf::part-2 | 荣誉附件正文｜Award Zhang Shuhao（第2部分） | `7e536ceb-00e7-4e2c-a444-576538683dea.json` |
| homepage:contents/awards/基金/LOA Combine.pdf::part-10 | 荣誉附件正文｜LOA Combine（第10部分） | `5e1df9b5-664e-4caa-ba0e-918cefc7783e.json` |
| homepage:contents/awards/基金/LOA Combine.pdf::part-11 | 荣誉附件正文｜LOA Combine（第11部分） | `a4b8565d-7975-4aa7-9bb9-6a53159eb9b8.json` |
| homepage:contents/awards/基金/LOA Combine.pdf::part-12 | 荣誉附件正文｜LOA Combine（第12部分） | `d859c40e-9a90-4162-8989-ac84cf4f4847.json` |
| homepage:contents/awards/基金/LOA Combine.pdf::part-13 | 荣誉附件正文｜LOA Combine（第13部分） | `62b4ace7-026b-4d17-a31e-b1c7021a8f01.json` |
| homepage:contents/awards/基金/LOA Combine.pdf::part-1 | 荣誉附件正文｜LOA Combine（第1部分） | `f3724bdd-3275-4fb3-94fd-5d924fc88ebe.json` |
| homepage:contents/awards/基金/LOA Combine.pdf::part-2 | 荣誉附件正文｜LOA Combine（第2部分） | `ab556e02-5c19-41c9-b768-b132cf334ded.json` |
| homepage:contents/awards/基金/LOA Combine.pdf::part-3 | 荣誉附件正文｜LOA Combine（第3部分） | `f80f4791-c8e3-4d56-b31f-aea7cc081094.json` |
| homepage:contents/awards/基金/LOA Combine.pdf::part-4 | 荣誉附件正文｜LOA Combine（第4部分） | `a81c5328-b6f3-44b1-a4fc-3805871a988f.json` |
| homepage:contents/awards/基金/LOA Combine.pdf::part-5 | 荣誉附件正文｜LOA Combine（第5部分） | `83ffa4d7-a0b5-417f-a3d6-691cd0ef1f07.json` |
| homepage:contents/awards/基金/LOA Combine.pdf::part-6 | 荣誉附件正文｜LOA Combine（第6部分） | `bbdd2d6c-b724-4e74-87a5-54e0af3c6f6d.json` |
| homepage:contents/awards/基金/LOA Combine.pdf::part-7 | 荣誉附件正文｜LOA Combine（第7部分） | `046486b7-68a5-4569-b535-9e2a9a4a8faf.json` |
| homepage:contents/awards/基金/LOA Combine.pdf::part-8 | 荣誉附件正文｜LOA Combine（第8部分） | `7679c46e-7845-4915-b6f5-262f092f8aa4.json` |
| homepage:contents/awards/基金/LOA Combine.pdf::part-9 | 荣誉附件正文｜LOA Combine（第9部分） | `0a4b46eb-fae1-4e4f-a64a-5ced20292aa3.json` |
| homepage:contents/awards/基金/LOA full.pdf::part-10 | 荣誉附件正文｜LOA full（第10部分） | `0c0ffbd1-c4a8-495d-9b05-5814977be7b7.json` |
| homepage:contents/awards/基金/LOA full.pdf::part-11 | 荣誉附件正文｜LOA full（第11部分） | `42685173-0eec-4812-969a-a7ea896d4225.json` |
| homepage:contents/awards/基金/LOA full.pdf::part-12 | 荣誉附件正文｜LOA full（第12部分） | `10bedfee-b8b0-4221-8016-1caa32f37bd1.json` |
| homepage:contents/awards/基金/LOA full.pdf::part-13 | 荣誉附件正文｜LOA full（第13部分） | `31a5cba6-2c6d-4850-96a4-813f839d72da.json` |
| homepage:contents/awards/基金/LOA full.pdf::part-14 | 荣誉附件正文｜LOA full（第14部分） | `be2cfab1-967e-4ddd-a534-ea4daf7a9d24.json` |
| homepage:contents/awards/基金/LOA full.pdf::part-15 | 荣誉附件正文｜LOA full（第15部分） | `5dc89c43-a53a-4601-96ae-abfe9a71a76e.json` |
| homepage:contents/awards/基金/LOA full.pdf::part-16 | 荣誉附件正文｜LOA full（第16部分） | `a014921f-aeb5-4164-ab43-9f641aa2ac03.json` |
| homepage:contents/awards/基金/LOA full.pdf::part-1 | 荣誉附件正文｜LOA full（第1部分） | `eebac62d-c198-4d8f-a987-ba8d8f7ef51e.json` |
| homepage:contents/awards/基金/LOA full.pdf::part-2 | 荣誉附件正文｜LOA full（第2部分） | `b5d8eeb4-55dd-442c-8391-1e65c51f819a.json` |
| homepage:contents/awards/基金/LOA full.pdf::part-3 | 荣誉附件正文｜LOA full（第3部分） | `8d6b4847-b2f8-4595-8df9-8769b4075ab5.json` |
| homepage:contents/awards/基金/LOA full.pdf::part-4 | 荣誉附件正文｜LOA full（第4部分） | `01449b87-2409-4f37-89ff-ea2dd029b94c.json` |
| homepage:contents/awards/基金/LOA full.pdf::part-5 | 荣誉附件正文｜LOA full（第5部分） | `58f40e72-ad11-428d-81fe-97ec82c33376.json` |
| homepage:contents/awards/基金/LOA full.pdf::part-6 | 荣誉附件正文｜LOA full（第6部分） | `4db42db8-4ef1-4931-a75a-3d4a488f6f21.json` |
| homepage:contents/awards/基金/LOA full.pdf::part-7 | 荣誉附件正文｜LOA full（第7部分） | `8a1521a9-c2c3-473f-a2aa-7cc6281322a6.json` |
| homepage:contents/awards/基金/LOA full.pdf::part-8 | 荣誉附件正文｜LOA full（第8部分） | `428a9d9e-108d-41e7-b203-f490ed40641a.json` |
| homepage:contents/awards/基金/LOA full.pdf::part-9 | 荣誉附件正文｜LOA full（第9部分） | `d5dc35a6-2c38-4966-9a79-ccf2e66f416c.json` |
| homepage:contents/awards/基金/T2EP20122-0035 Letter of Award.pdf | 荣誉附件正文｜T2EP20122 0035 Letter of Award | `0d3a35ea-0253-4284-9f64-cc58e291ea9f.json` |
| homepage:contents/research_papers/2019/2019_thesis_proposal.md#文档::part-10 | 论文页面｜文档（第10部分） | `91435173-1303-456a-bee1-af13b15d331d.json` |
| homepage:contents/research_papers/2019/2019_thesis_proposal.md#文档::part-11 | 论文页面｜文档（第11部分） | `f0ebfdf4-5b4d-48d5-9f78-86ab2a89feb7.json` |
| homepage:contents/research_papers/2019/2019_thesis_proposal.md#文档::part-12 | 论文页面｜文档（第12部分） | `6995077a-5eb5-4b32-ad6f-150ca3e9a928.json` |
| homepage:contents/research_papers/2019/2019_thesis_proposal.md#文档::part-1 | 论文页面｜文档（第1部分） | `4e5a3885-acb4-4646-8369-d0397fc76449.json` |
| homepage:contents/research_papers/2019/2019_thesis_proposal.md#文档::part-2 | 论文页面｜文档（第2部分） | `6bb46fb7-5b57-4da4-9797-9c40e87e07a1.json` |
| homepage:contents/research_papers/2019/2019_thesis_proposal.md#文档::part-3 | 论文页面｜文档（第3部分） | `9d99a9e2-7cb0-447f-8b27-3f3224f5b022.json` |
| homepage:contents/research_papers/2019/2019_thesis_proposal.md#文档::part-4 | 论文页面｜文档（第4部分） | `6494c977-88d5-4e2b-a380-7c119917612b.json` |
| homepage:contents/research_papers/2019/2019_thesis_proposal.md#文档::part-5 | 论文页面｜文档（第5部分） | `4b345cfb-cf68-4db6-b72a-dfd33dca8e98.json` |
| homepage:contents/research_papers/2019/2019_thesis_proposal.md#文档::part-6 | 论文页面｜文档（第6部分） | `23d74d36-4478-4426-8aea-60f537bfa9d7.json` |
| homepage:contents/research_papers/2019/2019_thesis_proposal.md#文档::part-7 | 论文页面｜文档（第7部分） | `c218ced3-6186-4d0a-a576-f00063b2f7d5.json` |
| homepage:contents/research_papers/2019/2019_thesis_proposal.md#文档::part-8 | 论文页面｜文档（第8部分） | `e81c177a-85fd-48df-9fe9-d2ce286af039.json` |
| homepage:contents/research_papers/2019/2019_thesis_proposal.md#文档::part-9 | 论文页面｜文档（第9部分） | `9cb9f619-c2bc-4d98-b3d8-4690e7994549.json` |
| private-materials:综合整理 | 课题组研究方向概述：从流处理到国产推理引擎 | `research-directions-overview-2026.json` |

## 显式 Manager (1)

| 来源 | 标题 | 文件 |
| --- | --- | --- |
| manual:team-members-directory-2026-06 | 管理资料｜课题组成员信息总表 | `6ac1a7d7-7f57-4d76-89ca-bf8c17d7e001.json` |

## 显式 Admin (8)

| 来源 | 标题 | 文件 |
| --- | --- | --- |
| private-materials:overview | Portfolio \| private-materials README | `7f636f0a-1e94-4edb-a66e-39b83d4cf048.json` |
| private-materials:industry-talk-inference | 演讲材料｜大模型推理服务系统 | `4c416e9d-dd36-4e67-8a4b-c5fd2c72faa6.json` |
| private-materials:academic-presentation | 演讲材料｜学术汇报 | `c5ec7ad5-8498-4845-95df-90ed9efecd41.json` |
| private-materials:huawei-proposal-qa | 申报材料｜华为孵化中心项目 Q&A | `5a0e8b46-727f-436e-acff-c4caea9595a6.json` |
| private-materials:public-homepage-sync-boundary | 私有材料精选｜公开主页素材同步边界 | `d3bec73a-0d6e-4096-82fb-e18b70cdd7de.json` |
| private-materials:interview-rubric | 课题组管理｜推免直博面试题纲与评分标准 | `b1b33b40-4c2e-4832-8a59-300098bb4a7e.json` |
| private-materials:national-project-guidelines | 项目文档｜重大专项指南 | `be162e09-0d78-4412-8775-914e81cd33b0.json` |
| private-materials:project-4-implementation-plan | 项目文档｜面向国产硬件极致性能优化的推理引擎（课题实施方案） | `5a9ae372-cde1-406f-8246-2c2b952528f2.json` |

## 显式 Undergraduate (5)

| 来源 | 标题 | 文件 |
| --- | --- | --- |
| homepage:contents/teaching/database/202605数据库系统原理实践任务书.docx::part-1 | 课程附件正文｜数据库实验课｜202605数据库系统原理实践任务书（第1部分） | `f9023a0f-b2c6-4077-8e80-b5319be48d41.json` |
| homepage:contents/teaching/database/202605数据库系统原理实践任务书.docx::part-2 | 课程附件正文｜数据库实验课｜202605数据库系统原理实践任务书（第2部分） | `bd8cce07-617c-4420-8ab2-f28a19f3850e.json` |
| homepage:contents/teaching/database/Clone头歌平台代码到本地.pptx | 课程附件正文｜数据库实验课｜Clone头歌平台代码到本地 | `ed30fb2b-9035-43d2-82a2-afa6aed391c8.json` |
| homepage:contents/teaching/database/数据库系统原理实践报告模板2026春季mysql环境版.docx::part-1 | 课程附件正文｜数据库实验课｜数据库系统原理实践报告模板2026春季mysql环境版（第1部分） | `ad447530-e0ad-4795-a002-fc5091b0b490.json` |
| homepage:contents/teaching/database/数据库系统原理实践报告模板2026春季mysql环境版.docx::part-2 | 课程附件正文｜数据库实验课｜数据库系统原理实践报告模板2026春季mysql环境版（第2部分） | `34bf5a24-d8c2-4ae6-9fe4-c223090bcca6.json` |

## 显式 Graduate (69)

主要是研究生课程材料。下面保留完整标题清单，便于审阅。

| 来源 | 标题 | 文件 |
| --- | --- | --- |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#Tutorials::contents/teaching/intro-to-llm-inference-engines/2026/tutorials/Tutorial_01_工作负载与评价指标.pdf | 课件正文｜大模型推理基础设施课程材料｜Tutorial 1 工作负载与评价指标 | `3a3aa3d3-d4f7-4959-8018-d1bfdda14baf.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#Tutorials::contents/teaching/intro-to-llm-inference-engines/2026/tutorials/Tutorial_10_实验方法与验证.pdf | 课件正文｜大模型推理基础设施课程材料｜Tutorial 10 实验方法与验证 | `b0d47d3e-1b35-438d-a026-c3df9c841c3d.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#Tutorials::contents/teaching/intro-to-llm-inference-engines/2026/tutorials/Tutorial_11_开源系统实践.pdf | 课件正文｜大模型推理基础设施课程材料｜Tutorial 11 开源系统实践 | `c08a1ed2-dab2-456e-bb81-f902f6a4972f.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#Tutorials::contents/teaching/intro-to-llm-inference-engines/2026/tutorials/Tutorial_12_课程项目工作坊.pdf | 课件正文｜大模型推理基础设施课程材料｜Tutorial 12 课程项目工作坊 | `9ac46302-11b5-49bc-b68a-1cbded0948f2.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#Tutorials::contents/teaching/intro-to-llm-inference-engines/2026/tutorials/Tutorial_13_课程总结与汇报.pdf | 课件正文｜大模型推理基础设施课程材料｜Tutorial 13 课程总结与汇报 | `6c4e023d-c862-474b-8f7d-854664a09376.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#Tutorials::contents/teaching/intro-to-llm-inference-engines/2026/tutorials/Tutorial_02_请求生命周期与PrefillDecode.pdf | 课件正文｜大模型推理基础设施课程材料｜Tutorial 2 请求生命周期与 Prefill / Decode | `b7c7d26c-4f47-439a-b9bd-3e5f8babb5c8.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#Tutorials::contents/teaching/intro-to-llm-inference-engines/2026/tutorials/Tutorial_03_调度与连续批处理观察.pdf | 课件正文｜大模型推理基础设施课程材料｜Tutorial 3 调度与连续批处理观察 | `7b1341e4-17cc-4f6e-9f14-1a17cc0f862c.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#Tutorials::contents/teaching/intro-to-llm-inference-engines/2026/tutorials/Tutorial_04_KV_Cache与状态组织.pdf | 课件正文｜大模型推理基础设施课程材料｜Tutorial 4 KV Cache 与状态组织 | `9923972c-e584-4b05-8c6a-74c9378d3271.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#Tutorials::contents/teaching/intro-to-llm-inference-engines/2026/tutorials/Tutorial_05_状态管理与记忆组织.pdf | 课件正文｜大模型推理基础设施课程材料｜Tutorial 5 状态管理与记忆组织 | `a9c55dca-ddfd-4acc-8f62-112375beca0f.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#Tutorials::contents/teaching/intro-to-llm-inference-engines/2026/tutorials/Tutorial_06_推理系统架构.pdf | 课件正文｜大模型推理基础设施课程材料｜Tutorial 6 推理系统架构 | `a6c37e74-6286-4170-885f-8a6a0ed37304.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#Tutorials::contents/teaching/intro-to-llm-inference-engines/2026/tutorials/Tutorial_07_执行优化与异构路径.pdf | 课件正文｜大模型推理基础设施课程材料｜Tutorial 7 执行优化与异构路径 | `f0526479-9f43-4b52-957c-9516a92d46e1.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#Tutorials::contents/teaching/intro-to-llm-inference-engines/2026/tutorials/Tutorial_08_异构平台适配.pdf | 课件正文｜大模型推理基础设施课程材料｜Tutorial 8 异构平台适配 | `0a04132e-4014-415e-aa7e-6de799559d85.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#Tutorials::contents/teaching/intro-to-llm-inference-engines/2026/tutorials/Tutorial_09_论文比较方法.pdf | 课件正文｜大模型推理基础设施课程材料｜Tutorial 9 论文比较方法 | `a6c826f6-744c-4b58-b785-ba3bb48094f5.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#实验单与项目说明::contents/teaching/intro-to-llm-inference-engines/2026/experiments/nano-vLLM实验课/experiment_1_最小运行与代码地图/sheet.pdf::part-1 | 课件正文｜大模型推理基础设施课程材料｜实验 1 最小运行与代码地图（第1部分） | `13ce0f0b-bced-414e-9c42-bf8b7d82bcb2.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#实验单与项目说明::contents/teaching/intro-to-llm-inference-engines/2026/experiments/nano-vLLM实验课/experiment_1_最小运行与代码地图/sheet.pdf::part-2 | 课件正文｜大模型推理基础设施课程材料｜实验 1 最小运行与代码地图（第2部分） | `3ed262fb-08a1-4d00-bed5-c4166cb719fd.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#实验单与项目说明::contents/teaching/intro-to-llm-inference-engines/2026/experiments/nano-vLLM实验课/experiment_2_请求生命周期观察/sheet.pdf | 课件正文｜大模型推理基础设施课程材料｜实验 2 请求生命周期观察 | `817cbc62-c1a2-4f67-89c9-ff0080c7b377.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#实验单与项目说明::contents/teaching/intro-to-llm-inference-engines/2026/experiments/nano-vLLM实验课/experiment_3_调度与连续批处理实验/sheet.pdf | 课件正文｜大模型推理基础设施课程材料｜实验 3 调度与连续批处理实验 | `a5d3827d-4b7b-4b57-be96-efe0a09abeac.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#实验单与项目说明::contents/teaching/intro-to-llm-inference-engines/2026/experiments/nano-vLLM实验课/experiment_4_KV状态与缓存组织实验/sheet.pdf | 课件正文｜大模型推理基础设施课程材料｜实验 4 KV 状态与缓存组织实验 | `81a288c4-5752-404c-a5cd-06d54c43b883.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#实验单与项目说明::contents/teaching/intro-to-llm-inference-engines/2026/experiments/nano-vLLM实验课/experiment_5_指标观测与最小复现实验/sheet.pdf | 课件正文｜大模型推理基础设施课程材料｜实验 5 指标观测与最小复现实验 | `b4d5c4d6-3302-42ba-85b6-167c1fd17d4a.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第01讲_课程导论.pdf::part-1 | 课件正文｜大模型推理基础设施课程材料｜第 1 讲 课程导论（第1部分） | `d66b5ed3-c285-4eef-8459-85f2b76131b4.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第01讲_课程导论.pdf::part-2 | 课件正文｜大模型推理基础设施课程材料｜第 1 讲 课程导论（第2部分） | `d3af8640-5609-402d-b458-d30bb1fbe888.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第10讲_论文比较方法.pdf::part-1 | 课件正文｜大模型推理基础设施课程材料｜第 10 讲 论文比较方法（第1部分） | `62aa57a0-8470-4e54-b9e0-87965ad24284.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第10讲_论文比较方法.pdf::part-2 | 课件正文｜大模型推理基础设施课程材料｜第 10 讲 论文比较方法（第2部分） | `1a95a669-71f4-4882-99e6-3a9f70e18aee.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第11讲_实验方法与验证.pdf::part-1 | 课件正文｜大模型推理基础设施课程材料｜第 11 讲 实验方法与验证（第1部分） | `6308f671-3b4c-4cb9-aaf1-ea2954abb9f2.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第11讲_实验方法与验证.pdf::part-2 | 课件正文｜大模型推理基础设施课程材料｜第 11 讲 实验方法与验证（第2部分） | `32ec8404-7e40-462c-ad69-5e1b1f38a125.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第12讲_开源系统实践.pdf::part-1 | 课件正文｜大模型推理基础设施课程材料｜第 12 讲 开源系统实践（第1部分） | `deb399a2-8be1-4b9a-a0a3-2c57d3ab8e83.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第12讲_开源系统实践.pdf::part-2 | 课件正文｜大模型推理基础设施课程材料｜第 12 讲 开源系统实践（第2部分） | `67710995-1f63-469f-bec8-c13bcc6a0e63.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第13讲_课程项目工作坊.pdf::part-1 | 课件正文｜大模型推理基础设施课程材料｜第 13 讲 课程项目工作坊（第1部分） | `6b6739a8-502a-4902-bdbb-a701b934f3fe.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第13讲_课程项目工作坊.pdf::part-2 | 课件正文｜大模型推理基础设施课程材料｜第 13 讲 课程项目工作坊（第2部分） | `d44af33b-2ddd-48b2-a71c-c3f9452c53af.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第14讲_课程总结与汇报.pdf::part-1 | 课件正文｜大模型推理基础设施课程材料｜第 14 讲 课程总结与汇报（第1部分） | `4fe1dc25-dcaa-4362-8047-718e3cbe81cd.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第14讲_课程总结与汇报.pdf::part-2 | 课件正文｜大模型推理基础设施课程材料｜第 14 讲 课程总结与汇报（第2部分） | `29073376-5052-4a25-8706-5f65145aa4b6.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第02讲_工作负载与评价指标.pdf::part-1 | 课件正文｜大模型推理基础设施课程材料｜第 2 讲 工作负载与评价指标（第1部分） | `42994dd6-a964-4590-b386-e44cc850fee7.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第02讲_工作负载与评价指标.pdf::part-2 | 课件正文｜大模型推理基础设施课程材料｜第 2 讲 工作负载与评价指标（第2部分） | `10bf0238-0f9d-4814-ac9f-6a2eec6866d2.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第03讲_请求生命周期.pdf::part-1 | 课件正文｜大模型推理基础设施课程材料｜第 3 讲 请求生命周期（第1部分） | `80f8b656-863b-4091-bfbc-aa9f3cf005ba.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第03讲_请求生命周期.pdf::part-2 | 课件正文｜大模型推理基础设施课程材料｜第 3 讲 请求生命周期（第2部分） | `2e276c64-90de-4e74-9bdc-8154fe4cb289.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第04讲_请求调度.pdf::part-1 | 课件正文｜大模型推理基础设施课程材料｜第 4 讲 请求调度（第1部分） | `856ff830-3104-4b4c-8f7d-fd150a8d24e8.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第04讲_请求调度.pdf::part-2 | 课件正文｜大模型推理基础设施课程材料｜第 4 讲 请求调度（第2部分） | `50236b9b-32c5-4809-afff-02362f6839d0.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第05讲_KV缓存.pdf::part-1 | 课件正文｜大模型推理基础设施课程材料｜第 5 讲 KV 缓存（第1部分） | `79895f57-ee06-4b71-818f-b8edd99924bf.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第05讲_KV缓存.pdf::part-2 | 课件正文｜大模型推理基础设施课程材料｜第 5 讲 KV 缓存（第2部分） | `785ac3d5-8ac3-46e4-8b41-ae55956ae2f0.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第06讲_状态管理与记忆组织.pdf::part-1 | 课件正文｜大模型推理基础设施课程材料｜第 6 讲 状态管理与记忆组织（第1部分） | `628a156d-a4a3-4e23-80c6-905b233cff4f.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第06讲_状态管理与记忆组织.pdf::part-2 | 课件正文｜大模型推理基础设施课程材料｜第 6 讲 状态管理与记忆组织（第2部分） | `e73b541f-287d-4150-b49c-f4ae05ce0d20.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第07讲_推理系统架构.pdf::part-1 | 课件正文｜大模型推理基础设施课程材料｜第 7 讲 推理系统架构（第1部分） | `dde6c6fd-5ce8-4048-a007-440d89b96dbd.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第07讲_推理系统架构.pdf::part-2 | 课件正文｜大模型推理基础设施课程材料｜第 7 讲 推理系统架构（第2部分） | `a9489eeb-9ef5-425c-9c43-384d169e5a75.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第08讲_执行优化与异构路径.pdf::part-1 | 课件正文｜大模型推理基础设施课程材料｜第 8 讲 执行优化与异构路径（第1部分） | `2571cd3a-92f2-4934-9bdb-86f59489503c.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第08讲_执行优化与异构路径.pdf::part-2 | 课件正文｜大模型推理基础设施课程材料｜第 8 讲 执行优化与异构路径（第2部分） | `98226b8b-025e-42ba-82be-673e059e1581.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第09讲_异构平台适配.pdf::part-1 | 课件正文｜大模型推理基础设施课程材料｜第 9 讲 异构平台适配（第1部分） | `98f71cdf-e529-483e-9c2b-c19169ac7c9b.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/大模型推理基础设施_第09讲_异构平台适配.pdf::part-2 | 课件正文｜大模型推理基础设施课程材料｜第 9 讲 异构平台适配（第2部分） | `d2cc75a9-c0d9-4703-b24b-6e2041376a13.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::contents/teaching/intro-to-llm-inference-engines/2026/slides/handouts/大模型推理基础设施_课程导论讲义.pdf | 课件正文｜大模型推理基础设施课程材料｜课程导论讲义 | `f06a7b25-a2cf-4de9-b23a-8e9707451c83.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#实验单与项目说明::contents/teaching/intro-to-llm-inference-engines/2026/experiments/nano-vLLM实验课/project_课程项目实验说明/sheet.pdf | 课件正文｜大模型推理基础设施课程材料｜课程项目实验说明 | `50d304cd-faff-41e2-8351-6e119c7fdc66.json` |
| homepage:contents/teaching/graduate-paper-writing-course.md#公开课件::contents/teaching/graduate-paper-writing-course/2026/lecture-5-beamer.pdf::part-1 | 课件正文｜研究生论文写作课程材料｜第 5 讲 多维视角看论文写作（第1部分） | `e501f7d3-a35f-4e67-8c10-71e088e03f51.json` |
| homepage:contents/teaching/graduate-paper-writing-course.md#公开课件::contents/teaching/graduate-paper-writing-course/2026/lecture-5-beamer.pdf::part-2 | 课件正文｜研究生论文写作课程材料｜第 5 讲 多维视角看论文写作（第2部分） | `9a5bf26e-fb4b-465f-a9b9-36d495da5bda.json` |
| homepage:contents/teaching/graduate-paper-writing-course.md#公开课件::contents/teaching/graduate-paper-writing-course/2026/lecture-5-beamer.pdf::part-3 | 课件正文｜研究生论文写作课程材料｜第 5 讲 多维视角看论文写作（第3部分） | `8de2c2f3-4813-4f61-8a08-52383b7640a9.json` |
| homepage:contents/teaching/graduate-paper-writing-course.md#公开课件::contents/teaching/graduate-paper-writing-course/2026/lecture-5-beamer.pdf::part-4 | 课件正文｜研究生论文写作课程材料｜第 5 讲 多维视角看论文写作（第4部分） | `d8fa251b-4cca-4361-9b30-8b0cd32e1780.json` |
| homepage:contents/teaching/graduate-paper-writing-course.md#公开课件::contents/teaching/graduate-paper-writing-course/2026/lecture-5-beamer.pdf::part-5 | 课件正文｜研究生论文写作课程材料｜第 5 讲 多维视角看论文写作（第5部分） | `af5b788e-6e8c-4a5e-b8da-ee9bfde5eb7d.json` |
| homepage:contents/teaching/graduate-paper-writing-course.md#公开课件::contents/teaching/graduate-paper-writing-course/2026/lecture-6-beamer.pdf::part-1 | 课件正文｜研究生论文写作课程材料｜第 6 讲 培养写作能力的若干建议（第1部分） | `9f45865c-587f-49ea-88fa-04c66c9021c6.json` |
| homepage:contents/teaching/graduate-paper-writing-course.md#公开课件::contents/teaching/graduate-paper-writing-course/2026/lecture-6-beamer.pdf::part-2 | 课件正文｜研究生论文写作课程材料｜第 6 讲 培养写作能力的若干建议（第2部分） | `2c7180ed-5481-4de1-9305-46c3293d237e.json` |
| homepage:contents/teaching/graduate-paper-writing-course.md#公开课件::contents/teaching/graduate-paper-writing-course/2026/lecture-6-beamer.pdf::part-3 | 课件正文｜研究生论文写作课程材料｜第 6 讲 培养写作能力的若干建议（第3部分） | `5cd59e8c-f090-463b-8888-4d1c7511bb9b.json` |
| homepage:contents/teaching/graduate-paper-writing-course.md#公开课件::contents/teaching/graduate-paper-writing-course/2026/lecture-7-beamer.pdf::part-1 | 课件正文｜研究生论文写作课程材料｜第 7 讲 发表高水平论文（第1部分） | `b61346c1-c9dc-4ea2-a18a-b2bb3c581973.json` |
| homepage:contents/teaching/graduate-paper-writing-course.md#公开课件::contents/teaching/graduate-paper-writing-course/2026/lecture-7-beamer.pdf::part-2 | 课件正文｜研究生论文写作课程材料｜第 7 讲 发表高水平论文（第2部分） | `3d970212-894b-4006-9032-4352a32ddbc9.json` |
| homepage:contents/teaching/graduate-paper-writing-course.md#公开课件::contents/teaching/graduate-paper-writing-course/2026/lecture-7-beamer.pdf::part-3 | 课件正文｜研究生论文写作课程材料｜第 7 讲 发表高水平论文（第3部分） | `26ec2665-c965-4d1f-b0ae-5d9497218e0d.json` |
| homepage:contents/teaching/graduate-paper-writing-course.md#公开课件::contents/teaching/graduate-paper-writing-course/2026/lecture-8-beamer.pdf::part-1 | 课件正文｜研究生论文写作课程材料｜第 8 讲 研究生毕业论文中常见的问题（第1部分） | `71051604-bcd2-4557-9ce9-c37dd5302080.json` |
| homepage:contents/teaching/graduate-paper-writing-course.md#公开课件::contents/teaching/graduate-paper-writing-course/2026/lecture-8-beamer.pdf::part-2 | 课件正文｜研究生论文写作课程材料｜第 8 讲 研究生毕业论文中常见的问题（第2部分） | `55401e51-5372-42eb-a977-e85689b72507.json` |
| homepage:contents/teaching/graduate-paper-writing-course.md#公开课件::contents/teaching/graduate-paper-writing-course/2026/lecture-8-beamer.pdf::part-3 | 课件正文｜研究生论文写作课程材料｜第 8 讲 研究生毕业论文中常见的问题（第3部分） | `73bfaecb-2e98-44ee-9838-f3a26616bbd5.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#大模型推理基础设施课程材料 | 课程资料｜大模型推理基础设施课程材料 | `198ad457-134b-4493-94cf-f70c2af64782.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#Tutorials | 课程资料｜大模型推理基础设施课程材料｜Tutorials | `757c48e1-f432-4576-b2cc-e0da90a8d351.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#实验单与项目说明 | 课程资料｜大模型推理基础设施课程材料｜实验单与项目说明 | `ce9cd4a7-48f3-477c-bf49-c73967f97349.json` |
| homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论 | 课程资料｜大模型推理基础设施课程材料｜讲义与导论 | `e49227ae-0f9e-4639-8bdb-2cd87faf9e87.json` |
| homepage:contents/teaching/graduate-paper-writing-course.md#研究生论文写作课程材料 | 课程资料｜研究生论文写作课程材料 | `79f2f601-1f77-4340-b87b-f1d119924be3.json` |
| homepage:contents/teaching/graduate-paper-writing-course.md#公开课件 | 课程资料｜研究生论文写作课程材料｜公开课件 | `336e3a17-0389-471f-8e95-a7064e2bd806.json` |

## 未显式标注但被推断为 Lab Member 的敏感来源 (0)

这些条目没有显式 audience，但代码会根据来源、路径或 tag 的敏感信号将其限制为 `lab_member`。本轮已将原来的 52 条补为显式标注，因此这里应为 0。

| 来源 | 标题 | 文件 |
| --- | --- | --- |

## 无显式标注且默认公开 (484)

这些条目没有 audience 标签，也没有命中敏感来源/路径信号，因此当前对所有人可见。如果 homepage 导入里有不应公开的附件，应优先检查这个桶。

| 来源族 | 数量 |
| --- | ---: |
| `homepage:contents` | 464 |
| `team-schedule` | 6 |
| `wiki:tech-notes` | 3 |
| `graduate-paper-writing-course:lecture-6` | 1 |
| `curated_faq:meeting-preparation-checklist` | 1 |
| `paper-writing:revision-lessons-english` | 1 |
| `https:` | 1 |
| `paper-writing:revision-lessons-chinese-survey` | 1 |
| `curated_faq` | 1 |
| `graduate-paper-writing-course:lecture-8` | 1 |
| `graduate-paper-writing-course:lecture-7` | 1 |
| `graduate-paper-writing-course:lecture-5` | 1 |
| `homepage:publications-index` | 1 |
| `wiki:tutorials` | 1 |

代表性标题：
- `7a0e2c30-8a4f-4a4b-a271-0a7a44b5a301.json`: FAQ \| my-twin 可以做什么 — curated_faq
- `2b7748b9-0b90-422d-b581-3f1f0d82070f.json`: 常见问题：和老师约会议前需要准备什么材料 — curated_faq:meeting-preparation-checklist
- `b125d014-ae95-4864-b39f-8d6b4d5b8b1b.json`: 论文写作课程｜第5讲：多维视角看论文写作（七种视角分析法） — graduate-paper-writing-course:lecture-5
- `1e17862b-a084-4b11-a901-8bc6fc8cf906.json`: 论文写作课程｜第6讲：培养写作能力的若干建议 — graduate-paper-writing-course:lecture-6
- `8de8aeb4-2aee-4759-b297-81c7fa3bc99a.json`: 论文写作课程｜第7讲：发表高水平论文 — graduate-paper-writing-course:lecture-7
- `89a2ae57-e0d6-4d39-afe6-274a16288b37.json`: 论文写作课程｜第8讲：研究生毕业论文中常见的问题 — graduate-paper-writing-course:lecture-8
- `d882d9b9-a6bc-42c7-a592-a5f3de409d53.json`: 荣誉资料｜代表性知识产权 — homepage:contents/awards.md#代表性知识产权
- `62a7d234-1f5e-452e-8dbe-aa8136884cd3.json`: 荣誉资料｜学术服务 — homepage:contents/awards.md#学术服务
- `46e7f40e-9bcb-4e37-bb9b-070e76bdc0d5.json`: 荣誉资料｜荣誉奖励 — homepage:contents/awards.md#荣誉奖励
- `9b15a61c-8dcf-4eee-a183-a5bf68db7399.json`: 荣誉附件正文｜2025AIC国赛二等奖获奖证书 赛马制 — homepage:contents/awards/2025AIC国赛二等奖获奖证书-赛马制.pdf
- `08f281c1-ce4a-4e04-9462-9d066749dfb9.json`: 荣誉附件正文｜NDBC2025 — homepage:contents/awards/NDBC2025.pdf
- `ccf59a14-3861-4e82-802d-9b24ff3c3e84.json`: 荣誉附件正文｜数据库老师获奖证书 — homepage:contents/awards/数据库老师获奖证书.pdf
- `cc6bed63-8851-4b61-88c6-d5a841128f4e.json`: 主页配置｜config — homepage:contents/config.yml#full
- `0aa1be11-67c0-4c3b-ade8-d7f052b2296c.json`: 主页附件正文｜cv en（第1部分） — homepage:contents/cv_en.pdf::part-1
- `8d16b5d7-1822-41ae-8237-8f1bac1e1670.json`: 主页附件正文｜cv en（第2部分） — homepage:contents/cv_en.pdf::part-2
- `1745eea3-83a2-418e-85bb-3299f98faabf.json`: 主页资料｜张书豪 — homepage:contents/home.md#张书豪
- `10475972-71a8-4336-8109-a0bff4bde04c.json`: 主页资料｜当前系统建设 — homepage:contents/home.md#当前系统建设
- `46047f56-ffaf-43e9-acac-15e12cfe32ce.json`: 主页资料｜招生与合作 — homepage:contents/home.md#招生与合作
- `9b1d9818-d361-4231-b4d1-89b91269fa32.json`: 主页资料｜研究板块 — homepage:contents/home.md#研究板块
- `5636cb77-1348-4e4d-b77a-bee9628a6fbb.json`: 主页资料｜联系方式 — homepage:contents/home.md#联系方式
- `e484dd94-ee1b-4273-b125-9a8879bf2148.json`: 主页资料｜近期动态 — homepage:contents/news.md#recent-updates
- `3aa5f2af-1bfb-4507-8c33-843560f6d26f.json`: 研究总览｜一、共享状态访问、调度与运行时管理 — homepage:contents/publications.md#一、共享状态访问、调度与运行时管理
- `a718f128-ad0c-4e3b-a4f3-418d7a54948f.json`: 研究总览｜三、共享状态演化、复用与稳定推理 — homepage:contents/publications.md#三、共享状态演化、复用与稳定推理
- `e5df1678-24ad-475d-8912-3855c7498882.json`: 研究总览｜二、状态感知执行优化与软硬件协同设计 — homepage:contents/publications.md#二、状态感知执行优化与软硬件协同设计
- `8bacb863-2d19-4506-b249-92382053f33d.json`: 研究总览｜简介 — homepage:contents/publications.md#简介
- `f3e2294a-caf6-41ed-b6e0-e91a29b533c0.json`: 研究总览｜研究主线 — homepage:contents/publications.md#首页导读
- `7908616b-43a0-4f60-b8af-7f98e1cbf4dd.json`: 论文页面｜文档（第1部分） — homepage:contents/research_papers/2013/2013_omnidb_vldb_2013.md#文档::part-1
- `4b68f61a-21e2-4b83-b8ec-d72e82c9c311.json`: 论文页面｜文档（第2部分） — homepage:contents/research_papers/2013/2013_omnidb_vldb_2013.md#文档::part-2
- `eb365018-5216-43dc-9690-8d6a56964f66.json`: 论文页面｜文档（第3部分） — homepage:contents/research_papers/2013/2013_omnidb_vldb_2013.md#文档::part-3
- `61bb3b64-dbfe-4507-8336-b4bde98fad06.json`: 论文页面｜文档（第1部分） — homepage:contents/research_papers/2014/2014_in_cache_query_co_processing_vldb_2014.md#文档::part-1
- `e7bc529e-793e-4199-a103-3b282e39bd5e.json`: 论文页面｜文档（第2部分） — homepage:contents/research_papers/2014/2014_in_cache_query_co_processing_vldb_2014.md#文档::part-2
- `61c809f8-28f1-4d7d-90a9-35da6d140bc4.json`: 论文页面｜文档（第3部分） — homepage:contents/research_papers/2014/2014_in_cache_query_co_processing_vldb_2014.md#文档::part-3
- `28104104-89e8-422f-ab44-2f4132114c4b.json`: 论文页面｜文档（第4部分） — homepage:contents/research_papers/2014/2014_in_cache_query_co_processing_vldb_2014.md#文档::part-4
- `b0f81912-3017-4c80-8082-5d76cd0b252a.json`: 论文页面｜文档（第5部分） — homepage:contents/research_papers/2014/2014_in_cache_query_co_processing_vldb_2014.md#文档::part-5
- `c653701c-bb96-400e-954b-2a621aebfd7f.json`: 论文页面｜文档（第6部分） — homepage:contents/research_papers/2014/2014_in_cache_query_co_processing_vldb_2014.md#文档::part-6
- `5b86c6f2-1796-43b5-b07d-c1929e2ea4aa.json`: 论文页面｜文档（第1部分） — homepage:contents/research_papers/2015/2015_to_co_run_or_not_mascots_2015.md#文档::part-1
- `cc825760-8247-487b-96f2-0f64d07966c7.json`: 论文页面｜文档（第2部分） — homepage:contents/research_papers/2015/2015_to_co_run_or_not_mascots_2015.md#文档::part-2
- `ce47ed2d-e8ec-4321-88e8-862854017c4a.json`: 论文页面｜文档（第1部分） — homepage:contents/research_papers/2016/2016_co_run_study_tpds_2016.md#文档::part-1
- `614d4489-14c3-415e-8de5-e249fe2215bf.json`: 论文页面｜文档（第2部分） — homepage:contents/research_papers/2016/2016_co_run_study_tpds_2016.md#文档::part-2
- `c73b50b3-c015-45ed-b2fc-dd3021ca96e1.json`: 论文页面｜文档（第3部分） — homepage:contents/research_papers/2016/2016_co_run_study_tpds_2016.md#文档::part-3
- `673597f0-8d83-4333-bf3a-1a8100ec8e54.json`: 论文页面｜文档（第4部分） — homepage:contents/research_papers/2016/2016_co_run_study_tpds_2016.md#文档::part-4
- `23f334db-9340-4ac7-bd01-3a8272f9eaea.json`: 论文页面｜文档（第5部分） — homepage:contents/research_papers/2016/2016_co_run_study_tpds_2016.md#文档::part-5
- `cb829210-5290-4532-ba09-072df801b11b.json`: 论文页面｜Cores（第1部分） — homepage:contents/research_papers/2016/2016_sc_paper_sc_2016.md#Cores::part-1
- `8b1cabd0-3b14-4cb4-85e3-fc37cbf220ce.json`: 论文页面｜Cores（第2部分） — homepage:contents/research_papers/2016/2016_sc_paper_sc_2016.md#Cores::part-2
- `5fc8d802-4f31-4100-a31b-0d68d2228115.json`: 论文页面｜Cores（第3部分） — homepage:contents/research_papers/2016/2016_sc_paper_sc_2016.md#Cores::part-3
- `7a435523-ecc5-4a65-87b6-1d1118d05b0b.json`: 论文页面｜Cores（第4部分） — homepage:contents/research_papers/2016/2016_sc_paper_sc_2016.md#Cores::part-4
- `7dd754ed-6a75-44f3-81f6-19d5314041ac.json`: 论文页面｜Cores（第5部分） — homepage:contents/research_papers/2016/2016_sc_paper_sc_2016.md#Cores::part-5
- `fc4abc50-9bd0-40dd-9456-a6ff1e2c5f9d.json`: 论文页面｜文档（第1部分） — homepage:contents/research_papers/2017/2017_melia_tpds_2017.md#文档::part-1
- `1396115a-b00f-43d7-a019-11f87bb6086c.json`: 论文页面｜文档（第2部分） — homepage:contents/research_papers/2017/2017_melia_tpds_2017.md#文档::part-2
- `6a1d8d3a-f64f-417d-acc2-54673abc7eb9.json`: 论文页面｜文档（第3部分） — homepage:contents/research_papers/2017/2017_melia_tpds_2017.md#文档::part-3
- `9172764c-72ba-47e9-8c56-9b3a3aafdbb4.json`: 论文页面｜文档（第4部分） — homepage:contents/research_papers/2017/2017_melia_tpds_2017.md#文档::part-4
- `44729235-e716-4ceb-82db-8b0395351ece.json`: 论文页面｜文档（第5部分） — homepage:contents/research_papers/2017/2017_melia_tpds_2017.md#文档::part-5
- `8508b254-e47e-4f58-a9eb-a65b3f82e928.json`: 论文页面｜文档（第1部分） — homepage:contents/research_papers/2017/2017_motto.md#文档::part-1
- `64015e92-f6a1-4e87-922c-64c5a8196d6d.json`: 论文页面｜文档（第2部分） — homepage:contents/research_papers/2017/2017_motto.md#文档::part-2
- `79f80d44-804f-42bd-a4d6-5f23f7798c2a.json`: 论文页面｜文档（第3部分） — homepage:contents/research_papers/2017/2017_motto.md#文档::part-3
- `7380110a-40d5-4512-bf5a-e667d20836a0.json`: 论文页面｜文档（第4部分） — homepage:contents/research_papers/2017/2017_motto.md#文档::part-4
- `2ad5bd23-6376-4124-92af-c956c84f148d.json`: 论文页面｜文档（第1部分） — homepage:contents/research_papers/2017/2017_profiling_final.md#文档::part-1
- `6f59a4b1-f119-4742-8b73-0c380128fc65.json`: 论文页面｜文档（第2部分） — homepage:contents/research_papers/2017/2017_profiling_final.md#文档::part-2
- `dabe114d-57ee-43b5-bfab-ebf95dfe96e9.json`: 论文页面｜文档（第3部分） — homepage:contents/research_papers/2017/2017_profiling_final.md#文档::part-3
- `85bc68c5-fc7d-4ace-bda1-94054c20462c.json`: 论文页面｜文档（第4部分） — homepage:contents/research_papers/2017/2017_profiling_final.md#文档::part-4
- `27f5eff4-18f5-468e-88bc-f0ce085e4376.json`: 论文页面｜文档（第1部分） — homepage:contents/research_papers/2019/2019_briskstream.md#文档::part-1
- `8c9b741a-7b53-43c8-bb8e-8cdf541ee2e7.json`: 论文页面｜文档（第10部分） — homepage:contents/research_papers/2019/2019_briskstream.md#文档::part-10
- `0e50ad21-9963-4b41-9cf7-3bd4f8bf1201.json`: 论文页面｜文档（第2部分） — homepage:contents/research_papers/2019/2019_briskstream.md#文档::part-2
- `0be921f2-e5cd-47b4-80df-547fd0ba6020.json`: 论文页面｜文档（第3部分） — homepage:contents/research_papers/2019/2019_briskstream.md#文档::part-3
- `0ea45e27-ca67-4ce4-a6b3-ddda9582563f.json`: 论文页面｜文档（第4部分） — homepage:contents/research_papers/2019/2019_briskstream.md#文档::part-4
- `6f282be4-cf55-49a4-83f7-754e78f57399.json`: 论文页面｜文档（第5部分） — homepage:contents/research_papers/2019/2019_briskstream.md#文档::part-5
- `c5c34286-cddb-42c7-8880-8c16a52a40bc.json`: 论文页面｜文档（第6部分） — homepage:contents/research_papers/2019/2019_briskstream.md#文档::part-6
- `42cef54c-c1d5-4704-a97c-2e38777018fc.json`: 论文页面｜文档（第7部分） — homepage:contents/research_papers/2019/2019_briskstream.md#文档::part-7
- `4e28b775-4cee-4d0e-ba2f-7e146f7fff7c.json`: 论文页面｜文档（第8部分） — homepage:contents/research_papers/2019/2019_briskstream.md#文档::part-8
- `b3370fe3-bc05-4e76-b767-45aa7d7b8eed.json`: 论文页面｜文档（第9部分） — homepage:contents/research_papers/2019/2019_briskstream.md#文档::part-9
- `2fd32783-37ba-4686-8079-2276b9c81b5f.json`: 论文页面｜文档（第1部分） — homepage:contents/research_papers/2019/2019_trav_bigmm_2019.md#文档::part-1
- `03582572-eac9-4b8b-a3c2-7e18e8a525e7.json`: 论文页面｜文档（第2部分） — homepage:contents/research_papers/2019/2019_trav_bigmm_2019.md#文档::part-2
- `aad2ee39-5f18-493e-bc0f-2a83f9bc9981.json`: 论文页面｜文档（第3部分） — homepage:contents/research_papers/2019/2019_trav_bigmm_2019.md#文档::part-3
- `9d670a02-685d-4eaa-ab72-778764043d3d.json`: 论文页面｜文档（第1部分） — homepage:contents/research_papers/2019/2019_zhangsh.md#文档::part-1
- `0b933c04-b98b-495d-b1fd-998be2669aeb.json`: 论文页面｜文档（第10部分） — homepage:contents/research_papers/2019/2019_zhangsh.md#文档::part-10
- `e04826a3-ec0b-4846-a00b-f8cd0b3f8494.json`: 论文页面｜文档（第11部分） — homepage:contents/research_papers/2019/2019_zhangsh.md#文档::part-11
- `e82d60c5-500e-4835-9e7f-1580e8289b1c.json`: 论文页面｜文档（第12部分） — homepage:contents/research_papers/2019/2019_zhangsh.md#文档::part-12
- `84d19cda-2b35-46e5-befa-05c0ee91f02c.json`: 论文页面｜文档（第13部分） — homepage:contents/research_papers/2019/2019_zhangsh.md#文档::part-13
- `7ec5b8a0-0d04-4089-af41-fcd226090126.json`: 论文页面｜文档（第14部分） — homepage:contents/research_papers/2019/2019_zhangsh.md#文档::part-14
- `4bc729fe-180a-4ac5-ad0a-ee9efadba0b5.json`: 论文页面｜文档（第15部分） — homepage:contents/research_papers/2019/2019_zhangsh.md#文档::part-15
- ... 404 条默认公开项目未在代表性列表中展开。

