"""/decks/{id}/due, /cards/{id}/review, /cards/{id}/history."""


def _upload(client, headers, make_pdf, mock_llm, title="Deck", pages=None, cards=None):
    if pages is None:
        pages = ["Some instructional content about the subject matter."]
    if cards is not None:
        mock_llm(cards)
    pdf_bytes = make_pdf(pages)
    return client.post(
        "/decks/upload",
        headers=headers,
        data={"title": title},
        files={"file": ("notes.pdf", pdf_bytes, "application/pdf")},
    )


def test_new_cards_are_immediately_due(client, auth_headers, make_pdf, mock_llm):
    headers = auth_headers()
    deck = _upload(client, headers, make_pdf, mock_llm).json()

    resp = client.get(f"/decks/{deck['id']}/due", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_due_cards_scoped_to_owner(client, auth_headers, make_pdf, mock_llm):
    headers_a = auth_headers(email="due-a@example.com")
    deck = _upload(client, headers_a, make_pdf, mock_llm).json()

    headers_b = auth_headers(email="due-b@example.com")
    resp = client.get(f"/decks/{deck['id']}/due", headers=headers_b)
    assert resp.status_code == 404


def test_submitting_review_updates_sm2_state(client, auth_headers, make_pdf, mock_llm):
    headers = auth_headers()
    deck = _upload(client, headers, make_pdf, mock_llm).json()
    card_id = deck["cards"][0]["id"]

    resp = client.post(f"/cards/{card_id}/review", headers=headers, json={"quality": 4})
    assert resp.status_code == 200
    body = resp.json()
    assert body["repetitions"] == 1
    assert body["interval_days"] == 1
    assert body["last_reviewed_at"] is not None


def test_card_no_longer_due_immediately_after_a_passing_review(
    client, auth_headers, make_pdf, mock_llm
):
    headers = auth_headers()
    deck = _upload(client, headers, make_pdf, mock_llm).json()
    card_id = deck["cards"][0]["id"]

    client.post(f"/cards/{card_id}/review", headers=headers, json={"quality": 4})

    resp = client.get(f"/decks/{deck['id']}/due", headers=headers)
    assert resp.json() == []


def test_failed_review_keeps_card_due_again_soon(client, auth_headers, make_pdf, mock_llm):
    headers = auth_headers()
    deck = _upload(client, headers, make_pdf, mock_llm).json()
    card_id = deck["cards"][0]["id"]

    # Pass once so repetitions/interval move off their initial zero state...
    client.post(f"/cards/{card_id}/review", headers=headers, json={"quality": 4})
    # ...then fail, which should reset repetitions back to 0.
    resp = client.post(f"/cards/{card_id}/review", headers=headers, json={"quality": 1})
    assert resp.json()["repetitions"] == 0
    assert resp.json()["interval_days"] == 1


def test_review_rejects_out_of_range_quality(client, auth_headers, make_pdf, mock_llm):
    headers = auth_headers()
    deck = _upload(client, headers, make_pdf, mock_llm).json()
    card_id = deck["cards"][0]["id"]

    resp = client.post(f"/cards/{card_id}/review", headers=headers, json={"quality": 9})
    assert resp.status_code == 422


def test_review_scoped_to_owner(client, auth_headers, make_pdf, mock_llm):
    headers_a = auth_headers(email="rev-a@example.com")
    deck = _upload(client, headers_a, make_pdf, mock_llm).json()
    card_id = deck["cards"][0]["id"]

    headers_b = auth_headers(email="rev-b@example.com")
    resp = client.post(f"/cards/{card_id}/review", headers=headers_b, json={"quality": 4})
    assert resp.status_code == 404


def test_card_history_records_each_review_in_order(client, auth_headers, make_pdf, mock_llm):
    headers = auth_headers()
    deck = _upload(client, headers, make_pdf, mock_llm).json()
    card_id = deck["cards"][0]["id"]

    client.post(f"/cards/{card_id}/review", headers=headers, json={"quality": 4})
    client.post(f"/cards/{card_id}/review", headers=headers, json={"quality": 5})

    resp = client.get(f"/cards/{card_id}/history", headers=headers)
    assert resp.status_code == 200
    history = resp.json()
    assert len(history) == 2
    # Most recent first.
    assert history[0]["quality"] == 5
    assert history[1]["quality"] == 4


def test_reviewing_touches_deck_last_studied_at(client, auth_headers, make_pdf, mock_llm):
    headers = auth_headers()
    deck = _upload(client, headers, make_pdf, mock_llm).json()
    assert deck["last_studied_at"] is None
    card_id = deck["cards"][0]["id"]

    client.post(f"/cards/{card_id}/review", headers=headers, json={"quality": 4})

    resp = client.get(f"/decks/{deck['id']}", headers=headers)
    assert resp.json()["last_studied_at"] is not None
