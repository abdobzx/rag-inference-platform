"""Real tests for the auth flow (register -> verify-email -> login), exercising
the actual endpoints through FastAPI's TestClient rather than reimplementing
the validation logic separately.
"""

VALID_USER = {
    "username": "testuser",
    "email": "testuser@mysothemalab.com",
    "password": "Str0ng!Pass",
    "full_name": "Test User",
}


def test_register_success(client, no_email_sending):
    response = client.post("/auth/register", json=VALID_USER)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == VALID_USER["email"]
    assert "user_id" in body


def test_register_rejects_wrong_email_domain(client, no_email_sending):
    payload = {**VALID_USER, "email": "testuser@gmail.com"}
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 422  # rejected by Pydantic validation, never reaches the DB


def test_register_rejects_weak_password(client, no_email_sending):
    payload = {**VALID_USER, "password": "weak"}
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 422


def test_register_duplicate_email_conflicts(client, no_email_sending):
    client.post("/auth/register", json=VALID_USER)
    response = client.post("/auth/register", json={**VALID_USER, "username": "differentuser"})
    assert response.status_code == 409


def test_register_duplicate_username_conflicts(client, no_email_sending):
    client.post("/auth/register", json=VALID_USER)
    response = client.post(
        "/auth/register", json={**VALID_USER, "email": "someoneelse@mysothemalab.com"}
    )
    assert response.status_code == 409


def test_verify_email_wrong_code_rejected(client, no_email_sending):
    client.post("/auth/register", json=VALID_USER)
    response = client.post(
        "/auth/verify-email", json={"email": VALID_USER["email"], "code": "000000"}
    )
    assert response.status_code == 400


def test_verify_email_correct_code_succeeds(client, sent_emails):
    client.post("/auth/register", json=VALID_USER)
    _, code, _ = sent_emails[0]

    response = client.post(
        "/auth/verify-email", json={"email": VALID_USER["email"], "code": code}
    )
    assert response.status_code == 200


def test_login_fails_before_verification(client, no_email_sending):
    client.post("/auth/register", json=VALID_USER)
    response = client.post(
        "/token",
        data={"username": VALID_USER["email"], "password": VALID_USER["password"]},
    )
    assert response.status_code == 403  # registered but not yet verified


def test_login_fails_with_wrong_password(client, no_email_sending):
    client.post("/auth/register", json=VALID_USER)
    response = client.post(
        "/token",
        data={"username": VALID_USER["email"], "password": "WrongPassword1!"},
    )
    assert response.status_code == 401


def test_login_fails_for_unknown_user(client):
    response = client.post(
        "/token",
        data={"username": "nobody@mysothemalab.com", "password": "whatever1!"},
    )
    assert response.status_code == 401


def test_full_register_verify_login_flow(client, sent_emails):
    client.post("/auth/register", json=VALID_USER)
    _, code, _ = sent_emails[0]

    verify_response = client.post(
        "/auth/verify-email", json={"email": VALID_USER["email"], "code": code}
    )
    assert verify_response.status_code == 200

    login_response = client.post(
        "/token",
        data={"username": VALID_USER["email"], "password": VALID_USER["password"]},
    )
    assert login_response.status_code == 200
    token_body = login_response.json()
    assert token_body["token_type"] == "bearer"
    assert "access_token" in token_body
