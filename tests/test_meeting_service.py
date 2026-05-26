import json
from datetime import date, datetime
from pathlib import Path

from sage_faculty_twin.config import AppSettings
from sage_faculty_twin.meeting import MeetingService
from sage_faculty_twin.models import BookingRequest


def test_booking_accepts_available_slot() -> None:
    availability_path = Path("/tmp/test_booking_accepts_available_slot.json")
    if availability_path.exists():
        availability_path.unlink()
    service = MeetingService(AppSettings(availability_schedule_path=availability_path))
    response = service.book(
        BookingRequest(
            student_name="Alice",
            student_email="alice@example.com",
            topic="Project guidance",
            preferred_start=datetime(2026, 5, 25, 10, 0),
            preferred_end=datetime(2026, 5, 25, 10, 45),
        )
    )

    assert response.accepted is True
    assert response.booking is not None
    assert response.booking.status == "待确认"


def test_booking_rejects_conflicting_slot() -> None:
    availability_path = Path("/tmp/test_booking_rejects_conflicting_slot.json")
    if availability_path.exists():
        availability_path.unlink()
    service = MeetingService(AppSettings(availability_schedule_path=availability_path))
    first = BookingRequest(
        student_name="Alice",
        student_email="alice@example.com",
        topic="Project guidance",
        preferred_start=datetime(2026, 5, 25, 10, 0),
        preferred_end=datetime(2026, 5, 25, 10, 45),
    )
    second = BookingRequest(
        student_name="Bob",
        student_email="bob@example.com",
        topic="Reading group",
        preferred_start=datetime(2026, 5, 25, 10, 15),
        preferred_end=datetime(2026, 5, 25, 11, 0),
    )

    service.book(first)
    response = service.book(second)

    assert response.accepted is False
    assert response.message == "所选时间已被其他学生提交预约申请，正在等待管理员确认，请更换时间。"
    assert response.alternative_slots


def test_admin_can_confirm_pending_booking() -> None:
    availability_path = Path("/tmp/test_admin_can_confirm_pending_booking.json")
    if availability_path.exists():
        availability_path.unlink()
    service = MeetingService(AppSettings(availability_schedule_path=availability_path))
    created = service.book(
        BookingRequest(
            student_name="Alice",
            student_email="alice@example.com",
            topic="Project guidance",
            preferred_start=datetime(2026, 5, 25, 10, 0),
            preferred_end=datetime(2026, 5, 25, 10, 45),
        )
    )

    assert created.booking is not None
    confirmed = service.confirm_booking(created.booking.booking_id)

    assert confirmed.accepted is True
    assert confirmed.booking is not None
    assert confirmed.booking.status == "已确认"


def test_rejected_booking_releases_slot() -> None:
    availability_path = Path("/tmp/test_rejected_booking_releases_slot.json")
    if availability_path.exists():
        availability_path.unlink()
    service = MeetingService(AppSettings(availability_schedule_path=availability_path))
    created = service.book(
        BookingRequest(
            student_name="Alice",
            student_email="alice@example.com",
            topic="Project guidance",
            preferred_start=datetime(2026, 5, 25, 10, 0),
            preferred_end=datetime(2026, 5, 25, 10, 45),
        )
    )

    assert created.booking is not None
    rejected = service.reject_booking(created.booking.booking_id)
    assert rejected.booking is not None
    assert rejected.booking.status == "已拒绝"

    follow_up = service.book(
        BookingRequest(
            student_name="Bob",
            student_email="bob@example.com",
            topic="Reading group",
            preferred_start=datetime(2026, 5, 25, 10, 0),
            preferred_end=datetime(2026, 5, 25, 10, 45),
        )
    )

    assert follow_up.accepted is True
    assert follow_up.booking is not None
    assert follow_up.booking.status == "待确认"


def test_reject_booking_records_reason() -> None:
    availability_path = Path("/tmp/test_reject_booking_records_reason.json")
    if availability_path.exists():
        availability_path.unlink()
    service = MeetingService(AppSettings(availability_schedule_path=availability_path))
    created = service.book(
        BookingRequest(
            student_name="Alice",
            student_email="alice@example.com",
            topic="Project guidance",
            preferred_start=datetime(2026, 5, 25, 10, 0),
            preferred_end=datetime(2026, 5, 25, 10, 45),
        )
    )

    assert created.booking is not None
    rejected = service.reject_booking(created.booking.booking_id, rejection_reason="这周日程已满，请改约下周。")

    assert rejected.accepted is True
    assert rejected.booking is not None
    assert rejected.booking.rejection_reason == "这周日程已满，请改约下周。"


def test_booking_respects_weekly_availability_file(tmp_path: Path) -> None:
    availability_path = tmp_path / "availability" / "current_week.json"
    availability_path.parent.mkdir(parents=True, exist_ok=True)
    availability_path.write_text(
        json.dumps(
            {
                "week_of": "2026-05-25",
                "timezone": "Asia/Shanghai",
                "days": [
                    {
                        "date": "2026-05-26",
                        "windows": [{"start": "14:00", "end": "16:00"}],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    service = MeetingService(AppSettings(availability_schedule_path=availability_path))

    accepted = service.book(
        BookingRequest(
            student_name="Alice",
            student_email="alice@example.com",
            topic="Project guidance",
            preferred_start=datetime(2026, 5, 26, 14, 0),
            preferred_end=datetime(2026, 5, 26, 14, 45),
        )
    )
    rejected = service.book(
        BookingRequest(
            student_name="Bob",
            student_email="bob@example.com",
            topic="Reading group",
            preferred_start=datetime(2026, 5, 26, 10, 0),
            preferred_end=datetime(2026, 5, 26, 10, 45),
        )
    )

    assert accepted.accepted is True
    assert rejected.accepted is False
    assert rejected.message == "所选时间不在本周开放预约时段内。"
    assert rejected.alternative_slots == [
        "2026-05-26T14:30:00",
        "2026-05-26T15:00:00",
        "2026-05-26T15:30:00",
    ]


def test_meeting_service_can_update_weekly_availability_file(tmp_path: Path) -> None:
    availability_path = tmp_path / "availability" / "current_week.json"
    service = MeetingService(AppSettings(availability_schedule_path=availability_path))

    saved = service.update_availability_schedule(
        {
            "week_of": "2026-05-25",
            "days": [
                {
                    "date": "2026-05-27",
                    "windows": [{"start": "09:00", "end": "11:00"}],
                    "note": "仅线上",
                }
            ],
        }
    )

    assert availability_path.exists()
    assert saved.days[0].date.isoformat() == "2026-05-27"
    assert service.get_availability_schedule().days[0].windows[0].start == "09:00"


def test_meeting_service_can_load_previous_week_template(tmp_path: Path) -> None:
    availability_path = tmp_path / "availability" / "current_week.json"
    service = MeetingService(AppSettings(availability_schedule_path=availability_path))

    service.update_availability_schedule(
        {
            "week_of": "2026-05-18",
            "days": [
                {
                    "date": "2026-05-18",
                    "windows": [{"start": "09:00", "end": "11:00"}],
                },
                {
                    "date": "2026-05-19",
                    "windows": [{"start": "14:00", "end": "16:00"}],
                },
            ],
        }
    )
    service.update_availability_schedule(
        {
            "week_of": "2026-05-25",
            "days": [],
        }
    )

    copied = service.get_previous_week_availability_template(date(2026, 5, 25))

    assert copied.week_of is not None
    assert copied.week_of.isoformat() == "2026-05-25"
    assert [day.date.isoformat() for day in copied.days] == ["2026-05-25", "2026-05-26"]
    assert copied.days[0].windows[0].start == "09:00"
