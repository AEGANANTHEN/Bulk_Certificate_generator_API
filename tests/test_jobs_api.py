from app.models.enums import JobStatus, CertificateStatus
from app.services.job_service import JobService


def test_create_job_and_poll_status(client, test_db):
    """Test full workflow: create job, process background task, and verify status."""
    payload = {
        "title": "Certificate of Completion",
        "event_name": "Full Stack & Cloud Bootcamp",
        "issuer_name": "AEREO Academy",
        "issue_date": "2026-10-12",
        "recipients": [
            {"name": "Alice Johnson", "email": "alice@example.com"},
            {"name": "Bob Smith", "email": "bob@example.com"}
        ]
    }

    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["total_count"] == 2
    job_id = data["job_id"]

    # In TestClient, FastAPI executes background tasks synchronously before returning
    # Let's verify the updated status
    status_response = client.get(f"/api/v1/jobs/{job_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()

    assert status_data["job_id"] == job_id
    assert status_data["status"] == JobStatus.COMPLETED
    assert status_data["total_count"] == 2
    assert status_data["processed_count"] == 2
    assert status_data["success_count"] == 2
    assert status_data["failure_count"] == 0
    assert status_data["progress_percentage"] == 100.0
    assert len(status_data["certificates"]) == 2

    # Check recipient details
    for cert in status_data["certificates"]:
        assert cert["status"] == CertificateStatus.SUCCESS
        assert cert["download_pdf_url"] is not None
        assert cert["download_png_url"] is not None
        assert cert["certificate_code"].startswith("AEREO-")


def test_list_jobs(client):
    """Test GET /api/v1/jobs returns paginated job list."""
    payload = {
        "event_name": "Python Mastery",
        "recipients": [{"name": "User 1"}]
    }
    client.post("/api/v1/jobs", json=payload)

    response = client.get("/api/v1/jobs?limit=10")
    assert response.status_code == 200
    jobs = response.json()
    assert isinstance(jobs, list)
    assert len(jobs) >= 1
    assert "job_id" in jobs[0]


def test_get_nonexistent_job(client):
    """Test 404 response for non-existent job ID."""
    response = client.get("/api/v1/jobs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
