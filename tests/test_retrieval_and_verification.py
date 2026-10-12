import io
import zipfile
from app.models.enums import CertificateStatus


def test_download_individual_certificates(client):
    """Test downloading individual PDF and PNG certificate files."""
    payload = {
        "event_name": "Drone Flight Operations",
        "recipients": [{"name": "Priya Sharma", "email": "priya@example.com"}]
    }

    create_res = client.post("/api/v1/jobs", json=payload)
    job_id = create_res.json()["job_id"]

    job_res = client.get(f"/api/v1/jobs/{job_id}")
    cert = job_res.json()["certificates"][0]
    cert_id = cert["id"]
    code = cert["certificate_code"]

    # 1. Download PDF
    pdf_res = client.get(f"/api/v1/certificates/{cert_id}/download?format=pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 1000

    # 2. Download PNG
    png_res = client.get(f"/api/v1/certificates/{cert_id}/download?format=png")
    assert png_res.status_code == 200
    assert png_res.headers["content-type"] == "image/png"
    assert len(png_res.content) > 1000

    # 3. Verify public authenticity endpoint
    verify_res = client.get(f"/api/v1/certificates/verify/{code}")
    assert verify_res.status_code == 200
    vdata = verify_res.json()
    assert vdata["is_valid"] is True
    assert vdata["recipient_name"] == "Priya Sharma"
    assert vdata["event_name"] == "Drone Flight Operations"
    assert vdata["certificate_code"] == code


def test_bulk_zip_download(client):
    """Test downloading all generated certificates in a job as a single ZIP archive."""
    payload = {
        "event_name": "Robotics & AI Symposium",
        "recipients": [
            {"name": "Dev Patel"},
            {"name": "Sneha Roy"}
        ]
    }

    create_res = client.post("/api/v1/jobs", json=payload)
    job_id = create_res.json()["job_id"]

    zip_res = client.get(f"/api/v1/jobs/{job_id}/download-zip?format=pdf")
    assert zip_res.status_code == 200
    assert zip_res.headers["content-type"] == "application/zip"

    # Inspect zip contents
    with zipfile.ZipFile(io.BytesIO(zip_res.content)) as zf:
        namelist = zf.namelist()
        assert len(namelist) == 2
        for name in namelist:
            assert name.endswith(".pdf")


def test_verify_nonexistent_certificate(client):
    """Test verifying a fake or non-existent certificate returns invalid."""
    verify_res = client.get("/api/v1/certificates/verify/FAKE-CODE-9999")
    assert verify_res.status_code == 200
    vdata = verify_res.json()
    assert vdata["is_valid"] is False
