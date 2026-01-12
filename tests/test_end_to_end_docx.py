"""End-to-end integration test for DOCX translation workflow."""
import io
import tempfile
from pathlib import Path

from docx import Document


def create_test_docx(text_content: str) -> bytes:
    """Create a test DOCX file with given content."""
    doc = Document()
    for para in text_content.split('\n'):
        if para.strip():
            doc.add_paragraph(para)
    
    # Save to bytes
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.read()


def test_docx_extraction():
    """Test extracting text from a DOCX file."""
    from app.services.extract.docx_extract import extract_docx
    
    # Create a test DOCX
    content = "Hello world.\nThis is a test document.\nThird paragraph here."
    docx_bytes = create_test_docx(content)
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
        f.write(docx_bytes)
        temp_path = Path(f.name)
    
    try:
        paragraphs = extract_docx(temp_path)
        
        assert len(paragraphs) == 3
        assert paragraphs[0] == "Hello world."
        assert paragraphs[1] == "This is a test document."
        assert paragraphs[2] == "Third paragraph here."
    finally:
        temp_path.unlink()


def test_pdf_render():
    """Test rendering paragraphs to PDF."""
    from app.services.render.pdf_render import render_pdf
    
    paragraphs = [
        "[VI] Hello world.",
        "[VI] This is translated.",
        "[VI] Third paragraph."
    ]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "test_output.pdf"
        
        result_path = render_pdf(paragraphs, output_path)
        
        assert result_path.exists()
        assert result_path.stat().st_size > 0
        
        # Read PDF and verify it's valid
        with open(result_path, 'rb') as f:
            header = f.read(8)
            assert header.startswith(b'%PDF')


def test_full_docx_translation_workflow():
    """Test the complete workflow: DOCX -> extract -> translate -> PDF."""
    from app.services.extract.docx_extract import extract_docx
    from app.services.translation import MockTranslator
    from app.services.render.pdf_render import render_pdf
    
    # Create test DOCX with English content
    english_content = """Welcome to the book.
This chapter introduces key concepts.
Programming is the art of solving problems."""
    
    docx_bytes = create_test_docx(english_content)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save input DOCX
        input_path = Path(temp_dir) / "input.docx"
        with open(input_path, 'wb') as f:
            f.write(docx_bytes)
        
        # Step 1: Extract
        paragraphs = extract_docx(input_path)
        assert len(paragraphs) == 3
        
        # Step 2: Translate with mock
        translator = MockTranslator()
        translated = [translator.translate(p) for p in paragraphs]
        
        assert all(t.startswith("[VI]") for t in translated)
        
        # Step 3: Render PDF
        output_path = Path(temp_dir) / "output.pdf"
        render_pdf(translated, output_path)
        
        assert output_path.exists()
        assert output_path.stat().st_size > 500  # Reasonable PDF size


def test_e2e_upload_and_sync_translate(client):
    """End-to-end test: upload DOCX, run translation synchronously, download PDF."""
    from app.models import job_store, JobStatus
    from app.services.extract.docx_extract import extract_docx
    from app.services.translation import MockTranslator
    from app.services.render.pdf_render import render_pdf
    from app.services.file_handler import get_job_directory, get_output_path
    
    # Create test DOCX
    english_content = "Hello from the test.\nThis is English text."
    docx_bytes = create_test_docx(english_content)
    
    # Upload file
    response = client.post(
        "/api/upload",
        files={"file": ("test_book.docx", io.BytesIO(docx_bytes), 
               "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    
    # Simulate translation workflow (since Celery isn't running)
    job_dir = get_job_directory(job_id)
    original_file = list(job_dir.glob("original_*"))[0]
    
    # Extract
    paragraphs = extract_docx(original_file)
    assert len(paragraphs) == 2
    
    # Translate
    translator = MockTranslator()
    translated = [translator.translate(p) for p in paragraphs]
    
    # Render
    output_path = get_output_path(job_id)
    render_pdf(translated, output_path)
    
    # Mark job as done
    job_store.update(job_id, status=JobStatus.DONE, step="Done", percent=100)
    
    # Check job status
    status_response = client.get(f"/api/jobs/{job_id}")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "done"
    
    # Download translated PDF
    download_response = client.get(f"/api/download/{job_id}")
    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == "application/pdf"
    
    # Verify PDF content
    pdf_content = download_response.content
    assert pdf_content.startswith(b'%PDF')
    assert len(pdf_content) > 500
    
    # Verify filename
    content_disposition = download_response.headers.get("content-disposition", "")
    assert "test_book_vietnamese.pdf" in content_disposition
