from pathlib import Path
from datetime import UTC, datetime
from uuid import uuid4

import sage_faculty_twin.knowledge_import as knowledge_import
from sage_faculty_twin.config import AppSettings
from sage_faculty_twin.knowledge_base import LocalKnowledgeStore
from sage_faculty_twin.knowledge_import import import_homepage_materials
from sage_faculty_twin.models import KnowledgeDocumentRecord


def test_import_homepage_materials_creates_searchable_documents_and_skips_duplicates(
    tmp_path: Path,
) -> None:
    homepage_dir = tmp_path / "homepage"
    contents_dir = homepage_dir / "contents"
    research_dir = contents_dir / "research_papers"
    research_dir.mkdir(parents=True)

    (contents_dir / "home.md").write_text(
        "# 张书豪\n\n"
        "研究方向聚焦大模型推理服务、KV cache 和多级记忆。\n\n"
        "## 招生与合作\n\n"
        "联系时建议附上简历、代码链接，以及最想研究的 1-2 个问题。\n",
        encoding="utf-8",
    )
    (contents_dir / "news.md").write_text(
        "- Mar 2026 recruiting students interested in LLM inference systems\n",
        encoding="utf-8",
    )
    (contents_dir / "publications.md").write_text(
        "## 首页导读\n\n"
        "研究主线围绕流处理系统、大模型推理与记忆增强。\n\n"
        "## 代表性论文\n\n"
        "### 一、共享状态访问、调度与运行时管理\n\n"
        "这一方向关注共享状态与运行时调度。\n",
        encoding="utf-8",
    )
    (research_dir / "publications_summary.md").write_text(
        "# Coverage Notes\n\n"
        "- 元信息前言不应被导入为论文提炼。\n\n"
        "### 0.1 FlowRAG: Continual Learning for Dynamic Retriever in Retrieval-Augmented Generation\n\n"
        "Abstract: FlowRAG improves retrieval quality for evolving corpora.\n\n"
        "### 1.1 Older Work\n\n"
        "Abstract: legacy section should now also be distilled into the twin knowledge base.\n",
        encoding="utf-8",
    )

    settings = AppSettings(knowledge_base_dir=tmp_path / "knowledge")
    store = LocalKnowledgeStore(settings)

    first_report = import_homepage_materials(store, homepage_dir)

    assert first_report.created_count == 7
    assert first_report.updated_count == 0
    assert first_report.skipped_count == 0
    assert any(title.startswith("主页资料｜张书豪") for title in first_report.created_titles)
    assert any(title.startswith("研究总览｜研究主线") for title in first_report.created_titles)
    assert any(title.startswith("论文提炼｜FlowRAG") for title in first_report.created_titles)
    assert any(title.startswith("论文提炼｜Older Work") for title in first_report.created_titles)

    hits = store.search("联系老师时建议附上什么材料？")
    assert hits
    assert any("招生与合作" in hit.title for hit in hits)

    publication_hits = store.search("你的研究主线和 FlowRAG 主要做什么？")
    assert publication_hits
    assert any(hit.title.startswith("研究总览｜研究主线") or hit.title.startswith("论文提炼｜FlowRAG") for hit in publication_hits)

    second_report = import_homepage_materials(store, homepage_dir)

    assert second_report.created_count == 0
    assert second_report.updated_count == 7
    assert second_report.skipped_count == 0


def test_import_homepage_materials_refreshes_existing_source_content(tmp_path: Path) -> None:
    homepage_dir = tmp_path / "homepage"
    contents_dir = homepage_dir / "contents"
    research_dir = contents_dir / "research_papers"
    research_dir.mkdir(parents=True)

    (contents_dir / "home.md").write_text(
        "# 张书豪\n\n研究方向聚焦大模型推理服务。\n",
        encoding="utf-8",
    )
    (contents_dir / "news.md").write_text("- 初版动态\n", encoding="utf-8")
    (contents_dir / "publications.md").write_text(
        "## 首页导读\n\n研究主线聚焦大模型推理服务。\n",
        encoding="utf-8",
    )
    (research_dir / "publications_summary.md").write_text(
        "### 0.1 FlowRAG\n\nAbstract: 初版摘要。\n",
        encoding="utf-8",
    )

    settings = AppSettings(knowledge_base_dir=tmp_path / "knowledge")
    store = LocalKnowledgeStore(settings)
    import_homepage_materials(store, homepage_dir)

    (contents_dir / "home.md").write_text(
        "# 张书豪\n\n研究方向聚焦大模型推理服务与记忆中间件。\n",
        encoding="utf-8",
    )

    report = import_homepage_materials(store, homepage_dir)

    assert report.created_count == 0
    assert report.updated_count >= 1
    hits = store.search("记忆中间件")
    assert hits
    assert any(hit.title.startswith("主页资料｜张书豪") for hit in hits)


def test_import_homepage_materials_rebuilds_indexes_once_per_sync(
    tmp_path: Path,
    monkeypatch,
) -> None:
    homepage_dir = tmp_path / "homepage"
    contents_dir = homepage_dir / "contents"
    research_dir = contents_dir / "research_papers"
    research_dir.mkdir(parents=True)

    (contents_dir / "home.md").write_text(
        "# 张书豪\n\n研究方向聚焦大模型推理服务。\n",
        encoding="utf-8",
    )
    (contents_dir / "news.md").write_text("- 初版动态\n", encoding="utf-8")
    (contents_dir / "publications.md").write_text(
        "## 首页导读\n\n研究主线聚焦大模型推理服务。\n",
        encoding="utf-8",
    )
    (research_dir / "publications_summary.md").write_text(
        "### 0.1 FlowRAG\n\nAbstract: 初版摘要。\n",
        encoding="utf-8",
    )

    settings = AppSettings(knowledge_base_dir=tmp_path / "knowledge")
    store = LocalKnowledgeStore(settings)
    import_homepage_materials(store, homepage_dir)

    rebuild_calls = 0

    def record_rebuild() -> None:
        nonlocal rebuild_calls
        rebuild_calls += 1

    monkeypatch.setattr(store, "rebuild_indexes", record_rebuild)

    (contents_dir / "home.md").write_text(
        "# 张书豪\n\n研究方向聚焦大模型推理服务与记忆中间件。\n",
        encoding="utf-8",
    )

    import_homepage_materials(store, homepage_dir)

    assert rebuild_calls == 1


def test_import_homepage_materials_includes_teaching_material_indexes(tmp_path: Path) -> None:
    homepage_dir = tmp_path / "homepage"
    contents_dir = homepage_dir / "contents"
    research_dir = contents_dir / "research_papers"
    teaching_dir = contents_dir / "teaching"
    research_dir.mkdir(parents=True)
    teaching_dir.mkdir(parents=True)

    (contents_dir / "home.md").write_text("# 张书豪\n\n简介。\n", encoding="utf-8")
    (contents_dir / "news.md").write_text("- news\n", encoding="utf-8")
    (contents_dir / "publications.md").write_text(
        "## 首页导读\n\n研究主线聚焦课程与系统。\n",
        encoding="utf-8",
    )
    (contents_dir / "resources.md").write_text(
        "这里收录公开教学材料。\n\n- 大模型推理基础设施：[页面](/intro-to-llm-inference-engines.html)\n",
        encoding="utf-8",
    )
    (research_dir / "publications_summary.md").write_text(
        "### 0.1 FlowRAG\n\nAbstract: 摘要。\n",
        encoding="utf-8",
    )
    (teaching_dir / "intro-to-llm-inference-engines.md").write_text(
        "# 大模型推理基础设施课程材料\n\n"
        "这里汇总课程 PDF。\n\n"
        "## 讲义与导论\n\n"
        "- 第 5 讲 KV 缓存：[PDF](/contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/kv.pdf)\n\n"
        "## Tutorials\n\n"
        "- Tutorial 4 KV Cache 与状态组织：[PDF](/contents/teaching/intro-to-llm-inference-engines/2026/tutorials/tutorial4.pdf)\n",
        encoding="utf-8",
    )

    settings = AppSettings(knowledge_base_dir=tmp_path / "knowledge")
    store = LocalKnowledgeStore(settings)

    report = import_homepage_materials(store, homepage_dir)

    assert report.created_count >= 6
    tutorial_sections = [
        document
        for document in store.list_documents()
        if document.source_name == "homepage:contents/teaching/intro-to-llm-inference-engines.md#Tutorials"
    ]
    assert tutorial_sections
    assert "tutorial" in tutorial_sections[0].tags
    assert "identity:teacher" in tutorial_sections[0].tags
    assert "domain:teaching" in tutorial_sections[0].tags
    assert "course:llm-inference" in tutorial_sections[0].tags
    assert "material:tutorial" in tutorial_sections[0].tags
    assert tutorial_sections[0].metadata["identity"] == "teacher"
    assert tutorial_sections[0].metadata["domain"] == "teaching"
    assert tutorial_sections[0].metadata["audience"] == "graduate"
    assert tutorial_sections[0].metadata["course_id"] == "llm-inference"
    assert tutorial_sections[0].metadata["material_type"] == "tutorial"
    hits = store.search("KV 缓存是第几讲？")
    assert hits
    assert any(hit.title.startswith("课程资料｜大模型推理基础设施课程材料") for hit in hits)


def test_chunk_text_prefers_sentence_boundaries_for_long_paragraphs() -> None:
    text = "第一句比较短。第二句也比较短。第三句还是比较短。第四句继续补充说明。"

    chunks = knowledge_import._chunk_text(text, max_chars=18)

    assert len(chunks) >= 2
    assert all(chunk.endswith(("。", ".")) for chunk in chunks[:-1])
    assert "第三句还是比较短。" in " ".join(chunks)


def test_chunk_text_adds_bounded_overlap_between_adjacent_chunks() -> None:
    text = "\n\n".join(
        [
            "第一段 " + ("A" * 1800),
            "第二段 " + ("B" * 1800),
            "第三段 " + ("C" * 1800),
        ]
    )

    chunks = knowledge_import._chunk_text(text, max_chars=3000)

    assert len(chunks) == 3
    overlap_prefix, second_body = chunks[1].split("\n\n", 1)
    assert overlap_prefix
    assert overlap_prefix in chunks[0]
    assert second_body.startswith("第二段 ")
    assert len(chunks[1]) <= 3000


def test_import_homepage_materials_extracts_teaching_pdf_text(
    tmp_path: Path,
    monkeypatch,
) -> None:
    homepage_dir = tmp_path / "homepage"
    contents_dir = homepage_dir / "contents"
    research_dir = contents_dir / "research_papers"
    teaching_dir = contents_dir / "teaching"
    pdf_dir = teaching_dir / "intro-to-llm-inference-engines" / "2026" / "slides" / "lectures"
    research_dir.mkdir(parents=True)
    pdf_dir.mkdir(parents=True)
    teaching_dir.mkdir(parents=True, exist_ok=True)

    (contents_dir / "home.md").write_text("# 张书豪\n\n简介。\n", encoding="utf-8")
    (contents_dir / "news.md").write_text("- news\n", encoding="utf-8")
    (contents_dir / "publications.md").write_text(
        "## 首页导读\n\n研究主线聚焦课程与系统。\n",
        encoding="utf-8",
    )
    (contents_dir / "resources.md").write_text("课程资源。\n", encoding="utf-8")
    (research_dir / "publications_summary.md").write_text(
        "### 0.1 FlowRAG\n\nAbstract: 摘要。\n",
        encoding="utf-8",
    )
    pdf_path = pdf_dir / "kv.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 placeholder")
    (teaching_dir / "intro-to-llm-inference-engines.md").write_text(
        "# 大模型推理基础设施课程材料\n\n"
        "## 讲义与导论\n\n"
        "- 第 5 讲 KV 缓存：[PDF](/contents/teaching/intro-to-llm-inference-engines/2026/slides/lectures/kv.pdf)\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        knowledge_import,
        "_extract_pdf_text",
        lambda path: "KV 缓存会影响 prefill 与 decode 阶段的状态管理。",
    )

    settings = AppSettings(knowledge_base_dir=tmp_path / "knowledge")
    store = LocalKnowledgeStore(settings)

    report = knowledge_import.import_homepage_materials(store, homepage_dir)

    assert any(title.startswith("课件正文｜大模型推理基础设施课程材料｜第 5 讲 KV 缓存") for title in report.created_titles)
    hits = store.search("prefill 和 decode 阶段的状态管理")
    assert hits
    assert any(hit.title.startswith("课件正文｜大模型推理基础设施课程材料｜第 5 讲 KV 缓存") for hit in hits)


def test_import_homepage_materials_removes_stale_homepage_documents(tmp_path: Path) -> None:
    homepage_dir = tmp_path / "homepage"
    contents_dir = homepage_dir / "contents"
    research_dir = contents_dir / "research_papers"
    research_dir.mkdir(parents=True)

    (contents_dir / "home.md").write_text("# 张书豪\n\n简介。\n", encoding="utf-8")
    (contents_dir / "news.md").write_text("- news\n", encoding="utf-8")
    (contents_dir / "publications.md").write_text("## 首页导读\n\n研究主线。\n", encoding="utf-8")
    (research_dir / "publications_summary.md").write_text(
        "### 0.1 FlowRAG\n\nAbstract: 摘要。\n",
        encoding="utf-8",
    )

    settings = AppSettings(knowledge_base_dir=tmp_path / "knowledge")
    store = LocalKnowledgeStore(settings)
    stale_record = KnowledgeDocumentRecord(
        document_id=str(uuid4()),
        title="论文提炼｜Coverage Notes",
        content="旧的前言知识，不应继续保留。",
        tags=["homepage", "research", "publication"],
        source_name="homepage:contents/research_papers/publications_summary.md#Coverage Notes",
        created_at=datetime.now(UTC),
    )
    (settings.knowledge_base_dir / f"{stale_record.document_id}.json").write_text(
        stale_record.model_dump_json(indent=2),
        encoding="utf-8",
    )

    store = LocalKnowledgeStore(settings)
    report = import_homepage_materials(store, homepage_dir)

    assert report.skipped_count == 0
    assert all(document.source_name != stale_record.source_name for document in store.list_documents())