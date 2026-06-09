from __future__ import annotations

import pytest
from fastapi import HTTPException

from sage_faculty_twin.history_auth import resolve_authenticated_history_email


def test_history_requires_authenticated_session() -> None:
    with pytest.raises(HTTPException) as exc_info:
        resolve_authenticated_history_email(
            is_authenticated=False,
            account_email=None,
            requested_email="alice@example.com",
        )

    assert exc_info.value.status_code == 403


def test_history_rejects_requested_email_override() -> None:
    with pytest.raises(HTTPException) as exc_info:
        resolve_authenticated_history_email(
            is_authenticated=True,
            account_email="student@example.com",
            requested_email="alice@example.com",
        )

    assert exc_info.value.status_code == 403


def test_history_uses_authenticated_account_email() -> None:
    assert resolve_authenticated_history_email(
        is_authenticated=True,
        account_email="Student@Example.com ",
        requested_email=None,
    ) == "student@example.com"


def test_history_allows_matching_requested_email() -> None:
    assert resolve_authenticated_history_email(
        is_authenticated=True,
        account_email="student@example.com",
        requested_email="Student@example.com",
    ) == "student@example.com"