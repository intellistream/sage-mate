from __future__ import annotations

import json
import threading
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from unittest.mock import patch

from sage_faculty_twin.calendar_bridge import CalendarBridgeClient
from sage_faculty_twin.config import AppSettings


class _CalendarHandler(BaseHTTPRequestHandler):
    token = "test-token"
    requests: list[str] = []

    def do_GET(self) -> None:  # noqa: N802
        self.__class__.requests.append(self.path)
        if self.headers.get("Authorization") != f"Bearer {self.token}":
            self.send_response(401)
            self.end_headers()
            return
        payload: dict[str, Any] = {
            "events": [
                {
                    "title": "项目讨论",
                    "start": "2026-07-01T09:00:00.000",
                    "end": "2026-07-01T10:00:00.000",
                    "allDay": False,
                    "location": "办公室",
                }
            ]
        }
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return


def test_calendar_bridge_disabled_by_default() -> None:
    client = CalendarBridgeClient(AppSettings())

    assert client.should_fetch_for_question("今天有什么安排？") is False
    assert client.describe_for_prompt("今天有什么安排？") == ""


def test_calendar_bridge_fetches_for_schedule_questions() -> None:
    _CalendarHandler.requests = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), _CalendarHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        settings = AppSettings(
            calendar_bridge_enabled=True,
            calendar_bridge_url=f"http://127.0.0.1:{server.server_port}",
            calendar_bridge_token="test-token",
        )
        client = CalendarBridgeClient(settings)

        prompt = client.describe_for_prompt("我今天什么时候有空？")

        assert "Owner calendar context" in prompt
        assert "BUSY | 2026-07-01 09:00-10:00 | 项目讨论" in prompt
        assert "办公室" in prompt
        assert "must NOT be suggested as meeting slots" in prompt
        assert "Respect the user's requested date range strictly" in prompt
        assert _CalendarHandler.requests
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_calendar_bridge_marks_open_windows_as_candidates() -> None:
    settings = AppSettings(
        calendar_bridge_enabled=True,
        calendar_bridge_url="http://127.0.0.1:1",
        calendar_bridge_token="test-token",
    )
    client = CalendarBridgeClient(settings)

    busy = client._parse_event({
        "title": "科研指导",
        "start": "2026-07-02T14:00:00.000",
        "end": "2026-07-02T17:00:00.000",
    })
    open_window = client._parse_event({
        "title": "学生 1:1 开放时段",
        "start": "2026-07-01T14:00:00.000",
        "end": "2026-07-01T17:00:00.000",
    })

    assert client._looks_like_open_window(busy) is False
    assert client._looks_like_open_window(open_window) is True


def test_calendar_bridge_limits_this_week_query_window() -> None:
    settings = AppSettings(
        calendar_bridge_enabled=True,
        calendar_bridge_url="http://127.0.0.1:1",
        calendar_bridge_token="test-token",
    )
    client = CalendarBridgeClient(settings)

    class FixedDateTime:
        @classmethod
        def now(cls, timezone):
            from datetime import datetime

            return datetime(2026, 6, 29, 8, 30, tzinfo=timezone)

        @classmethod
        def combine(cls, *args, **kwargs):
            from datetime import datetime

            return datetime.combine(*args, **kwargs)

        @classmethod
        def fromisoformat(cls, value):
            from datetime import datetime

            return datetime.fromisoformat(value)

    with patch("sage_faculty_twin.calendar_bridge.datetime", FixedDateTime):
        start, end = client._query_window("今天下午不方便的话，本周内还有什么时间？")

    assert start.date() == date(2026, 6, 29)
    assert end.date() == date(2026, 7, 5)
    assert end.hour == 23
