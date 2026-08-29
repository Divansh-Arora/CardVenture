"""/decks/* -- upload, list/get/delete, progress, breakdown, search."""


def _upload(client, headers, make_pdf, mock_llm, title="Biology 101", pages=None, cards=None):
    if pages is None:
        pages = ["Mitochondria are the powerhouse of the cell. They produce ATP."]
    if cards is not None:
        mock_llm(cards)
    pdf_bytes = make_pdf(pages)
    return client.post(
        "/decks/upload",
        headers=headers,
        data={"title": title},
        files={"file": ("notes.pdf", pdf_bytes, "application/pdf")},
    )


def test_upload_requires_auth(client, make_pdf):
    resp = client.post(
        "/decks/upload",
        data={"title": "X"},
        files={"file": ("a.pdf", make_pdf(["hi"]), "application/pdf")},
    )
    assert resp.status_code == 403


def test_upload_rejects_non_pdf(client, auth_headers):
    headers = auth_headers()
    resp = client.post(
        "/decks/upload",
        headers=headers,
        data={"title": "X"},
        files={"file": ("a.txt", b"not a pdf", "text/plain")},
    )
    assert resp.status_code == 400


def test_upload_creates_deck_with_generated_cards(client, auth_headers, make_pdf, mock_llm):
    headers = auth_headers()
    resp = _upload(client, headers, make_pdf, mock_llm)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["title"] == "Biology 101"
    assert body["card_count"] == 1
    assert body["cards"][0]["question"].startswith("What is a stub question")
    assert body["cards"][0]["ease_factor"] == 2.5
    assert body["cards"][0]["repetitions"] == 0


def test_upload_with_no_usable_cards_returns_422(client, auth_headers, make_pdf, mock_llm):
    headers = auth_headers()
    resp = _upload(client, headers, make_pdf, mock_llm, cards=[])
    assert resp.status_code == 422


def test_upload_scanned_pdf_with_no_text_returns_422(client, auth_headers, make_pdf, mock_llm):
    import io
    from reportlab.pdfgen import canvas

    headers = auth_headers()
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.showPage()
    c.save()

    resp = client.post(
        "/decks/upload",
        headers=headers,
        data={"title": "Blank"},
        files={"file": ("blank.pdf", buffer.getvalue(), "application/pdf")},
    )
    assert resp.status_code == 422


def test_list_decks_only_returns_own_decks(client, auth_headers, make_pdf, mock_llm):
    headers_a = auth_headers(email="a@example.com")
    _upload(client, headers_a, make_pdf, mock_llm, title="A's Deck")

    headers_b = auth_headers(email="b@example.com")
    resp = client.get("/decks", headers=headers_b)
    assert resp.status_code == 200
    assert resp.json() == []

    resp = client.get("/decks", headers=headers_a)
    assert len(resp.json()) == 1
    assert resp.json()[0]["title"] == "A's Deck"


def test_list_decks_search_by_title(client, auth_headers, make_pdf, mock_llm):
    headers = auth_headers()
    _upload(client, headers, make_pdf, mock_llm, title="Organic Chemistry")
    _upload(client, headers, make_pdf, mock_llm, title="Linear Algebra")

    resp = client.get("/decks", headers=headers, params={"q": "chem"})
    assert resp.status_code == 200
    titles = [d["title"] for d in resp.json()]
    assert titles == ["Organic Chemistry"]


def test_list_decks_sort_last_studied_prioritizes_studied_deck(
    client, auth_headers, make_pdf, mock_llm
):
    headers = auth_headers()
    _upload(client, headers, make_pdf, mock_llm, title="Never Studied")
    studied = _upload(client, headers, make_pdf, mock_llm, title="Studied Recently").json()

    card_id = studied["cards"][0]["id"]
    review = client.post(f"/cards/{card_id}/review", headers=headers, json={"quality": 4})
    assert review.status_code == 200

    resp = client.get("/decks", headers=headers, params={"sort": "last_studied"})
    titles = [d["title"] for d in resp.json()]
    assert titles[0] == "Studied Recently"
    assert resp.json()[0]["last_studied_at"] is not None
    assert resp.json()[1]["last_studied_at"] is None


def test_get_deck_not_found_for_other_users_deck(client, auth_headers, make_pdf, mock_llm):
    headers_a = auth_headers(email="owner@example.com")
    deck = _upload(client, headers_a, make_pdf, mock_llm).json()

    headers_b = auth_headers(email="intruder@example.com")
    resp = client.get(f"/decks/{deck['id']}", headers=headers_b)
    assert resp.status_code == 404


def test_deck_progress_buckets(client, auth_headers, make_pdf, mock_llm):
    headers = auth_headers()
    facts = [
        ("What produces ATP in a cell?", "The mitochondria."),
        ("What is the powerhouse of the cell?", "The mitochondrion."),
        ("What pigment absorbs light for photosynthesis?", "Chlorophyll."),
    ]
    cards = [
        {
            "question": q,
            "answer": a,
            "card_type": "definition",
            "difficulty": "medium",
            "topic": "T",
            "explanation": None,
            "source_page": None,
        }
        for q, a in facts
    ]
    deck = _upload(client, headers, make_pdf, mock_llm, cards=cards).json()

    resp = client.get(f"/decks/{deck['id']}/progress", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    # All brand new cards (repetitions == 0) count as "shaky".
    assert body["shaky"] == 3
    assert body["mastered"] == 0


def test_deck_breakdown_counts_by_type(client, auth_headers, make_pdf, mock_llm):
    headers = auth_headers()
    cards = [
        {"question": "What is a noun?", "answer": "A word that names a person, place, or thing.", "card_type": "definition", "difficulty": "easy", "topic": "T", "explanation": None, "source_page": None},
        {"question": "What is a verb?", "answer": "A word that describes an action or state of being.", "card_type": "definition", "difficulty": "easy", "topic": "T", "explanation": None, "source_page": None},
        {"question": "What is the formula for kinetic energy?", "answer": "E=mc^2", "card_type": "formula", "difficulty": "hard", "topic": "T", "explanation": None, "source_page": None},
    ]
    deck = _upload(client, headers, make_pdf, mock_llm, cards=cards).json()

    resp = client.get(f"/decks/{deck['id']}/breakdown", headers=headers)
    assert resp.status_code == 200
    breakdown = {row["card_type"]: row["count"] for row in resp.json()}
    assert breakdown["definition"] == 2
    assert breakdown["formula"] == 1


def test_search_deck_cards_matches_question_and_answer(client, auth_headers, make_pdf, mock_llm):
    headers = auth_headers()
    cards = [
        {"question": "What is entropy in thermodynamics?", "answer": "A measure of disorder.", "card_type": "definition", "difficulty": "medium", "topic": "T", "explanation": None, "source_page": None},
        {"question": "What is a lever used for?", "answer": "Multiplying force via a fulcrum.", "card_type": "definition", "difficulty": "medium", "topic": "T", "explanation": None, "source_page": None},
    ]
    deck = _upload(client, headers, make_pdf, mock_llm, cards=cards).json()

    resp = client.get(f"/decks/{deck['id']}/cards/search", headers=headers, params={"q": "entropy"})
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert "entropy" in results[0]["question"].lower()

    resp2 = client.get(f"/decks/{deck['id']}/cards/search", headers=headers, params={"q": "fulcrum"})
    assert len(resp2.json()) == 1
    assert "lever" in resp2.json()[0]["question"].lower()


def test_search_deck_cards_scoped_to_owner(client, auth_headers, make_pdf, mock_llm):
    headers_a = auth_headers(email="owner2@example.com")
    deck = _upload(client, headers_a, make_pdf, mock_llm).json()

    headers_b = auth_headers(email="intruder2@example.com")
    resp = client.get(f"/decks/{deck['id']}/cards/search", headers=headers_b, params={"q": "stub"})
    assert resp.status_code == 404


def test_delete_deck_removes_it_and_its_cards(client, auth_headers, make_pdf, mock_llm):
    headers = auth_headers()
    deck = _upload(client, headers, make_pdf, mock_llm).json()

    resp = client.delete(f"/decks/{deck['id']}", headers=headers)
    assert resp.status_code == 204

    resp = client.get(f"/decks/{deck['id']}", headers=headers)
    assert resp.status_code == 404
