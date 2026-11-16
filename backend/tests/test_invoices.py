from datetime import datetime, timezone, timedelta

def test_invoice_creation_for_completed_booking(client, staff_headers, seed_test_users):
    """Test successful invoice creation against a completed booking."""
    customer_id = seed_test_users["customer_profile"].id
    service_id = seed_test_users["service"].id
    scheduled = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    # 1. Create booking
    b_res = client.post("/api/bookings", json={
        "customer_id": customer_id,
        "service_id": service_id,
        "scheduled_at": scheduled
    }, headers=staff_headers)
    booking_id = b_res.json()["id"]

    # 2. Progress booking to completed
    client.patch(f"/api/bookings/{booking_id}/status", json={"status": "confirmed"}, headers=staff_headers)
    client.patch(f"/api/bookings/{booking_id}/status", json={"status": "completed"}, headers=staff_headers)

    # 3. Create invoice with 10% tax
    inv_res = client.post("/api/invoices", json={
        "booking_id": booking_id,
        "tax": 10.0
    }, headers=staff_headers)

    assert inv_res.status_code == 201
    data = inv_res.json()
    assert data["invoice_no"].startswith("INV-")
    assert data["booking_id"] == booking_id
    assert data["amount"] == 100.0
    assert data["tax"] == 10.0
    assert data["total_amount"] == 110.0
    assert data["status"] == "issued"

def test_invoice_creation_rejected_for_uncompleted_booking(client, staff_headers, seed_test_users):
    """Test invoice creation fails with 400 for pending or confirmed bookings."""
    customer_id = seed_test_users["customer_profile"].id
    service_id = seed_test_users["service"].id
    scheduled = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    # Create pending booking
    b_res = client.post("/api/bookings", json={
        "customer_id": customer_id,
        "service_id": service_id,
        "scheduled_at": scheduled
    }, headers=staff_headers)
    booking_id = b_res.json()["id"]

    # Attempt invoice on pending booking
    inv_res_pending = client.post("/api/invoices", json={
        "booking_id": booking_id
    }, headers=staff_headers)
    assert inv_res_pending.status_code == 400
    assert "only be created for completed bookings" in inv_res_pending.json()["detail"]

    # Transition to confirmed and test again
    client.patch(f"/api/bookings/{booking_id}/status", json={"status": "confirmed"}, headers=staff_headers)
    inv_res_confirmed = client.post("/api/invoices", json={
        "booking_id": booking_id
    }, headers=staff_headers)
    assert inv_res_confirmed.status_code == 400

def test_duplicate_invoice_prevented(client, staff_headers, seed_test_users):
    """Test that a completed booking can have at most one invoice."""
    customer_id = seed_test_users["customer_profile"].id
    service_id = seed_test_users["service"].id
    scheduled = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    b_res = client.post("/api/bookings", json={
        "customer_id": customer_id,
        "service_id": service_id,
        "scheduled_at": scheduled
    }, headers=staff_headers)
    booking_id = b_res.json()["id"]

    client.patch(f"/api/bookings/{booking_id}/status", json={"status": "confirmed"}, headers=staff_headers)
    client.patch(f"/api/bookings/{booking_id}/status", json={"status": "completed"}, headers=staff_headers)

    # First invoice succeeds
    inv1 = client.post("/api/invoices", json={"booking_id": booking_id}, headers=staff_headers)
    assert inv1.status_code == 201

    # Second invoice must fail
    inv2 = client.post("/api/invoices", json={"booking_id": booking_id}, headers=staff_headers)
    assert inv2.status_code == 400
    assert "already exists" in inv2.json()["detail"]

def test_invoice_status_update(client, staff_headers, seed_test_users):
    """Test updating invoice status to paid."""
    customer_id = seed_test_users["customer_profile"].id
    service_id = seed_test_users["service"].id
    scheduled = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    b_res = client.post("/api/bookings", json={
        "customer_id": customer_id,
        "service_id": service_id,
        "scheduled_at": scheduled
    }, headers=staff_headers)
    booking_id = b_res.json()["id"]

    client.patch(f"/api/bookings/{booking_id}/status", json={"status": "confirmed"}, headers=staff_headers)
    client.patch(f"/api/bookings/{booking_id}/status", json={"status": "completed"}, headers=staff_headers)

    inv = client.post("/api/invoices", json={"booking_id": booking_id}, headers=staff_headers).json()
    invoice_id = inv["id"]

    update_res = client.patch(f"/api/invoices/{invoice_id}/status?new_status=paid", headers=staff_headers)
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "paid"
