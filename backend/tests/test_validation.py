def test_login_invalid_email_format(client):
    """Test malformed email triggers Pydantic 422 Unprocessable Entity."""
    response = client.post("/auth/login", json={
        "email": "not-an-email",
        "password": "Password123!"
    })
    assert response.status_code == 422

def test_service_validation_negative_price(client, admin_headers):
    """Test negative price in service creation triggers 422."""
    payload = {
        "name": "Invalid Service",
        "price": -50.0,
        "duration_minutes": 60
    }
    response = client.post("/api/services", json=payload, headers=admin_headers)
    assert response.status_code == 422

def test_service_validation_empty_name(client, admin_headers):
    """Test empty service name triggers 422."""
    payload = {
        "name": "a", # min_length is 2
        "price": 50.0,
        "duration_minutes": 60
    }
    response = client.post("/api/services", json=payload, headers=admin_headers)
    assert response.status_code == 422

def test_health_check_endpoint(client):
    """Test Nagios probe endpoint GET /health."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["db"] == "ok"
    assert "version" in data

def test_readiness_probe_endpoint(client):
    """Test Ansible/Ops readiness probe GET /ready."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["ready"] is True
    assert data["checks"]["database"] == "connected"
    assert data["checks"]["integrity"] == "verified"
