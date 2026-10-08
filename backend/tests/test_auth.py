def test_register_and_login(client):
    reg_payload = {
        "name": "New User",
        "email": "newuser@example.com",
        "password": "Password123!",
        "role": "BUSINESS_OWNER"
    }
    res = client.post("/api/auth/register", json=reg_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "newuser@example.com"
    assert "password_hash" not in data

    # Login
    login_payload = {
        "email": "newuser@example.com",
        "password": "Password123!"
    }
    res = client.post("/api/auth/login", json=login_payload)
    assert res.status_code == 200
    token_data = res.json()
    assert "access_token" in token_data

    # Test me endpoint
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    res = client.get("/api/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["email"] == "newuser@example.com"

def test_login_invalid_password(client, reviewer_user):
    login_payload = {
        "email": reviewer_user.email,
        "password": "WrongPassword!"
    }
    res = client.post("/api/auth/login", json=login_payload)
    assert res.status_code == 401
