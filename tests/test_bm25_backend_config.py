from __future__ import annotations

from sage_faculty_twin.config import AppSettings
from sage_faculty_twin.memory_store import NeuroMemConversationStore


def test_bm25_default_index_config_pins_numpy_backend(tmp_path) -> None:
    settings = AppSettings(
        conversation_memory_dir=tmp_path / "conversation-memory",
        conversation_memory_index_type="bm25",
    )
    store = NeuroMemConversationStore(settings)
    config = store._default_collection_index_config("bm25")
    assert config.get("backend") == "numpy"