import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.enums import JobStatus, CertificateStatus
from app.models.job import CertificateJob
from app.schemas.job import JobCreateRequest, JobSummaryResponse, JobDetailResponse
from app.schemas.certificate import CertificateItemResponse
from app.services.job_service import JobService
from app.services.archive_service import ArchiveService
from app.config import settings

router = APIRouter(prefix="/jobs", tags=["Certificate Jobs"])


def _build_summary_response(job: CertificateJob) -> JobSummaryResponse:
    pct = round((job.processed_count / job.total_count) * 100, 2) if job.total_count > 0 else 0.0
    status_url = f"{settings.API_V1_PREFIX}/jobs/{job.id}"
    msg = f"Job is currently {job.status}. Processed {job.processed_count}/{job.total_count} recipients."
    if job.status == JobStatus.COMPLETED:
        msg = f"Job completed successfully. All {job.success_count} certificates generated."
    elif job.status == JobStatus.PARTIALLY_COMPLETED:
        msg = f"Job completed with errors. {job.success_count} succeeded, {job.failure_count} failed."
    elif job.status == JobStatus.FAILED:
        msg = f"Job failed. None of the certificates were generated."

    return JobSummaryResponse(
        job_id=job.id,
        status=job.status,
        title=job.title,
        event_name=job.event_name,
        issuer_name=job.issuer_name,
        issue_date=job.issue_date,
        total_count=job.total_count,
        processed_count=job.processed_count,
        success_count=job.success_count,
        failure_count=job.failure_count,
        progress_percentage=pct,
        status_url=status_url,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
        message=msg
    )


@router.post(
    "",
    response_model=JobSummaryResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a bulk certificate generation job",
    description="Accepts a list of recipients and enqueues certificate generation in the background."
)
def create_generation_job(
    payload: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Submits a bulk certificate request.
    Validates the structure, records the job in the database with status PENDING,
    and enqueues background processing immediately returning a 202 Accepted status with job_id.
    """
    job = JobService.create_job(db, payload)
    
    # Launch async background worker
    background_tasks.add_task(JobService.process_job_task, job.id)

    return _build_summary_response(job)


@router.get(
    "",
    response_model=List[JobSummaryResponse],
    summary="List all certificate jobs"
)
def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List recent certificate generation jobs with pagination."""
    jobs = (
        db.query(CertificateJob)
        .order_by(CertificateJob.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_build_summary_response(j) for j in jobs]


@router.get(
    "/{job_id}",
    response_model=JobDetailResponse,
    summary="Get job status, progress, and recipient certificate details"
)
def get_job_status(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Poll the progress and details of a certificate generation job.
    Returns status, percentage progress, counts, and per-recipient certificate status.
    """
    job = JobService.get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found."
        )

    summary = _build_summary_response(job)
    
    cert_items = []
    for cert in job.certificates:
        pdf_url = None
        png_url = None
        if cert.status == CertificateStatus.SUCCESS:
            pdf_url = f"{settings.API_V1_PREFIX}/certificates/{cert.id}/download?format=pdf"
            png_url = f"{settings.API_V1_PREFIX}/certificates/{cert.id}/download?format=png"

        cert_items.append(
            CertificateItemResponse(
                id=cert.id,
                recipient_name=cert.recipient_name,
                recipient_email=cert.recipient_email,
                certificate_code=cert.certificate_code,
                status=cert.status,
                download_pdf_url=pdf_url,
                download_png_url=png_url,
                error_message=cert.error_message,
                created_at=cert.created_at,
                generated_at=cert.generated_at
            )
        )

    zip_url = None
    if job.success_count > 0:
        zip_url = f"{settings.API_V1_PREFIX}/jobs/{job.id}/download-zip"

    return JobDetailResponse(
        **summary.model_dump(),
        zip_download_url=zip_url,
        certificates=cert_items
    )


@router.get(
    "/{job_id}/download-zip",
    summary="Download all generated certificates as a single ZIP archive",
    response_description="Returns a ZIP archive of certificates"
)
def download_job_zip(
    job_id: str,
    format: str = Query("pdf", pattern="^(pdf|png|both)$", description="Format to include in zip: 'pdf', 'png', or 'both'"),
    db: Session = Depends(get_db)
):
    """
    Downloads a single ZIP archive containing all successful certificates for this job.
    """
    job = JobService.get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found."
        )

    if job.success_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No certificates have been successfully generated for this job yet. Current status: {job.status}"
        )

    zip_path = ArchiveService.create_job_zip(job, format_type=format)
    if not zip_path or not os.path.exists(zip_path):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate the ZIP archive for this job."
        )

    filename = f"certificates_{job.id[:8]}_{format}.zip"
    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=filename
    )
