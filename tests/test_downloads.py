import io
import zipfile
from app.models.certificate import JobStatus, ItemStatus

def test_download_individual_certificate(client):
    payload = {
        "event_name": "Drone Flight Operations",
        "issuer_name": "Aereo Systems",
        "recipients": [
            {"name": "Neil Armstrong", "email": "neil@apollo.org"}
        ]
    }
    create_res = client.post("/api/v1/jobs", json=payload)
    job_id = create_res.json()["job_id"]

    job_data = client.get(f"/api/v1/jobs/{job_id}").json()
    cert_id = job_data["items"][0]["id"]

    # 1. Test get certificate metadata
    meta_res = client.get(f"/api/v1/certificates/{cert_id}")
    assert meta_res.status_code == 200
    assert meta_res.json()["recipient_name"] == "Neil Armstrong"

    # 2. Test download certificate PDF
    dl_res = client.get(f"/api/v1/certificates/{cert_id}/download")
    assert dl_res.status_code == 200
    assert dl_res.headers["content-type"] == "application/pdf"
    assert dl_res.content.startswith(b"%PDF-")

def test_download_failed_certificate_fails(client):
    payload = {
        "event_name": "Testing",
        "issuer_name": "Aereo",
        "recipients": [
            {"name": "Invalid Recipient", "email": "not-valid"}
        ]
    }
    create_res = client.post("/api/v1/jobs", json=payload)
    job_id = create_res.json()["job_id"]
    job_data = client.get(f"/api/v1/jobs/{job_id}").json()
    cert_id = job_data["items"][0]["id"]

    # Downloading a failed certificate must return 400
    dl_res = client.get(f"/api/v1/certificates/{cert_id}/download")
    assert dl_res.status_code == 400

def test_download_nonexistent_certificate_404(client):
    res = client.get("/api/v1/certificates/00000000-0000-0000-0000-000000000000/download")
    assert res.status_code == 404

def test_download_bulk_zip(client):
    payload = {
        "event_name": "Aero Design Conclave",
        "issuer_name": "Aereo Systems",
        "recipients": [
            {"name": "Participant One", "email": "p1@example.com"},
            {"name": "Participant Two", "email": "p2@example.com"}
        ]
    }
    create_res = client.post("/api/v1/jobs", json=payload)
    job_id = create_res.json()["job_id"]

    # Download bulk zip
    zip_res = client.get(f"/api/v1/jobs/{job_id}/download")
    assert zip_res.status_code == 200
    assert zip_res.headers["content-type"] == "application/zip"

    # Verify zip content
    with zipfile.ZipFile(io.BytesIO(zip_res.content)) as zf:
        namelist = zf.namelist()
        assert len(namelist) == 2
        for name in namelist:
            assert name.endswith(".pdf")

def test_download_bulk_zip_zero_successes_fails(client):
    payload = {
        "event_name": "Bad Batch",
        "issuer_name": "Aereo",
        "recipients": [
            {"name": "Invalid", "email": "bad_email"}
        ]
    }
    create_res = client.post("/api/v1/jobs", json=payload)
    job_id = create_res.json()["job_id"]

    # Downloading zip for all-failed job must return 400
    zip_res = client.get(f"/api/v1/jobs/{job_id}/download")
    assert zip_res.status_code == 400
