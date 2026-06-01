from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from sage_faculty_twin.config import AppSettings
from sage_faculty_twin.memory_store import (
    ConversationMemoryRecord,
    NeuroMemConversationStore,
    ProfileMemoryRecord,
)
from sage_faculty_twin.models import ChatRequest


def test_store_persists_neuromem_collections_without_records_or_profiles_dirs(
    tmp_path: Path,
) -> None:
    settings = AppSettings(
        knowledge_base_dir=tmp_path / "knowledge",
        conversation_memory_dir=tmp_path / "conversation-memory",
    )
    store = NeuroMemConversationStore(settings)

    request = ChatRequest(
        student_name="Alice",
        student_email="alice@example.com",
        course_context="科研指导",
        conversation_id="conv-persist",
        question="我想继续讨论推理系统选型。",
    )

    record = store.add_exchange(
        request,
        conversation_id="conv-persist",
        answer="建议先明确吞吐目标和延迟预算。",
        workflow_action="answer",
        interaction_domain="advising",
        knowledge_hit_count=1,
        booking_result=None,
    )
    consolidated = store.consolidate_profiles(record)

    reloaded_store = NeuroMemConversationStore(settings)

    recent_records = reloaded_store.list_recent_conversation_records("conv-persist")
    profiles = reloaded_store.list_profiles_for_student(
        student_name="Alice",
        student_email="alice@example.com",
    )

    assert consolidated >= 1
    assert [item.question for item in recent_records] == ["我想继续讨论推理系统选型。"]
    assert recent_records[0].answer == "建议先明确吞吐目标和延迟预算。"
    assert any(profile.category == "course_context" for profile in profiles)
    assert (
        settings.conversation_memory_dir
        / "collections"
        / "conversation-memory"
        / "raw_data.json"
    ).exists()
    assert (
        settings.conversation_memory_dir
        / "collections"
        / "conversation-profile-memory"
        / "raw_data.json"
    ).exists()
    assert not (settings.conversation_memory_dir / "records").exists()
    assert not (settings.conversation_memory_dir / "profiles").exists()


def test_store_migrates_legacy_json_layout_once_and_removes_it(tmp_path: Path) -> None:
    base_dir = tmp_path / "conversation-memory"
    records_dir = base_dir / "records"
    profiles_dir = base_dir / "profiles"
    records_dir.mkdir(parents=True, exist_ok=True)
    profiles_dir.mkdir(parents=True, exist_ok=True)

    created_at = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
    legacy_root_record = ConversationMemoryRecord(
        memory_id="legacy-root-record",
        conversation_id="conv-legacy",
        student_name="Alice",
        student_email="alice@example.com",
        course_context="科研指导",
        question="我们上次讨论了什么？",
        answer="上次主要讨论了推理系统选型。",
        workflow_action="answer",
        interaction_domain="advising",
        knowledge_hit_count=1,
        booking_summary=None,
        created_at=created_at,
    )
    legacy_records_record = ConversationMemoryRecord(
        memory_id="legacy-records-record",
        conversation_id="conv-legacy",
        student_name="Alice",
        student_email="alice@example.com",
        course_context="科研指导",
        question="再补充一下下一步怎么做？",
        answer="下一步先把约束条件列清楚。",
        workflow_action="answer",
        interaction_domain="advising",
        knowledge_hit_count=0,
        booking_summary=None,
        created_at=datetime(2026, 6, 1, 12, 5, tzinfo=UTC),
    )
    legacy_profile = ProfileMemoryRecord(
        profile_id="alice-example-com-course_context",
        student_key="alice@example.com",
        student_name="Alice",
        student_email="alice@example.com",
        category="course_context",
        summary="该用户最近的主要交流场景是：科研指导",
        evidence="Question: 我们上次讨论了什么？",
        updated_at=created_at,
    )

    (base_dir / "legacy-root-record.json").write_text(
        json.dumps(legacy_root_record.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (records_dir / "legacy-records-record.json").write_text(
        json.dumps(legacy_records_record.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (profiles_dir / "alice-example-com-course_context.json").write_text(
        json.dumps(legacy_profile.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    settings = AppSettings(
        knowledge_base_dir=tmp_path / "knowledge",
        conversation_memory_dir=base_dir,
    )

    store = NeuroMemConversationStore(settings)

    recent_records = store.list_recent_conversation_records("conv-legacy")
    profiles = store.list_profiles_for_student(
        student_name="Alice",
        student_email="alice@example.com",
    )

    assert [record.memory_id for record in recent_records] == [
        "legacy-records-record",
        "legacy-root-record",
    ]
    assert any(
        profile.profile_id == "alice-example-com-course_context" for profile in profiles
    )
    assert not (base_dir / "legacy-root-record.json").exists()
    assert not records_dir.exists()
    assert not profiles_dir.exists()
    assert (base_dir / "collections" / "conversation-memory" / "raw_data.json").exists()
    assert (
        base_dir / "collections" / "conversation-profile-memory" / "raw_data.json"
    ).exists()


def test_profile_upsert_replaces_existing_collection_entry(tmp_path: Path) -> None:
    settings = AppSettings(
        knowledge_base_dir=tmp_path / "knowledge",
        conversation_memory_dir=tmp_path / "conversation-memory",
    )
    store = NeuroMemConversationStore(settings)

    older = ProfileMemoryRecord(
        profile_id="alice-example-com-course_context",
        student_key="alice@example.com",
        student_name="Alice",
        student_email="alice@example.com",
        category="course_context",
        summary="该用户最近的主要交流场景是：科研指导",
        evidence="Question: 第一次讨论科研指导。",
        updated_at=datetime(2026, 6, 1, 12, 0, tzinfo=UTC),
    )
    newer = ProfileMemoryRecord(
        profile_id="alice-example-com-course_context",
        student_key="alice@example.com",
        student_name="Alice",
        student_email="alice@example.com",
        category="course_context",
        summary="该用户最近的主要交流场景是：推理系统选型",
        evidence="Question: 第二次讨论推理系统选型。",
        updated_at=datetime(2026, 6, 1, 12, 30, tzinfo=UTC),
    )

    store._upsert_profile(older)
    store._persist_collection(store._profile_collection, store._profile_collection_dir)
    store._upsert_profile(newer)
    store._persist_collection(store._profile_collection, store._profile_collection_dir)

    reloaded_store = NeuroMemConversationStore(settings)
    profiles = reloaded_store.list_profiles_for_student(
        student_name="Alice",
        student_email="alice@example.com",
    )

    assert reloaded_store._profile_collection.size() == 1
    assert len(profiles) == 1
    assert profiles[0].summary == "该用户最近的主要交流场景是：推理系统选型"
    assert profiles[0].evidence == "Question: 第二次讨论推理系统选型。"


def test_store_canonicalizes_duplicate_profile_entries_on_startup(
    tmp_path: Path,
) -> None:
    settings = AppSettings(
        knowledge_base_dir=tmp_path / "knowledge",
        conversation_memory_dir=tmp_path / "conversation-memory",
    )
    store = NeuroMemConversationStore(settings)

    older = ProfileMemoryRecord(
        profile_id="alice-example-com-course_context",
        student_key="alice@example.com",
        student_name="Alice",
        student_email="alice@example.com",
        category="course_context",
        summary="旧画像",
        evidence="Question: 旧问题。",
        updated_at=datetime(2026, 6, 1, 12, 0, tzinfo=UTC),
    )
    newer = ProfileMemoryRecord(
        profile_id="alice-example-com-course_context",
        student_key="alice@example.com",
        student_name="Alice",
        student_email="alice@example.com",
        category="course_context",
        summary="新画像",
        evidence="Question: 新问题。",
        updated_at=datetime(2026, 6, 1, 12, 30, tzinfo=UTC),
    )

    older_entry = store._build_profile_memory_entry(older)
    newer_entry = store._build_profile_memory_entry(newer)
    store._profile_collection.insert(
        older_entry.text, older_entry.metadata, index_names=["search"]
    )
    store._profile_collection.insert(
        newer_entry.text, newer_entry.metadata, index_names=["search"]
    )
    store._persist_collection(store._profile_collection, store._profile_collection_dir)

    deduped_store = NeuroMemConversationStore(settings)
    profiles = deduped_store.list_profiles_for_student(
        student_name="Alice",
        student_email="alice@example.com",
    )

    assert deduped_store._profile_collection.size() == 1
    assert len(profiles) == 1
    assert profiles[0].summary == "新画像"
    assert profiles[0].evidence == "Question: 新问题。"
