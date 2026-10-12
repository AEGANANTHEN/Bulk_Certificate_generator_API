from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.enums import CertificateStatus

class CertificateItemResponse(BaseModel):
    id: str
    recipient_name: str
    recipient_email: Optional[str] = None
    certificate_code: str
    status: CertificateStatus
    download_pdf_url: Optional[str] = None
    download_png_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    generated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CertificateVerificationResponse(BaseModel):
    is_valid: bool
    certificate_code: str
    recipient_name: Optional[str] = None
    event_name: Optional[str] = None
    issuer_name: Optional[str] = None
    issue_date: Optional[str] = None
    issued_at: Optional[datetime] = None
    download_url: Optional[str] = None
    message: str
