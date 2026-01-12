"""End-to-end integration test for PDF translation workflow."""
import io
import tempfile
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet


def create_test_pdf(text_paragraphs: list) -> bytes:
    """Create a test PDF file with given paragraphs."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    content = []
    for para in text_paragraphs:
        content.append(Paragraph(para, styles['Normal']))
    
    doc.build(content)
    buffer.seek(0)
    return buffer.read()


def test_pdf_extraction():
    """Test extracting text from a PDF file."""
    from app.services.extract.pdf_extract import extract_pdf
    
    # Create a test PDF
    paragraphs = [
        "Welcome to this document.",
        "This is the second paragraph.",
        "And here is a third one.",
    ]
    pdf_bytes = create_test_pdf(paragraphs)
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(pdf_bytes)
        temp_path = Path(f.name)
    
    try:
        extracted = extract_pdf(temp_path)
        
        # PDF extraction may combine or split paragraphs differently
        assert len(extracted) > 0
        
        # Verify the content is present
        full_text = ' '.join(extracted)
        assert "Welcome" in full_text
        assert "second paragraph" in full_text
        assert "third one" in full_text
    finally:
        temp_path.unlink()


def test_full_pdf_translation_workflow():
    """Test the complete workflow: PDF -> extract -> translate -> PDF."""
    from app.services.extract.pdf_extract import extract_pdf
    from app.services.translation import MockTranslator
    from app.services.render.pdf_render import render_pdf
    
    # Create test PDF with English content
    english_paragraphs = [
        "Chapter One: Introduction.",
        "This book covers programming fundamentals.",
        "Let us begin our journey.",
    ]
    pdf_bytes = create_test_pdf(english_paragraphs)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save input PDF
        input_path = Path(temp_dir) / "input.pdf"
        with open(input_path, 'wb') as f:
            f.write(pdf_bytes)
        
        # Step 1: Extract
        paragraphs = extract_pdf(input_path)
        assert len(paragraphs) > 0
        
        # Verify content was extracted
        full_text = ' '.join(paragraphs)
        assert "Introduction" in full_text
        
        # Step 2: Translate with mock
        translator = MockTranslator()
        translated = [translator.translate(p) for p in paragraphs]
        
        assert all("[VI]" in t for t in translated if t.strip())
        
        # Step 3: Render PDF
        output_path = Path(temp_dir) / "output.pdf"
        render_pdf(translated, output_path)
        
        assert output_path.exists()
        assert output_path.stat().st_size > 500  # Reasonable PDF size
        
        # Verify it's a valid PDF
        with open(output_path, 'rb') as f:
            assert f.read(4) == b'%PDF'


def test_e2e_pdf_upload_and_sync_translate(client):
    """End-to-end test: upload PDF, run translation synchronously, download PDF."""
    from app.models import job_store, JobStatus
    from app.services.extract.pdf_extract import extract_pdf
    from app.services.translation import MockTranslator
    from app.services.render.pdf_render import render_pdf
    from app.services.file_handler import get_job_directory, get_output_path
    
    # Create test PDF
    english_paragraphs = [
        "Hello from the PDF test.",
        "This is English text in PDF format.",
    ]
    pdf_bytes = create_test_pdf(english_paragraphs)
    
    # Upload file
    response = client.post(
        "/api/upload",
        files={"file": ("test_book.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    )
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    
    # Simulate translation workflow (since Celery isn't running)
    job_dir = get_job_directory(job_id)
    original_file = list(job_dir.glob("original_*"))[0]
    
    # Extract
    paragraphs = extract_pdf(original_file)
    assert len(paragraphs) > 0
    
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
