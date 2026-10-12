import os
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.enums import CertificateStatus
from app.schemas.certificate import CertificateVerificationResponse
from app.services.job_service import JobService
from app.config import settings

router = APIRouter(prefix="/certificates", tags=["Certificates"])


@router.get(
    "/{cert_id}/download",
    summary="Download an individual certificate",
    response_description="Returns the PDF or PNG certificate file"
)
def download_certificate(
    cert_id: str,
    format: str = Query("pdf", pattern="^(pdf|png)$", description="Format to download: 'pdf' or 'png'"),
    db: Session = Depends(get_db)
):
    """
    Download an individual certificate in PDF or PNG format.
    """
    cert = JobService.get_certificate_by_id(db, cert_id)
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID '{cert_id}' not found."
        )

    if cert.status != CertificateStatus.SUCCESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate generation has not completed successfully. Current status: {cert.status}. Error: {cert.error_message or 'None'}"
        )

    file_path = cert.file_path_pdf if format == "pdf" else cert.file_path_png
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The requested {format.upper()} file was not found on the server."
        )

    media_type = "application/pdf" if format == "pdf" else "image/png"
    clean_name = "".join(c for c in cert.recipient_name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    filename = f"{cert.certificate_code}_{clean_name}.{format}"

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename
    )


@router.get(
    "/verify/{certificate_code}",
    response_model=CertificateVerificationResponse,
    summary="Verify authenticity of a certificate by certificate code"
)
def verify_certificate(
    certificate_code: str,
    db: Session = Depends(get_db)
):
    """
    Public verification endpoint to authenticate a certificate using its unique certificate ID.
    This endpoint is encoded into the QR code printed on every certificate.
    """
    cert = JobService.get_certificate_by_code(db, certificate_code.strip())
    if not cert or cert.status != CertificateStatus.SUCCESS:
        return CertificateVerificationResponse(
            is_valid=False,
            certificate_code=certificate_code,
            message="Certificate is INVALID or does not exist in the records."
        )

    job = cert.job
    return CertificateVerificationResponse(
        is_valid=True,
        certificate_code=cert.certificate_code,
        recipient_name=cert.recipient_name,
        event_name=job.event_name if job else "N/A",
        issuer_name=job.issuer_name if job else "N/A",
        issue_date=job.issue_date if job else "N/A",
        issued_at=cert.generated_at,
        message="Certificate is authentic and verified."
    )


@router.get(
    "/sample-preview",
    summary="Get sample certificate preview image",
    response_description="Returns a rendered sample PNG certificate for template preview"
)
def get_sample_preview():
    """
    Returns a sample rendered certificate PNG for previewing the template design.
    """
    sample_png = settings.CERTIFICATES_DIR / "sample_preview.png"
    if not sample_png.exists():
        from app.services.generator import CertificateGenerator
        png_path, _ = CertificateGenerator.generate_certificate(
            recipient_name="Aarav Sharma",
            event_name="Autonomous Drone Systems & Computer Vision",
            title="Certificate of Achievement",
            issuer_name="AEREO Academy",
            issue_date="2026-10-12",
            certificate_code="AEREO-SAMPLE-PREVIEW",
            output_dir=settings.CERTIFICATES_DIR
        )
        return FileResponse(path=png_path, media_type="image/png")

    return FileResponse(path=str(sample_png), media_type="image/png")

