"""/auth/register, /auth/login, /auth/me."""


def test_register_creates_user(client):
    resp = client.post(
        "/auth/register", json={"email": "new@example.com", "password": "password123"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "new@example.com"
    assert "id" in body
    assert "hashed_password" not in body


def test_register_rejects_duplicate_email(client, register_user):
    register_user(email="dupe@example.com")
    resp = client.post(
        "/auth/register", json={"email": "dupe@example.com", "password": "password123"}
    )
    assert resp.status_code == 400


def test_register_rejects_short_password(client):
    resp = client.post(
        "/auth/register", json={"email": "short@example.com", "password": "abc"}
    )
    assert resp.status_code == 422


def test_register_rejects_invalid_email(client):
    resp = client.post(
        "/auth/register", json={"email": "not-an-email", "password": "password123"}
    )
    assert resp.status_code == 422


def test_login_returns_bearer_token(client, register_user):
    register_user(email="login@example.com", password="password123")
    resp = client.post(
        "/auth/login", json={"email": "login@example.com", "password": "password123"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 10


def test_login_rejects_wrong_password(client, register_user):
    register_user(email="wrongpw@example.com", password="password123")
    resp = client.post(
        "/auth/login", json={"email": "wrongpw@example.com", "password": "nope12345"}
    )
    assert resp.status_code == 401


def test_login_rejects_unknown_email(client):
    resp = client.post(
        "/auth/login", json={"email": "ghost@example.com", "password": "password123"}
    )
    assert resp.status_code == 401


def test_me_requires_auth(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 403  # HTTPBearer returns 403 with no credentials


def test_me_rejects_bad_token(client):
    resp = client.get("/auth/me", headers={"Authorization": "Bearer garbage.token.here"})
    assert resp.status_code == 401


def test_me_returns_current_user(client, auth_headers):
    headers = auth_headers(email="me@example.com")
    resp = client.get("/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"
