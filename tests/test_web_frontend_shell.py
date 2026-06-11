from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from sage_faculty_twin.api import app


client = TestClient(app)
WEB_DIR = Path(__file__).resolve().parents[1] / "src" / "sage_faculty_twin" / "web"


def test_chat_shell_exposes_feedback_and_homepage_entrypoints() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    html = response.text
    assert 'id="lucky-question-button"' in html
    assert "随便问" in html
    assert 'id="open-suggestions"' in html
    assert 'id="suggestion-modal"' in html
    assert 'id="homepage-link"' in html
    assert "匿名留言" in html
    assert 'id="knowledge-feedback-web-list"' in html
    assert "联网资料审查区" in html


def test_embedded_homepage_route_is_served() -> None:
    response = client.get("/home/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "<html" in response.text.lower()


def test_overlay_modal_registry_tolerates_missing_identity_modal() -> None:
    index_html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
    app_js = (WEB_DIR / "app.js").read_text(encoding="utf-8")

    assert 'id="identity-modal"' not in index_html
    assert 'id="lucky-question-button"' in index_html
    assert 'id="knowledge-feedback-web-list"' in index_html
    assert "const RANDOM_CHAT_QUESTION_BANKS = {" in app_js
    assert "function applyLuckyQuestionPreferences(selection)" in app_js
    assert "function handleLuckyQuestionClick()" in app_js
    assert "function isFeedbackWebKnowledgeRecord(record)" in app_js
    assert "function handleFeedbackWebKnowledgeAction(event)" in app_js
    assert "data-feedback-web-action" in app_js
    assert "const overlayModals = [" in app_js
    assert "function hasVisibleOverlayModal()" in app_js
    assert 'identityModal.classList.contains("hidden")' not in app_js
    assert "[identityModal, knowledgeModal" not in app_js
