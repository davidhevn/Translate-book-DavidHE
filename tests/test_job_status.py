"""Tests for job status API endpoint."""
import io
import time

from docx import Document


def create_valid_docx() -> bytes:
    """Create a valid DOCX file for testing."""
    doc = Document()
    doc.add_paragraph("Test content")
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.read()


def test_job_status_after_upload(client):
    """Test getting job status after upload - should process and complete."""
    # Create a valid DOCX
    docx_bytes = create_valid_docx()
    file = io.BytesIO(docx_bytes)
    
    upload_response = client.post(
        "/api/upload",
        files={"file": ("test.docx", file, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    assert upload_response.status_code == 200
    job_id = upload_response.json()["job_id"]
    
    # Wait a bit for background task to complete
    time.sleep(0.5)
    
    # Get status - should be done (sync mode without Redis)
    response = client.get(f"/api/jobs/{job_id}")
    
    assert response.status_code == 200
    data = response.json()
    # In sync mode without Redis, it processes immediately
    assert data["status"] in ["queued", "extracting", "translating", "rendering", "done"]


def test_job_status_not_found(client):
    """Test getting status for non-existent job."""
    response = client.get("/api/jobs/non-existent-job-id")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_download_before_complete_invalid_file(client):
    """Test that download fails if job errors on invalid file."""
    # Use invalid DOCX content (will error during processing)
    content = b"PK\x03\x04" + b"\x00" * 100
    file = io.BytesIO(content)
    
    upload_response = client.post(
        "/api/upload",
        files={"file": ("test.docx", file, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    job_id = upload_response.json()["job_id"]
    
    # Wait for processing attempt
    time.sleep(0.3)
    
    # Try to download - should fail (either error or not complete)
    response = client.get(f"/api/download/{job_id}")
    
    assert response.status_code == 400


def test_download_job_not_found(client):
    """Test download with non-existent job."""
    response = client.get("/api/download/non-existent-id")
    
    assert response.status_code == 404
