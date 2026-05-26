from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

from fastapi import HTTPException, Request, Response, status

from .config import AppSettings
from .models import AdminSessionResponse

ADMIN_COOKIE_NAME = "faculty_twin_admin"
USER_COOKIE_NAME = "faculty_twin_user"


def decode_admin_session_token(token: str | None, settings: AppSettings) -> dict[str, Any] | None:
    return _decode_session_cookie(token, settings.admin_session_secret)


def build_admin_session_token(settings: AppSettings) -> str:
    now = int(time.time())
    payload = {
        "sub": settings.admin_username,
        "iat": now,
        "exp": now + settings.admin_session_ttl_seconds,
        "nonce": secrets.token_hex(8),
    }
    return _encode_session_cookie(payload, settings.admin_session_secret)


def decode_user_session_token(token: str | None, settings: AppSettings) -> dict[str, Any] | None:
    return _decode_session_cookie(token, settings.user_session_secret)


def build_user_session_token(*, user_id: str, email: str, settings: AppSettings) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "email": email,
        "iat": now,
        "exp": now + settings.user_session_ttl_seconds,
        "nonce": secrets.token_hex(8),
    }
    return _encode_session_cookie(payload, settings.user_session_secret)


def set_admin_session_cookie(response: Response, token: str, settings: AppSettings) -> None:
    response.set_cookie(
        key=ADMIN_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=settings.admin_session_ttl_seconds,
        path="/",
    )


def clear_admin_session_cookie(response: Response) -> None:
    response.delete_cookie(ADMIN_COOKIE_NAME, path="/")


def set_user_session_cookie(response: Response, token: str, settings: AppSettings) -> None:
    response.set_cookie(
        key=USER_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=settings.user_session_ttl_seconds,
        path="/",
    )


def clear_user_session_cookie(response: Response) -> None:
    response.delete_cookie(USER_COOKIE_NAME, path="/")


def build_admin_session_response(request: Request, settings: AppSettings) -> AdminSessionResponse:
    payload = decode_admin_session_token(request.cookies.get(ADMIN_COOKIE_NAME), settings)
    if payload is None:
        return AdminSessionResponse(is_admin=False, mode="user")
    return AdminSessionResponse(
        is_admin=True,
        mode="admin",
        username=str(payload.get("sub") or settings.admin_username),
    )


def issue_admin_session(response: Response, settings: AppSettings) -> AdminSessionResponse:
    token = build_admin_session_token(settings)
    set_admin_session_cookie(response, token, settings)
    return AdminSessionResponse(is_admin=True, mode="admin", username=settings.admin_username)


def clear_admin_session(response: Response) -> AdminSessionResponse:
    clear_admin_session_cookie(response)
    return AdminSessionResponse(is_admin=False, mode="user")


def require_admin(request: Request, settings: AppSettings) -> dict[str, Any]:
    payload = decode_admin_session_token(request.cookies.get(ADMIN_COOKIE_NAME), settings)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员身份验证。",
        )
    return payload


def validate_admin_credentials(username: str, password: str, settings: AppSettings) -> None:
    username_ok = secrets.compare_digest(username, settings.admin_username)
    password_ok = secrets.compare_digest(password, settings.admin_password)
    if not username_ok or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="管理员账号或密码错误。",
        )


def _encode_session_cookie(payload: dict[str, Any], secret: str) -> str:
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_json).decode("ascii")
    signature = hmac.new(
        secret.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload_b64}.{signature}"


def _decode_session_cookie(token: str | None, secret: str) -> dict[str, Any] | None:
    if not token or "." not in token:
        return None

    payload_b64, signature = token.rsplit(".", 1)
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not secrets.compare_digest(signature, expected_signature):
        return None

    try:
        payload_json = base64.urlsafe_b64decode(payload_b64.encode("ascii"))
        payload = json.loads(payload_json.decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return None

    if int(payload.get("exp", 0)) < int(time.time()):
        return None
    return payload