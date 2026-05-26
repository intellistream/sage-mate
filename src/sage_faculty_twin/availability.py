from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path

from .config import AppSettings
from .models import AvailabilityDay, AvailabilitySchedule


class WeeklyAvailabilityStore:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._path = settings.availability_schedule_path
        self._history_dir = self._path.parent / "history"

    def load(self) -> AvailabilitySchedule:
        if not self._path.exists():
            return AvailabilitySchedule(timezone=self._settings.booking_timezone)

        payload = json.loads(self._path.read_text(encoding="utf-8"))
        schedule = AvailabilitySchedule.model_validate(payload)
        if not schedule.timezone:
            schedule.timezone = self._settings.booking_timezone
        return schedule

    def save(self, schedule: AvailabilitySchedule) -> AvailabilitySchedule:
        normalized = AvailabilitySchedule.model_validate(schedule.model_dump(mode="json"))
        if not normalized.timezone:
            normalized.timezone = self._settings.booking_timezone
        if normalized.week_of is None:
            normalized.week_of = self._current_week_start()
        normalized.days = sorted(normalized.days, key=lambda item: item.date)

        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(normalized.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self._history_dir.mkdir(parents=True, exist_ok=True)
        self._history_path(normalized.week_of).write_text(
            json.dumps(normalized.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return normalized

    def load_previous_week_template(self, week_of: date | None = None) -> AvailabilitySchedule:
        current_week_of = week_of or self.load().week_of or self._current_week_start()
        previous_week_of = current_week_of - timedelta(days=7)
        previous_path = self._history_path(previous_week_of)
        if not previous_path.exists():
            return AvailabilitySchedule(week_of=current_week_of, timezone=self._settings.booking_timezone)

        schedule = AvailabilitySchedule.model_validate(
            json.loads(previous_path.read_text(encoding="utf-8"))
        )
        shifted_days = [
            AvailabilityDay(
                date=day.date + timedelta(days=7),
                windows=day.windows,
                note=day.note,
            )
            for day in schedule.days
        ]
        return AvailabilitySchedule(
            week_of=current_week_of,
            timezone=schedule.timezone or self._settings.booking_timezone,
            days=shifted_days,
        )

    def is_available(self, start_at: datetime, end_at: datetime) -> bool:
        schedule = self.load()
        if not schedule.days:
            return True

        day = self._find_day(schedule.days, start_at.date())
        if day is None:
            return False

        for window_start, window_end in self._iter_windows(day):
            if start_at >= window_start and end_at <= window_end:
                return True
        return False

    def suggest_slots(
        self,
        anchor: datetime,
        duration_minutes: int,
        existing_bookings: list[tuple[datetime, datetime]],
        limit: int = 3,
    ) -> list[str]:
        schedule = self.load()
        if not schedule.days:
            return []

        suggestions: list[str] = []
        slot_duration = timedelta(minutes=duration_minutes)

        for day in sorted(schedule.days, key=lambda item: item.date):
            if day.date < anchor.date():
                continue
            for window_start, window_end in self._iter_windows(day):
                candidate = window_start
                while candidate + slot_duration <= window_end:
                    if candidate >= anchor and not self._has_conflict(
                        candidate,
                        candidate + slot_duration,
                        existing_bookings,
                    ):
                        suggestions.append(candidate.isoformat())
                        if len(suggestions) >= limit:
                            return suggestions
                    candidate += slot_duration
        return suggestions

    def describe_for_prompt(self) -> str:
        schedule = self.load()
        if not schedule.days:
            return ""

        lines = ["Current weekly meeting availability:"]
        for day in sorted(schedule.days, key=lambda item: item.date):
            windows = "、".join(f"{window.start}-{window.end}" for window in day.windows) or "不开放预约"
            note = f"（{day.note}）" if day.note else ""
            lines.append(f"- {day.date.isoformat()}: {windows}{note}")
        return "\n".join(lines) + "\n"

    def _find_day(self, days: list[AvailabilityDay], target_date: date) -> AvailabilityDay | None:
        for day in days:
            if day.date == target_date:
                return day
        return None

    def _iter_windows(self, day: AvailabilityDay) -> list[tuple[datetime, datetime]]:
        windows: list[tuple[datetime, datetime]] = []
        for window in day.windows:
            start_hour, start_minute = self._parse_hhmm(window.start)
            end_hour, end_minute = self._parse_hhmm(window.end)
            start_at = datetime.combine(day.date, time(start_hour, start_minute))
            end_at = datetime.combine(day.date, time(end_hour, end_minute))
            if end_at > start_at:
                windows.append((start_at, end_at))
        return windows

    def _parse_hhmm(self, value: str) -> tuple[int, int]:
        hour_text, minute_text = value.split(":", 1)
        return int(hour_text), int(minute_text)

    def _history_path(self, week_of: date) -> Path:
        return self._history_dir / f"{week_of.isoformat()}.json"

    def _current_week_start(self) -> date:
        today = datetime.now().date()
        return today - timedelta(days=today.weekday())

    def _has_conflict(
        self,
        start_at: datetime,
        end_at: datetime,
        existing_bookings: list[tuple[datetime, datetime]],
    ) -> bool:
        for booking_start, booking_end in existing_bookings:
            if start_at < booking_end and end_at > booking_start:
                return True
        return False