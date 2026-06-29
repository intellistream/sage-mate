#!/usr/bin/env python3
"""Serve a narrow read-only HTTP bridge to the local yxcal calendar.

The bridge is intended to bind to 127.0.0.1 on the Mac and be exposed to the
remote faculty-twin server only through SSH reverse forwarding.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timedelta
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


DEFAULT_DB = (
    Path.home()
    / "Library/Containers/cn.youxiao.yxcalendar/Data/Library/Application Support"
    / "cn.youxiao.yxcalendar/cn.youxiao.yxcalendar/events.db"
)
DEFAULT_CLI = Path("/Applications/优效日历.app/Contents/MacOS/yxcal-cli")
DEFAULT_CATEGORY_IDS = "default_category_none"


class BridgeState:
    def __init__(
        self,
        *,
        token: str,
        db_path: Path,
        cli_path: Path,
        allowed_category_ids: set[str],
        max_window_days: int,
    ) -> None:
        self.token = token
        self.db_path = db_path
        self.cli_path = cli_path
        self.allowed_category_ids = allowed_category_ids
        self.max_window_days = max_window_days


class YxcalBridgeHandler(BaseHTTPRequestHandler):
    server_version = "yxcal-bridge/1.0"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._write_json({"ok": True})
            return
        if parsed.path != "/events":
            self._write_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)
            return
        if not self._authorized():
            self._write_json({"error": "unauthorized"}, status=HTTPStatus.UNAUTHORIZED)
            return

        try:
            params = parse_qs(parsed.query)
            start = self._first(params, "start") or datetime.now().isoformat(timespec="seconds")
            end = self._first(params, "end")
            if not end:
                end = (datetime.now() + timedelta(days=14)).isoformat(timespec="seconds")
            limit = min(max(int(self._first(params, "limit") or "40"), 1), 100)
            include_description = self._first(params, "include_description") == "1"
            events = self._load_events(
                start=start,
                end=end,
                limit=limit,
                include_description=include_description,
            )
            self._write_json({"events": events, "count": len(events)})
        except Exception as exc:
            self._write_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def log_message(self, format: str, *args: Any) -> None:
        if os.environ.get("YXCAL_BRIDGE_QUIET", "1") != "1":
            super().log_message(format, *args)

    def _authorized(self) -> bool:
        state: BridgeState = self.server.state  # type: ignore[attr-defined]
        expected = f"Bearer {state.token}"
        return bool(state.token) and self.headers.get("Authorization") == expected

    def _load_events(
        self,
        *,
        start: str,
        end: str,
        limit: int,
        include_description: bool,
    ) -> list[dict[str, Any]]:
        state: BridgeState = self.server.state  # type: ignore[attr-defined]
        self._validate_window(start, end, state.max_window_days)
        raw_events = self._run_yxcal_cli(start=start, end=end)
        filtered: list[dict[str, Any]] = []
        for event in raw_events:
            event_id = str(event.get("id") or "")
            if self._looks_like_non_owner_schedule(event):
                continue
            item = {
                "id": event_id,
                "title": event.get("title") or "未命名日程",
                "start": event.get("start") or "",
                "end": event.get("end") or "",
                "allDay": bool(event.get("allDay") or False),
                "location": event.get("location") or "",
            }
            if include_description:
                item["description"] = event.get("description") or ""
            filtered.append(item)
            if len(filtered) >= limit:
                break
        return filtered

    def _run_yxcal_cli(self, *, start: str, end: str) -> list[dict[str, Any]]:
        state: BridgeState = self.server.state  # type: ignore[attr-defined]
        output = subprocess.check_output(
            [
                str(state.cli_path),
                "--json",
                "events",
                "list",
                "--start",
                start,
                "--end",
                end,
            ],
            text=True,
            stderr=subprocess.STDOUT,
            timeout=8,
        )
        payload = json.loads(output)
        events = payload.get("events", [])
        if not isinstance(events, list):
            raise ValueError("yxcal-cli returned invalid events payload")
        return events

    def _validate_window(self, start: str, end: str, max_days: int) -> None:
        start_at = self._parse_datetime(start)
        end_at = self._parse_datetime(end)
        if end_at <= start_at:
            raise ValueError("end must be after start")
        if end_at - start_at > timedelta(days=max_days):
            raise ValueError(f"query window exceeds {max_days} days")

    def _parse_datetime(self, value: str) -> datetime:
        normalized = value.replace("Z", "+00:00")
        if len(normalized) >= 5 and normalized[-5] in {"+", "-"} and normalized[-3] != ":":
            normalized = normalized[:-2] + ":" + normalized[-2:]
        return datetime.fromisoformat(normalized)

    def _looks_like_non_owner_schedule(self, event: dict[str, Any]) -> bool:
        text = "\n".join(
            str(event.get(key) or "")
            for key in ("title", "description", "location")
        )
        blocked_markers = (
            "角色：工程师",
            "engineer-weekly-schedule",
            "角色：项目助理",
            "project-assistant-weekly-schedule",
            "角色：兼职助理",
            "part-time-assistant-weekly-schedule",
            "龙斌",
        )
        return any(marker in text for marker in blocked_markers)

    def _first(self, params: dict[str, list[str]], key: str) -> str | None:
        values = params.get(key)
        return values[0] if values else None

    def _write_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local yxcal read-only bridge.")
    parser.add_argument("--host", default=os.environ.get("YXCAL_BRIDGE_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("YXCAL_BRIDGE_PORT", "55619")))
    parser.add_argument("--token", default=os.environ.get("YXCAL_BRIDGE_TOKEN", ""))
    parser.add_argument("--db", type=Path, default=Path(os.environ.get("YXCAL_BRIDGE_DB", DEFAULT_DB)))
    parser.add_argument("--cli", type=Path, default=Path(os.environ.get("YXCAL_CLI", DEFAULT_CLI)))
    parser.add_argument(
        "--allowed-category-ids",
        default=os.environ.get("YXCAL_BRIDGE_ALLOWED_CATEGORY_IDS", DEFAULT_CATEGORY_IDS),
    )
    parser.add_argument(
        "--max-window-days",
        type=int,
        default=int(os.environ.get("YXCAL_BRIDGE_MAX_WINDOW_DAYS", "31")),
    )
    args = parser.parse_args()

    if not args.token:
        raise SystemExit("Set YXCAL_BRIDGE_TOKEN or pass --token.")
    if not args.db.exists():
        raise SystemExit(f"events db not found: {args.db}")
    if not args.cli.exists():
        raise SystemExit(f"yxcal-cli not found: {args.cli}")

    allowed_category_ids = {
        item.strip()
        for item in str(args.allowed_category_ids).split(",")
        if item.strip()
    }
    if not allowed_category_ids:
        raise SystemExit("At least one allowed category id is required.")

    server = ThreadingHTTPServer((args.host, args.port), YxcalBridgeHandler)
    server.state = BridgeState(  # type: ignore[attr-defined]
        token=args.token,
        db_path=args.db,
        cli_path=args.cli,
        allowed_category_ids=allowed_category_ids,
        max_window_days=args.max_window_days,
    )
    print(f"yxcal bridge listening on http://{args.host}:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
