from __future__ import annotations

import json
import secrets
import string
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path


_CODE_ALPHABET = string.ascii_uppercase + string.digits


@dataclass(slots=True)
class SlackUserLinkRecord:
    slack_user_id: str
    user_id: str
    email: str
    visitor_profile: str
    linked_at: datetime

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> SlackUserLinkRecord:
        return cls(
            slack_user_id=str(payload["slack_user_id"]),
            user_id=str(payload["user_id"]),
            email=str(payload["email"]),
            visitor_profile=str(payload["visitor_profile"]),
            linked_at=datetime.fromisoformat(str(payload["linked_at"])),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "slack_user_id": self.slack_user_id,
            "user_id": self.user_id,
            "email": self.email,
            "visitor_profile": self.visitor_profile,
            "linked_at": self.linked_at.isoformat(),
        }


@dataclass(slots=True)
class SlackLinkCodeRecord:
    code: str
    user_id: str
    email: str
    visitor_profile: str
    expires_at: datetime
    created_at: datetime

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> SlackLinkCodeRecord:
        return cls(
            code=str(payload["code"]),
            user_id=str(payload["user_id"]),
            email=str(payload["email"]),
            visitor_profile=str(payload["visitor_profile"]),
            expires_at=datetime.fromisoformat(str(payload["expires_at"])),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "user_id": self.user_id,
            "email": self.email,
            "visitor_profile": self.visitor_profile,
            "expires_at": self.expires_at.isoformat(),
            "created_at": self.created_at.isoformat(),
        }


class SlackUserLinkStore:
    def __init__(self, root_dir: Path) -> None:
        self._root_dir = root_dir
        self._links_dir = root_dir / "links"
        self._codes_dir = root_dir / "codes"
        self._links_dir.mkdir(parents=True, exist_ok=True)
        self._codes_dir.mkdir(parents=True, exist_ok=True)
        self._links_by_slack_id: dict[str, SlackUserLinkRecord] = {}
        self._links_by_user_id: dict[str, SlackUserLinkRecord] = {}
        self._codes: dict[str, SlackLinkCodeRecord] = {}
        self._load()

    def get_link_for_slack_user(self, slack_user_id: str) -> SlackUserLinkRecord | None:
        return self._links_by_slack_id.get(slack_user_id.strip())

    def get_link_for_user(self, user_id: str) -> SlackUserLinkRecord | None:
        return self._links_by_user_id.get(user_id.strip())

    def create_code(
        self,
        *,
        user_id: str,
        email: str,
        visitor_profile: str,
        ttl_seconds: int = 600,
    ) -> SlackLinkCodeRecord:
        self.prune_expired_codes()
        now = datetime.now(UTC)
        for _ in range(20):
            code = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(8))
            if code not in self._codes:
                break
        else:
            raise RuntimeError("Unable to generate a unique Slack link code.")
        record = SlackLinkCodeRecord(
            code=code,
            user_id=user_id,
            email=email,
            visitor_profile=visitor_profile,
            expires_at=now + timedelta(seconds=ttl_seconds),
            created_at=now,
        )
        self._codes[code] = record
        self._persist_code(record)
        return record

    def consume_code(self, code: str, *, slack_user_id: str) -> SlackUserLinkRecord | None:
        normalized_code = code.strip().upper()
        self.prune_expired_codes()
        record = self._codes.pop(normalized_code, None)
        if record is None:
            return None
        self._delete_code(normalized_code)
        link = SlackUserLinkRecord(
            slack_user_id=slack_user_id.strip(),
            user_id=record.user_id,
            email=record.email,
            visitor_profile=record.visitor_profile,
            linked_at=datetime.now(UTC),
        )
        previous = self._links_by_slack_id.get(link.slack_user_id)
        if previous is not None:
            self._links_by_user_id.pop(previous.user_id, None)
        self._links_by_slack_id[link.slack_user_id] = link
        self._links_by_user_id[link.user_id] = link
        self._persist_link(link)
        return link

    def prune_expired_codes(self) -> None:
        now = datetime.now(UTC)
        expired = [code for code, record in self._codes.items() if record.expires_at <= now]
        for code in expired:
            self._codes.pop(code, None)
            self._delete_code(code)

    def _load(self) -> None:
        for path in sorted(self._links_dir.glob("*.json")):
            record = SlackUserLinkRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))
            self._links_by_slack_id[record.slack_user_id] = record
            self._links_by_user_id[record.user_id] = record
        for path in sorted(self._codes_dir.glob("*.json")):
            record = SlackLinkCodeRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))
            self._codes[record.code] = record
        self.prune_expired_codes()

    def _persist_link(self, record: SlackUserLinkRecord) -> None:
        self._links_dir.mkdir(parents=True, exist_ok=True)
        (self._links_dir / f"{record.slack_user_id}.json").write_text(
            json.dumps(record.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _persist_code(self, record: SlackLinkCodeRecord) -> None:
        self._codes_dir.mkdir(parents=True, exist_ok=True)
        (self._codes_dir / f"{record.code}.json").write_text(
            json.dumps(record.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _delete_code(self, code: str) -> None:
        try:
            (self._codes_dir / f"{code}.json").unlink()
        except FileNotFoundError:
            pass
