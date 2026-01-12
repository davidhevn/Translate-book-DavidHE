"""Tests for file upload API endpoint."""
import io


def test_upload_valid_docx(client):
    """Test uploading a valid DOCX file."""
    # Create a minimal fake DOCX file (real DOCX is a ZIP)
    content = b"PK\x03\x04" + b"\x00" * 100  # ZIP header signature
    file = io.BytesIO(content)
    
    response = client.post(
        "/api/upload",
        files={"file": ("test_document.docx", file, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert len(data["job_id"]) == 36  # UUID format


def test_upload_valid_pdf(client):
    """Test uploading a valid PDF file."""
    content = b"%PDF-1.4\n" + b"\x00" * 100
    file = io.BytesIO(content)
    
    response = client.post(
        "/api/upload",
        files={"file": ("test_document.pdf", file, "application/pdf")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data


def test_upload_invalid_extension(client):
    """Test that uploading unsupported file types fails."""
    content = b"not a real file"
    file = io.BytesIO(content)
    
    response = client.post(
        "/api/upload",
        files={"file": ("test_document.txt", file, "text/plain")}
    )
    
    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"].lower()


def test_upload_no_file(client):
    """Test that upload fails without a file."""
    response = client.post("/api/upload")
    assert response.status_code == 422  # Validation error
