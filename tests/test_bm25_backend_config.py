from __future__ import annotations

from sage_faculty_twin.config import AppSettings
from sage_faculty_twin.memory_store import NeuroMemConversationStore


def test_faiss_default_index_config_uses_cosine_metric(tmp_path) -> None:
    settings = AppSettings(
        conversation_memory_dir=tmp_path / "conversation-memory",
        conversation_memory_index_type="faiss",
    )
    store = NeuroMemConversationStore(settings)
    config = store._default_collection_index_config("faiss")
    assert config.get("metric") == "cosine"
