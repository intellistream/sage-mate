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
