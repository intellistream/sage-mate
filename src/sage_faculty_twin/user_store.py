from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import scrypt
from uuid import uuid4

from fastapi import HTTPException, status

from .config import AppSettings
from .models import UserAccountResponse


@dataclass(slots=True)
class UserAccountRecord:
    user_id: str
    name: str
    email: str
    visitor_profile: str
    password_salt: str
    password_hash: str
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, object]:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "visitor_profile": self.visitor_profile,
            "password_salt": self.password_salt,
            "password_hash": self.password_hash,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> UserAccountRecord:
        return cls(
            user_id=str(payload["user_id"]),
            name=str(payload["name"]),
            email=str(payload["email"]),
            visitor_profile=str(payload.get("visitor_profile") or "general_visitor"),
            password_salt=str(payload["password_salt"]),
            password_hash=str(payload["password_hash"]),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
            updated_at=datetime.fromisoformat(str(payload["updated_at"])),
        )

    def to_response(self) -> UserAccountResponse:
        return UserAccountResponse(
            user_id=self.user_id,
            name=self.name,
            email=self.email,
            visitor_profile=self.visitor_profile,
            created_at=self.created_at,
        )


class UserAccountStore:
    def __init__(self, settings: AppSettings) -> None:
        self._path = settings.user_account_store_dir
        self._path.mkdir(parents=True, exist_ok=True)
        self._records_by_id: dict[str, UserAccountRecord] = {}
        self._records_by_email: dict[str, UserAccountRecord] = {}
        self._load_from_disk()

    def register_user(
        self, *, name: str, email: str, visitor_profile: str, password: str
    ) -> UserAccountResponse:
        normalized_name = name.strip()
        normalized_email = self._normalize_email(email)
        normalized_visitor_profile = visitor_profile.strip()
        if not normalized_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名不能为空。")
        if not self._looks_like_email(normalized_email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="请输入有效的邮箱地址。"
            )
        if normalized_visitor_profile not in _VISITOR_PROFILE_VALUES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="请选择有效的访问身份。"
            )
        if normalized_email in self._records_by_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="该邮箱已注册，请直接登录。"
            )

        now = datetime.now(UTC)
        salt = secrets.token_hex(16)
        record = UserAccountRecord(
            user_id=str(uuid4()),
            name=normalized_name,
            email=normalized_email,
            visitor_profile=normalized_visitor_profile,
            password_salt=salt,
            password_hash=self._hash_password(password=password, salt=salt),
            created_at=now,
            updated_at=now,
        )
        self._records_by_id[record.user_id] = record
        self._records_by_email[record.email] = record
        self._persist_record(record)
        return record.to_response()

    def authenticate_user(self, *, email: str, password: str) -> UserAccountResponse:
        normalized_email = self._normalize_email(email)
        record = self._records_by_email.get(normalized_email)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="用户邮箱或密码错误。"
            )

        expected_hash = self._hash_password(password=password, salt=record.password_salt)
        if not secrets.compare_digest(record.password_hash, expected_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="用户邮箱或密码错误。"
            )
        return record.to_response()

    def get_user_by_id(self, user_id: str) -> UserAccountResponse | None:
        record = self._records_by_id.get(user_id)
        return record.to_response() if record else None

    def count_users(self) -> int:
        return len(self._records_by_id)

    def _persist_record(self, record: UserAccountRecord) -> None:
        # Defensive: re-create the directory in case it was wiped at runtime.
        self._path.mkdir(parents=True, exist_ok=True)
        (self._path / f"{record.user_id}.json").write_text(
            json.dumps(record.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _load_from_disk(self) -> None:
        for file_path in sorted(self._path.glob("*.json")):
            payload = json.loads(file_path.read_text(encoding="utf-8"))
            record = UserAccountRecord.from_dict(payload)
            self._records_by_id[record.user_id] = record
            self._records_by_email[self._normalize_email(record.email)] = record

    def _normalize_email(self, email: str) -> str:
        return email.strip().lower()

    def _hash_password(self, *, password: str, salt: str) -> str:
        return scrypt(
            password=password.encode("utf-8"),
            salt=salt.encode("utf-8"),
            n=2**14,
            r=8,
            p=1,
            dklen=64,
        ).hex()

    def _looks_like_email(self, email: str) -> bool:
        return "@" in email and "." in email.rsplit("@", 1)[-1]


_VISITOR_PROFILE_VALUES = {
    "hust_undergraduate",
    "paper_writing_student",
    "lab_member",
    "general_visitor",
}
