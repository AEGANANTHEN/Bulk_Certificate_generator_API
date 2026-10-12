import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import JobStatus, CertificateStatus


class CertificateJob(Base):
    __tablename__ = "certificate_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    event_name = Column(String(255), nullable=False)
    issuer_name = Column(String(255), nullable=False)
    issue_date = Column(String(50), nullable=False)
    
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    total_count = Column(Integer, default=0, nullable=False)
    processed_count = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    certificates = relationship(
        "CertificateRecord",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="CertificateRecord.created_at"
    )

    def __repr__(self):
        return f"<CertificateJob(id={self.id}, status={self.status}, total={self.total_count})>"


class CertificateRecord(Base):
    __tablename__ = "certificate_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("certificate_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    recipient_name = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=True)
    certificate_code = Column(String(64), unique=True, nullable=False, index=True)
    
    status = Column(SQLEnum(CertificateStatus), default=CertificateStatus.PENDING, nullable=False, index=True)
    file_path_pdf = Column(String(512), nullable=True)
    file_path_png = Column(String(512), nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    generated_at = Column(DateTime, nullable=True)

    # Relationship
    job = relationship("CertificateJob", back_populates="certificates")

    def __repr__(self):
        return f"<CertificateRecord(id={self.id}, code={self.certificate_code}, status={self.status})>"
