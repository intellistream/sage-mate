import math
from pathlib import Path
from types import SimpleNamespace

import pytest

from sage_faculty_twin.config import AppSettings
from sage_faculty_twin.knowledge_base import LocalKnowledgeStore
from sage_faculty_twin.models import KnowledgeDocumentCreate, KnowledgeSearchHit


class _FakeNeuromemCollection:
    def __init__(self, document_id: str) -> None:
        self._document_id = document_id

    def retrieve(self, *_args, **_kwargs):
        return [{"metadata": {"document_id": self._document_id}}]


class _FakeSageVDB:
    def __init__(self, document_id: str) -> None:
        self._document_id = document_id

    def search(self, *_args, **_kwargs):
        return [SimpleNamespace(metadata={"document_id": self._document_id})]


def test_link_expansion_is_opt_in(tmp_path: Path) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path, knowledge_backend="local")
    store = LocalKnowledgeStore(settings)

    assert settings.knowledge_link_expansion_enabled is False
    assert store._link_expansion_enabled is False


def test_link_expansion_settings_load_from_deployment_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DIGITAL_TWIN_KNOWLEDGE_LINK_EXPANSION_ENABLED", "true")
    monkeypatch.setenv("DIGITAL_TWIN_KNOWLEDGE_LINK_EXPANSION_DECAY", "0.25")
    monkeypatch.setenv("DIGITAL_TWIN_KNOWLEDGE_LINK_EXPANSION_MAX_DOCUMENTS", "3")

    settings = AppSettings(knowledge_base_dir=tmp_path, knowledge_backend="local")

    assert settings.knowledge_link_expansion_enabled is True
    assert settings.knowledge_link_expansion_decay == 0.25
    assert settings.knowledge_link_expansion_max_documents == 3


def test_search_cache_separates_link_expansion_configurations(tmp_path: Path) -> None:
    settings = AppSettings(
        knowledge_base_dir=tmp_path,
        knowledge_backend="local",
        knowledge_search_cache_ttl_seconds=300,
        knowledge_search_cache_max_entries=8,
        knowledge_link_expansion_enabled=True,
        knowledge_link_expansion_decay=0.25,
    )
    store = LocalKnowledgeStore(settings)
    source = store.add_document(
        KnowledgeDocumentCreate(
            title="Quasar retrieval note",
            content="quasar retrieval",
            tags=[],
            source_name="source",
        )
    )
    linked = store.add_document(
        KnowledgeDocumentCreate(
            title="Unrelated linked note",
            content="no lexical overlap",
            tags=[],
            source_name="linked",
        )
    )
    store._link_graph = {source.document_id: [linked.document_id]}

    store._link_expansion_enabled = False
    baseline = store.search("quasar", top_k=2)
    store._link_expansion_enabled = True
    expanded = store.search("quasar", top_k=2)
    settings.knowledge_link_expansion_max_documents = 0
    disabled_by_limit = store.search("quasar", top_k=2)

    assert linked.document_id not in {hit.document_id for hit in baseline}
    assert linked.document_id in {hit.document_id for hit in expanded}
    assert linked.document_id not in {hit.document_id for hit in disabled_by_limit}
    source_hit = next(hit for hit in expanded if hit.document_id == source.document_id)
    linked_hit = next(hit for hit in expanded if hit.document_id == linked.document_id)
    assert math.isclose(linked_hit.score, source_hit.score * 0.25)


def test_link_expansion_can_be_disabled_by_setting_or_zero_decay(tmp_path: Path) -> None:
    settings = AppSettings(
        knowledge_base_dir=tmp_path,
        knowledge_backend="local",
        knowledge_link_expansion_enabled=False,
        knowledge_link_expansion_decay=0.0,
    )
    store = LocalKnowledgeStore(settings)
    source = store.add_document(
        KnowledgeDocumentCreate(
            title="Quasar retrieval note",
            content="quasar retrieval",
            tags=[],
            source_name="source",
        )
    )
    linked = store.add_document(
        KnowledgeDocumentCreate(
            title="Unrelated linked note",
            content="no lexical overlap",
            tags=[],
            source_name="linked",
        )
    )
    store._link_graph = {source.document_id: [linked.document_id]}

    assert store._link_expansion_enabled is False
    disabled = store.search("quasar", top_k=2)
    store._link_expansion_enabled = True
    zero_decay = store.search("quasar", top_k=2)

    assert linked.document_id not in {hit.document_id for hit in disabled}
    assert linked.document_id not in {hit.document_id for hit in zero_decay}


def test_link_expansion_does_not_bypass_document_visibility(tmp_path: Path) -> None:
    settings = AppSettings(
        knowledge_base_dir=tmp_path,
        knowledge_backend="local",
        knowledge_link_expansion_enabled=True,
        knowledge_link_expansion_decay=0.5,
    )
    store = LocalKnowledgeStore(settings)
    source = store.add_document(
        KnowledgeDocumentCreate(
            title="Public quasar note",
            content="quasar retrieval",
            tags=[],
            source_name="source",
        )
    )
    private = store.add_document(
        KnowledgeDocumentCreate(
            title="Private linked note",
            content="no lexical overlap",
            tags=["audience:private"],
            source_name="private",
            metadata={"audience": "private"},
        )
    )
    store._link_graph = {source.document_id: [private.document_id]}

    hits = store.search("quasar", top_k=2, visitor_profile="general_visitor")

    assert private.document_id not in {hit.document_id for hit in hits}


@pytest.mark.parametrize("backend", ["local", "neuromem", "sagevdb"])
def test_all_backends_apply_the_same_link_expansion_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    backend: str,
) -> None:
    settings = AppSettings(
        knowledge_base_dir=tmp_path,
        knowledge_backend="local",
        knowledge_search_cache_ttl_seconds=0,
        knowledge_link_expansion_enabled=True,
        knowledge_link_expansion_decay=0.5,
    )
    store = LocalKnowledgeStore(settings)
    source = store.add_document(
        KnowledgeDocumentCreate(
            title="Quasar retrieval note",
            content="quasar retrieval",
            tags=[],
            source_name="source",
        )
    )
    linked = store.add_document(
        KnowledgeDocumentCreate(
            title="Unrelated linked note",
            content="no lexical overlap",
            tags=[],
            source_name="linked",
        )
    )
    store._link_graph = {source.document_id: [linked.document_id]}
    store._backend = backend

    if backend == "neuromem":
        store._neuromem_collection = _FakeNeuromemCollection(source.document_id)
        store._neuromem_index_type = "segment"
    elif backend == "sagevdb":
        store._sagevdb = _FakeSageVDB(source.document_id)
        store._np = object()
        monkeypatch.setattr(store, "_uses_sagevdb_anns_backend", lambda: True)
        monkeypatch.setattr(store, "_embed_text", lambda _text: object())

    hits = store.search("quasar", top_k=2)

    assert [hit.document_id for hit in hits] == [source.document_id, linked.document_id]


def test_link_graph_phase_flags_drive_runtime_and_ablation_graphs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path, knowledge_backend="local")
    store = LocalKnowledgeStore(settings)
    monkeypatch.setattr(store, "_MANUAL_CROSS_REFS", {})
    monkeypatch.setattr(store, "_CONCEPT_TO_WIKI", {"quasar": ["wiki:target"]})

    wiki = store.add_document(
        KnowledgeDocumentCreate(
            title="Target wiki page",
            content="target",
            tags=[],
            source_name="wiki:target",
        )
    )
    explicit = store.add_document(
        KnowledgeDocumentCreate(
            title="Explicit source",
            content="explicit",
            tags=[],
            source_name="explicit",
            metadata={"linked_source_names": "wiki:target"},
        )
    )
    tagged_a = store.add_document(
        KnowledgeDocumentCreate(
            title="Tagged source A",
            content="tagged a",
            tags=["RAG"],
            source_name="tagged-a",
        )
    )
    tagged_b = store.add_document(
        KnowledgeDocumentCreate(
            title="Tagged source B",
            content="tagged b",
            tags=[" rag "],
            source_name="tagged-b",
        )
    )
    concept = store.add_document(
        KnowledgeDocumentCreate(
            title="Quasar deployment note",
            content="concept",
            tags=[],
            source_name="concept",
        )
    )

    explicit_graph = store.build_link_graph(
        include_manual=False,
        include_tags=False,
        include_concepts=False,
    )
    tag_graph = store.build_link_graph(
        include_explicit=False,
        include_manual=False,
        include_tags=True,
        include_concepts=False,
    )
    concept_graph = store.build_link_graph(
        include_explicit=False,
        include_manual=False,
        include_tags=False,
        include_concepts=True,
    )
    combined_graph = store.build_link_graph()

    assert wiki.document_id in explicit_graph[explicit.document_id]
    assert tagged_b.document_id in tag_graph[tagged_a.document_id]
    assert wiki.document_id in concept_graph[concept.document_id]
    assert combined_graph == store._link_graph


def test_concept_bridges_take_priority_over_tag_edges_at_degree_cap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path, knowledge_backend="local")
    store = LocalKnowledgeStore(settings)
    monkeypatch.setattr(store, "_MANUAL_CROSS_REFS", {})
    monkeypatch.setattr(store, "_CONCEPT_TO_WIKI", {"quasar": ["wiki:target"]})

    wiki = store.add_document(
        KnowledgeDocumentCreate(
            title="Target wiki page",
            content="target",
            tags=[],
            source_name="wiki:target",
        )
    )
    source = store.add_document(
        KnowledgeDocumentCreate(
            title="Quasar source",
            content="source",
            tags=["rag"],
            source_name="source",
        )
    )
    for index in range(12):
        store.add_document(
            KnowledgeDocumentCreate(
                title=f"Tag neighbor {index}",
                content="neighbor",
                tags=["rag"],
                source_name=f"neighbor-{index}",
            )
        )

    graph = store.build_link_graph(
        include_explicit=False,
        include_manual=False,
        include_tags=True,
        include_concepts=True,
    )

    assert len(graph[source.document_id]) == 12
    assert graph[source.document_id][0] == wiki.document_id


def test_link_candidates_accumulate_only_top_k_source_support(tmp_path: Path) -> None:
    settings = AppSettings(knowledge_base_dir=tmp_path, knowledge_backend="local")
    store = LocalKnowledgeStore(settings)
    source_a = store.add_document(
        KnowledgeDocumentCreate(
            title="Source A",
            content="source a",
            tags=[],
            source_name="source-a",
        )
    )
    source_b = store.add_document(
        KnowledgeDocumentCreate(
            title="Source B",
            content="source b",
            tags=[],
            source_name="source-b",
        )
    )
    outside_top_k = store.add_document(
        KnowledgeDocumentCreate(
            title="Outside top k",
            content="outside",
            tags=[],
            source_name="outside",
        )
    )
    shared_target = store.add_document(
        KnowledgeDocumentCreate(
            title="Shared target",
            content="shared",
            tags=[],
            source_name="shared",
        )
    )
    excluded_target = store.add_document(
        KnowledgeDocumentCreate(
            title="Excluded target",
            content="excluded",
            tags=[],
            source_name="excluded",
        )
    )
    store._link_graph = {
        source_a.document_id: [shared_target.document_id],
        source_b.document_id: [shared_target.document_id],
        outside_top_k.document_id: [excluded_target.document_id],
    }

    def hit(document, score: float) -> KnowledgeSearchHit:
        return KnowledgeSearchHit(
            document_id=document.document_id,
            title=document.title,
            excerpt=document.content,
            score=score,
            tags=document.tags,
            source_name=document.source_name,
            metadata=document.metadata,
        )

    expanded = store._expand_hits_with_links(
        [hit(source_a, 4.0), hit(source_b, 2.0), hit(outside_top_k, 100.0)],
        {"query"},
        SimpleNamespace(visitor_profile=None, admin_role=None),
        max_expansion=8,
        decay=0.5,
        source_limit=2,
    )

    by_id = {item.document_id: item for item in expanded}
    assert by_id[shared_target.document_id].score == 3.0
    assert excluded_target.document_id not in by_id


def test_link_expansion_can_promote_a_document_below_visible_first_stage_top_k(
    tmp_path: Path,
) -> None:
    settings = AppSettings(
        knowledge_base_dir=tmp_path,
        knowledge_backend="local",
        knowledge_link_expansion_enabled=True,
        knowledge_link_expansion_decay=0.5,
    )
    store = LocalKnowledgeStore(settings)
    source = store.add_document(
        KnowledgeDocumentCreate(
            title="Source",
            content="source",
            tags=[],
            source_name="source",
        )
    )
    filler = store.add_document(
        KnowledgeDocumentCreate(
            title="Filler",
            content="filler",
            tags=[],
            source_name="filler",
        )
    )
    target = store.add_document(
        KnowledgeDocumentCreate(
            title="Target",
            content="target",
            tags=[],
            source_name="target",
        )
    )
    store._link_graph = {source.document_id: [target.document_id]}

    def hit(document, score: float) -> KnowledgeSearchHit:
        return KnowledgeSearchHit(
            document_id=document.document_id,
            title=document.title,
            excerpt=document.content,
            score=score,
            tags=document.tags,
            source_name=document.source_name,
            metadata=document.metadata,
        )

    finalized = store._expand_and_finalize_hits(
        [hit(source, 20.0), hit(filler, 9.0), hit(target, 1.0)],
        {"query"},
        SimpleNamespace(
            visitor_profile=None,
            admin_role=None,
            document_types=frozenset(),
            topic_domains=frozenset(),
        ),
        2,
    )

    assert [item.document_id for item in finalized] == [source.document_id, target.document_id]
