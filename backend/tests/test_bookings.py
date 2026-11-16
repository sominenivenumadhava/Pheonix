from datetime import datetime, timezone, timedelta

def test_create_booking_persistence(client, customer_headers, seed_test_users):
    """Test booking creation, readable booking number generation, and persistence."""
    customer_id = seed_test_users["customer_profile"].id
    service_id = seed_test_users["service"].id
    scheduled = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

    payload = {
        "customer_id": customer_id,
        "service_id": service_id,
        "scheduled_at": scheduled,
        "notes": "Urgent server recovery drill"
    }

    response = client.post("/api/bookings", json=payload, headers=customer_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["booking_no"].startswith("BK-")
    assert data["status"] == "pending"
    assert data["total_price"] == 100.0
    assert data["notes"] == "Urgent server recovery drill"

def test_booking_status_workflow(client, staff_headers, seed_test_users):
    """Test valid booking lifecycle: pending -> confirmed -> completed."""
    customer_id = seed_test_users["customer_profile"].id
    service_id = seed_test_users["service"].id
    scheduled = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    # Create booking
    create_res = client.post("/api/bookings", json={
        "customer_id": customer_id,
        "service_id": service_id,
        "scheduled_at": scheduled
    }, headers=staff_headers)
    booking_id = create_res.json()["id"]
    assert create_res.json()["status"] == "pending"

    # 1. Transition: pending -> confirmed
    confirm_res = client.patch(
        f"/api/bookings/{booking_id}/status",
        json={"status": "confirmed"},
        headers=staff_headers
    )
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] == "confirmed"

    # 2. Transition: confirmed -> completed
    complete_res = client.patch(
        f"/api/bookings/{booking_id}/status",
        json={"status": "completed"},
        headers=staff_headers
    )
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "completed"

def test_invalid_booking_transition_skip_confirmed(client, staff_headers, seed_test_users):
    """Test that skipping intermediate status (pending -> completed) is strictly rejected."""
    customer_id = seed_test_users["customer_profile"].id
    service_id = seed_test_users["service"].id
    scheduled = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()

    create_res = client.post("/api/bookings", json={
        "customer_id": customer_id,
        "service_id": service_id,
        "scheduled_at": scheduled
    }, headers=staff_headers)
    booking_id = create_res.json()["id"]

    # Attempt illegal transition: pending -> completed
    res = client.patch(
        f"/api/bookings/{booking_id}/status",
        json={"status": "completed"},
        headers=staff_headers
    )
    assert res.status_code == 400
    assert "Invalid transition" in res.json()["detail"]

def test_completed_booking_is_terminal(client, staff_headers, seed_test_users):
    """Test that completed bookings cannot transition to any other status."""
    customer_id = seed_test_users["customer_profile"].id
    service_id = seed_test_users["service"].id
    scheduled = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    create_res = client.post("/api/bookings", json={
        "customer_id": customer_id,
        "service_id": service_id,
        "scheduled_at": scheduled
    }, headers=staff_headers)
    booking_id = create_res.json()["id"]

    client.patch(f"/api/bookings/{booking_id}/status", json={"status": "confirmed"}, headers=staff_headers)
    client.patch(f"/api/bookings/{booking_id}/status", json={"status": "completed"}, headers=staff_headers)

    # Attempt illegal transition from completed
    res = client.patch(f"/api/bookings/{booking_id}/status", json={"status": "cancelled"}, headers=staff_headers)
    assert res.status_code == 400
    assert "Invalid transition" in res.json()["detail"]

def test_booking_cancellation_workflow(client, staff_headers, seed_test_users):
    """Test booking cancellation from pending status."""
    customer_id = seed_test_users["customer_profile"].id
    service_id = seed_test_users["service"].id
    scheduled = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    create_res = client.post("/api/bookings", json={
        "customer_id": customer_id,
        "service_id": service_id,
        "scheduled_at": scheduled
    }, headers=staff_headers)
    booking_id = create_res.json()["id"]

    cancel_res = client.patch(f"/api/bookings/{booking_id}/status", json={"status": "cancelled"}, headers=staff_headers)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"

    # Attempt to reopen cancelled booking (must fail)
    reopen_res = client.patch(f"/api/bookings/{booking_id}/status", json={"status": "confirmed"}, headers=staff_headers)
    assert reopen_res.status_code == 400
