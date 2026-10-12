import os
from pathlib import Path
from PIL import Image
from app.services.generator import CertificateGenerator


def test_certificate_generator_creates_files(temp_storage):
    """Test that CertificateGenerator produces valid PNG and PDF files."""
    png_path, pdf_path = CertificateGenerator.generate_certificate(
        recipient_name="Alice Smith",
        event_name="Robotics and Embedded Systems",
        title="Certificate of Excellence",
        issuer_name="AEREO Labs",
        issue_date="2026-10-12",
        certificate_code="TEST-CERT-1234",
        output_dir=temp_storage / "certificates"
    )

    # Assert paths exist
    assert os.path.exists(png_path)
    assert os.path.exists(pdf_path)

    # Check PNG properties
    with Image.open(png_path) as img:
        assert img.size == (2000, 1414)
        assert img.format == "PNG"

    # Check PDF file size is non-zero
    assert os.path.getsize(pdf_path) > 1000


def test_certificate_generator_auto_scales_long_name(temp_storage):
    """Test that very long recipient names do not crash the generator."""
    long_name = "Dr. Alexander Bartholomew Montgomery-Cunningham III"
    png_path, pdf_path = CertificateGenerator.generate_certificate(
        recipient_name=long_name,
        event_name="Aerospace Engineering & Navigation Systems",
        certificate_code="TEST-CERT-LONG",
        output_dir=temp_storage / "certificates"
    )

    assert os.path.exists(png_path)
    assert os.path.exists(pdf_path)
