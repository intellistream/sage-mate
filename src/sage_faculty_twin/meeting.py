from __future__ import annotations

from datetime import date, datetime, timedelta
from uuid import uuid4

from .availability import WeeklyAvailabilityStore
from .config import AppSettings
from .models import AvailabilitySchedule, BookingRecord, BookingRequest, BookingResponse


class MeetingService:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._bookings: list[BookingRecord] = []
        self._availability_store = WeeklyAvailabilityStore(settings)

    def book(self, request: BookingRequest) -> BookingResponse:
        requested_minutes = (request.preferred_end - request.preferred_start).total_seconds() / 60
        if requested_minutes < self._settings.meeting_duration_minutes:
            return BookingResponse(
                accepted=False,
                message=(
                    f"预约时间窗口至少需要 {self._settings.meeting_duration_minutes} 分钟。"
                ),
            )

        slot_start = request.preferred_start.replace(second=0, microsecond=0)
        slot_end = slot_start + timedelta(minutes=self._settings.meeting_duration_minutes)

        if not self._is_within_booking_hours(slot_start, slot_end):
            return BookingResponse(
                accepted=False,
                message="所选时间不在可预约时段内。",
                alternative_slots=self._suggest_slots(slot_start),
            )

        if not self._availability_store.is_available(slot_start, slot_end):
            return BookingResponse(
                accepted=False,
                message="所选时间不在本周开放预约时段内。",
                alternative_slots=self._suggest_slots(slot_start),
            )

        conflicting_booking = self._find_conflicting_booking(slot_start, slot_end)
        if conflicting_booking is not None:
            return BookingResponse(
                accepted=False,
                message=self._build_conflict_message(conflicting_booking),
                alternative_slots=self._suggest_slots(slot_start),
            )

        booking = BookingRecord(
            booking_id=str(uuid4()),
            student_name=request.student_name,
            student_email=request.student_email,
            topic=request.topic,
            start_at=slot_start,
            end_at=slot_end,
            status="待确认",
            rejection_reason=None,
        )
        self._bookings.append(booking)
        return BookingResponse(
            accepted=True,
            message="预约请求已提交，等待管理员确认。",
            booking=booking,
        )

    def list_bookings(self, status: str | None = None) -> list[BookingRecord]:
        if status is None:
            return list(self._bookings)
        return [booking for booking in self._bookings if booking.status == status]

    def confirm_booking(self, booking_id: str) -> BookingResponse:
        booking = next((item for item in self._bookings if item.booking_id == booking_id), None)
        if booking is None:
            return BookingResponse(accepted=False, message="未找到对应的预约请求。")

        if booking.status == "已拒绝":
            return BookingResponse(
                accepted=False,
                message="该预约已被拒绝，不能再确认。",
                booking=booking,
            )

        if booking.status == "已确认":
            return BookingResponse(
                accepted=True,
                message="该预约已处于确认状态。",
                booking=booking,
            )

        booking.status = "已确认"
        return BookingResponse(
            accepted=True,
            message="预约已确认。",
            booking=booking,
        )

    def reject_booking(self, booking_id: str, rejection_reason: str | None = None) -> BookingResponse:
        booking = next((item for item in self._bookings if item.booking_id == booking_id), None)
        if booking is None:
            return BookingResponse(accepted=False, message="未找到对应的预约请求。")

        if booking.status == "已拒绝":
            return BookingResponse(
                accepted=True,
                message="该预约已处于拒绝状态。",
                booking=booking,
            )

        if booking.status == "已确认":
            return BookingResponse(
                accepted=False,
                message="该预约已经确认，不能再拒绝。",
                booking=booking,
            )

        booking.status = "已拒绝"
        booking.rejection_reason = rejection_reason.strip() if rejection_reason else None
        return BookingResponse(
            accepted=True,
            message="预约已拒绝。",
            booking=booking,
        )

    def get_availability_schedule(self) -> AvailabilitySchedule:
        return self._availability_store.load()

    def get_previous_week_availability_template(self, week_of: date | None = None) -> AvailabilitySchedule:
        return self._availability_store.load_previous_week_template(week_of)

    def update_availability_schedule(self, schedule: AvailabilitySchedule | dict) -> AvailabilitySchedule:
        normalized = AvailabilitySchedule.model_validate(schedule)
        return self._availability_store.save(normalized)

    def describe_current_availability(self) -> str:
        return self._availability_store.describe_for_prompt()

    def _is_within_booking_hours(self, start_at: datetime, end_at: datetime) -> bool:
        if start_at.date() != end_at.date():
            return False
        return (
            self._settings.booking_start_hour <= start_at.hour < self._settings.booking_end_hour
            and self._settings.booking_start_hour < end_at.hour <= self._settings.booking_end_hour
        )

    def _find_conflicting_booking(self, start_at: datetime, end_at: datetime) -> BookingRecord | None:
        for booking in self._bookings:
            if booking.status == "已拒绝":
                continue
            if start_at < booking.end_at and end_at > booking.start_at:
                return booking
        return None

    def _build_conflict_message(self, booking: BookingRecord) -> str:
        if booking.status == "待确认":
            return "所选时间已被其他学生提交预约申请，正在等待管理员确认，请更换时间。"
        return "所选时间已被其他学生预约，请更换时间。"

    def _suggest_slots(self, anchor: datetime) -> list[str]:
        weekly_suggestions = self._availability_store.suggest_slots(
            anchor,
            self._settings.meeting_duration_minutes,
            [(booking.start_at, booking.end_at) for booking in self._bookings],
        )
        if weekly_suggestions:
            return weekly_suggestions

        suggestions: list[str] = []
        for offset in range(1, 4):
            candidate = anchor + timedelta(hours=offset)
            end_at = candidate + timedelta(minutes=self._settings.meeting_duration_minutes)
            if self._is_within_booking_hours(candidate, end_at) and self._find_conflicting_booking(
                candidate,
                end_at,
            ) is None:
                suggestions.append(candidate.isoformat())
        return suggestions
