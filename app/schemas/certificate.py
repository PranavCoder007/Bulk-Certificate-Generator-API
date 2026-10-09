from datetime import datetime, date
from typing import List, Optional, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.models.certificate import JobStatus, ItemStatus

class RecipientInput(BaseModel):
    name: Any = Field(..., description="Full name of the recipient")
    email: Any = Field(..., description="Email address of the recipient")

class BulkCertificateCreateRequest(BaseModel):
    event_name: str = Field(..., min_length=1, max_length=255, description="Name of event, course, or workshop")
    certificate_title: Optional[str] = Field("Certificate of Completion", max_length=255, description="Title of the certificate")
    issuer_name: str = Field(..., min_length=1, max_length=255, description="Issuing authority or organization")
    issue_date: Optional[str] = Field(None, max_length=50, description="Date of issuance (e.g. YYYY-MM-DD or formatted date). Defaults to today.")
    recipients: List[RecipientInput] = Field(..., description="List of recipient details")

    @field_validator("event_name", "issuer_name")
    @classmethod
    def check_non_empty_strings(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace only")
        return v.strip()

    @field_validator("recipients")
    @classmethod
    def check_recipients_not_empty(cls, v: List[RecipientInput]) -> List[RecipientInput]:
        if not v:
            raise ValueError("Recipients list cannot be empty")
        return v

class CertificateItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    recipient_name: str
    recipient_email: str
    certificate_number: str
    status: ItemStatus
    file_name: Optional[str] = None
    download_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class JobSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    status: JobStatus
    event_name: str
    total_count: int
    processed_count: int
    success_count: int
    failure_count: int
    created_at: datetime
    updated_at: datetime
    message: str
    status_url: str

class JobDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    event_name: str
    certificate_title: str
    issuer_name: str
    issue_date: str
    status: JobStatus
    total_count: int
    processed_count: int
    success_count: int
    failure_count: int
    created_at: datetime
    updated_at: datetime
    zip_download_url: Optional[str] = None
    items: List[CertificateItemResponse]
