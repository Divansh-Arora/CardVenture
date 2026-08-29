"""
Shared pytest fixtures.

Sets required config via environment variables *before* app.config /
app.database are ever imported, so the test suite is fully self-contained:
it never reads the real .env file and never needs a live Postgres or
NVIDIA API key. See app/database.py's GUID type for why SQLite works here
at all despite the models being written against Postgres in production.
"""
import io
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("NVIDIA_API_KEY", "test-nvidia-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-not-for-production")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")

import pytest
from fastapi.testclient import TestClient
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.database import Base, engine, SessionLocal, get_db
from app.main import app


@pytest.fixture(autouse=True)
def _clean_database():
    """Fresh schema for every test -- full isolation, no test can see
    another test's users/decks/cards."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    def _get_db_override():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def make_pdf():
    """Builds a real, extractable-text PDF in memory. `pages` is a list of
    strings, one per page, each line-wrapped manually onto the page --
    real content, not a mocked extractor, so pdf_service/chunking/
    content_filter are exercised against actual pypdf output."""

    def _make(pages: list[str]) -> bytes:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        for page_text in pages:
            y = 750
            for line in page_text.splitlines():
                c.drawString(72, y, line)
                y -= 16
                if y < 72:
                    c.showPage()
                    y = 750
            c.showPage()
        c.save()
        return buffer.getvalue()

    return _make


@pytest.fixture
def register_user(client):
    def _register(email="student@example.com", password="hunter22pass"):
        resp = client.post("/auth/register", json={"email": email, "password": password})
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _register


@pytest.fixture
def mock_llm(mocker):
    """Stubs the NVIDIA/OpenAI chat completion call so deck-upload tests
    never hit the network or need a real API key. `cards_per_chunk` can be
    a fixed list of card dicts (same cards returned for every chunk) or a
    callable receiving the chunk's user-message text and returning a list
    of card dicts, for tests that want different content per chunk.
    """
    import json as _json
    from types import SimpleNamespace

    from app.services import llm_service

    default_cards = [
        {
            "question": "What is a stub question about this material?",
            "answer": "A stub answer with enough length to pass quality checks.",
            "card_type": "definition",
            "difficulty": "medium",
            "topic": "Stub Topic",
            "explanation": "Stub explanation.",
            "source_page": None,
        }
    ]

    state = {"cards": default_cards}

    def _fake_create(*args, **kwargs):
        user_message = kwargs["messages"][1]["content"]
        cards = state["cards"](user_message) if callable(state["cards"]) else state["cards"]
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=_json.dumps(cards)))]
        )

    mocker.patch.object(llm_service._client.chat.completions, "create", side_effect=_fake_create)
    mocker.patch.object(llm_service.time, "sleep")  # skip the real rate-limit delay in tests

    def _set_cards(cards):
        state["cards"] = cards

    _set_cards.default_cards = default_cards
    return _set_cards


@pytest.fixture
def auth_headers(client, register_user):
    def _auth(email="student@example.com", password="hunter22pass"):
        register_user(email, password)
        resp = client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200, resp.text
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _auth
