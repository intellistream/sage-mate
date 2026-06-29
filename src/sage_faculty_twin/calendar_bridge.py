from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from .config import AppSettings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CalendarEvent:
    title: str
    start: str
    end: str
    all_day: bool = False
    location: str = ""
    description: str = ""


class CalendarBridgeClient:
    """Read-only client for the owner's local yxcal bridge."""

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    def should_fetch_for_question(self, question: str) -> bool:
        if not self._settings.calendar_bridge_enabled:
            return False
        if not self._settings.calendar_bridge_url or not self._settings.calendar_bridge_token:
            return False

        lowered = question.lower()
        markers = (
            "日程",
            "安排",
            "空",
            "忙",
            "有事",
            "会议",
            "预约",
            "约",
            "今天",
            "明天",
            "本周",
            "下周",
            "schedule",
            "calendar",
            "available",
            "availability",
            "free",
            "busy",
            "meeting",
            "book",
        )
        return any(marker in lowered or marker in question for marker in markers)

    def describe_for_prompt(self, question: str) -> str:
        if not self.should_fetch_for_question(question):
            return ""

        try:
            events = self.fetch_upcoming_events(question)
        except Exception as exc:  # pragma: no cover - network failures are environment-specific
            logger.warning("Calendar bridge fetch failed: %s", exc)
            return (
                "Owner calendar context:\n"
                "- 实时日程暂时不可用；回答时不要编造具体空闲时间。\n"
            )

        if not events:
            return "Owner calendar context:\n- 近期未查到默认日历中的已安排事项。\n"

        lines = [
            "Owner calendar context (read-only, default calendar only):",
            "Use these real calendar events only for scheduling/availability questions; do not expose unnecessary private detail.",
            "Interpretation rules:",
            "- Events marked BUSY are occupied time and must NOT be suggested as meeting slots.",
            "- Only events marked OPEN_CANDIDATE may be treated as intentionally available meeting windows.",
            "- If no OPEN_CANDIDATE fits, suggest gaps between BUSY events; do not recommend a BUSY event just because its title sounds relevant.",
            "- Respect the user's requested date range strictly. If the user asks for today, tomorrow, or this week, do not suggest events outside that range even if they appear below.",
        ]
        for event in events[: self._settings.calendar_bridge_max_events]:
            time_text = self._format_event_time(event)
            location = f" @ {event.location}" if event.location else ""
            status = "OPEN_CANDIDATE" if self._looks_like_open_window(event) else "BUSY"
            lines.append(f"- {status} | {time_text} | {event.title}{location}")
            if self._settings.calendar_bridge_include_description and event.description:
                lines.append(f"  note: {event.description[:160]}")
        return "\n".join(lines) + "\n"

    def fetch_upcoming_events(self, question: str = "") -> list[CalendarEvent]:
        now, end_at = self._query_window(question)
        query = {
            "start": now.isoformat(timespec="seconds"),
            "end": end_at.isoformat(timespec="seconds"),
            "limit": str(self._settings.calendar_bridge_max_events),
            "include_description": "1"
            if self._settings.calendar_bridge_include_description
            else "0",
        }
        url = self._settings.calendar_bridge_url.rstrip("/") + "/events?" + urllib.parse.urlencode(query)
        request = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {self._settings.calendar_bridge_token}",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(
            request,
            timeout=self._settings.calendar_bridge_timeout_seconds,
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return [self._parse_event(item) for item in payload.get("events", [])]

    def _query_window(self, question: str) -> tuple[datetime, datetime]:
        timezone = ZoneInfo(self._settings.booking_timezone)
        now = datetime.now(timezone)
        today = now.date()
        lowered = question.lower()
        if "本周" in question or "this week" in lowered:
            week_end = today + timedelta(days=6 - today.weekday())
            return now, datetime.combine(week_end, time(23, 59, 59), tzinfo=timezone)
        if "下周" in question or "next week" in lowered:
            next_monday = today + timedelta(days=7 - today.weekday())
            next_sunday = next_monday + timedelta(days=6)
            return (
                datetime.combine(next_monday, time(0, 0), tzinfo=timezone),
                datetime.combine(next_sunday, time(23, 59, 59), tzinfo=timezone),
            )
        if "明天" in question or "tomorrow" in lowered:
            tomorrow = today + timedelta(days=1)
            return (
                datetime.combine(tomorrow, time(0, 0), tzinfo=timezone),
                datetime.combine(tomorrow, time(23, 59, 59), tzinfo=timezone),
            )
        if "今天" in question or "today" in lowered:
            return now, datetime.combine(today, time(23, 59, 59), tzinfo=timezone)
        return now, now + timedelta(days=self._settings.calendar_bridge_lookahead_days)

    def _parse_event(self, payload: dict[str, Any]) -> CalendarEvent:
        return CalendarEvent(
            title=str(payload.get("title") or "未命名日程"),
            start=str(payload.get("start") or ""),
            end=str(payload.get("end") or ""),
            all_day=bool(payload.get("allDay") or payload.get("all_day") or False),
            location=str(payload.get("location") or ""),
            description=str(payload.get("description") or ""),
        )

    def _format_event_time(self, event: CalendarEvent) -> str:
        if event.all_day:
            start_date = event.start[:10] if event.start else "unknown-date"
            return f"{start_date} 全天"

        start = self._parse_datetime(event.start)
        end = self._parse_datetime(event.end)
        if start is None:
            return event.start or "unknown-time"
        if end is None:
            return start.strftime("%Y-%m-%d %H:%M")
        if start.date() == end.date():
            return f"{start:%Y-%m-%d %H:%M}-{end:%H:%M}"
        return f"{start:%Y-%m-%d %H:%M} - {end:%Y-%m-%d %H:%M}"

    def _parse_datetime(self, value: str) -> datetime | None:
        if not value:
            return None
        normalized = value.replace("Z", "+00:00")
        if len(normalized) >= 5 and normalized[-5] in {"+", "-"} and normalized[-3] != ":":
            normalized = normalized[:-2] + ":" + normalized[-2:]
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None

    def _looks_like_open_window(self, event: CalendarEvent) -> bool:
        text = f"{event.title}\n{event.description}".lower()
        markers = (
            "开放时段",
            "开放预约",
            "可预约",
            "office hour",
            "office hours",
            "open slot",
            "available",
        )
        return any(marker in text for marker in markers)
