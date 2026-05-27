from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .config import AppSettings
from .knowledge_base import LocalKnowledgeStore
from .models import KnowledgeDocumentCreate

_FRONT_MATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
_PDF_LABEL_RE = re.compile(r"\[PDF\]\(([^)]+\.pdf)\)", re.IGNORECASE)


@dataclass(frozen=True)
class ImportReport:
    created_count: int
    updated_count: int
    skipped_count: int
    created_titles: list[str]
    updated_titles: list[str]
    skipped_sources: list[str]


def import_homepage_materials(
    store: LocalKnowledgeStore,
    homepage_dir: Path,
) -> ImportReport:
    contents_dir = homepage_dir / "contents"
    if not contents_dir.exists():
        raise FileNotFoundError(f"Homepage contents directory does not exist: {contents_dir}")

    payloads = [
        *_build_homepage_profile_payloads(contents_dir / "home.md"),
        *_build_news_payloads(contents_dir / "news.md"),
        *_build_resources_payloads(contents_dir / "resources.md"),
        *_build_teaching_payloads(contents_dir / "teaching"),
        *_build_publication_overview_payloads(contents_dir / "publications.md"),
        *_build_publication_digest_payloads(contents_dir / "research_papers" / "publications_summary.md"),
    ]

    desired_sources = {payload.source_name for payload in payloads if payload.source_name}
    stale_document_ids = _find_stale_homepage_document_ids(store.list_documents(), desired_sources)
    if stale_document_ids:
        store.delete_documents(stale_document_ids, rebuild_indexes=False)

    existing_sources = {
        document.source_name
        for document in store.list_documents()
        if document.source_name
    }
    created_titles: list[str] = []
    updated_titles: list[str] = []
    skipped_sources: list[str] = []
    changed = bool(stale_document_ids)

    for payload in payloads:
        existing = payload.source_name and payload.source_name in existing_sources
        record, created = store.upsert_document(payload, rebuild_indexes=False)
        if created:
            created_titles.append(record.title)
            changed = True
            if payload.source_name:
                existing_sources.add(payload.source_name)
            continue
        if existing:
            updated_titles.append(record.title)
            changed = True
            continue
        skipped_sources.append(payload.source_name or record.document_id)

    if changed:
        store.rebuild_indexes()

    return ImportReport(
        created_count=len(created_titles),
        updated_count=len(updated_titles),
        skipped_count=len(skipped_sources),
        created_titles=created_titles,
        updated_titles=updated_titles,
        skipped_sources=skipped_sources,
    )


def _build_homepage_profile_payloads(path: Path) -> list[KnowledgeDocumentCreate]:
    if not path.exists():
        return []

    title, sections = _split_markdown_by_heading(path.read_text(encoding="utf-8"), heading_level=2)
    payloads: list[KnowledgeDocumentCreate] = []
    intro_title = f"主页资料｜{title or '个人简介'}"
    for index, (section_title, body) in enumerate(sections):
        normalized_title = intro_title if index == 0 else f"主页资料｜{section_title}"
        payloads.extend(
            _make_payloads(
                title=normalized_title,
                content=body,
                tags=["homepage", "profile"],
                source_stub=f"homepage:contents/home.md#{section_title or 'intro'}",
            )
        )
    return payloads


def _build_news_payloads(path: Path) -> list[KnowledgeDocumentCreate]:
    if not path.exists():
        return []

    content = _normalize_markdown(path.read_text(encoding="utf-8"))
    return _make_payloads(
        title="主页资料｜近期动态",
        content=content,
        tags=["homepage", "news"],
        source_stub="homepage:contents/news.md#recent-updates",
    )


def _build_publication_overview_payloads(path: Path) -> list[KnowledgeDocumentCreate]:
    if not path.exists():
        return []

    _, sections = _split_markdown_by_heading(path.read_text(encoding="utf-8"), heading_level=2)
    payloads: list[KnowledgeDocumentCreate] = []
    for section_title, body in sections:
        if section_title == "首页导读":
            payloads.extend(
                _make_payloads(
                    title="研究总览｜研究主线",
                    content=_normalize_markdown(body),
                    tags=["homepage", "research", "publication", "overview"],
                    source_stub="homepage:contents/publications.md#首页导读",
                )
            )
            continue

        if section_title != "代表性论文":
            continue

        _, theme_sections = _split_markdown_by_heading(body, heading_level=3)
        for theme_title, theme_body in theme_sections:
            normalized_theme = _strip_numeric_prefix(theme_title)
            payloads.extend(
                _make_payloads(
                    title=f"研究总览｜{normalized_theme}",
                    content=_normalize_markdown(theme_body),
                    tags=["homepage", "research", "publication", "overview", *_infer_publication_tags(normalized_theme, theme_body)],
                    source_stub=f"homepage:contents/publications.md#{normalized_theme}",
                )
            )
    return payloads


def _build_publication_digest_payloads(path: Path) -> list[KnowledgeDocumentCreate]:
    if not path.exists():
        return []

    _, sections = _split_markdown_by_heading(path.read_text(encoding="utf-8"), heading_level=3)
    payloads: list[KnowledgeDocumentCreate] = []
    for section_title, body in sections:
        if not re.match(r"^\d+\.\d+\s+", section_title):
            continue
        clean_title = _strip_numeric_prefix(section_title)
        digest_content = _build_publication_digest_content(clean_title, body)
        payloads.extend(
            _make_payloads(
                title=f"论文提炼｜{clean_title}",
                content=digest_content,
                tags=["homepage", "research", "publication", "paper-digest", *_infer_publication_tags(clean_title, body)],
                source_stub=f"homepage:contents/research_papers/publications_summary.md#{section_title}",
            )
        )
    return payloads


def _find_stale_homepage_document_ids(
    documents: list,
    desired_sources: set[str],
) -> list[str]:
    source_to_documents: dict[str, list] = {}
    stale_ids: list[str] = []

    for document in documents:
        source_name = getattr(document, "source_name", None)
        if not source_name or not source_name.startswith("homepage:"):
            continue
        source_to_documents.setdefault(source_name, []).append(document)

    for source_name, items in source_to_documents.items():
        ordered = sorted(items, key=lambda item: getattr(item, "created_at"), reverse=True)
        if source_name not in desired_sources:
            stale_ids.extend(getattr(item, "document_id") for item in ordered)
            continue
        if len(ordered) > 1:
            stale_ids.extend(getattr(item, "document_id") for item in ordered[1:])

    return stale_ids


def _build_publication_digest_content(title: str, body: str) -> str:
    normalized = _normalize_markdown(body)
    metadata = _parse_publication_metadata(normalized)
    summary_text = metadata.get("abstract") or metadata.get("summary") or normalized
    research_theme = _infer_publication_theme(title, summary_text)
    one_line = _first_meaningful_sentence(summary_text)

    lines = [
        f"论文名称：{title}",
        f"研究主题：{research_theme}",
    ]

    if metadata.get("venue"):
        lines.append(f"发表 venue：{metadata['venue']}")
    if metadata.get("year"):
        lines.append(f"发表年份：{metadata['year']}")
    if metadata.get("authors"):
        lines.append(f"作者：{metadata['authors']}")

    role_summary = _build_author_role_summary(metadata)
    if role_summary:
        lines.append(f"作者角色：{role_summary}")

    if one_line:
        lines.append(f"一句话总结：{one_line}")

    lines.extend(
        [
            "核心内容：",
            summary_text,
            "适合回答的问题：",
            "- 这篇论文主要解决什么问题，以及它为什么重要。",
            "- 这篇论文的核心方法、系统设计或算法思路是什么。",
            f"- 这篇论文与 {research_theme} 这条研究主线的关系是什么。",
        ]
    )
    return "\n".join(lines).strip()


def _parse_publication_metadata(text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("Venue:"):
            metadata["venue"] = line.partition(":")[2].strip()
            continue
        if line.startswith("Year:"):
            metadata["year"] = line.partition(":")[2].strip()
            continue
        if line.startswith("Authors:"):
            metadata["authors"] = line.partition(":")[2].strip()
            continue
        if line.startswith("Status:"):
            metadata["status"] = line.partition(":")[2].strip()
            continue
        if line.startswith("Abstract:"):
            metadata["abstract"] = line.partition(":")[2].strip()
            continue
        if line.startswith("Summary:"):
            metadata["summary"] = line.partition(":")[2].strip()
            continue
        if line.startswith("Corresponding Author:"):
            value = line.partition(":")[2].strip()
            if "|" in value:
                corresponding, _, trailing = value.partition("|")
                metadata["corresponding_author"] = corresponding.strip()
                trailing = trailing.strip()
                if trailing.startswith("First Author:"):
                    metadata["first_author"] = trailing.partition(":")[2].strip()
            else:
                metadata["corresponding_author"] = value
            continue
        if line.startswith("First Author:"):
            metadata["first_author"] = line.partition(":")[2].strip()
    return metadata


def _build_author_role_summary(metadata: dict[str, str]) -> str:
    roles: list[str] = []
    if metadata.get("corresponding_author", "").lower() == "yes":
        roles.append("你是通讯作者")
    if metadata.get("first_author", "").lower() == "yes":
        roles.append("你是第一作者")
    if metadata.get("status"):
        roles.append(metadata["status"])
    if not roles:
        return "合作作者或共同作者"
    return "；".join(roles)


def _first_meaningful_sentence(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return ""
    match = re.search(r"(.+?[。！？.!?])(?:\s|$)", normalized)
    sentence = match.group(1).strip() if match else normalized
    return sentence[:280].rstrip()


def _infer_publication_theme(title: str, body: str) -> str:
    lowered = f"{title} {body}".lower()
    if any(keyword in lowered for keyword in ("rag", "retriever", "memory", "kv cache", "llm", "agentic", "hallucination", "knowledge graph")):
        return "大模型推理、检索增强与记忆系统"
    if any(keyword in lowered for keyword in ("stream", "streaming", "window", "transactional", "recovery", "scheduling", "compression")):
        return "流处理系统、共享状态与运行时调度"
    if any(keyword in lowered for keyword in ("multicore", "cpu", "gpu", "fpga", "approximate", "matrix", "hardware", "energy")):
        return "软硬件协同优化与高性能系统"
    if any(keyword in lowered for keyword in ("graph", "ann", "vector", "clustering", "continual learning", "sentiment")):
        return "动态数据管理、持续学习与智能分析"
    return "数据系统与智能基础设施"


def _infer_publication_tags(title: str, body: str) -> list[str]:
    lowered = f"{title} {body}".lower()
    tags: list[str] = []
    keyword_pairs = [
        ("llm", "llm"),
        ("rag", "rag"),
        ("memory", "memory"),
        ("kv cache", "kv-cache"),
        ("stream", "stream-processing"),
        ("transactional", "transactional-stream"),
        ("compression", "compression"),
        ("graph", "graph"),
        ("ann", "ann"),
        ("multicore", "multicore"),
        ("gpu", "gpu"),
        ("approximate", "approximate-computing"),
        ("clustering", "clustering"),
        ("continual learning", "continual-learning"),
    ]
    for keyword, tag in keyword_pairs:
        if keyword in lowered and tag not in tags:
            tags.append(tag)
    return tags


def _build_resources_payloads(path: Path) -> list[KnowledgeDocumentCreate]:
    if not path.exists():
        return []

    content = _normalize_markdown(path.read_text(encoding="utf-8"))
    return _make_payloads(
        title="课程资料｜公开教学资源",
        content=content,
        tags=["homepage", "teaching", "resources"],
        source_stub="homepage:contents/resources.md#teaching-resources",
    )


def _build_teaching_payloads(teaching_dir: Path) -> list[KnowledgeDocumentCreate]:
    if not teaching_dir.exists():
        return []

    payloads: list[KnowledgeDocumentCreate] = []
    repo_root = teaching_dir.parent.parent
    for path in sorted(teaching_dir.glob("*.md")):
        raw_text = path.read_text(encoding="utf-8")
        course_title, sections = _split_markdown_by_heading(raw_text, heading_level=2)
        if not sections:
            continue
        source_prefix = f"homepage:{path.relative_to(teaching_dir.parent.parent).as_posix()}"
        course_tags = _teaching_course_tags(path, course_title)
        for index, (section_title, body) in enumerate(sections):
            normalized_title = f"课程资料｜{course_title or '课程材料'}"
            if index > 0:
                normalized_title = f"课程资料｜{course_title}｜{section_title}"
            material_tags = _teaching_material_tags(section_title)
            payloads.extend(
                _make_payloads(
                    title=normalized_title,
                    content=body,
                    tags=_dedupe_tags([
                        "homepage",
                        "teaching",
                        "courseware",
                        *course_tags,
                        *material_tags,
                        *_teaching_section_tags(section_title),
                    ]),
                    source_stub=f"{source_prefix}#{section_title or 'intro'}",
                )
            )
            payloads.extend(
                _build_teaching_pdf_payloads(
                    repo_root=repo_root,
                    course_title=course_title or "课程材料",
                    section_title=section_title,
                    section_body=body,
                    course_tags=course_tags,
                    source_prefix=source_prefix,
                )
            )
    return payloads


def _build_teaching_pdf_payloads(
    *,
    repo_root: Path,
    course_title: str,
    section_title: str,
    section_body: str,
    course_tags: list[str],
    source_prefix: str,
) -> list[KnowledgeDocumentCreate]:
    payloads: list[KnowledgeDocumentCreate] = []
    for line in section_body.splitlines():
        if "[PDF](" not in line:
            continue
        match = _PDF_LABEL_RE.search(line)
        if match is None:
            continue
        relative_pdf = match.group(1)
        pdf_path = _resolve_repo_path(repo_root, relative_pdf)
        if not pdf_path.exists():
            continue
        item_title = _title_from_pdf_line(line)
        pdf_text = _extract_pdf_text(pdf_path)
        if not pdf_text:
            continue
        material_tags = _teaching_material_tags(section_title, item_title)
        payloads.extend(
            _make_payloads(
                title=f"课件正文｜{course_title}｜{item_title}",
                content=pdf_text,
                tags=_dedupe_tags([
                    "homepage",
                    "teaching",
                    "courseware",
                    "pdf",
                    "material:pdf",
                    *course_tags,
                    *material_tags,
                    *_teaching_section_tags(section_title),
                ]),
                source_stub=f"{source_prefix}#{section_title}::{pdf_path.relative_to(repo_root).as_posix()}",
                max_chars=3200,
            )
        )
    return payloads


def _make_payloads(
    title: str,
    content: str,
    tags: list[str],
    source_stub: str,
    *,
    max_chars: int = 6000,
) -> list[KnowledgeDocumentCreate]:
    normalized_content = _normalize_markdown(content)
    if not normalized_content:
        return []

    chunks = _chunk_text(normalized_content, max_chars=max_chars)
    payloads: list[KnowledgeDocumentCreate] = []
    for index, chunk in enumerate(chunks, start=1):
        title_suffix = f"（第{index}部分）" if len(chunks) > 1 else ""
        source_suffix = f"::part-{index}" if len(chunks) > 1 else ""
        payloads.append(
            KnowledgeDocumentCreate(
                title=f"{title}{title_suffix}",
                content=chunk,
                tags=tags,
                source_name=f"{source_stub}{source_suffix}",
            )
        )
    return payloads


def _split_markdown_by_heading(text: str, heading_level: int) -> tuple[str | None, list[tuple[str, str]]]:
    stripped_text = _FRONT_MATTER_RE.sub("", text)
    heading_token = "#" * heading_level
    matches = [match for match in _HEADING_RE.finditer(stripped_text) if match.group(1) == heading_token]

    title_match = re.search(r"^#\s+(.+)$", stripped_text, re.MULTILINE)
    title = _clean_inline_markdown(title_match.group(1)) if title_match else None
    if not matches:
        return title, [(title or "文档", stripped_text)]

    sections: list[tuple[str, str]] = []
    preamble = stripped_text[: matches[0].start()].strip()
    if preamble:
        sections.append((title or "简介", preamble))

    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(stripped_text)
        section_title = _clean_inline_markdown(match.group(2))
        body = stripped_text[start:end].strip()
        if body:
            sections.append((section_title, body))
    return title, sections


def _normalize_markdown(text: str) -> str:
    text = _FRONT_MATTER_RE.sub("", text)
    lines: list[str] = []
    in_code_block = False

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if stripped.startswith("|"):
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if cells and not all(set(cell) <= {"-", ":", " "} for cell in cells):
                stripped = " ; ".join(cell for cell in cells if cell)
        stripped = _clean_inline_markdown(stripped)
        if not stripped:
            if lines and lines[-1] != "":
                lines.append("")
            continue
        lines.append(stripped)

    return "\n".join(lines).strip()


def _clean_inline_markdown(text: str) -> str:
    text = _LINK_RE.sub(lambda match: match.group(1), text)
    text = re.sub(r"^[#>]+\s*", "", text)
    text = re.sub(r"^[-*+]\s+", "- ", text)
    text = text.replace("`", "")
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("*", "")
    text = text.replace("_", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _resolve_repo_path(repo_root: Path, raw_path: str) -> Path:
    normalized = raw_path.strip()
    if normalized.startswith("/"):
        normalized = normalized[1:]
    return repo_root / normalized


def _title_from_pdf_line(line: str) -> str:
    cleaned = _PDF_LABEL_RE.sub("", line)
    cleaned = _clean_inline_markdown(cleaned)
    cleaned = re.sub(r"^-\s*", "", cleaned)
    cleaned = cleaned.rstrip("：: ")
    return cleaned or "课件正文"


def _teaching_section_tags(section_title: str) -> list[str]:
    normalized = section_title.lower()
    if "tutorial" in normalized:
        return ["tutorial"]
    if "实验" in section_title or "project" in normalized:
        return ["experiment"]
    if "讲义" in section_title or "课件" in section_title:
        return ["lecture"]
    return []


def _teaching_course_tags(path: Path, course_title: str | None) -> list[str]:
    normalized = f"{path.stem} {course_title or ''}".lower()
    tags = ["identity:teacher", "domain:teaching", "audience:graduate"]
    if "intro-to-llm-inference-engines" in normalized or "大模型推理" in normalized:
        tags.append("course:llm-inference")
    elif "graduate-paper-writing-course" in normalized or "论文写作" in normalized:
        tags.append("course:paper-writing")
    else:
        tags.append(f"course:{path.stem}")
    return tags


def _teaching_material_tags(section_title: str, item_title: str = "") -> list[str]:
    combined = f"{section_title} {item_title}".lower()
    tags: list[str] = []
    if "tutorial" in combined or "教程" in combined or "习题" in combined:
        tags.append("material:tutorial")
        match = re.search(r"tutorial\s*0?(\d+)", combined, re.IGNORECASE)
        if match:
            tags.append(f"tutorial:{int(match.group(1))}")
    elif "实验" in section_title or "experiment" in combined or "project" in combined or "项目" in combined:
        tags.append("material:experiment")
        match = re.search(r"(?:实验|experiment)\s*0?(\d+)", combined, re.IGNORECASE)
        if match:
            tags.append(f"experiment:{int(match.group(1))}")
    elif "讲义" in section_title or "课件" in section_title or "lecture" in combined or re.search(r"第\s*\d+\s*讲", item_title):
        tags.append("material:lecture")
        match = re.search(r"第\s*0?(\d+)\s*讲|lecture[-_\s]?0?(\d+)", combined, re.IGNORECASE)
        if match:
            number = next(group for group in match.groups() if group)
            tags.append(f"lecture:{int(number)}")
    else:
        tags.append("material:course-overview")
    return tags


def _dedupe_tags(tags: list[str]) -> list[str]:
    return list(dict.fromkeys(tag for tag in tags if tag))


def _extract_pdf_text(pdf_path: Path) -> str:
    pdftotext_binary = shutil.which("pdftotext")
    if pdftotext_binary:
        extracted = _extract_pdf_text_with_pdftotext(pdftotext_binary, pdf_path)
        if extracted:
            return extracted

    return _extract_pdf_text_with_pypdf(pdf_path)


def _extract_pdf_text_with_pdftotext(binary: str, pdf_path: Path) -> str:
    result = subprocess.run(
        [binary, "-layout", str(pdf_path), "-"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ""
    return _normalize_pdf_text(result.stdout.replace("\f", "\n\n"))


def _extract_pdf_text_with_pypdf(pdf_path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "Offline PDF import requires either the pdftotext system binary or the pypdf package. "
            "Install with: python -m pip install -e ."
        ) from exc

    reader = PdfReader(str(pdf_path))
    page_chunks: list[str] = []
    for page_number, page in enumerate(reader.pages, start=1):
        extracted = _normalize_pdf_text(page.extract_text() or "")
        if extracted:
            page_chunks.append(f"第 {page_number} 页\n{extracted}")
    return "\n\n".join(page_chunks).strip()


def _normalize_pdf_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    paragraphs: list[str] = []
    current: list[str] = []
    for line in lines:
        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(line)
    if current:
        paragraphs.append(" ".join(current))
    cleaned = "\n\n".join(paragraphs)
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.replace(" \n", "\n")
    return cleaned.strip()


def _chunk_text(text: str, *, max_chars: int) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_length = 0
    for paragraph in paragraphs:
        paragraph_length = len(paragraph)
        if paragraph_length > max_chars:
            if current:
                chunks.append("\n\n".join(current))
                current = []
                current_length = 0
            chunks.extend(_split_long_paragraph(paragraph, max_chars=max_chars))
            continue
        if current and current_length + paragraph_length + 2 > max_chars:
            chunks.append("\n\n".join(current))
            current = [paragraph]
            current_length = paragraph_length
            continue
        current.append(paragraph)
        current_length += paragraph_length + (2 if current_length else 0)

    if current:
        chunks.append("\n\n".join(current))
    return _apply_chunk_overlap(chunks, max_chars=max_chars)


def _apply_chunk_overlap(chunks: list[str], *, max_chars: int) -> list[str]:
    if len(chunks) <= 1:
        return chunks

    overlap_target = min(400, max(120, max_chars // 8))
    overlapped_chunks = [chunks[0]]
    for chunk in chunks[1:]:
        overlap = _extract_chunk_overlap(overlapped_chunks[-1], target_chars=overlap_target)
        if not overlap:
            overlapped_chunks.append(chunk)
            continue

        available = max_chars - len(chunk) - 2
        if available <= 0:
            overlapped_chunks.append(chunk)
            continue

        if len(overlap) > available:
            overlap = overlap[-available:].strip()
        if not overlap:
            overlapped_chunks.append(chunk)
            continue
        overlapped_chunks.append(f"{overlap}\n\n{chunk}".strip())
    return overlapped_chunks


def _extract_chunk_overlap(text: str, *, target_chars: int) -> str:
    if not text or target_chars <= 0:
        return ""

    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    if not paragraphs:
        return text[-target_chars:].strip()

    selected: list[str] = []
    total_length = 0
    for paragraph in reversed(paragraphs):
        paragraph_length = len(paragraph)
        separator_length = 2 if selected else 0
        if selected and total_length + separator_length + paragraph_length > target_chars:
            break
        if paragraph_length > target_chars and not selected:
            return paragraph[-target_chars:].strip()
        if total_length + separator_length + paragraph_length > target_chars:
            continue
        selected.insert(0, paragraph)
        total_length += paragraph_length + separator_length

    if selected:
        return "\n\n".join(selected).strip()
    return text[-target_chars:].strip()


def _split_long_paragraph(paragraph: str, *, max_chars: int) -> list[str]:
    sentences = [item.strip() for item in re.findall(r"[^。！？.!?；;]+[。！？.!?；;]?", paragraph) if item.strip()]
    if len(sentences) <= 1:
        return [paragraph[start : start + max_chars].strip() for start in range(0, len(paragraph), max_chars)]

    chunks: list[str] = []
    current: list[str] = []
    current_length = 0
    for sentence in sentences:
        sentence_length = len(sentence)
        if sentence_length > max_chars:
            if current:
                chunks.append(" ".join(current).strip())
                current = []
                current_length = 0
            chunks.extend(sentence[start : start + max_chars].strip() for start in range(0, sentence_length, max_chars))
            continue
        separator_length = 1 if current else 0
        if current and current_length + separator_length + sentence_length > max_chars:
            chunks.append(" ".join(current).strip())
            current = [sentence]
            current_length = sentence_length
            continue
        current.append(sentence)
        current_length += sentence_length + separator_length

    if current:
        chunks.append(" ".join(current).strip())
    return chunks


def _strip_numeric_prefix(title: str) -> str:
    return re.sub(r"^\d+(?:\.\d+)*\s+", "", title).strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import curated homepage materials into the twin knowledge base.")
    parser.add_argument("--homepage-dir", required=True, type=Path)
    parser.add_argument("--knowledge-dir", type=Path, default=Path("data/knowledge_base"))
    parser.add_argument("--knowledge-backend", default="neuromem")
    args = parser.parse_args(argv)

    settings = AppSettings(
        knowledge_base_dir=args.knowledge_dir,
        knowledge_backend=args.knowledge_backend,
    )
    store = LocalKnowledgeStore(settings)
    report = import_homepage_materials(store, args.homepage_dir)
    print(f"created={report.created_count}")
    print(f"updated={report.updated_count}")
    print(f"skipped={report.skipped_count}")
    for title in report.created_titles:
        print(f"+ {title}")
    for title in report.updated_titles:
        print(f"~ {title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())