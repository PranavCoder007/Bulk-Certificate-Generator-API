import logging
import re
from typing import Any, Optional
from datetime import datetime, timezone

from app.core.database import SessionLocal
from app.models.certificate import GenerationJob, CertificateItem, JobStatus, ItemStatus
from app.services.generator import CertificateGenerator
from app.services.storage import StorageService

logger = logging.getLogger(__name__)

# Basic robust email regex
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def validate_recipient(name: Any, email: Any) -> Optional[str]:
    """
    Validates recipient details.
    Returns an error message string if invalid, or None if valid.
    """
    if not name or not isinstance(name, str) or not name.strip():
        return "Recipient name is required and cannot be empty"
    if not email or not isinstance(email, str) or not email.strip():
        return "Recipient email is required and cannot be empty"
    if not EMAIL_REGEX.match(email.strip()):
        return f"Invalid email format: '{email}'"
    return None

def process_bulk_job(job_id: str) -> None:
    """
    Background worker function that processes all certificate items for a job.
    Includes strict fault isolation: failure of one certificate never interrupts the rest.
    """
    db = SessionLocal()
    try:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found for background execution.")
            return

        # Mark job as PROCESSING
        job.status = JobStatus.PROCESSING.value
        job.updated_at = datetime.now(timezone.utc)
        db.commit()

        items = db.query(CertificateItem).filter(CertificateItem.job_id == job_id).all()
        
        for item in items:
            try:
                # 1. Recipient Validation
                val_error = validate_recipient(item.recipient_name, item.recipient_email)
                if val_error:
                    item.status = ItemStatus.FAILED.value
                    item.error_message = f"Validation Error: {val_error}"
                    job.failure_count += 1
                else:
                    # 2. Certificate Generation
                    output_file = StorageService.get_certificate_path(
                        job_id=job.id,
                        recipient_name=item.recipient_name,
                        cert_number=item.certificate_number
                    )
                    
                    CertificateGenerator.generate_pdf(
                        output_path=output_file,
                        recipient_name=item.recipient_name.strip(),
                        event_name=job.event_name,
                        certificate_title=job.certificate_title,
                        issuer_name=job.issuer_name,
                        issue_date=job.issue_date,
                        certificate_number=item.certificate_number
                    )

                    item.file_path = str(output_file)
                    item.file_name = output_file.name
                    item.status = ItemStatus.SUCCESS.value
                    item.error_message = None
                    job.success_count += 1

            except Exception as exc:
                # Fault isolation: record failure reason and continue with next item
                logger.exception(f"Error generating certificate for item {item.id}: {exc}")
                item.status = ItemStatus.FAILED.value
                item.error_message = f"Generation Error: {str(exc)}"
                job.failure_count += 1

            finally:
                item.updated_at = datetime.now(timezone.utc)
                job.processed_count += 1
                db.commit()

        # Update final job status
        if job.success_count == job.total_count and job.total_count > 0:
            job.status = JobStatus.COMPLETED.value
            job.error_summary = "All certificates generated successfully."
        elif job.failure_count == job.total_count:
            job.status = JobStatus.FAILED.value
            job.error_summary = "All certificate generations failed."
        else:
            job.status = JobStatus.PARTIALLY_COMPLETED.value
            job.error_summary = (
                f"Completed with {job.success_count} succeeded and {job.failure_count} failed."
            )

        job.updated_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as e:
        logger.exception(f"Fatal error processing job {job_id}: {e}")
        if job:
            job.status = JobStatus.FAILED.value
            job.error_summary = f"Fatal system error: {str(e)}"
            db.commit()
    finally:
        db.close()
