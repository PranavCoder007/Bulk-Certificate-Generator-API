import pytest
from app.models.certificate import JobStatus

def test_create_bulk_job_success(client):
    payload = {
        "event_name": "Full Stack AI Bootcamp",
        "certificate_title": "Certificate of Excellence",
        "issuer_name": "Aereo Academy",
        "issue_date": "2026-10-09",
        "recipients": [
            {"name": "Alice Smith", "email": "alice@example.com"},
            {"name": "Bob Jones", "email": "bob@example.com"}
        ]
    }

    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status"] in [JobStatus.PENDING.value, JobStatus.PROCESSING.value, JobStatus.COMPLETED.value]
    assert data["total_count"] == 2
    assert "status_url" in data

def test_create_bulk_job_validation_missing_fields(client):
    # Missing event_name and issuer_name
    payload = {
        "recipients": [{"name": "Alice", "email": "alice@example.com"}]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422

def test_create_bulk_job_validation_empty_event_name(client):
    payload = {
        "event_name": "   ",
        "issuer_name": "Aereo Academy",
        "recipients": [{"name": "Alice", "email": "alice@example.com"}]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422

def test_create_bulk_job_validation_empty_recipients(client):
    payload = {
        "event_name": "Python Mastery",
        "issuer_name": "Aereo Academy",
        "recipients": []
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422

def test_get_non_existent_job_404(client):
    response = client.get("/api/v1/jobs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404

def test_list_jobs(client):
    # Create two jobs
    for name in ["Job 1", "Job 2"]:
        client.post("/api/v1/jobs", json={
            "event_name": name,
            "issuer_name": "Aereo",
            "recipients": [{"name": "User", "email": "user@example.com"}]
        })

    response = client.get("/api/v1/jobs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
