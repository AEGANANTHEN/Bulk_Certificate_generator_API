import re
import uuid
import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

import app.database as database
from app.models.job import CertificateJob, CertificateRecord
from app.models.enums import JobStatus, CertificateStatus
from app.schemas.job import JobCreateRequest
from app.schemas.recipient import RecipientRawInput
from app.services.generator import CertificateGenerator
from app.config import settings

logger = logging.getLogger(__name__)
EMAIL_REGEX = re.compile(r"^[\w\.\+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-\.]+$")


class JobService:
    """Business logic for certificate generation jobs and background workers."""

    @staticmethod
    def generate_unique_code() -> str:
        """Generate a clean, professional, unique certificate code."""
        year = datetime.utcnow().year
        token = uuid.uuid4().hex[:8].upper()
        return f"AEREO-{year}-{token}"

    @classmethod
    def create_job(cls, db: Session, job_data: JobCreateRequest) -> CertificateJob:
        """
        Creates a new CertificateJob and pre-registers CertificateRecords for each recipient.
        Status is initialized as PENDING.
        """
        job = CertificateJob(
            title=job_data.title or settings.DEFAULT_TITLE,
            event_name=job_data.event_name,
            issuer_name=job_data.issuer_name or settings.DEFAULT_ISSUER,
            issue_date=job_data.issue_date or datetime.utcnow().strftime("%Y-%m-%d"),
            status=JobStatus.PENDING,
            total_count=len(job_data.recipients),
            processed_count=0,
            success_count=0,
            failure_count=0,
        )
        db.add(job)
        db.flush()  # Populate job.id

        # Pre-create certificate records
        for item in job_data.recipients:
            cert_record = CertificateRecord(
                job_id=job.id,
                recipient_name=item.name.strip() if item.name else "",
                recipient_email=item.email.strip() if item.email else None,
                certificate_code=cls.generate_unique_code(),
                status=CertificateStatus.PENDING,
            )
            db.add(cert_record)

        db.commit()
        db.refresh(job)
        return job

    @classmethod
    def process_job_task(cls, job_id: str):
        """
        Background task worker:
        Processes each recipient in the job independently.
        Catches and records failures per recipient to ensure fault isolation.
        Updates job status to COMPLETED, PARTIALLY_COMPLETED, or FAILED.
        """
        db: Session = database.SessionLocal()
        try:
            job = db.query(CertificateJob).filter(CertificateJob.id == job_id).first()
            if not job:
                logger.error(f"Job {job_id} not found for background execution.")
                return

            job.status = JobStatus.PROCESSING
            job.updated_at = datetime.utcnow()
            db.commit()

            records: List[CertificateRecord] = (
                db.query(CertificateRecord)
                .filter(CertificateRecord.job_id == job_id)
                .all()
            )

            for record in records:
                try:
                    # 1. Validation check
                    validation_error = cls._validate_recipient(record.recipient_name, record.recipient_email)
                    if validation_error:
                        record.status = CertificateStatus.FAILED
                        record.error_message = validation_error
                        job.failure_count += 1
                    else:
                        # 2. Certificate file generation
                        png_path, pdf_path = CertificateGenerator.generate_certificate(
                            recipient_name=record.recipient_name,
                            event_name=job.event_name,
                            title=job.title,
                            issuer_name=job.issuer_name,
                            issue_date=job.issue_date,
                            certificate_code=record.certificate_code,
                        )
                        record.file_path_png = png_path
                        record.file_path_pdf = pdf_path
                        record.status = CertificateStatus.SUCCESS
                        record.generated_at = datetime.utcnow()
                        job.success_count += 1

                except Exception as exc:
                    # Fault isolation: an individual exception does not abort the rest of the job
                    logger.exception(f"Error generating certificate for {record.recipient_name}: {exc}")
                    record.status = CertificateStatus.FAILED
                    record.error_message = f"Generation failed: {str(exc)}"
                    job.failure_count += 1

                finally:
                    job.processed_count += 1
                    job.updated_at = datetime.utcnow()
                    db.commit()

            # Final Job Status Determination
            if job.failure_count == 0 and job.success_count > 0:
                job.status = JobStatus.COMPLETED
            elif job.success_count > 0 and job.failure_count > 0:
                job.status = JobStatus.PARTIALLY_COMPLETED
            else:
                job.status = JobStatus.FAILED

            job.completed_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            db.commit()

        except Exception as e:
            logger.exception(f"Fatal error while processing job {job_id}: {e}")
            try:
                job = db.query(CertificateJob).filter(CertificateJob.id == job_id).first()
                if job:
                    job.status = JobStatus.FAILED
                    db.commit()
            except Exception:
                pass
        finally:
            db.close()

    @staticmethod
    def _validate_recipient(name: str, email: Optional[str]) -> Optional[str]:
        """
        Validates individual recipient fields.
        Returns an error string if invalid, or None if valid.
        """
        if not name or not name.strip():
            return "Recipient name cannot be empty or only whitespace."
        if len(name.strip()) > 200:
            return "Recipient name exceeds maximum length of 200 characters."
        if name.strip().startswith("__FAIL__"):
            return "Simulated recipient generation failure for testing fault isolation."
        
        if email:
            clean_email = email.strip()
            if not EMAIL_REGEX.match(clean_email):
                return f"Invalid email format: '{email}'."

        return None

    @classmethod
    def get_job_by_id(cls, db: Session, job_id: str) -> Optional[CertificateJob]:
        """Fetch job with certificates by job_id."""
        return db.query(CertificateJob).filter(CertificateJob.id == job_id).first()

    @classmethod
    def get_certificate_by_id(cls, db: Session, cert_id: str) -> Optional[CertificateRecord]:
        """Fetch certificate by ID."""
        return db.query(CertificateRecord).filter(CertificateRecord.id == cert_id).first()

    @classmethod
    def get_certificate_by_code(cls, db: Session, code: str) -> Optional[CertificateRecord]:
        """Fetch certificate by public verification code."""
        return db.query(CertificateRecord).filter(CertificateRecord.certificate_code == code).first()
