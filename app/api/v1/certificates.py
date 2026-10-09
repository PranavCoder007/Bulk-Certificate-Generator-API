from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.certificate import CertificateItem, ItemStatus
from app.schemas.certificate import CertificateItemResponse

router = APIRouter(prefix="/certificates", tags=["Certificates"])

@router.get(
    "/{certificate_id}",
    response_model=CertificateItemResponse,
    summary="Get single certificate metadata",
    description="Fetches metadata and download status for an individual certificate."
)
def get_certificate_info(
    certificate_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    item = db.query(CertificateItem).filter(CertificateItem.id == certificate_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate item '{certificate_id}' not found."
        )

    base_url = str(request.base_url).rstrip("/")
    download_url = f"{base_url}/api/v1/certificates/{item.id}/download" if item.status == ItemStatus.SUCCESS.value else None

    return CertificateItemResponse(
        id=item.id,
        recipient_name=item.recipient_name,
        recipient_email=item.recipient_email,
        certificate_number=item.certificate_number,
        status=ItemStatus(item.status),
        file_name=item.file_name,
        download_url=download_url,
        error_message=item.error_message,
        created_at=item.created_at,
        updated_at=item.updated_at
    )

@router.get(
    "/{certificate_id}/download",
    summary="Download single certificate PDF",
    description="Downloads the generated PDF certificate for an individual recipient."
)
def download_certificate_pdf(
    certificate_id: str,
    db: Session = Depends(get_db)
):
    item = db.query(CertificateItem).filter(CertificateItem.id == certificate_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate item '{certificate_id}' not found."
        )

    if item.status != ItemStatus.SUCCESS.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate is not ready for download. Current status: '{item.status}'. {item.error_message or ''}"
        )

    if not item.file_path or not Path(item.file_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generated certificate file not found on disk."
        )

    return FileResponse(
        path=item.file_path,
        media_type="application/pdf",
        filename=item.file_name or "certificate.pdf"
    )
