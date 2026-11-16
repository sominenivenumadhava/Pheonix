def test_backup_record_logging_and_retrieval(client, seed_test_users):
    """Test registering and querying backup audit records."""
    payload = {
        "location": "/var/backups/phoenix-db/phoenix_backup_test.db",
        "size_bytes": 1048576,
        "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "restore_verified": True,
        "details": "Integration test verified"
    }

    create_res = client.post("/api/ops/backups", json=payload)
    assert create_res.status_code == 201
    created_id = create_res.json()["id"]

    list_res = client.get("/api/ops/backups")
    assert list_res.status_code == 200
    records = list_res.json()
    assert any(r["id"] == created_id for r in records)
    match = [r for r in records if r["id"] == created_id][0]
    assert match["restore_verified"] is True
    assert match["checksum_sha256"] == payload["checksum_sha256"]

def test_recovery_event_audit_logging(client, seed_test_users):
    """Test auditing self-healing and disaster recovery events."""
    event_payload = {
        "event_type": "DRIFT_REPAIRED",
        "detail": "Restored /etc/nginx/sites-available/phoenix baseline via Puppet catalog",
        "triggered_by": "PUPPET_AGENT"
    }

    create_res = client.post("/api/ops/recovery-events", json=event_payload)
    assert create_res.status_code == 201
    assert create_res.json()["event_type"] == "DRIFT_REPAIRED"

    list_res = client.get("/api/ops/recovery-events")
    assert list_res.status_code == 200
    events = list_res.json()
    assert any(e["triggered_by"] == "PUPPET_AGENT" for e in events)

def test_system_status_endpoint(client, seed_test_users):
    """Test GET /api/status provides operational dashboard counts."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert data["total_users"] >= 4
    assert data["total_services"] >= 1
    assert "latest_backup" in data
    assert "recent_recovery_events" in data
