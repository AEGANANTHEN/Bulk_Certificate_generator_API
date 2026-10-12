import pytest
from pydantic import ValidationError
from app.schemas.recipient import RecipientInput
from app.schemas.job import JobCreateRequest


def test_recipient_input_valid():
    """Test valid recipient input schema."""
    rec = RecipientInput(name="  John Doe  ", email="  JOHN.DOE@EXAMPLE.COM ")
    assert rec.name == "John Doe"
    assert rec.email == "john.doe@example.com"


def test_recipient_input_empty_name():
    """Test recipient with empty name fails validation."""
    with pytest.raises(ValidationError):
        RecipientInput(name="   ", email="john@example.com")


def test_recipient_input_invalid_email():
    """Test recipient with invalid email syntax fails validation."""
    with pytest.raises(ValidationError):
        RecipientInput(name="John Doe", email="not-an-email")


def test_job_create_request_empty_recipients():
    """Test job request with empty recipients list fails."""
    with pytest.raises(ValidationError):
        JobCreateRequest(
            event_name="Machine Learning Bootcamp",
            recipients=[]
        )


def test_job_create_request_invalid_date():
    """Test job request with malformed date fails."""
    with pytest.raises(ValidationError):
        JobCreateRequest(
            event_name="Machine Learning Bootcamp",
            issue_date="12/10/2026",  # Must be YYYY-MM-DD
            recipients=[{"name": "Alice"}]
        )


def test_api_validation_errors(client):
    """Test that API returns 422 on invalid payload."""
    # Empty payload
    response = client.post("/api/v1/jobs", json={})
    assert response.status_code == 422

    # Empty recipients list
    response = client.post("/api/v1/jobs", json={
        "event_name": "Test Event",
        "recipients": []
    })
    assert response.status_code == 422

    # Malformed date
    response = client.post("/api/v1/jobs", json={
        "event_name": "Test Event",
        "issue_date": "invalid-date",
        "recipients": [{"name": "Bob"}]
    })
    assert response.status_code == 422
