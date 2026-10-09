import re
import zipfile
from pathlib import Path
from typing import List, Optional
from app.core.config import settings
from app.models.certificate import CertificateItem, ItemStatus

class StorageService:
    @staticmethod
    def sanitize_filename(name: str) -> str:
        """Removes unsafe characters for file paths."""
        cleaned = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', name.strip())
        return cleaned[:80]

    @classmethod
    def get_job_dir(cls, job_id: str) -> Path:
        """Returns and creates the dedicated directory for a generation job."""
        job_dir = settings.STORAGE_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir

    @classmethod
    def get_certificate_path(cls, job_id: str, recipient_name: str, cert_number: str) -> Path:
        """Determines the output file path for a recipient's certificate."""
        clean_name = cls.sanitize_filename(recipient_name)
        file_name = f"{clean_name}_{cert_number}.pdf"
        return cls.get_job_dir(job_id) / file_name

    @classmethod
    def get_job_zip_path(cls, job_id: str) -> Path:
        """Returns the path for the bulk zip archive of a job."""
        return cls.get_job_dir(job_id) / f"job_{job_id}_certificates.zip"

    @classmethod
    def create_job_zip(cls, job_id: str, items: List[CertificateItem]) -> Optional[Path]:
        """
        Creates a ZIP archive containing all successful certificate PDFs for the given job.
        Returns the Path to the zip file, or None if no successful certificates exist.
        """
        zip_path = cls.get_job_zip_path(job_id)
        successful_items = [
            item for item in items 
            if item.status == ItemStatus.SUCCESS.value and item.file_path and Path(item.file_path).exists()
        ]

        if not successful_items:
            return None

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for item in successful_items:
                source_path = Path(item.file_path)
                arcname = item.file_name or source_path.name
                zip_file.write(source_path, arcname=arcname)

        return zip_path
