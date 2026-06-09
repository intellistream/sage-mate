from __future__ import annotations

from fastapi import HTTPException, status


def resolve_authenticated_history_email(
    *,
    is_authenticated: bool,
    account_email: str | None,
    requested_email: str | None,
) -> str:
    normalized_account_email = (account_email or "").strip().lower()
    normalized_requested_email = (requested_email or "").strip().lower()

    if not is_authenticated or not normalized_account_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要先登录账号后才能同步历史对话。",
        )

    if normalized_requested_email and normalized_requested_email != normalized_account_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="历史对话只能访问当前登录账号的数据。",
        )

    return normalized_account_email