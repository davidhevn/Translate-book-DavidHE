"""Tests for job status API endpoint."""
import io


def test_job_status_after_upload(client):
    """Test getting job status after upload."""
    # First upload a file
    content = b"PK\x03\x04" + b"\x00" * 100
    file = io.BytesIO(content)
    
    upload_response = client.post(
        "/api/upload",
        files={"file": ("test.docx", file, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    job_id = upload_response.json()["job_id"]
    
    # Get status
    response = client.get(f"/api/jobs/{job_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert data["step"] == "Queued"
    assert data["percent"] == 0
    assert data["error"] is None


def test_job_status_not_found(client):
    """Test getting status for non-existent job."""
    response = client.get("/api/jobs/non-existent-job-id")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_download_before_complete(client):
    """Test that download fails if job not complete."""
    # Upload a file first
    content = b"PK\x03\x04" + b"\x00" * 100
    file = io.BytesIO(content)
    
    upload_response = client.post(
        "/api/upload",
        files={"file": ("test.docx", file, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    job_id = upload_response.json()["job_id"]
    
    # Try to download before complete
    response = client.get(f"/api/download/{job_id}")
    
    assert response.status_code == 400
    assert "not complete" in response.json()["detail"].lower()


def test_download_job_not_found(client):
    """Test download with non-existent job."""
    response = client.get("/api/download/non-existent-id")
    
    assert response.status_code == 404
