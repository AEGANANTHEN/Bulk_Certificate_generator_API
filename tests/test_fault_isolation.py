from app.models.enums import JobStatus, CertificateStatus


def test_individual_failure_fault_isolation(client):
    """
    Test that invalid recipient data or generation errors for one recipient
    do NOT prevent other valid certificates in the same job from generating.
    """
    payload = {
        "title": "Certificate of Attendance",
        "event_name": "Autonomous Navigation Workshop",
        "issuer_name": "AEREO Flight Operations",
        "issue_date": "2026-10-12",
        "recipients": [
            {"name": "Valid Recipient One", "email": "valid1@example.com"},
            {"name": "   ", "email": "emptyname@example.com"},  # Fails: empty name
            {"name": "Valid Recipient Three", "email": "valid3@example.com"},
            {"name": "Invalid Email Person", "email": "bad_email@@domain..com"},  # Fails: invalid email format
            {"name": "__FAIL__ Simulated Error Person", "email": "test@example.com"},  # Fails: simulated failure
            {"name": "Valid Recipient Six", "email": "valid6@example.com"}
        ]
    }

    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    # Poll status after background execution
    status_response = client.get(f"/api/v1/jobs/{job_id}")
    assert status_response.status_code == 200
    data = status_response.json()

    # Aggregate assertions
    assert data["status"] == JobStatus.PARTIALLY_COMPLETED
    assert data["total_count"] == 6
    assert data["processed_count"] == 6
    assert data["success_count"] == 3
    assert data["failure_count"] == 3
    assert data["progress_percentage"] == 100.0

    # Per-recipient assertions
    certs = data["certificates"]
    assert len(certs) == 6

    # Verify successful recipients
    success_names = [c["recipient_name"] for c in certs if c["status"] == CertificateStatus.SUCCESS]
    assert "Valid Recipient One" in success_names
    assert "Valid Recipient Three" in success_names
    assert "Valid Recipient Six" in success_names

    # Verify failed recipients have explanatory error messages
    failed_certs = [c for c in certs if c["status"] == CertificateStatus.FAILED]
    assert len(failed_certs) == 3
    for f in failed_certs:
        assert f["error_message"] is not None
        assert len(f["error_message"]) > 0


def test_all_recipients_failing_sets_status_to_failed(client):
    """Test that if 100% of recipients fail, the job status is FAILED."""
    payload = {
        "event_name": "Broken Batch",
        "recipients": [
            {"name": "   "},
            {"name": "__FAIL__ One"}
        ]
    }

    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    status_response = client.get(f"/api/v1/jobs/{job_id}")
    data = status_response.json()

    assert data["status"] == JobStatus.FAILED
    assert data["total_count"] == 2
    assert data["success_count"] == 0
    assert data["failure_count"] == 2
