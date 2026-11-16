def test_admin_can_create_service(client, admin_headers):
    """Admin role can create new services in catalog."""
    payload = {
        "name": "Cloud Architecture Review",
        "description": "Comprehensive review of cloud infra",
        "price": 275.0,
        "duration_minutes": 90,
        "is_active": True
    }
    response = client.post("/api/services", json=payload, headers=admin_headers)
    assert response.status_code == 201
    assert response.json()["name"] == "Cloud Architecture Review"

def test_staff_cannot_create_service(client, staff_headers):
    """Staff role is blocked from creating services (Admin only)."""
    payload = {
        "name": "Unauthorized Service",
        "price": 100.0,
        "duration_minutes": 60
    }
    response = client.post("/api/services", json=payload, headers=staff_headers)
    assert response.status_code == 403
    assert "Operation not permitted" in response.json()["detail"]

def test_customer_cannot_create_service(client, customer_headers):
    """Customer role is blocked from creating services."""
    payload = {
        "name": "Customer Created Service",
        "price": 50.0,
        "duration_minutes": 30
    }
    response = client.post("/api/services", json=payload, headers=customer_headers)
    assert response.status_code == 403

def test_customer_cannot_list_all_customers(client, customer_headers):
    """Customer cannot view the entire business customer registry."""
    response = client.get("/api/customers", headers=customer_headers)
    assert response.status_code == 403

def test_staff_and_admin_can_list_customers(client, staff_headers, admin_headers):
    """Staff and Admin can list registered customers."""
    staff_res = client.get("/api/customers", headers=staff_headers)
    assert staff_res.status_code == 200
    assert len(staff_res.json()) >= 1

    admin_res = client.get("/api/customers", headers=admin_headers)
    assert admin_res.status_code == 200
    assert len(admin_res.json()) >= 1

def test_admin_can_deactivate_service(client, admin_headers, seed_test_users):
    """Admin can soft-delete / deactivate services."""
    service_id = seed_test_users["service"].id
    response = client.delete(f"/api/services/{service_id}", headers=admin_headers)
    assert response.status_code == 200
    assert "deactivated successfully" in response.json()["message"]
