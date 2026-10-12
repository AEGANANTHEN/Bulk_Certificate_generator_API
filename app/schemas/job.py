from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.models.enums import JobStatus
from app.schemas.recipient import RecipientRawInput
from app.schemas.certificate import CertificateItemResponse


class JobCreateRequest(BaseModel):
    title: Optional[str] = Field("Certificate of Achievement", max_length=200, description="Certificate heading")
    event_name: str = Field(..., min_length=2, max_length=200, description="Name of the course, training, or event")
    issuer_name: Optional[str] = Field("AEREO Academy", max_length=200, description="Issuing organization or authority")
    issue_date: Optional[str] = Field(None, description="Issue date in YYYY-MM-DD format, defaults to current date")
    recipients: List[RecipientRawInput] = Field(..., description="List of recipients to generate certificates for")

    @field_validator("recipients")
    @classmethod
    def validate_recipients_not_empty(cls, v: List[RecipientRawInput]) -> List[RecipientRawInput]:
        if not v:
            raise ValueError("The recipients list cannot be empty. At least one recipient is required.")
        if len(v) > 5000:
            raise ValueError("Maximum 5000 recipients allowed per single bulk generation request.")
        return v

    @field_validator("issue_date")
    @classmethod
    def validate_issue_date(cls, v: Optional[str]) -> str:
        if not v:
            return date.today().strftime("%Y-%m-%d")
        try:
            # Validate format YYYY-MM-DD
            parsed = datetime.strptime(v.strip(), "%Y-%m-%d")
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid issue_date format. Must be YYYY-MM-DD (e.g., 2026-10-12).")


class JobSummaryResponse(BaseModel):
    job_id: str
    status: JobStatus
    title: str
    event_name: str
    issuer_name: str
    issue_date: str
    total_count: int
    processed_count: int
    success_count: int
    failure_count: int
    progress_percentage: float
    status_url: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    message: str

    model_config = ConfigDict(from_attributes=True)


class JobDetailResponse(JobSummaryResponse):
    zip_download_url: Optional[str] = None
    certificates: List[CertificateItemResponse] = []

    model_config = ConfigDict(from_attributes=True)
