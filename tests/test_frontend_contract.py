"""Frontend-to-API contract test.

Validates that every DOM element ID referenced inside an API POST body
construction in app.js actually exists in index.html. This catches the
exact class of bug where a required Pydantic field (e.g. visitor_profile)
sends an empty/null value because the DOM element was removed from HTML,
resulting in a 422 Unprocessable Entity error.
"""
from __future__ import annotations

import re
from pathlib import Path

WEB_DIR = Path(__file__).resolve().parents[1] / "src" / "sage_faculty_twin" / "web"

# Each entry: (endpoint, list_of_dom_ids_used_in_payload)
# These IDs are read by app.js to construct JSON POST bodies.
API_PAYLOAD_CONTRACTS = [
    ("/auth/admin/login", ["admin-username", "admin-password"]),
    ("/auth/user/register", [
        "user-register-name",
        "user-register-email",
        "user-register-profile",
        "user-register-password",
    ]),
    ("/auth/user/login", ["user-login-email", "user-login-password"]),
    ("/chat", [
        "chat-question",
        "student-name",
        "student-email",
        "course-context",
        "visitor-profile",
        "deep-thinking-checkbox",
    ]),
    ("/knowledge", [
        "knowledge-title",
        "knowledge-source",
        "knowledge-content",
        "knowledge-tags",
    ]),
    ("/bookings", [
        "booking-student-name",
        "booking-email",
        "booking-topic",
        "booking-start",
        "booking-end",
    ]),
    ("/suggestions", ["suggestion-message", "suggestion-category"]),
]

# Known missing IDs that exist in app.js but not in index.html.
# These use optional chaining in JS and do NOT affect API payloads.
# This count must only decrease over time (ratchet).
KNOWN_MISSING_ID_CEILING = 43


def _extract_html_ids(html: str) -> set[str]:
    return set(re.findall(r'id="([^"]+)"', html))


def _extract_js_element_ids(js: str) -> set[str]:
    return set(re.findall(r'getElementById\("([^"]+)"\)', js))


def test_api_payload_dom_ids_exist_in_html() -> None:
    """Every DOM ID used to build an API POST payload must exist in HTML."""
    html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
    html_ids = _extract_html_ids(html)

    missing: list[tuple[str, str]] = []
    for endpoint, dom_ids in API_PAYLOAD_CONTRACTS:
        for dom_id in dom_ids:
            if dom_id not in html_ids:
                missing.append((endpoint, dom_id))

    assert not missing, (
        "DOM IDs used in API payloads are missing from index.html:\n"
        + "\n".join(f"  {endpoint}: #{dom_id}" for endpoint, dom_id in missing)
    )


def test_missing_element_ids_do_not_grow() -> None:
    """The number of JS getElementById refs missing from HTML must not increase."""
    html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
    js = (WEB_DIR / "app.js").read_text(encoding="utf-8")

    html_ids = _extract_html_ids(html)
    js_ids = _extract_js_element_ids(js)
    missing = js_ids - html_ids

    assert len(missing) <= KNOWN_MISSING_ID_CEILING, (
        f"Missing ID count grew to {len(missing)} (ceiling is {KNOWN_MISSING_ID_CEILING}).\n"
        f"New missing IDs:\n"
        + "\n".join(f"  #{mid}" for mid in sorted(missing))
    )


def test_conversation_history_storage_is_scoped_per_account() -> None:
    """Local conversation history must be partitioned by guest/user scope."""
    js = (WEB_DIR / "app.js").read_text(encoding="utf-8")

    assert "function resolveConversationHistoryStorageScope()" in js
    assert "function switchConversationHistoryScope(nextScope" in js
    assert "return `${CHAT_HISTORY_STORAGE_KEY}:${scope || \"guest\"}`;" in js
    assert "return `${CHAT_HISTORY_META_STORAGE_KEY}:${scope || \"guest\"}`;" in js


def test_history_sync_uses_authenticated_session_email_only() -> None:
    js = (WEB_DIR / "app.js").read_text(encoding="utf-8")

    assert "let currentUserAccountEmail = \"\";" in js
    assert "currentUserAccountEmail = authenticated ? String(session.account?.email || \"\").trim().toLowerCase() : \"\";" in js
    assert "return currentUserAccountEmail || \"\";" in js
    assert "student_email" not in js[js.index("async function syncConversationHistoryFromServer"):js.index("function setHistoryRailCollapsed")]


def test_send_button_uses_animation_state() -> None:
    html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
    css = (WEB_DIR / "styles.css").read_text(encoding="utf-8")
    js = (WEB_DIR / "app.js").read_text(encoding="utf-8")

    assert "send-button-label" in html
    assert "send-button-icon" in html
    assert "send-button-spinner" in html
    assert "function setChatSubmitLoading(isLoading)" in js
    assert "chatSubmitButton.classList.toggle(\"is-sending\", loading)" in js
    assert "chatSubmitButton.textContent = \"发送中\"" not in js
    assert ".send-button.is-sending" in css
    assert "@keyframes send-spinner-spin" in css
    assert "@keyframes send-button-pulse" in css


def test_local_code_setup_does_not_block_or_auto_open_profile_modal() -> None:
    js = (WEB_DIR / "app.js").read_text(encoding="utf-8")
    setup_fn = js[js.index("function shouldShowSageMateSetup"):js.index("async function maybeOpenSageMateSetup")]

    assert 'params.get("setup") === "local-code"' in setup_fn
    assert "return !data.api_key_set" not in setup_fn
    assert "const localCodeConfigPromise = maybeOpenSageMateSetup();" in js
    assert "await maybeOpenSageMateSetup();" not in js
    assert "initializePage().catch(" in js


def test_account_entry_stays_in_sidebar_not_topbar() -> None:
    html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
    js = (WEB_DIR / "app.js").read_text(encoding="utf-8")

    assert 'id="sidebar-user-icon"' in html
    assert 'id="topbar-user-badge" class="topbar-user-badge hidden"' in html
    assert 'topbarUserBadge.classList.remove("hidden"' not in js
    assert 'topbarUserBadge.classList.add("hidden")' in js
