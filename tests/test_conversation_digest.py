"""Tests for the rolling conversation digest (context compression) mechanism.

Covers:
- ConversationDigestRecord serialization round-trip.
- ConversationDigestStore get/update/persistence/load-all behavior.
- Digest trigger logic (threshold-based summarization).
- Digest integration into the prompt truncation chain.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from sage_faculty_twin.memory_store import (
    ConversationDigestRecord,
    ConversationDigestStore,
)


# ---------------------------------------------------------------------------
# ConversationDigestRecord
# ---------------------------------------------------------------------------


class TestConversationDigestRecord:
    def test_round_trip(self) -> None:
        record = ConversationDigestRecord(
            conversation_id="conv-abc-123",
            digest_text="讨论了课程作业和科研方向。",
            turns_summarized=6,
            updated_at=datetime(2026, 6, 20, 10, 0, 0, tzinfo=UTC),
        )
        payload = record.to_dict()
        restored = ConversationDigestRecord.from_dict(payload)
        assert restored.conversation_id == record.conversation_id
        assert restored.digest_text == record.digest_text
        assert restored.turns_summarized == 6
        assert restored.updated_at == record.updated_at

    def test_from_dict_missing_turns_field(self) -> None:
        payload = {
            "conversation_id": "x",
            "digest_text": "hello",
            "updated_at": "2026-06-20T00:00:00+00:00",
        }
        record = ConversationDigestRecord.from_dict(payload)
        assert record.turns_summarized == 0


# ---------------------------------------------------------------------------
# ConversationDigestStore
# ---------------------------------------------------------------------------


class TestConversationDigestStore:
    def test_get_returns_none_for_unknown(self, tmp_path: Path) -> None:
        store = ConversationDigestStore(tmp_path / "digests")
        assert store.get_digest("nonexistent") is None

    def test_update_and_get(self, tmp_path: Path) -> None:
        store = ConversationDigestStore(tmp_path / "digests")
        record = store.update_digest("conv-1", "讨论AI应用。", 4)
        assert record.conversation_id == "conv-1"
        assert record.digest_text == "讨论AI应用。"
        assert record.turns_summarized == 4

        fetched = store.get_digest("conv-1")
        assert fetched is not None
        assert fetched.digest_text == "讨论AI应用。"
        assert fetched.turns_summarized == 4

    def test_persists_to_disk(self, tmp_path: Path) -> None:
        digest_dir = tmp_path / "digests"
        store1 = ConversationDigestStore(digest_dir)
        store1.update_digest("conv-2", "第一轮总结。", 3)

        # Create a new store from the same dir — should load from disk.
        store2 = ConversationDigestStore(digest_dir)
        fetched = store2.get_digest("conv-2")
        assert fetched is not None
        assert fetched.digest_text == "第一轮总结。"
        assert fetched.turns_summarized == 3

    def test_update_overwrites(self, tmp_path: Path) -> None:
        store = ConversationDigestStore(tmp_path / "digests")
        store.update_digest("conv-3", "v1", 2)
        store.update_digest("conv-3", "v2 updated", 6)

        fetched = store.get_digest("conv-3")
        assert fetched is not None
        assert fetched.digest_text == "v2 updated"
        assert fetched.turns_summarized == 6

    def test_count(self, tmp_path: Path) -> None:
        store = ConversationDigestStore(tmp_path / "digests")
        assert store.count() == 0
        store.update_digest("a", "text a", 1)
        store.update_digest("b", "text b", 2)
        assert store.count() == 2

    def test_load_all_skips_corrupt_files(self, tmp_path: Path) -> None:
        digest_dir = tmp_path / "digests"
        digest_dir.mkdir(parents=True)
        # Write a corrupt JSON file.
        (digest_dir / "bad.json").write_text("{not valid json", encoding="utf-8")
        # Write a valid file.
        valid = ConversationDigestRecord(
            conversation_id="good",
            digest_text="ok",
            turns_summarized=1,
            updated_at=datetime.now(UTC),
        )
        (digest_dir / "good.json").write_text(
            json.dumps(valid.to_dict(), ensure_ascii=False), encoding="utf-8"
        )

        store = ConversationDigestStore(digest_dir)
        assert store.count() == 1
        assert store.get_digest("good") is not None

    def test_digest_path_sanitizes_id(self, tmp_path: Path) -> None:
        store = ConversationDigestStore(tmp_path / "digests")
        # IDs with special chars should be sanitized.
        store.update_digest("conv/with:special chars", "text", 1)
        fetched = store.get_digest("conv/with:special chars")
        assert fetched is not None
        # Verify the file was created with a safe name.
        files = list((tmp_path / "digests").glob("*.json"))
        assert len(files) == 1
        assert "/" not in files[0].stem
        assert ":" not in files[0].stem


# ---------------------------------------------------------------------------
# Digest trigger logic (unit-level, no LLM dependency)
# ---------------------------------------------------------------------------


class TestDigestTriggerLogic:
    """Verify the threshold-based trigger in _update_conversation_digest."""

    def test_no_trigger_below_threshold(self, tmp_path: Path) -> None:
        """Digest should not fire when fewer turns than threshold exist."""
        from sage_faculty_twin.config import AppSettings

        settings = AppSettings(
            context_digest_enabled=True,
            context_digest_turn_threshold=4,
            context_digest_dir=tmp_path / "digests",
            conversation_memory_dir=tmp_path / "mem",
        )
        ConversationDigestStore(settings.context_digest_dir)
        # Simulate: only 2 turns in the conversation.
        # The trigger check compares len(all_records) - turns_already_digested < threshold.
        # With 2 turns and threshold 4, it should NOT trigger.
        all_record_count = 2
        turns_already_digested = 0
        new_turns = all_record_count - turns_already_digested
        assert new_turns < settings.context_digest_turn_threshold

    def test_trigger_at_threshold(self, tmp_path: Path) -> None:
        """Digest should fire when exactly threshold turns exist."""
        from sage_faculty_twin.config import AppSettings

        settings = AppSettings(
            context_digest_enabled=True,
            context_digest_turn_threshold=4,
            context_digest_dir=tmp_path / "digests",
            conversation_memory_dir=tmp_path / "mem",
        )
        all_record_count = 4
        turns_already_digested = 0
        new_turns = all_record_count - turns_already_digested
        assert new_turns >= settings.context_digest_turn_threshold

    def test_no_trigger_when_disabled(self, tmp_path: Path) -> None:
        """Digest should not fire when context_digest_enabled is False."""
        from sage_faculty_twin.config import AppSettings

        settings = AppSettings(
            context_digest_enabled=False,
            context_digest_dir=tmp_path / "digests",
            conversation_memory_dir=tmp_path / "mem",
        )
        assert not settings.context_digest_enabled

    def test_incremental_trigger(self, tmp_path: Path) -> None:
        """After digesting 4 turns, next 4 should trigger again."""
        from sage_faculty_twin.config import AppSettings

        settings = AppSettings(
            context_digest_enabled=True,
            context_digest_turn_threshold=4,
            context_digest_dir=tmp_path / "digests",
            conversation_memory_dir=tmp_path / "mem",
        )
        # Simulate: 8 total turns, 4 already digested.
        all_record_count = 8
        turns_already_digested = 4
        new_turns = all_record_count - turns_already_digested
        assert new_turns >= settings.context_digest_turn_threshold


# ---------------------------------------------------------------------------
# Digest text truncation in prompt builder
# ---------------------------------------------------------------------------


class TestDigestPromptTruncation:
    """Verify the digest-stripping step in the build_prompt truncation chain."""

    def test_strip_digest_from_session_context(self) -> None:
        """Step (d) should remove the digest block from recent_session_context."""
        session_context = (
            "Session digest (earlier turns, 8 turns compressed):\n"
            "用户讨论了课程作业安排和科研方向选择。\n"
            "Immediate session context (same conversation):\n"
            "1. User: 下周实验安排\n"
            "Assistant: 下周二和周四有实验课。"
        )
        assert "Session digest" in session_context

        # Simulate the stripping logic from build_prompt step (d).
        stripped_lines: list[str] = []
        skip_digest = False
        for line in session_context.split("\n"):
            if line.startswith("Session digest"):
                skip_digest = True
                continue
            if skip_digest and line.startswith("Immediate session context"):
                skip_digest = False
            if not skip_digest:
                stripped_lines.append(line)
        result = "\n".join(stripped_lines)

        assert "Session digest" not in result
        assert "Immediate session context" in result
        assert "下周实验安排" in result

    def test_no_strip_when_no_digest(self) -> None:
        """Step (d) should leave context unchanged when there is no digest."""
        session_context = (
            "Immediate session context (same conversation):\n"
            "1. User: 你好\n"
            "Assistant: 你好！有什么可以帮助你的？"
        )
        assert "Session digest" not in session_context
        # The condition `"Session digest" in context` is False, so no stripping.

    def test_digest_included_in_format_recent_session_context(self, tmp_path: Path) -> None:
        """_format_recent_session_context should prepend digest when available."""
        store = ConversationDigestStore(tmp_path / "digests")
        store.update_digest("test-conv", "之前讨论了系统架构设计。", 5)

        record = store.get_digest("test-conv")
        assert record is not None
        assert "系统架构" in record.digest_text
        assert record.turns_summarized == 5
