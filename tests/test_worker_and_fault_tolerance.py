from pathlib import Path
from app.models.certificate import JobStatus, ItemStatus
from app.services.worker import process_bulk_job

def test_full_success_batch(client):
    payload = {
        "event_name": "Autonomous Drone Navigation",
        "certificate_title": "Certificate of Completion",
        "issuer_name": "Aereo Systems",
        "recipients": [
            {"name": "Sarah Connor", "email": "sarah@skynet-defense.org"},
            {"name": "John Connor", "email": "john@resistance.org"}
        ]
    }

    create_res = client.post("/api/v1/jobs", json=payload)
    assert create_res.status_code == 202
    job_id = create_res.json()["job_id"]

    # Since TestClient runs BackgroundTasks synchronously, job will have finished
    status_res = client.get(f"/api/v1/jobs/{job_id}")
    assert status_res.status_code == 200
    data = status_res.json()

    assert data["status"] == JobStatus.COMPLETED.value
    assert data["total_count"] == 2
    assert data["processed_count"] == 2
    assert data["success_count"] == 2
    assert data["failure_count"] == 0
    assert data["zip_download_url"] is not None

    for item in data["items"]:
        assert item["status"] == ItemStatus.SUCCESS.value
        assert item["download_url"] is not None
        assert item["error_message"] is None

def test_fault_isolation_with_invalid_recipients(client):
    """
    CRITICAL REQUIREMENT TEST:
    A failure or invalid recipient data must NOT prevent other valid certificates
    in the same batch from being generated successfully.
    """
    payload = {
        "event_name": "Robotics Engineering Workshop",
        "issuer_name": "Aereo Systems",
        "recipients": [
            {"name": "Valid Student One", "email": "student1@example.com"},
            {"name": "Bad Email Student", "email": "invalid_email_format"},
            {"name": "", "email": "noname@example.com"},
            {"name": "Valid Student Two", "email": "student2@example.com"}
        ]
    }

    create_res = client.post("/api/v1/jobs", json=payload)
    assert create_res.status_code == 202
    job_id = create_res.json()["job_id"]

    status_res = client.get(f"/api/v1/jobs/{job_id}")
    assert status_res.status_code == 200
    data = status_res.json()

    # Job status should be PARTIALLY_COMPLETED
    assert data["status"] == JobStatus.PARTIALLY_COMPLETED.value
    assert data["total_count"] == 4
    assert data["processed_count"] == 4
    assert data["success_count"] == 2
    assert data["failure_count"] == 2

    items = data["items"]
    # Item 0 (Valid Student One) should SUCCEED
    assert items[0]["recipient_name"] == "Valid Student One"
    assert items[0]["status"] == ItemStatus.SUCCESS.value
    assert items[0]["download_url"] is not None

    # Item 1 (Bad Email) should FAIL with clear error message
    assert items[1]["recipient_name"] == "Bad Email Student"
    assert items[1]["status"] == ItemStatus.FAILED.value
    assert "Invalid email format" in items[1]["error_message"]
    assert items[1]["download_url"] is None

    # Item 2 (Blank name) should FAIL with clear error message
    assert items[2]["status"] == ItemStatus.FAILED.value
    assert "Recipient name is required" in items[2]["error_message"]
    assert items[2]["download_url"] is None

    # Item 3 (Valid Student Two) MUST SUCCEED despite earlier failures
    assert items[3]["recipient_name"] == "Valid Student Two"
    assert items[3]["status"] == ItemStatus.SUCCESS.value
    assert items[3]["download_url"] is not None

def test_all_failed_batch(client):
    payload = {
        "event_name": "Test Course",
        "issuer_name": "Aereo Systems",
        "recipients": [
            {"name": "User 1", "email": "invalid_email"},
            {"name": "", "email": "bad"}
        ]
    }

    create_res = client.post("/api/v1/jobs", json=payload)
    job_id = create_res.json()["job_id"]

    status_res = client.get(f"/api/v1/jobs/{job_id}")
    data = status_res.json()

    assert data["status"] == JobStatus.FAILED.value
    assert data["total_count"] == 2
    assert data["success_count"] == 0
    assert data["failure_count"] == 2
    assert data["zip_download_url"] is None
