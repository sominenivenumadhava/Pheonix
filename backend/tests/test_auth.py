def test_login_success(client, seed_test_users):
    """Test successful user authentication with valid credentials."""
    response = client.post("/auth/login", json={
        "email": "admin@test.local",
        "password": "AdminPass123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "admin"
    assert data["email"] == "admin@test.local"

def test_login_invalid_password(client, seed_test_users):
    """Test login failure with wrong password."""
    response = client.post("/auth/login", json={
        "email": "admin@test.local",
        "password": "WrongPassword!"
    })
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

def test_login_unknown_user(client, seed_test_users):
    """Test login failure with nonexistent email."""
    response = client.post("/auth/login", json={
        "email": "unknown@test.local",
        "password": "Password123!"
    })
    assert response.status_code == 401

def test_login_inactive_user_blocked(client, seed_test_users):
    """Test that inactive users are strictly blocked from logging in."""
    response = client.post("/auth/login", json={
        "email": "inactive@test.local",
        "password": "InactivePass123!"
    })
    assert response.status_code == 403
    assert "inactive" in response.json()["detail"].lower()

def test_get_current_user_profile(client, admin_headers):
    """Test /auth/me returns authenticated user profile."""
    response = client.get("/auth/me", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@test.local"
    assert data["role"] == "admin"
    assert data["is_active"] is True

def test_protected_route_without_token(client):
    """Test accessing protected route without credentials returns 401."""
    response = client.get("/auth/me")
    assert response.status_code == 401
