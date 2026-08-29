"""/decks/{id}/analytics and /analytics/today."""


def _upload(client, headers, make_pdf, mock_llm, title="Deck", cards=None):
    if cards is not None:
        mock_llm(cards)
    pdf_bytes = make_pdf(["Some instructional content about the subject matter."])
    return client.post(
        "/decks/upload",
        headers=headers,
        data={"title": title},
        files={"file": ("notes.pdf", pdf_bytes, "application/pdf")},
    ).json()


def test_analytics_with_no_reviews_yet(client, auth_headers, make_pdf, mock_llm):
    headers = auth_headers()
    deck = _upload(client, headers, make_pdf, mock_llm)

    resp = client.get(f"/decks/{deck['id']}/analytics", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["reviews_today"] == 0
    assert body["accuracy_pct"] == 0.0
    assert body["total_cards"] == 1
    assert body["cards_struggling"] == 1  # brand-new card, repetitions == 0


def test_analytics_tracks_reviews_and_accuracy(client, auth_headers, make_pdf, mock_llm):
    headers = auth_headers()
    facts = [
        ("What is a synonym for happy?", "Joyful."),
        ("What is a synonym for sad?", "Unhappy."),
    ]
    cards = [
        {"question": q, "answer": a, "card_type": "definition", "difficulty": "easy", "topic": "T", "explanation": None, "source_page": None}
        for q, a in facts
    ]
    deck = _upload(client, headers, make_pdf, mock_llm, cards=cards)
    ids = [c["id"] for c in deck["cards"]]
    assert len(ids) == 2

    client.post(f"/cards/{ids[0]}/review", headers=headers, json={"quality": 5})  # correct
    client.post(f"/cards/{ids[1]}/review", headers=headers, json={"quality": 1})  # incorrect

    resp = client.get(f"/decks/{deck['id']}/analytics", headers=headers)
    body = resp.json()
    assert body["reviews_today"] == 2
    assert body["correct_today"] == 1
    assert body["accuracy_pct"] == 50.0


def test_today_analytics_aggregates_across_decks(client, auth_headers, make_pdf, mock_llm):
    headers = auth_headers()
    deck1 = _upload(client, headers, make_pdf, mock_llm, title="Deck One")
    deck2 = _upload(client, headers, make_pdf, mock_llm, title="Deck Two")

    client.post(f"/cards/{deck1['cards'][0]['id']}/review", headers=headers, json={"quality": 4})
    client.post(f"/cards/{deck2['cards'][0]['id']}/review", headers=headers, json={"quality": 4})

    resp = client.get("/analytics/today", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["reviews_today"] == 2
    assert resp.json()["total_cards"] == 2


def test_today_analytics_scoped_to_current_user(client, auth_headers, make_pdf, mock_llm):
    headers_a = auth_headers(email="an-a@example.com")
    _upload(client, headers_a, make_pdf, mock_llm)

    headers_b = auth_headers(email="an-b@example.com")
    resp = client.get("/analytics/today", headers=headers_b)
    assert resp.json()["total_cards"] == 0


def test_deck_analytics_requires_ownership(client, auth_headers, make_pdf, mock_llm):
    headers_a = auth_headers(email="an2-a@example.com")
    deck = _upload(client, headers_a, make_pdf, mock_llm)

    headers_b = auth_headers(email="an2-b@example.com")
    resp = client.get(f"/decks/{deck['id']}/analytics", headers=headers_b)
    assert resp.status_code == 404
