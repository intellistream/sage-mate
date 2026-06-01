from pathlib import Path
from datetime import UTC, datetime

from sage_faculty_twin.config import AppSettings
from sage_faculty_twin.knowledge_base import LocalKnowledgeStore
from sage_faculty_twin.models import (
    InteractionIntent,
    KnowledgeDocumentCreate,
    KnowledgeDocumentRecord,
    KnowledgeSearchHit,
)
from sage_faculty_twin.service import DigitalTwinService


def test_knowledge_store_adds_and_searches_documents(tmp_path: Path) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path)
    store = LocalKnowledgeStore(settings)

    record = store.add_document(
        KnowledgeDocumentCreate(
            title="Lab onboarding policy",
            content="Students should read the onboarding checklist before asking for GPU access.",
            tags=["lab", "policy"],
            source_name="owner-note",
        )
    )

    hits = store.search("How do I get GPU access for the lab?")

    assert record.document_id
    assert len(store.list_documents()) == 1
    assert hits
    assert hits[0].title == "Lab onboarding policy"


def test_knowledge_store_derives_and_returns_explicit_metadata(tmp_path: Path) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path)
    store = LocalKnowledgeStore(settings)

    record = store.add_document(
        KnowledgeDocumentCreate(
            title="课件正文｜研究生论文写作课程材料｜第 7 讲 发表高水平论文",
            content="第 7 讲讨论高水平论文选题、贡献表述与投稿准备。",
            tags=[
                "homepage",
                "teaching",
                "courseware",
                "pdf",
                "lecture",
                "identity:teacher",
                "domain:teaching",
                "audience:graduate",
                "course:paper-writing",
                "material:lecture",
                "lecture:7",
            ],
            source_name="homepage:contents/teaching/graduate-paper-writing-course.md#公开课件::lecture-7.pdf",
        )
    )

    hits = store.search("研究生论文写作 第 7 讲讲什么？")

    assert record.metadata["identity"] == "teacher"
    assert record.metadata["domain"] == "teaching"
    assert record.metadata["course_id"] == "paper-writing"
    assert record.metadata["material_type"] == "lecture"
    assert record.metadata["ordinal_type"] == "lecture"
    assert record.metadata["ordinal"] == "7"
    assert hits
    assert hits[0].metadata["course_id"] == "paper-writing"


def test_knowledge_store_backfills_metadata_for_legacy_records(tmp_path: Path) -> None:
    legacy_record = KnowledgeDocumentRecord(
        document_id="legacy-lecture",
        title="课件正文｜大模型推理基础设施课程材料｜第 5 讲 KV 缓存",
        content="第 5 讲重点解释 KV 缓存、分页管理与状态复用。",
        tags=["homepage", "teaching", "courseware", "pdf", "lecture"],
        source_name="homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::lecture-5.pdf",
        created_at=datetime.now(UTC),
    )
    (tmp_path / "legacy-lecture.json").write_text(
        legacy_record.model_dump_json(), encoding="utf-8"
    )

    store = LocalKnowledgeStore(AppSettings(knowledge_base_dir=tmp_path))
    loaded_record = store.list_documents()[0]

    assert loaded_record.metadata["identity"] == "teacher"
    assert loaded_record.metadata["domain"] == "teaching"
    assert loaded_record.metadata["course_id"] == "llm-inference"
    assert loaded_record.metadata["material_type"] == "lecture"


def test_knowledge_store_supports_neuromem_backend(tmp_path: Path) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path, knowledge_backend="neuromem")
    store = LocalKnowledgeStore(settings)

    store.add_document(
        KnowledgeDocumentCreate(
            title="Neuromem meeting note",
            content="Before asking for a meeting, send your agenda and current blocker.",
            tags=["meeting", "policy"],
            source_name="owner-note",
        )
    )

    hits = store.search("What should I send before a meeting?")

    assert store.backend_name() == "neuromem"
    assert store.embedding_backend_name() == "bm25"
    assert hits
    assert hits[0].title == "Neuromem meeting note"


def test_knowledge_store_prefers_matching_teaching_material_type(
    tmp_path: Path,
) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path)
    store = LocalKnowledgeStore(settings)

    store.add_document(
        KnowledgeDocumentCreate(
            title="课件正文｜大模型推理基础设施课程材料｜Tutorial 12 课程项目工作坊",
            content="Tutorial 12 介绍课程项目工作坊、里程碑与协作方式。",
            tags=["homepage", "teaching", "courseware", "pdf", "tutorial"],
            source_name="homepage:teaching/tutorial_12.pdf",
        )
    )
    store.add_document(
        KnowledgeDocumentCreate(
            title="课件正文｜大模型推理基础设施课程材料｜第 5 讲 KV 缓存",
            content="第 5 讲重点解释 KV 缓存、分页管理与状态复用。",
            tags=["homepage", "teaching", "courseware", "pdf", "lecture"],
            source_name="homepage:teaching/lecture_05.pdf",
        )
    )
    store.add_document(
        KnowledgeDocumentCreate(
            title="课件正文｜大模型推理基础设施课程材料｜实验 3 调度与连续批处理实验",
            content="实验 3 讲解连续批处理观察、调度指标与实验步骤。",
            tags=["homepage", "teaching", "courseware", "pdf", "experiment"],
            source_name="homepage:teaching/experiment_3.pdf",
        )
    )

    tutorial_hits = store.search("Tutorial 12 讲什么？")
    lecture_hits = store.search("第 5 讲 KV 缓存讲什么？")
    experiment_hits = store.search("实验 3 调度与连续批处理实验讲什么？")

    assert tutorial_hits
    assert tutorial_hits[0].tags[-1] == "tutorial"
    assert lecture_hits
    assert lecture_hits[0].tags[-1] == "lecture"
    assert experiment_hits
    assert experiment_hits[0].tags[-1] == "experiment"


def test_neuromem_backend_prefers_matching_teaching_material_type(
    tmp_path: Path,
) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path, knowledge_backend="neuromem")
    store = LocalKnowledgeStore(settings)

    store.add_document(
        KnowledgeDocumentCreate(
            title="课件正文｜大模型推理基础设施课程材料｜Tutorial 12 课程项目工作坊",
            content="Tutorial 12 介绍课程项目工作坊、分组机制与展示要求。",
            tags=["homepage", "teaching", "courseware", "pdf", "tutorial"],
            source_name="homepage:contents/teaching/tutorial_12.pdf",
        )
    )
    store.add_document(
        KnowledgeDocumentCreate(
            title="课件正文｜大模型推理基础设施课程材料｜第 5 讲 KV 缓存",
            content="第 5 讲讲解 KV 缓存、分页映射与 decode 状态复用。",
            tags=["homepage", "teaching", "courseware", "pdf", "lecture"],
            source_name="homepage:contents/teaching/lecture_05.pdf",
        )
    )
    store.add_document(
        KnowledgeDocumentCreate(
            title="课件正文｜大模型推理基础设施课程材料｜实验 3 调度与连续批处理实验",
            content="实验 3 让学生观察调度、吞吐变化与连续批处理行为。",
            tags=["homepage", "teaching", "courseware", "pdf", "experiment"],
            source_name="homepage:contents/teaching/experiment_3.pdf",
        )
    )

    assert store.search("Tutorial 12 讲什么？")[0].tags[-1] == "tutorial"
    assert store.search("第 5 讲 KV 缓存讲什么？")[0].tags[-1] == "lecture"
    assert (
        store.search("实验 3 调度与连续批处理实验讲什么？")[0].tags[-1] == "experiment"
    )


def test_neuromem_backend_finds_exact_tutorial_ordinal(tmp_path: Path) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path, knowledge_backend="neuromem")
    store = LocalKnowledgeStore(settings)

    store.add_document(
        KnowledgeDocumentCreate(
            title="课件正文｜大模型推理基础设施课程材料｜Tutorial 7 执行优化与异构路径",
            content="Tutorial 7 解释执行优化、异构路径，以及 kernel 加速不一定改善端到端性能的原因。",
            tags=[
                "homepage",
                "teaching",
                "courseware",
                "pdf",
                "tutorial",
                "course:llm-inference",
                "material:tutorial",
                "tutorial:7",
            ],
            source_name="homepage:contents/teaching/intro-to-llm-inference-engines.md#tutorial-7.pdf",
        )
    )
    store.add_document(
        KnowledgeDocumentCreate(
            title="课件正文｜大模型推理基础设施课程材料｜第 7 讲 推理系统架构",
            content="第 7 讲介绍推理系统架构、调度路径与服务化设计。",
            tags=[
                "homepage",
                "teaching",
                "courseware",
                "pdf",
                "lecture",
                "course:llm-inference",
                "material:lecture",
                "lecture:7",
            ],
            source_name="homepage:contents/teaching/intro-to-llm-inference-engines.md#lecture-7.pdf",
        )
    )
    store.add_document(
        KnowledgeDocumentCreate(
            title="课件正文｜大模型推理基础设施课程材料｜Tutorial 12 课程项目工作坊",
            content="Tutorial 12 介绍课程项目工作坊、里程碑与协作方式。",
            tags=[
                "homepage",
                "teaching",
                "courseware",
                "pdf",
                "tutorial",
                "course:llm-inference",
                "material:tutorial",
                "tutorial:12",
            ],
            source_name="homepage:contents/teaching/intro-to-llm-inference-engines.md#tutorial-12.pdf",
        )
    )

    hits = store.search("大模型推理引擎这门课 tutorial 7 主要讲什么？", top_k=3)

    assert hits
    assert (
        hits[0].title
        == "课件正文｜大模型推理基础设施课程材料｜Tutorial 7 执行优化与异构路径"
    )


def test_knowledge_store_separates_same_lecture_number_across_courses(
    tmp_path: Path,
) -> None:
    for backend_name in ("local", "neuromem"):
        settings = AppSettings(
            knowledge_base_dir=tmp_path / backend_name,
            knowledge_backend="neuromem" if backend_name == "neuromem" else "local",
        )
        store = LocalKnowledgeStore(settings)

        store.add_document(
            KnowledgeDocumentCreate(
                title="课件正文｜大模型推理基础设施课程材料｜第 7 讲 推理系统架构",
                content="第 7 讲介绍推理系统架构、调度路径与服务化设计。",
                tags=[
                    "homepage",
                    "teaching",
                    "courseware",
                    "pdf",
                    "lecture",
                    "identity:teacher",
                    "domain:teaching",
                    "course:llm-inference",
                    "material:lecture",
                    "lecture:7",
                ],
                source_name="homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::lecture-7.pdf",
            )
        )
        store.add_document(
            KnowledgeDocumentCreate(
                title="课件正文｜研究生论文写作课程材料｜第 7 讲 发表高水平论文",
                content="第 7 讲讨论高水平论文选题、贡献表述与投稿准备。",
                tags=[
                    "homepage",
                    "teaching",
                    "courseware",
                    "pdf",
                    "lecture",
                    "identity:teacher",
                    "domain:teaching",
                    "course:paper-writing",
                    "material:lecture",
                    "lecture:7",
                ],
                source_name="homepage:contents/teaching/graduate-paper-writing-course.md#公开课件::lecture-7.pdf",
            )
        )
        store.add_document(
            KnowledgeDocumentCreate(
                title="课件正文｜数据库实验课课程材料｜第 7 讲 索引与查询优化实验",
                content="第 7 讲围绕数据库索引、执行计划和查询优化实验展开。",
                tags=[
                    "homepage",
                    "teaching",
                    "courseware",
                    "pdf",
                    "lecture",
                    "identity:teacher",
                    "domain:teaching",
                    "course:database-lab",
                    "material:lecture",
                    "lecture:7",
                ],
                source_name="homepage:contents/teaching/database-lab.md#公开课件::lecture-7.pdf",
            )
        )

        llm_hits = store.search("大模型推理基础设施 第 7 讲讲什么？", top_k=2)
        writing_hits = store.search("研究生论文写作 第 7 讲讲什么？", top_k=2)
        database_hits = store.search("数据库实验课 第 7 讲讲什么？", top_k=2)

        assert llm_hits
        assert "course:llm-inference" in llm_hits[0].tags
        assert writing_hits
        assert "course:paper-writing" in writing_hits[0].tags
        assert database_hits
        assert "course:database-lab" in database_hits[0].tags


def test_knowledge_store_prioritizes_research_materials_over_courseware_noise(
    tmp_path: Path,
) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path)
    store = LocalKnowledgeStore(settings)

    store.add_document(
        KnowledgeDocumentCreate(
            title="研究总览｜研究主线",
            content="研究主线围绕流处理系统、大模型推理与记忆增强。",
            tags=["homepage", "research", "publication", "overview"],
            source_name="homepage:contents/publications.md#首页导读",
        )
    )
    store.add_document(
        KnowledgeDocumentCreate(
            title="主页资料｜研究板块",
            content="主要研究大模型推理基础设施、智能系统与数据管理。",
            tags=["homepage", "profile"],
            source_name="homepage:contents/home.md#研究板块",
        )
    )
    store.add_document(
        KnowledgeDocumentCreate(
            title="课件正文｜研究生论文写作课程材料｜第 7 讲 发表高水平论文",
            content="这一讲讨论如何组织论文写作与研究表述。",
            tags=["homepage", "teaching", "courseware", "pdf", "lecture"],
            source_name="homepage:contents/teaching/graduate-paper-writing-course.md#公开课件::lecture-7.pdf",
        )
    )

    hits = store.search("你的研究主线是什么？", top_k=3)

    assert hits
    assert hits[0].title == "研究总览｜研究主线"
    assert all("teaching" not in hit.tags for hit in hits[:2])


def test_neuromem_backend_prioritizes_research_materials_over_courseware_noise(
    tmp_path: Path,
) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path, knowledge_backend="neuromem")
    store = LocalKnowledgeStore(settings)

    store.add_document(
        KnowledgeDocumentCreate(
            title="研究总览｜研究主线",
            content="研究主线围绕流处理系统、大模型推理与记忆增强。",
            tags=["homepage", "research", "publication", "overview"],
            source_name="homepage:contents/publications.md#首页导读",
        )
    )
    store.add_document(
        KnowledgeDocumentCreate(
            title="主页资料｜研究板块",
            content="主要研究大模型推理基础设施、智能系统与数据管理。",
            tags=["homepage", "profile"],
            source_name="homepage:contents/home.md#研究板块",
        )
    )
    store.add_document(
        KnowledgeDocumentCreate(
            title="课件正文｜研究生论文写作课程材料｜第 7 讲 发表高水平论文",
            content="这一讲讨论如何组织论文写作与研究表述。",
            tags=["homepage", "teaching", "courseware", "pdf", "lecture"],
            source_name="homepage:contents/teaching/graduate-paper-writing-course.md#公开课件::lecture-7.pdf",
        )
    )

    hits = store.search("你主要研究什么？", top_k=3)

    assert hits
    assert hits[0].title in {"研究总览｜研究主线", "主页资料｜研究板块"}
    assert all("teaching" not in hit.tags for hit in hits[:2])


def test_neuromem_backend_prioritizes_named_paper_queries_over_courseware_noise(
    tmp_path: Path,
) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path, knowledge_backend="neuromem")
    store = LocalKnowledgeStore(settings)

    store.add_document(
        KnowledgeDocumentCreate(
            title="论文提炼｜FlowRAG: Continual Learning for Dynamic Retriever in Retrieval-Augmented Generation",
            content="FlowRAG 主要解决动态语料下检索器持续学习与检索质量退化问题。",
            tags=[
                "homepage",
                "research",
                "publication",
                "paper-digest",
                "rag",
                "continual-learning",
            ],
            source_name="homepage:contents/research_papers/publications_summary.md#0.1 FlowRAG",
        )
    )
    store.add_document(
        KnowledgeDocumentCreate(
            title="主页资料｜研究板块",
            content="主要研究大模型推理基础设施、检索增强和数据系统。",
            tags=["homepage", "profile"],
            source_name="homepage:contents/home.md#研究板块",
        )
    )
    store.add_document(
        KnowledgeDocumentCreate(
            title="课件正文｜研究生论文写作课程材料｜第 7 讲 发表高水平论文",
            content="这一讲讨论如何组织论文写作与研究表述。",
            tags=["homepage", "teaching", "courseware", "pdf", "lecture"],
            source_name="homepage:contents/teaching/graduate-paper-writing-course.md#公开课件::lecture-7.pdf",
        )
    )

    hits = store.search("FlowRAG 主要做什么？", top_k=3)

    assert hits
    assert hits[0].title.startswith("论文提炼｜FlowRAG")
    assert all("teaching" not in hit.tags for hit in hits[:2])
    assert all("profile" not in hit.tags for hit in hits[:2])
    assert all(
        "flowrag" in hit.title.lower() or "flowrag" in (hit.source_name or "").lower()
        for hit in hits
    )


def test_search_dedupes_adjacent_chunks_from_same_courseware(tmp_path: Path) -> None:
    for backend_name in ("local", "neuromem"):
        settings = AppSettings(
            knowledge_base_dir=tmp_path / backend_name,
            knowledge_backend="neuromem" if backend_name == "neuromem" else "local",
        )
        store = LocalKnowledgeStore(settings)

        common_source = "homepage:contents/teaching/graduate-paper-writing-course.md#公开课件::contents/teaching/graduate-paper-writing-course/2026/lecture-7-beamer.pdf"
        store.add_document(
            KnowledgeDocumentCreate(
                title="课件正文｜研究生论文写作课程材料｜第 7 讲 发表高水平论文（第1部分）",
                content="第 7 讲介绍高水平论文选题、结构设计与叙事主线。",
                tags=["homepage", "teaching", "courseware", "pdf", "lecture"],
                source_name=f"{common_source}::part-1",
            )
        )
        store.add_document(
            KnowledgeDocumentCreate(
                title="课件正文｜研究生论文写作课程材料｜第 7 讲 发表高水平论文（第2部分）",
                content="第 7 讲继续讨论实验组织、结果汇报与贡献表述。",
                tags=["homepage", "teaching", "courseware", "pdf", "lecture"],
                source_name=f"{common_source}::part-2",
            )
        )
        store.add_document(
            KnowledgeDocumentCreate(
                title="课件正文｜研究生论文写作课程材料｜第 7 讲 发表高水平论文（第3部分）",
                content="第 7 讲补充论文打磨、投稿准备与答辩陈述。",
                tags=["homepage", "teaching", "courseware", "pdf", "lecture"],
                source_name=f"{common_source}::part-3",
            )
        )
        store.add_document(
            KnowledgeDocumentCreate(
                title="课程资料｜研究生论文写作课程材料｜公开课件",
                content="这里汇总第 7 讲到第 8 讲的公开课件链接。",
                tags=["homepage", "teaching", "courseware", "lecture"],
                source_name="homepage:contents/teaching/graduate-paper-writing-course.md#公开课件",
            )
        )
        store.add_document(
            KnowledgeDocumentCreate(
                title="课件正文｜大模型推理基础设施课程材料｜第 9 讲 异构平台适配（第1部分）",
                content="第 9 讲介绍 GPU、CPU 与异构路径适配。",
                tags=["homepage", "teaching", "courseware", "pdf", "lecture"],
                source_name="homepage:contents/teaching/intro-to-llm-inference-engines.md#讲义与导论::lecture-9.pdf::part-1",
            )
        )
        store.add_document(
            KnowledgeDocumentCreate(
                title="论文提炼｜Select Edges Wisely",
                content="这篇论文讨论磁盘 ANN 图布局优化。",
                tags=["homepage", "research", "publication", "paper-digest"],
                source_name="homepage:contents/research_papers/publications_summary.md#0.7 Select Edges Wisely",
            )
        )

        hits = store.search("第 7 讲 发表高水平论文讲什么？", top_k=5)
        same_courseware_hits = [
            hit
            for hit in hits
            if hit.source_name and hit.source_name.startswith(common_source)
        ]

        assert hits
        assert len(same_courseware_hits) == 1
        assert "第1部分" in same_courseware_hits[0].title
        assert all(
            (hit.source_name or "").startswith(common_source)
            or hit.source_name
            == "homepage:contents/teaching/graduate-paper-writing-course.md#公开课件"
            for hit in hits
        )
        assert all("paper-digest" not in hit.tags for hit in hits)


def test_knowledge_store_prefers_research_and_preparation_materials_over_courseware(
    tmp_path: Path,
) -> None:
    for backend_name in ("local", "neuromem"):
        knowledge_dir = tmp_path / backend_name
        settings = AppSettings(
            knowledge_base_dir=knowledge_dir,
            knowledge_backend="neuromem" if backend_name == "neuromem" else "local",
        )
        store = LocalKnowledgeStore(settings)

        store.add_document(
            KnowledgeDocumentCreate(
                title="研究总览｜研究主线",
                content="研究主线聚焦大模型推理、记忆系统与流处理基础设施。",
                tags=["homepage", "research", "publication", "overview"],
                source_name=f"{backend_name}:research-overview",
            )
        )
        store.add_document(
            KnowledgeDocumentCreate(
                title="论文提炼｜FlowRAG: Continual Learning for Dynamic Retriever in Retrieval-Augmented Generation",
                content="FlowRAG 主要解决动态语料下检索器持续学习与检索增强生成质量下降的问题。",
                tags=["homepage", "research", "publication", "paper-digest", "rag"],
                source_name=f"{backend_name}:flowrag",
            )
        )
        store.add_document(
            KnowledgeDocumentCreate(
                title="主页资料｜研究板块",
                content="我主要研究大模型推理系统、检索增强和系统优化。",
                tags=["homepage", "profile"],
                source_name=f"{backend_name}:profile",
            )
        )
        store.add_document(
            KnowledgeDocumentCreate(
                title="课件正文｜研究生论文写作课程材料｜第 8 讲 研究生毕业论文中常见的问题",
                content="本讲多次讨论研究主线、研究问题、论文结构与研究主线表述方式。",
                tags=["homepage", "teaching", "courseware", "pdf", "lecture"],
                source_name=f"{backend_name}:teaching-research-course",
            )
        )
        store.add_document(
            KnowledgeDocumentCreate(
                title="课程答疑前建议先准备的内容（模板）",
                content="和老师约时间前，建议先准备简历、议程、当前问题与想讨论的方向。",
                tags=["course", "qa", "preparation"],
                source_name=f"{backend_name}:starter-template",
            )
        )
        store.add_document(
            KnowledgeDocumentCreate(
                title="课件正文｜大模型推理基础设施课程材料｜第 13 讲 课程项目工作坊",
                content="课程项目工作坊介绍了项目准备、演示准备与里程碑准备。",
                tags=["homepage", "teaching", "courseware", "pdf", "lecture"],
                source_name=f"{backend_name}:project-workshop",
            )
        )

        research_hits = store.search("你的研究主线是什么？", top_k=3)
        paper_hits = store.search("FlowRAG 主要做什么？", top_k=3)
        preparation_hits = store.search("和老师约时间前，我应该先准备什么？", top_k=3)

        assert research_hits
        assert research_hits[0].title == "研究总览｜研究主线"
        assert "teaching" not in research_hits[0].tags
        assert all("teaching" not in hit.tags for hit in research_hits)
        assert paper_hits
        assert paper_hits[0].title.startswith("论文提炼｜FlowRAG")
        assert all("teaching" not in hit.tags for hit in paper_hits)
        assert preparation_hits
        assert preparation_hits[0].title == "课程答疑前建议先准备的内容（模板）"
        assert "teaching" not in preparation_hits[0].tags
        assert all("teaching" not in hit.tags for hit in preparation_hits)


def test_neuromem_backend_prefers_research_materials_for_research_queries(
    tmp_path: Path,
) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path, knowledge_backend="neuromem")
    store = LocalKnowledgeStore(settings)

    store.add_document(
        KnowledgeDocumentCreate(
            title="研究总览｜研究主线",
            content="主要研究方向包括流处理系统、状态管理、检索增强生成与智能体工作流。",
            tags=["homepage", "research", "publication", "overview"],
            source_name="homepage:contents/publications.md#首页导读",
        )
    )
    store.add_document(
        KnowledgeDocumentCreate(
            title="课程资料｜研究生论文写作课程材料",
            content="课程介绍论文写作结构、投稿准备与毕业论文常见问题。",
            tags=["homepage", "teaching", "courseware"],
            source_name="homepage:contents/teaching/graduate-paper-writing-course.md#intro",
        )
    )

    hits = store.search("你主要研究什么？")

    assert hits
    assert hits[0].title == "研究总览｜研究主线"
    assert "research" in hits[0].tags


def test_knowledge_store_reweights_paper_writing_results_by_visitor_profile(
    tmp_path: Path,
) -> None:
    for backend_name in ("local", "neuromem"):
        knowledge_dir = tmp_path / f"visitor-profile-{backend_name}"
        settings = AppSettings(
            knowledge_base_dir=knowledge_dir,
            knowledge_backend="neuromem" if backend_name == "neuromem" else "local",
        )
        store = LocalKnowledgeStore(settings)

        store.add_document(
            KnowledgeDocumentCreate(
                title="课程资料｜研究生论文写作课程材料",
                content="课程重点覆盖论文结构、related work、投稿准备和毕业论文常见问题。",
                tags=["homepage", "teaching", "courseware", "lecture"],
                source_name="homepage:contents/teaching/graduate-paper-writing-course.md#intro",
            )
        )
        store.add_document(
            KnowledgeDocumentCreate(
                title="研究总览｜论文写作智能体",
                content="研究方向聚焦自动写作 agent、审稿反馈吸收和协同 drafting workflow。",
                tags=["homepage", "research", "publication", "overview"],
                source_name=f"{backend_name}:paper-writing-agent-overview",
            )
        )

        paper_course_hits = store.search(
            "论文写作相关内容我应该先看什么？",
            top_k=2,
            visitor_profile="paper_writing_student",
        )
        lab_hits = store.search(
            "论文写作相关内容我应该先看什么？",
            top_k=2,
            visitor_profile="lab_member",
        )

        assert paper_course_hits
        assert paper_course_hits[0].title == "课程资料｜研究生论文写作课程材料"
        assert "teaching" in paper_course_hits[0].tags
        assert lab_hits
        assert lab_hits[0].title == "研究总览｜论文写作智能体"
        assert "research" in lab_hits[0].tags


def test_service_prompt_includes_retrieved_owner_materials(tmp_path: Path) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path)
    service = DigitalTwinService(settings)
    service.add_knowledge(
        KnowledgeDocumentCreate(
            title="Meeting preference",
            content="I prefer students to send an agenda and the current blocker before the meeting.",
            tags=["meeting"],
            source_name="advisor-note",
        )
    )

    hits = service.search_knowledge("What should I prepare before a meeting?").hits
    prompt = service._build_student_prompt(
        request=type(
            "Request",
            (),
            {
                "student_name": "Alice",
                "course_context": None,
                "question": "What should I prepare before a meeting?",
            },
        )(),
        knowledge_hits=hits,
    )

    assert hits
    assert "Relevant owner materials:" in prompt
    assert "Meeting preference" in prompt
    assert "agenda" in prompt


def test_service_prompt_filters_teaching_materials_for_research_queries(
    tmp_path: Path,
) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path)
    service = DigitalTwinService(settings)

    prompt = service._build_student_prompt(
        request=type(
            "Request",
            (),
            {
                "student_name": "Alice",
                "course_context": None,
                "question": "你主要研究什么？",
            },
        )(),
        knowledge_hits=[
            KnowledgeSearchHit(
                document_id="research-hit",
                title="研究总览｜研究主线",
                excerpt="主要研究方向包括流处理、状态管理与智能体工作流。",
                score=1.0,
                tags=["homepage", "research", "publication", "overview"],
                source_name="homepage:contents/publications.md#首页导读",
            ),
            KnowledgeSearchHit(
                document_id="teaching-hit",
                title="课程资料｜研究生论文写作课程材料",
                excerpt="课程介绍论文结构、写作方法与毕业论文常见问题。",
                score=0.9,
                tags=["homepage", "teaching", "courseware"],
                source_name="homepage:contents/teaching/graduate-paper-writing-course.md#intro",
            ),
        ],
        interaction_intent=InteractionIntent(
            action="answer",
            domain="research",
            retrieval_scopes=["publications", "profile"],
            exclude_scopes=["courseware"],
            confidence=0.9,
        ),
    )

    assert "current focus first" in prompt
    assert "LLM inference engines" in prompt
    assert "historical foundations or method background" in prompt
    assert "研究总览｜研究主线" in prompt
    assert "研究生论文写作课程材料" not in prompt


def test_service_filters_generic_profile_hits_for_preparation_guidance_queries(
    tmp_path: Path,
) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path)
    service = DigitalTwinService(settings)
    support = service._build_support()

    filtered = support._filter_knowledge_hits_by_intent(
        [
            KnowledgeSearchHit(
                document_id="profile-hit",
                title="主页资料｜研究板块",
                excerpt="当前研究大致分为三个相互衔接的板块。",
                score=1.0,
                tags=["homepage", "profile"],
                source_name="homepage:contents/home.md#研究板块",
            ),
            KnowledgeSearchHit(
                document_id="meeting-hit",
                title="Meeting preference",
                excerpt="Before asking for a meeting, send your agenda, current blocker, and latest draft.",
                score=0.8,
                tags=["meeting", "policy", "preparation"],
                source_name="advisor-note",
            ),
        ],
        InteractionIntent(
            action="answer",
            domain="advising",
            retrieval_scopes=["preparation", "meeting_policy", "profile"],
            exclude_scopes=["courseware"],
            decision_mode="advise_only",
            confidence=0.95,
        ),
    )

    assert [hit.document_id for hit in filtered] == ["meeting-hit"]


def test_service_prompt_adds_meeting_preparation_checklist_guidance(
    tmp_path: Path,
) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path)
    service = DigitalTwinService(settings)

    prompt = service._build_student_prompt(
        request=type(
            "Request",
            (),
            {
                "student_name": "Alice",
                "course_context": "科研指导",
                "question": "和老师约时间前，我应该先准备什么？",
            },
        )(),
        knowledge_hits=[],
        interaction_intent=InteractionIntent(
            action="answer",
            domain="advising",
            retrieval_scopes=["preparation", "meeting_policy", "profile"],
            exclude_scopes=["courseware"],
            decision_mode="advise_only",
            confidence=0.95,
        ),
    )

    assert (
        "agenda, current blocker, draft or progress summary, and 2-3 concrete questions"
        in prompt
    )
    assert (
        "Do not ask for time slots unless the student explicitly asks to book a meeting."
        in prompt
    )


def test_service_prompt_adds_project_scoping_guidance(tmp_path: Path) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path)
    service = DigitalTwinService(settings)

    prompt = service._build_student_prompt(
        request=type(
            "Request",
            (),
            {
                "student_name": "Alice",
                "course_context": "科研指导",
                "question": "老师，我现在想做一个跟推理系统有关的项目。如果题目太大，您一般会建议怎么收窄？",
            },
        )(),
        knowledge_hits=[],
        interaction_intent=InteractionIntent(
            action="answer",
            domain="advising",
            retrieval_scopes=["preparation", "meeting_policy", "profile"],
            exclude_scopes=["courseware"],
            decision_mode="advise_only",
            confidence=0.95,
        ),
    )

    assert "first pin down one core problem" in prompt
    assert "choose one setting or artifact" in prompt


def test_service_prompt_adds_draft_feedback_guidance(tmp_path: Path) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path)
    service = DigitalTwinService(settings)

    prompt = service._build_student_prompt(
        request=type(
            "Request",
            (),
            {
                "student_name": "Alice",
                "course_context": "科研指导",
                "question": "老师，我下周想带一个初稿来请您看。在您看之前，我自己最好先整理哪些信息，能让反馈更集中？",
            },
        )(),
        knowledge_hits=[],
        interaction_intent=InteractionIntent(
            action="answer",
            domain="advising",
            retrieval_scopes=["preparation", "meeting_policy", "profile"],
            exclude_scopes=["courseware"],
            decision_mode="advise_only",
            confidence=0.95,
        ),
    )

    assert "current goal, current version or evidence, main blocker" in prompt
    assert "Do not turn this into scheduling." in prompt


def test_service_prompt_adds_teaching_question_logistics_guidance(
    tmp_path: Path,
) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path)
    service = DigitalTwinService(settings)

    prompt = service._build_student_prompt(
        request=type(
            "Request",
            (),
            {
                "student_name": "Alice",
                "course_context": "LaMP personalization benchmark",
                "question": "结合我的情况，我下次问课上问题时应该先整理哪几类信息？作业里端到端性能分析不清楚，而且问题比较碎。",
            },
        )(),
        knowledge_hits=[],
        interaction_intent=InteractionIntent(
            action="answer",
            domain="teaching",
            retrieval_scopes=["courseware"],
            exclude_scopes=["publications"],
            confidence=0.95,
        ),
    )

    assert "the exact problem, the observed phenomenon or performance result" in prompt
    assert "Do not answer with another clarification question" in prompt
    assert "end-to-end performance issue" in prompt
    assert "questions feel fragmented" in prompt
    assert "must explicitly reflect the student's stated pain points" in prompt
    assert "Reuse the student's own wording" in prompt


def test_service_prompt_adds_publication_entry_guidance(tmp_path: Path) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path)
    service = DigitalTwinService(settings)

    prompt = service._build_student_prompt(
        request=type(
            "Request",
            (),
            {
                "student_name": "Alice",
                "course_context": "科研指导",
                "question": "如果我想从您的研究里先挑一个主题开始读，哪类会更适合我？我想先建立主线理解。",
            },
        )(),
        knowledge_hits=[],
        interaction_intent=InteractionIntent(
            action="answer",
            domain="research",
            retrieval_scopes=["publications", "profile"],
            exclude_scopes=["courseware"],
            confidence=0.95,
        ),
    )

    assert "recommend one clear topic or research main line to start from" in prompt
    assert "use wording such as '主题', '主线', or '切入'" in prompt


def test_service_prompt_adds_follow_up_next_step_guidance(tmp_path: Path) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path)
    service = DigitalTwinService(settings)

    prompt = service._build_student_prompt(
        request=type(
            "Request",
            (),
            {
                "student_name": "Alice",
                "course_context": "科研指导",
                "question": "上次已被建议按主题整理问题，我现在已经整理成三类。按我现在的进展，下一步更适合先发邮件还是继续补实验？",
            },
        )(),
        knowledge_hits=[],
        interaction_intent=InteractionIntent(
            action="answer",
            domain="advising",
            retrieval_scopes=["preparation", "meeting_policy", "profile"],
            exclude_scopes=["courseware"],
            decision_mode="advise_only",
            confidence=0.95,
        ),
    )

    assert (
        "State the recommendation explicitly with wording like '下一步可以先...'"
        in prompt
    )
    assert "connect it to the student's current progress" in prompt
    assert "既然你已经整理成三类" in prompt


def test_service_prompt_adds_course_research_boundary_guidance(tmp_path: Path) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path)
    service = DigitalTwinService(settings)

    prompt = service._build_student_prompt(
        request=type(
            "Request",
            (),
            {
                "student_name": "Alice",
                "course_context": "科研指导",
                "question": "老师，我既想问课程作业，也想顺便聊下研究。这种情况您一般建议一次都问完，还是分开准备？",
            },
        )(),
        knowledge_hits=[],
        interaction_intent=InteractionIntent(
            action="answer",
            domain="advising",
            retrieval_scopes=["preparation", "meeting_policy", "profile"],
            exclude_scopes=["courseware"],
            decision_mode="advise_only",
            confidence=0.95,
        ),
    )

    assert "mixed course-and-research questions" in prompt
    assert "should be prepared separately" in prompt
    assert "Use wording such as '分开', '分别', '课程', '研究', and '准备'." in prompt
