from pathlib import Path
from app.services.generator import CertificateGenerator
from app.services.storage import StorageService

def test_certificate_pdf_generation(tmp_path):
    output_pdf = tmp_path / "cert_test.pdf"
    
    result = CertificateGenerator.generate_pdf(
        output_path=output_pdf,
        recipient_name="Grace Hopper",
        event_name="Advanced Computer Architecture",
        certificate_title="Certificate of Achievement",
        issuer_name="National Computing Institute",
        issue_date="2026-10-09",
        certificate_number="CERT-GH-1945"
    )

    assert result.exists()
    assert result.stat().st_size > 500  # Should be a valid PDF file
    
    # Read first bytes to verify it's a valid PDF header
    with open(result, "rb") as f:
        header = f.read(5)
    assert header == b"%PDF-"

def test_filename_sanitization():
    unsafe_name = "Dr. Martin Luther King, Jr. / Special @ Winner *!?"
    sanitized = StorageService.sanitize_filename(unsafe_name)
    assert "/" not in sanitized
    assert "@" not in sanitized
    assert "*" not in sanitized
    assert "?" not in sanitized
    assert "Dr._Martin_Luther_King__Jr" in sanitized
