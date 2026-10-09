import uuid
from datetime import datetime, timezone, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.certificate import GenerationJob, CertificateItem, JobStatus, ItemStatus
from app.schemas.certificate import (
    BulkCertificateCreateRequest,
    JobSummaryResponse,
    JobDetailResponse,
    CertificateItemResponse
)
from app.services.worker import process_bulk_job
from app.services.storage import StorageService

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post(
    "",
    response_model=JobSummaryResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit bulk certificate generation job",
    description="Accepts bulk recipient records and queues an asynchronous generation job."
)
def create_bulk_certificate_job(
    payload: BulkCertificateCreateRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db)
):
    job_id = str(uuid.uuid4())
    issue_date_str = payload.issue_date or date.today().strftime("%B %d, %Y")

    job = GenerationJob(
        id=job_id,
        event_name=payload.event_name,
        certificate_title=payload.certificate_title or "Certificate of Completion",
        issuer_name=payload.issuer_name,
        issue_date=issue_date_str,
        status=JobStatus.PENDING.value,
        total_count=len(payload.recipients),
        processed_count=0,
        success_count=0,
        failure_count=0,
        error_summary=None
    )
    db.add(job)

    # Pre-populate items
    short_uuid = job_id[:8].upper()
    for idx, recipient in enumerate(payload.recipients, start=1):
        cert_number = f"CERT-{short_uuid}-{idx:04d}"
        item = CertificateItem(
            id=str(uuid.uuid4()),
            job_id=job_id,
            recipient_name=str(recipient.name) if recipient.name is not None else "",
            recipient_email=str(recipient.email) if recipient.email is not None else "",
            certificate_number=cert_number,
            status=ItemStatus.PENDING.value
        )
        db.add(item)

    db.commit()
    db.refresh(job)

    # Queue background task
    background_tasks.add_task(process_bulk_job, job_id)

    base_url = str(request.base_url).rstrip("/")
    status_url = f"{base_url}/api/v1/jobs/{job_id}"

    return JobSummaryResponse(
        job_id=job.id,
        status=JobStatus(job.status),
        event_name=job.event_name,
        total_count=job.total_count,
        processed_count=job.processed_count,
        success_count=job.success_count,
        failure_count=job.failure_count,
        created_at=job.created_at,
        updated_at=job.updated_at,
        message="Bulk certificate generation job queued successfully.",
        status_url=status_url
    )

@router.get(
    "/{job_id}",
    response_model=JobDetailResponse,
    summary="Get job status and recipient details",
    description="Retrieves the current progress and individual certificate results for a job."
)
def get_job_details(
    job_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate job with ID '{job_id}' not found."
        )

    base_url = str(request.base_url).rstrip("/")
    
    # Transform items to schema
    item_responses: List[CertificateItemResponse] = []
    for it in job.items:
        download_url = f"{base_url}/api/v1/certificates/{it.id}/download" if it.status == ItemStatus.SUCCESS.value else None
        item_responses.append(
            CertificateItemResponse(
                id=it.id,
                recipient_name=it.recipient_name,
                recipient_email=it.recipient_email,
                certificate_number=it.certificate_number,
                status=ItemStatus(it.status),
                file_name=it.file_name,
                download_url=download_url,
                error_message=it.error_message,
                created_at=it.created_at,
                updated_at=it.updated_at
            )
        )

    zip_url = f"{base_url}/api/v1/jobs/{job.id}/download" if job.success_count > 0 else None

    return JobDetailResponse(
        job_id=job.id,
        event_name=job.event_name,
        certificate_title=job.certificate_title,
        issuer_name=job.issuer_name,
        issue_date=job.issue_date,
        status=JobStatus(job.status),
        total_count=job.total_count,
        processed_count=job.processed_count,
        success_count=job.success_count,
        failure_count=job.failure_count,
        created_at=job.created_at,
        updated_at=job.updated_at,
        zip_download_url=zip_url,
        items=item_responses
    )

@router.get(
    "/{job_id}/download",
    summary="Download all certificates as ZIP archive",
    description="Downloads a ZIP archive containing all successfully generated certificates for this job."
)
def download_job_certificates_zip(
    job_id: str,
    db: Session = Depends(get_db)
):
    from fastapi.responses import FileResponse
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate job with ID '{job_id}' not found."
        )

    if job.success_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No successful certificates generated for job '{job_id}' yet (Status: {job.status})."
        )

    zip_file = StorageService.create_job_zip(job.id, job.items)
    if not zip_file or not zip_file.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to package certificates into a ZIP archive."
        )

    sanitized_event = StorageService.sanitize_filename(job.event_name)
    archive_name = f"{sanitized_event}_certificates_{job.id[:8]}.zip"

    return FileResponse(
        path=str(zip_file),
        media_type="application/zip",
        filename=archive_name
    )

@router.get(
    "",
    response_model=List[JobSummaryResponse],
    summary="List all certificate jobs",
    description="Lists recent certificate generation jobs."
)
def list_jobs(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    jobs = db.query(GenerationJob).order_by(GenerationJob.created_at.desc()).offset(offset).limit(limit).all()
    base_url = str(request.base_url).rstrip("/")
    
    results = []
    for job in jobs:
        results.append(
            JobSummaryResponse(
                job_id=job.id,
                status=JobStatus(job.status),
                event_name=job.event_name,
                total_count=job.total_count,
                processed_count=job.processed_count,
                success_count=job.success_count,
                failure_count=job.failure_count,
                created_at=job.created_at,
                updated_at=job.updated_at,
                message=f"Job {job.status}",
                status_url=f"{base_url}/api/v1/jobs/{job.id}"
            )
        )
    return results
