"""One-time ingestion of workspace repo READMEs + curated FAQ into the
sage-faculty-twin knowledge base.

Usage:
    cd /home/shuhao/sage-faculty-twin
    PYTHONPATH=src:/home/shuhao/SAGE/src:/home/shuhao/sageVDB:/home/shuhao/neuromem \
        python tools/ingest_workspace_repos.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sage_faculty_twin.config import AppSettings
from sage_faculty_twin.knowledge_base import LocalKnowledgeStore
from sage_faculty_twin.models import KnowledgeDocumentCreate

_MAX_CONTENT_LEN = 18000

_REPO_SOURCES = [
    {"path": "/home/shuhao/SAGE/README.md", "title": "Lab System | SAGE README", "tags": ["research", "publication", "system", "sage"], "source_name": "workspace/SAGE"},
    {"path": "/home/shuhao/neuromem/README.md", "title": "Lab System | Neuromem README", "tags": ["research", "publication", "system", "neuromem", "memory"], "source_name": "workspace/neuromem"},
    {"path": "/home/shuhao/sageVDB/README.md", "title": "Lab System | SageVDB README", "tags": ["research", "system", "vector-db", "sagevdb"], "source_name": "workspace/sageVDB"},
    {"path": "/home/shuhao/vllm-hust/README.md", "title": "Lab System | vLLM-HUST README", "tags": ["research", "system", "vllm", "inference-engine"], "source_name": "workspace/vllm-hust"},
    {"path": "/home/shuhao/vamos/README.md", "title": "Current Research | VAMOS README", "tags": ["research", "agenda", "current-focus", "vamos"], "source_name": "workspace/vamos"},
    {"path": "/home/shuhao/vamos/roadmap.md", "title": "Current Research | VAMOS Roadmap", "tags": ["research", "agenda", "current-focus", "vamos", "roadmap"], "source_name": "workspace/vamos/roadmap"},
    {"path": "/home/shuhao/vamos/docs/proposal/2026-ccf-ant-proposal.md", "title": "Current Research | 2026 CCF-Ant Proposal (VAMOS)", "tags": ["research", "agenda", "current-focus", "vamos", "proposal"], "source_name": "workspace/vamos/proposal"},
    {"path": "/home/shuhao/sage-tutorials/QUICK_START.md", "title": "Teaching | Sage-Tutorials Quick Start", "tags": ["teaching", "tutorial", "sage-tutorials"], "source_name": "workspace/sage-tutorials"},
]


def _read_file(path):
    p = Path(path)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")[:_MAX_CONTENT_LEN]


def main():
    settings = AppSettings()
    store = LocalKnowledgeStore(settings)

    payloads = []
    for src in _REPO_SOURCES:
        content = _read_file(src["path"])
        if not content.strip():
            print(f"  SKIP (empty): {src['path']}")
            continue
        payloads.append(KnowledgeDocumentCreate(title=src["title"], content=content, tags=src["tags"], source_name=src["source_name"]))

    faq_path = Path(__file__).resolve().parent.parent / "data" / "_seed_faq.json"
    if faq_path.exists():
        for item in json.loads(faq_path.read_text(encoding="utf-8")):
            payloads.append(KnowledgeDocumentCreate(title=item["title"], content=item["content"], tags=item.get("tags", []), source_name=item.get("source_name", "curated_faq")))
    else:
        print(f"  WARN: FAQ file not found at {faq_path}")

    print(f"Prepared {len(payloads)} documents for ingestion.")
    created = skipped = 0
    for payload in payloads:
        existing = [d for d in store.list_documents() if d.title == payload.title]
        if existing:
            print(f"  EXISTS: {payload.title}")
            skipped += 1
            continue
        record = store.add_document(payload)
        print(f"  CREATED: {record.title} ({record.document_id[:8]})")
        created += 1
    print(f"\nDone. created={created}, skipped={skipped}")


if __name__ == "__main__":
    main()
