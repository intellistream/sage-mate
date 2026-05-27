from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from .config import AppSettings
from .models import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentRecord,
    KnowledgeSearchHit,
)


class HashingTextEmbedder:
    def __init__(self, settings: AppSettings, np_module) -> None:
        self._settings = settings
        self._np = np_module
        self.dimension = settings.sagevdb_dimension

    def encode(self, text: str):
        vector = self._np.zeros(self.dimension, dtype=self._np.float32)
        token_counts: dict[str, int] = {}
        for token in _tokenize_text(text):
            token_counts[token] = token_counts.get(token, 0) + 1

        for token, count in token_counts.items():
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            hashed = int.from_bytes(digest, byteorder="big", signed=False)
            index = hashed % self.dimension
            sign = 1.0 if ((hashed >> 8) & 1) == 0 else -1.0
            vector[index] += sign * (1.0 + math.log1p(count))

        norm = float(self._np.linalg.norm(vector))
        if norm > 0.0:
            vector /= norm
        return vector


class SentenceTransformerTextEmbedder:
    def __init__(self, settings: AppSettings, np_module) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sagevdb embedding backend 'sentence-transformers' requires the sentence-transformers package. "
                "Install with: python -m pip install -e .[vdb]"
            ) from exc

        self._np = np_module
        self._model_name = settings.sagevdb_embedding_model
        self._model = SentenceTransformer(self._model_name)
        self.dimension = self._model.get_sentence_embedding_dimension()
        if not self.dimension:
            raise RuntimeError(
                f"Embedding model '{self._model_name}' did not report an embedding dimension."
            )

    def encode(self, text: str):
        vector = self._model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        array = self._np.asarray(vector, dtype=self._np.float32)
        if array.ndim != 1:
            array = array.reshape(-1)
        if int(array.shape[0]) != int(self.dimension):
            raise RuntimeError(
                f"Embedding dimension mismatch: model returned {array.shape[0]}, expected {self.dimension}."
            )
        return array


class LocalKnowledgeStore:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._base_dir = settings.knowledge_base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._documents: dict[str, KnowledgeDocumentRecord] = {}
        self._backend = settings.knowledge_backend.lower()
        self._sagevdb = None
        self._neuromem_collection = None
        self._np = None
        self._text_embedder = None
        self._document_id_to_vector_id: dict[str, int] = {}
        self._load_documents_from_disk()
        if self._backend == "sagevdb":
            self._initialize_sagevdb()
        elif self._backend == "neuromem":
            self._initialize_neuromem()

    def add_document(
        self,
        payload: KnowledgeDocumentCreate,
        *,
        rebuild_indexes: bool = True,
    ) -> KnowledgeDocumentRecord:
        record = KnowledgeDocumentRecord(
            document_id=str(uuid4()),
            title=payload.title,
            content=payload.content,
            tags=payload.tags,
            source_name=payload.source_name,
            created_at=datetime.now(UTC),
        )
        target_path = self._base_dir / f"{record.document_id}.json"
        target_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
        self._documents[record.document_id] = record
        if self._backend == "sagevdb":
            self._add_to_sagevdb(record, rebuild_index=rebuild_indexes)
        elif self._backend == "neuromem":
            self._add_to_neuromem(record)
        return record

    def upsert_document(
        self,
        payload: KnowledgeDocumentCreate,
        *,
        rebuild_indexes: bool = True,
    ) -> tuple[KnowledgeDocumentRecord, bool]:
        existing = self._find_document_by_source_name(payload.source_name)
        if existing is None:
            return self.add_document(payload, rebuild_indexes=rebuild_indexes), True

        updated_record = KnowledgeDocumentRecord(
            document_id=existing.document_id,
            title=payload.title,
            content=payload.content,
            tags=payload.tags,
            source_name=payload.source_name,
            created_at=datetime.now(UTC),
        )
        target_path = self._base_dir / f"{updated_record.document_id}.json"
        target_path.write_text(updated_record.model_dump_json(indent=2), encoding="utf-8")
        self._documents[updated_record.document_id] = updated_record
        self._remove_duplicate_documents_for_source(
            payload.source_name,
            keep_document_id=updated_record.document_id,
        )
        if rebuild_indexes:
            self._rebuild_backend_indexes()
        return updated_record, False

    def update_document(
        self,
        document_id: str,
        payload: KnowledgeDocumentCreate,
        *,
        rebuild_indexes: bool = True,
    ) -> KnowledgeDocumentRecord:
        existing = self._documents.get(document_id)
        if existing is None:
            raise KeyError(document_id)

        updated_record = KnowledgeDocumentRecord(
            document_id=existing.document_id,
            title=payload.title,
            content=payload.content,
            tags=payload.tags,
            source_name=payload.source_name,
            created_at=existing.created_at,
        )
        target_path = self._base_dir / f"{updated_record.document_id}.json"
        target_path.write_text(updated_record.model_dump_json(indent=2), encoding="utf-8")
        self._documents[updated_record.document_id] = updated_record
        self._remove_duplicate_documents_for_source(
            payload.source_name,
            keep_document_id=updated_record.document_id,
            persist=True,
        )
        if rebuild_indexes:
            self._rebuild_backend_indexes()
        return updated_record

    def list_documents(self) -> list[KnowledgeDocumentRecord]:
        return sorted(self._documents.values(), key=lambda item: item.created_at)

    def delete_documents(
        self,
        document_ids: list[str],
        *,
        rebuild_indexes: bool = True,
    ) -> int:
        removed = 0
        for document_id in {item for item in document_ids if item}:
            record = self._documents.pop(document_id, None)
            if record is None:
                continue
            target_path = self._base_dir / f"{document_id}.json"
            if target_path.exists():
                target_path.unlink()
            self._document_id_to_vector_id.pop(document_id, None)
            removed += 1

        if removed and rebuild_indexes:
            self._rebuild_backend_indexes()
        return removed

    def rebuild_indexes(self) -> None:
        self._rebuild_backend_indexes()

    def search(
        self,
        query: str,
        top_k: int | None = None,
        *,
        visitor_profile: str | None = None,
    ) -> list[KnowledgeSearchHit]:
        if self._backend == "sagevdb":
            return self._search_sagevdb(query, top_k, visitor_profile=visitor_profile)
        if self._backend == "neuromem":
            return self._search_neuromem(query, top_k, visitor_profile=visitor_profile)

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
        query_profile = _build_query_profile(query, visitor_profile=visitor_profile)

        scored_hits: list[KnowledgeSearchHit] = []
        for document in self.list_documents():
            score = self._score_document(document, query_tokens, query_profile)
            if score <= 0:
                continue
            scored_hits.append(
                KnowledgeSearchHit(
                    document_id=document.document_id,
                    title=document.title,
                    excerpt=self._build_excerpt(document.content, query_tokens),
                    score=score,
                    tags=document.tags,
                    source_name=document.source_name,
                )
            )

        limit = top_k or self._settings.retrieval_top_k
        reranked = sorted(scored_hits, key=lambda item: item.score, reverse=True)
        return self._finalize_hits(reranked, query_profile, limit)

    def count_documents(self) -> int:
        return len(self._documents)

    def backend_name(self) -> str:
        return self._backend

    def _load_documents_from_disk(self) -> None:
        for path in sorted(self._base_dir.glob("*.json")):
            document = KnowledgeDocumentRecord.model_validate_json(path.read_text(encoding="utf-8"))
            self._documents[document.document_id] = document
        self._deduplicate_loaded_documents()

    def _find_document_by_source_name(self, source_name: str | None) -> KnowledgeDocumentRecord | None:
        if not source_name:
            return None
        matches = self._find_documents_by_source_name(source_name)
        return matches[0] if matches else None

    def _find_documents_by_source_name(self, source_name: str | None) -> list[KnowledgeDocumentRecord]:
        if not source_name:
            return []
        matches = [
            document
            for document in self._documents.values()
            if document.source_name == source_name
        ]
        return sorted(matches, key=lambda item: item.created_at, reverse=True)

    def _deduplicate_loaded_documents(self) -> None:
        source_names = {
            document.source_name
            for document in self._documents.values()
            if document.source_name
        }
        for source_name in source_names:
            self._remove_duplicate_documents_for_source(source_name, persist=True)

    def _remove_duplicate_documents_for_source(
        self,
        source_name: str | None,
        *,
        keep_document_id: str | None = None,
        persist: bool = False,
    ) -> int:
        matches = self._find_documents_by_source_name(source_name)
        if len(matches) <= 1:
            return 0

        canonical_document_id = keep_document_id or matches[0].document_id
        removed = 0
        for document in matches:
            if document.document_id == canonical_document_id:
                continue
            self._documents.pop(document.document_id, None)
            target_path = self._base_dir / f"{document.document_id}.json"
            if persist and target_path.exists():
                target_path.unlink()
            removed += 1
        return removed

    def _rebuild_backend_indexes(self) -> None:
        if self._backend == "sagevdb":
            self._initialize_sagevdb()
        elif self._backend == "neuromem":
            self._initialize_neuromem()

    def _normalize_sagevdb_backend(self) -> str:
        return self._settings.sagevdb_backend.strip().lower().replace("_", "-")

    def _uses_sagevdb_anns_backend(self) -> bool:
        return self._normalize_sagevdb_backend() in {"sage-anns", "sageanns", "anns"}

    def _document_metadata(self, document: KnowledgeDocumentRecord) -> dict[str, str]:
        return {
            "document_id": document.document_id,
            "title": document.title,
            "tags": "|".join(document.tags),
            "source_name": document.source_name or "",
        }

    def _initialize_sagevdb(self) -> None:
        try:
            import numpy as np
            from sagevdb import DatabaseConfig, DistanceMetric, IndexType, create_database
        except ImportError as exc:
            raise RuntimeError(
                "DIGITAL_TWIN_KNOWLEDGE_BACKEND is set to 'sagevdb' but sagevdb is not available. "
                "Install isage-vdb or expose the local sageVDB checkout on PYTHONPATH."
            ) from exc

        self._np = np
        self._text_embedder = self._build_text_embedder(np)
        cfg = DatabaseConfig(int(self._text_embedder.dimension))
        backend = self._normalize_sagevdb_backend()
        cfg.metric = (
            DistanceMetric.INNER_PRODUCT
            if self._uses_sagevdb_anns_backend()
            else DistanceMetric.COSINE
        )
        cfg.index_type = IndexType.FLAT

        database_kwargs = {"backend": backend}
        if self._uses_sagevdb_anns_backend():
            algorithm = self._settings.sagevdb_anns_algorithm.strip()
            if not algorithm:
                raise RuntimeError(
                    "DIGITAL_TWIN_SAGEVDB_BACKEND is set to 'sage-anns' but "
                    "DIGITAL_TWIN_SAGEVDB_ANNS_ALGORITHM is empty."
                )
            database_kwargs["algorithm"] = algorithm

        try:
            self._sagevdb = create_database(cfg, **database_kwargs)
        except ImportError as exc:
            if self._uses_sagevdb_anns_backend():
                raise RuntimeError(
                    "DIGITAL_TWIN_SAGEVDB_BACKEND is set to 'sage-anns' but isage-anns is not available. "
                    "Install with: python -m pip install -e .[vdb-anns]"
                ) from exc
            raise
        except ValueError as exc:
            raise RuntimeError(f"Failed to initialize sagevdb backend '{backend}': {exc}") from exc

        self._document_id_to_vector_id.clear()
        if self._uses_sagevdb_anns_backend():
            self._rebuild_sagevdb_anns_index()
            return

        for document in self.list_documents():
            self._add_to_sagevdb(document, rebuild_index=False)
        self._sagevdb.build_index()

    def embedding_backend_name(self) -> str:
        if self._backend != "sagevdb":
            if self._backend == "neuromem":
                return "bm25"
            return "none"
        return self._settings.sagevdb_embedding_backend.lower()

    def _initialize_neuromem(self) -> None:
        try:
            from sage.neuromem import UnifiedCollection
        except ImportError as exc:
            raise RuntimeError(
                "DIGITAL_TWIN_KNOWLEDGE_BACKEND is set to 'neuromem' but isage-neuromem is not available. "
                "Install with: python -m pip install -e ."
            ) from exc

        collection_name = f"{self._base_dir.name}-owner-materials"
        self._neuromem_collection = UnifiedCollection(collection_name)
        self._neuromem_collection.add_index("search", "bm25", {})
        for document in self.list_documents():
            self._add_to_neuromem(document)

    def _add_to_neuromem(self, document: KnowledgeDocumentRecord) -> None:
        if self._neuromem_collection is None:
            return

        self._neuromem_collection.insert(
            self._expand_retrieval_text(self._compose_retrieval_text(document)),
            {
                "document_id": document.document_id,
                "title": document.title,
                "tags": document.tags,
                "source_name": document.source_name or "",
            },
            index_names=["search"],
        )

    def _search_neuromem(
        self,
        query: str,
        top_k: int | None = None,
        *,
        visitor_profile: str | None = None,
    ) -> list[KnowledgeSearchHit]:
        if self._neuromem_collection is None or not self._documents:
            return []

        limit = top_k or self._settings.retrieval_top_k
        expanded_query = self._expand_retrieval_text(query)
        results = self._neuromem_collection.retrieve("search", expanded_query, top_k=max(limit * 5, limit + 8))
        query_tokens = self._tokenize(query)
        query_profile = _build_query_profile(query, visitor_profile=visitor_profile)

        hits: list[KnowledgeSearchHit] = []
        seen_document_ids: set[str] = set()
        for rank, result in enumerate(results, start=1):
            metadata = dict(result.get("metadata") or {})
            document_id = metadata.get("document_id")
            if not document_id:
                continue
            document = self._documents.get(str(document_id))
            if document is None:
                continue
            if document.document_id in seen_document_ids:
                continue
            seen_document_ids.add(document.document_id)
            hits.append(
                KnowledgeSearchHit(
                    document_id=document.document_id,
                    title=document.title,
                    excerpt=self._build_excerpt(document.content, query_tokens),
                    score=1.0 / float(rank),
                    tags=document.tags,
                    source_name=document.source_name,
                )
            )
        reranked = sorted(
            hits,
            key=lambda item: (
                self._score_document(self._documents[item.document_id], query_tokens, query_profile),
                item.score,
            ),
            reverse=True,
        )
        return self._finalize_hits(reranked, query_profile, limit)

    def _build_text_embedder(self, np_module):
        embedding_backend = self._settings.sagevdb_embedding_backend.lower()
        if embedding_backend == "hash":
            return HashingTextEmbedder(self._settings, np_module)
        if embedding_backend == "sentence-transformers":
            return SentenceTransformerTextEmbedder(self._settings, np_module)
        raise RuntimeError(
            "Unsupported sagevdb embedding backend. Use 'sentence-transformers' or 'hash'."
        )

    def _rebuild_sagevdb_anns_index(self) -> None:
        if self._sagevdb is None or self._np is None:
            return

        documents = self.list_documents()
        if not documents:
            return

        vectors = []
        metadata_batch = []
        for vector_id, document in enumerate(documents):
            vectors.append(self._embed_text(self._compose_retrieval_text(document)))
            metadata_batch.append(self._document_metadata(document))
            self._document_id_to_vector_id[document.document_id] = int(vector_id)

        self._sagevdb.build_index(self._np.stack(vectors), metadata=metadata_batch)

    def _add_to_sagevdb(self, document: KnowledgeDocumentRecord, rebuild_index: bool = True) -> None:
        if self._sagevdb is None:
            return

        if self._uses_sagevdb_anns_backend():
            if rebuild_index:
                self._initialize_sagevdb()
            return

        vector = self._embed_text(self._compose_retrieval_text(document))
        vector_id = self._sagevdb.add(vector.tolist())
        self._document_id_to_vector_id[document.document_id] = int(vector_id)
        self._sagevdb.set_metadata(int(vector_id), self._document_metadata(document))
        if rebuild_index:
            self._sagevdb.build_index()

    def _search_sagevdb(
        self,
        query: str,
        top_k: int | None = None,
        *,
        visitor_profile: str | None = None,
    ) -> list[KnowledgeSearchHit]:
        if self._sagevdb is None or self._np is None or not self._documents:
            return []

        limit = top_k or self._settings.retrieval_top_k
        query_vector = self._embed_text(query)
        if self._uses_sagevdb_anns_backend():
            results = self._sagevdb.search(
                query_vector,
                k=min(limit, max(self.count_documents(), 1)),
                include_metadata=True,
            )
        else:
            from sagevdb import SearchParams, search_numpy

            results = search_numpy(
                self._sagevdb,
                query_vector,
                SearchParams(k=min(limit, max(self._sagevdb.size(), 1))),
            )

        hits: list[KnowledgeSearchHit] = []
        for result in results:
            if self._uses_sagevdb_anns_backend():
                metadata = dict(getattr(result, "metadata", {}) or {})
            else:
                metadata = dict(self._sagevdb.get_metadata(int(result.id)))
            document_id = metadata.get("document_id")
            if not document_id:
                continue
            document = self._documents.get(str(document_id))
            if document is None:
                continue
            hits.append(
                KnowledgeSearchHit(
                    document_id=document.document_id,
                    title=document.title,
                    excerpt=self._build_excerpt(document.content, self._tokenize(query)),
                    score=1.0 / (1.0 + max(float(result.score), 0.0)),
                    tags=document.tags,
                    source_name=document.source_name,
                )
            )
        return self._finalize_hits(hits, _build_query_profile(query, visitor_profile=visitor_profile), limit)

    def _score_document(
        self,
        document: KnowledgeDocumentRecord,
        query_tokens: set[str],
        query_profile: "QueryProfile",
    ) -> float:
        title_tokens = self._tokenize(document.title)
        content_tokens = self._tokenize(document.content)
        tag_tokens = {tag.lower() for tag in document.tags}

        title_overlap = len(query_tokens & title_tokens)
        content_overlap = len(query_tokens & content_tokens)
        tag_overlap = len(query_tokens & tag_tokens)

        base_score = float((title_overlap * 3) + (tag_overlap * 2) + content_overlap)
        return (
            base_score
            + self._document_intent_boost(document, query_profile)
            + self._document_visitor_profile_boost(document, query_profile)
            + self._document_course_scope_boost(document, query_profile)
        )

    def _document_course_scope_boost(
        self,
        document: KnowledgeDocumentRecord,
        query_profile: "QueryProfile",
    ) -> float:
        if not query_profile.course_ids:
            return 0.0
        document_course_ids = _document_course_ids(document)
        if not document_course_ids:
            return 0.0
        if document_course_ids & query_profile.course_ids:
            return 10.0
        return -9.0

    def _document_visitor_profile_boost(
        self,
        document: KnowledgeDocumentRecord,
        query_profile: "QueryProfile",
    ) -> float:
        visitor_profile = query_profile.visitor_profile
        if not visitor_profile:
            return 0.0

        document_tags = {tag.lower() for tag in document.tags}
        prefers_teaching = bool(query_profile.document_types or "teaching" in query_profile.topic_domains)
        prefers_research = bool(query_profile.research_focus or "research" in query_profile.topic_domains)
        prefers_meeting = "meeting" in query_profile.topic_domains

        if visitor_profile == "hust_undergraduate":
            if document_tags & _TEACHING_RELATED_TAGS:
                boost = 5.0
                if document_tags & {"lecture", "tutorial", "experiment"}:
                    boost += 2.0
                return boost
            if not prefers_research and document_tags & _RESEARCH_DOCUMENT_TAGS:
                return -2.0
            return 0.0

        if visitor_profile == "paper_writing_student":
            if _is_paper_writing_document(document):
                return 8.0
            if document_tags & _TEACHING_RELATED_TAGS:
                return 3.0
            if not prefers_research and document_tags & _RESEARCH_DOCUMENT_TAGS:
                return -3.0
            return 0.0

        if visitor_profile == "lab_member":
            boost = 0.0
            if document_tags & (_RESEARCH_DOCUMENT_TAGS | _MEETING_DOCUMENT_TAGS):
                boost += 4.5
            if document_tags & {"profile", "overview"}:
                boost += 1.5
            if not prefers_teaching and not prefers_meeting and document_tags & _TEACHING_RELATED_TAGS:
                boost -= 2.5
            return boost

        if visitor_profile == "general_visitor":
            if document_tags & {"profile", "overview"}:
                return 4.0
            if not prefers_teaching and document_tags & _RESEARCH_DOCUMENT_TAGS:
                return 2.0
            if not prefers_teaching and not prefers_research and not prefers_meeting and document_tags & _TEACHING_RELATED_TAGS:
                return -2.5

        return 0.0

    def _build_excerpt(self, content: str, query_tokens: set[str]) -> str:
        compact = " ".join(content.split())
        lowercase = compact.lower()
        hit_index = min((lowercase.find(token) for token in query_tokens if token in lowercase), default=-1)
        if hit_index == -1:
            return compact[:220]
        start = max(hit_index - 60, 0)
        end = min(hit_index + 160, len(compact))
        return compact[start:end]

    def _tokenize(self, text: str) -> set[str]:
        return _tokenize_text(text)

    def _compose_retrieval_text(self, document: KnowledgeDocumentRecord) -> str:
        title = ((document.title + " ") * 3).strip()
        tags = " ".join(document.tags + document.tags)
        tag_aliases = " ".join(_expand_document_aliases(document))
        source_tokens = _normalize_retrieval_text(document.source_name or "")
        return f"{title} {tags} {tag_aliases} {source_tokens} {document.content}".strip()

    def _document_intent_boost(
        self,
        document: KnowledgeDocumentRecord,
        query_profile: "QueryProfile",
    ) -> float:
        if (
            not query_profile.document_types
            and not query_profile.ordinal_numbers
            and not query_profile.topic_domains
        ):
            return 0.0

        document_tags = {tag.lower() for tag in document.tags}
        document_types = {tag for tag in document_tags if tag in _TEACHING_DOCUMENT_TYPES}
        boost = 0.0
        if query_profile.document_types:
            if document_types & query_profile.document_types:
                boost += 6.0
            elif document_types:
                boost -= 5.0
            else:
                boost -= 2.0

        if query_profile.ordinal_numbers:
            haystacks = [document.title, document.source_name or "", document.content[:400]]
            if any(_document_mentions_ordinal(haystack, query_profile.ordinal_numbers) for haystack in haystacks):
                boost += 4.0
                if document_types & query_profile.document_types:
                    boost += 2.0
            elif query_profile.document_types or document_types:
                boost -= 2.0

        if "research" in query_profile.topic_domains:
            if document_tags & _RESEARCH_DOCUMENT_TAGS:
                boost += 8.0
            elif document_tags & _TEACHING_RELATED_TAGS:
                boost -= 8.0

        if query_profile.research_focus == "paper":
            if "paper-digest" in document_tags:
                boost += 7.0
            elif "overview" in document_tags:
                boost += 3.0
            elif "profile" in document_tags:
                boost -= 3.0
        elif query_profile.research_focus == "overview":
            if "overview" in document_tags:
                boost += 6.0
            elif "paper-digest" in document_tags:
                boost += 2.0
            elif "profile" in document_tags:
                boost += 1.0

        if "meeting" in query_profile.topic_domains:
            if document_tags & _MEETING_DOCUMENT_TAGS:
                boost += 8.0
            elif document_tags & _TEACHING_RELATED_TAGS:
                boost -= 8.0

        if "teaching" in query_profile.topic_domains:
            if document_tags & _TEACHING_RELATED_TAGS:
                boost += 3.0
            elif document_tags & _RESEARCH_DOCUMENT_TAGS:
                boost -= 2.0

        if query_profile.prefers_intro_parts and document_tags & _TEACHING_RELATED_TAGS:
            part_index = _extract_document_part_index(document)
            if part_index == 1:
                boost += 5.0
            elif part_index == 2:
                boost += 1.5
            elif part_index and part_index >= 3:
                boost -= min(4.0, float(part_index - 2) * 1.5)

        return boost

    def _finalize_hits(
        self,
        hits: list[KnowledgeSearchHit],
        query_profile: "QueryProfile",
        limit: int,
    ) -> list[KnowledgeSearchHit]:
        if not hits:
            return []
        if not query_profile.document_types and not query_profile.topic_domains:
            return _dedupe_hits_by_source_group(hits, limit)

        aligned_hits = [
            hit
            for hit in hits
            if self._document_intent_boost(self._documents[hit.document_id], query_profile) >= 0.0
        ]
        if query_profile.ordinal_numbers and "teaching" in query_profile.topic_domains:
            ordinal_hits = [
                hit
                for hit in aligned_hits
                if _hit_matches_ordinal_query(
                    hit,
                    self._documents[hit.document_id],
                    query_profile.ordinal_numbers,
                    query_profile.document_types,
                )
            ]
            if ordinal_hits:
                aligned_hits = ordinal_hits
        if query_profile.course_ids and "teaching" in query_profile.topic_domains:
            course_hits = [
                hit
                for hit in aligned_hits
                if _document_course_ids(self._documents[hit.document_id]) & query_profile.course_ids
            ]
            if course_hits:
                aligned_hits = course_hits
        if query_profile.research_focus == "paper":
            paper_focused_hits = [
                hit
                for hit in aligned_hits
                if {tag.lower() for tag in hit.tags} & {"paper-digest", "overview", "publication"}
            ]
            if paper_focused_hits:
                aligned_hits = paper_focused_hits
            if query_profile.named_entities:
                entity_matched_hits = [
                    hit
                    for hit in aligned_hits
                    if _hit_matches_named_entities(hit, self._documents[hit.document_id], query_profile.named_entities)
                ]
                if entity_matched_hits:
                    aligned_hits = entity_matched_hits
        if aligned_hits:
            return _dedupe_hits_by_source_group(aligned_hits, limit)
        return _dedupe_hits_by_source_group(hits, limit)

    def _expand_retrieval_text(self, text: str) -> str:
        tokens = sorted(self._tokenize(text))
        if not tokens:
            return text
        return f"{text} {' '.join(tokens)}".strip()

    def _embed_text(self, text: str):
        if self._np is None or self._text_embedder is None:
            raise RuntimeError("sagevdb backend is not initialized")
        return self._text_embedder.encode(text)


def _tokenize_text(text: str) -> set[str]:
    tokens: set[str] = {token.lower() for token in re.findall(r"[A-Za-z0-9_]+", text) if len(token) > 1}
    for span in re.findall(r"[\u4e00-\u9fff]+", text):
        if not span:
            continue
        tokens.add(span)
        if len(span) == 1:
            continue
        tokens.update(span)
        for width in (2, 3):
            if len(span) < width:
                continue
            for index in range(len(span) - width + 1):
                tokens.add(span[index : index + width])
    return tokens


@dataclass(frozen=True)
class QueryProfile:
    document_types: frozenset[str]
    ordinal_numbers: frozenset[str]
    topic_domains: frozenset[str]
    course_ids: frozenset[str] = frozenset()
    research_focus: str | None = None
    prefers_intro_parts: bool = False
    named_entities: frozenset[str] = frozenset()
    visitor_profile: str | None = None


_TEACHING_DOCUMENT_TYPES = {"tutorial", "lecture", "experiment"}
_TEACHING_RELATED_TAGS = {"teaching", "courseware", "tutorial", "lecture", "experiment", "resources", "pdf"}
_RESEARCH_DOCUMENT_TAGS = {"research", "publication", "paper-digest", "overview", "profile"}
_MEETING_DOCUMENT_TAGS = {"meeting", "preparation", "policy", "qa", "course"}
_COURSE_ALIAS_MAP = {
    "llm-inference": (
        "大模型推理基础设施",
        "大模型推理",
        "推理基础设施",
        "推理系统",
        "llm inference",
        "inference engines",
        "inference infrastructure",
        "kv cache",
        "prefill",
        "decode",
    ),
    "paper-writing": (
        "研究生论文写作",
        "论文写作课程",
        "毕业论文",
        "发表高水平论文",
        "paper writing",
        "thesis writing",
    ),
}
_TEACHING_ALIAS_MAP = {
    "tutorial": ("tutorial", "教程", "习题", "练习", "workshop"),
    "lecture": ("lecture", "slides", "讲义", "课程讲解", "课件"),
    "experiment": ("experiment", "lab", "实验", "project", "项目"),
    "pdf": ("pdf", "课件正文", "讲义正文"),
    "research": ("research", "研究", "研究方向", "研究主题"),
    "publication": ("publication", "paper", "论文", "成果"),
    "paper-digest": ("paper digest", "论文提炼", "摘要"),
    "overview": ("overview", "研究主线", "研究总览"),
    "profile": ("profile", "主页资料", "个人简介"),
    "meeting": ("meeting", "预约", "office hour", "沟通"),
    "preparation": ("preparation", "准备", "提前准备", "材料"),
    "policy": ("policy", "建议", "要求", "规范"),
    "qa": ("qa", "答疑", "提问", "问题"),
    "course:llm-inference": ("大模型推理基础设施", "大模型推理", "推理系统", "kv cache", "prefill", "decode"),
    "course:paper-writing": ("研究生论文写作", "论文写作", "毕业论文", "发表高水平论文"),
    "identity:teacher": ("主课老师", "教师", "课程"),
    "identity:pi": ("课题组", "负责人", "导师", "PI"),
    "domain:teaching": ("教学", "课程", "研究生课程"),
    "domain:research-group": ("课题组", "研究团队", "组内"),
    "material:lecture": ("lecture", "讲义", "第几讲"),
    "material:tutorial": ("tutorial", "教程", "习题"),
    "material:experiment": ("experiment", "实验", "项目"),
    "material:pdf": ("pdf", "课件正文"),
}


def _build_query_profile(query: str, visitor_profile: str | None = None) -> QueryProfile:
    lowered = query.lower()
    document_types: set[str] = set()
    topic_domains: set[str] = set()
    course_ids = set(_infer_course_ids(query))
    research_focus: str | None = None
    named_entities = _extract_named_entities(query)
    if "tutorial" in lowered or "教程" in query or "习题" in query or "练习" in query:
        document_types.add("tutorial")
        topic_domains.add("teaching")
    if "lecture" in lowered or "讲义" in query or "课件" in query or re.search(r"第\s*\d+\s*讲", query):
        document_types.add("lecture")
        topic_domains.add("teaching")
    if "experiment" in lowered or "lab" in lowered or "实验" in query or "project" in lowered or "项目" in query:
        document_types.add("experiment")
        topic_domains.add("teaching")

    if course_ids:
        topic_domains.add("teaching")

    research_markers = (
        "研究主线",
        "研究方向",
        "主要研究",
        "研究什么",
        "做什么研究",
        "研究板块",
        "科研",
        "研究",
        "flowrag",
        "libamm",
        "publication",
        "publications",
        "research",
    )
    if any(marker in lowered for marker in research_markers) or any(marker in query for marker in research_markers):
        topic_domains.add("research")
        if any(marker in query for marker in ("研究主线", "研究方向", "主要研究", "研究什么", "研究板块")):
            research_focus = "overview"
        elif "论文" in query or _has_named_research_entity(query):
            research_focus = "paper"
    elif (
        "teaching" not in topic_domains
        and re.search(r"[A-Za-z][A-Za-z0-9_-]{3,}", query)
        and any(phrase in query for phrase in ("做什么", "是什么", "主要做什么"))
    ):
        topic_domains.add("research")
        research_focus = "paper"

    meeting_markers = (
        "meeting",
        "office hour",
        "office-hour",
        "agenda",
        "blocker",
        "预约",
        "约时间",
        "联系老师",
        "联系导师",
        "准备什么",
        "提前准备",
    )
    if any(marker in lowered for marker in meeting_markers) or any(marker in query for marker in meeting_markers):
        topic_domains.add("meeting")
    elif "准备" in query and any(role in query for role in ("老师", "导师")):
        topic_domains.add("meeting")

    prefers_intro_parts = "teaching" in topic_domains and any(
        phrase in query for phrase in ("讲什么", "讲了什么", "主要内容", "内容是什么", "介绍什么")
    )

    return QueryProfile(
        document_types=frozenset(document_types),
        ordinal_numbers=frozenset(re.findall(r"\d+", query)),
        topic_domains=frozenset(topic_domains),
        course_ids=frozenset(course_ids),
        research_focus=research_focus,
        prefers_intro_parts=prefers_intro_parts,
        named_entities=frozenset(named_entities),
        visitor_profile=visitor_profile,
    )


def _infer_course_ids(text: str) -> tuple[str, ...]:
    lowered = text.lower()
    course_ids: list[str] = []
    for course_id, aliases in _COURSE_ALIAS_MAP.items():
        if any(alias.lower() in lowered for alias in aliases):
            course_ids.append(course_id)
    return tuple(dict.fromkeys(course_ids))


def _document_course_ids(document: KnowledgeDocumentRecord) -> frozenset[str]:
    course_ids = {
        tag.split(":", 1)[1].lower()
        for tag in document.tags
        if tag.lower().startswith("course:") and ":" in tag
    }
    haystack = f"{document.title} {document.source_name or ''}".lower()
    for course_id, aliases in _COURSE_ALIAS_MAP.items():
        if any(alias.lower() in haystack for alias in aliases):
            course_ids.add(course_id)
    if "intro-to-llm-inference-engines" in haystack:
        course_ids.add("llm-inference")
    if "graduate-paper-writing-course" in haystack:
        course_ids.add("paper-writing")
    return frozenset(course_ids)


def _is_paper_writing_document(document: KnowledgeDocumentRecord) -> bool:
    document_tags = {tag.lower() for tag in document.tags}
    haystacks = (document.title, document.source_name or "", document.content[:400])
    matches_topic = any("论文写作" in haystack or "paper-writing" in haystack.lower() for haystack in haystacks)
    if not matches_topic:
        return False
    return bool(document_tags & _TEACHING_RELATED_TAGS) or "graduate-paper-writing-course" in (document.source_name or "")


def _has_named_research_entity(query: str) -> bool:
    return bool(re.search(r"[A-Za-z][A-Za-z0-9_-]{3,}", query))


def _extract_named_entities(query: str) -> tuple[str, ...]:
    entities: list[str] = []
    for match in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", query):
        if match.islower():
            continue
        entities.append(match.lower())
    return tuple(dict.fromkeys(entities))


def _expand_document_aliases(document: KnowledgeDocumentRecord) -> tuple[str, ...]:
    aliases: list[str] = []
    for tag in document.tags:
        aliases.extend(_TEACHING_ALIAS_MAP.get(tag.lower(), ()))
    return tuple(dict.fromkeys(aliases))


def _normalize_retrieval_text(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]+", " ", text).strip()


def _document_mentions_ordinal(text: str, ordinal_numbers: frozenset[str]) -> bool:
    if not text or not ordinal_numbers:
        return False

    normalized = text.lower()
    for raw_number in ordinal_numbers:
        number = str(int(raw_number))
        variants = {
            number,
            f"{int(raw_number):02d}",
            f"第 {number} 讲",
            f"第{number}讲",
            f"tutorial {number}",
            f"tutorial {int(raw_number):02d}",
            f"实验 {number}",
            f"实验{number}",
            f"experiment {number}",
        }
        if any(variant in normalized for variant in variants):
            return True
    return False


def _extract_document_part_index(document: KnowledgeDocumentRecord) -> int | None:
    for text in (document.title, document.source_name or ""):
        if not text:
            continue
        for pattern in (r"第\s*(\d+)\s*部分", r"part-(\d+)"):
            match = re.search(pattern, text, re.IGNORECASE)
            if match is not None:
                return int(match.group(1))
    return None


def _hit_matches_ordinal_query(
    hit: KnowledgeSearchHit,
    document: KnowledgeDocumentRecord,
    ordinal_numbers: frozenset[str],
    document_types: frozenset[str],
) -> bool:
    haystacks = [(hit.title or "").lower(), (hit.source_name or "").lower()]
    for raw_number in ordinal_numbers:
        number = int(raw_number)
        padded = f"{number:02d}"
        patterns: list[str] = []
        if not document_types or "lecture" in document_types:
            patterns.extend([
                rf"第\s*0?{number}\s*讲",
                rf"lecture[-_\s]?0?{number}\b",
                rf"第{padded}讲",
            ])
        if not document_types or "tutorial" in document_types:
            patterns.extend([
                rf"tutorial[-_\s]?0?{number}\b",
                rf"tutorial\s*{padded}\b",
            ])
        if not document_types or "experiment" in document_types:
            patterns.extend([
                rf"实验\s*0?{number}\b",
                rf"experiment[-_\s]?0?{number}\b",
            ])
        if any(re.search(pattern, haystack, re.IGNORECASE) for pattern in patterns for haystack in haystacks):
            return True
    return False


def _hit_matches_named_entities(
    hit: KnowledgeSearchHit,
    document: KnowledgeDocumentRecord,
    named_entities: frozenset[str],
) -> bool:
    if not named_entities:
        return False
    haystacks = [hit.title.lower(), (hit.source_name or "").lower(), document.content[:500].lower()]
    return any(any(entity in haystack for haystack in haystacks) for entity in named_entities)


def _dedupe_hits_by_source_group(hits: list[KnowledgeSearchHit], limit: int) -> list[KnowledgeSearchHit]:
    deduped_hits: list[KnowledgeSearchHit] = []
    seen_source_groups: set[str] = set()
    for hit in hits:
        source_group = _canonical_hit_group(hit)
        if source_group in seen_source_groups:
            continue
        seen_source_groups.add(source_group)
        deduped_hits.append(hit)
        if len(deduped_hits) >= limit:
            break
    return deduped_hits


def _canonical_hit_group(hit: KnowledgeSearchHit) -> str:
    source_group = _canonical_source_group(hit.source_name, hit.document_id)
    if source_group.startswith("knowledge-gap:"):
        normalized_title = re.sub(r"\s+", " ", hit.title.strip().lower())
        if normalized_title:
            return f"knowledge-gap-title:{normalized_title}"
    return source_group


def _canonical_source_group(source_name: str | None, fallback_id: str) -> str:
    if not source_name:
        return fallback_id
    return re.sub(r"::part-\d+$", "", source_name)