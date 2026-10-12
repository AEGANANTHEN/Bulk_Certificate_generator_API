import os
import zipfile
from pathlib import Path
from typing import Optional
from app.config import settings
from app.models.job import CertificateJob
from app.models.enums import CertificateStatus

ARCHIVES_DIR = settings.STORAGE_DIR / "archives"
ARCHIVES_DIR.mkdir(parents=True, exist_ok=True)


class ArchiveService:
    """Service to create and manage zip archives for bulk certificate downloads."""

    @classmethod
    def create_job_zip(cls, job: CertificateJob, format_type: str = "pdf") -> Optional[Path]:
        """
        Creates a ZIP file containing all successfully generated certificates for a job.
        format_type can be 'pdf', 'png', or 'both'.
        Returns Path to the created zip archive, or None if no successful certificates exist.
        """
        successful_certs = [
            cert for cert in job.certificates if cert.status == CertificateStatus.SUCCESS
        ]
        if not successful_certs:
            return None

        zip_filename = f"certificates_job_{job.id}_{format_type}.zip"
        zip_path = ARCHIVES_DIR / zip_filename

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for cert in successful_certs:
                # Sanitize recipient name for filename
                clean_name = "".join(c for c in cert.recipient_name if c.isalnum() or c in (" ", "_", "-")).strip()
                clean_name = clean_name.replace(" ", "_")

                if format_type in ("pdf", "both") and cert.file_path_pdf and os.path.exists(cert.file_path_pdf):
                    arcname = f"{cert.certificate_code}_{clean_name}.pdf"
                    zipf.write(cert.file_path_pdf, arcname=arcname)

                if format_type in ("png", "both") and cert.file_path_png and os.path.exists(cert.file_path_png):
                    arcname = f"{cert.certificate_code}_{clean_name}.png"
                    zipf.write(cert.file_path_png, arcname=arcname)

        return zip_path
