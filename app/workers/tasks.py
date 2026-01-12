"""Celery tasks for document translation."""
import logging
from typing import Optional

from app.workers.celery_app import celery_app
from app.models import JobStatus, job_store
from app.services.file_handler import get_job_directory, get_output_path

logger = logging.getLogger(__name__)


def update_job_progress(job_id: str, status: JobStatus, step: str, percent: int, error: Optional[str] = None):
    """Update job progress in the store."""
    job_store.update(
        job_id,
        status=status,
        step=step,
        percent=percent,
        error=error,
    )
    logger.info(f"Job {job_id}: {step} ({percent}%)")


@celery_app.task(bind=True, name="translate_document")
def translate_document_task(self, job_id: str, file_type: str):
    """Main translation task.
    
    Workflow:
    1. Extract text from document
    2. Translate text
    3. Render translated PDF
    """
    logger.info(f"Starting translation task for job {job_id}, type: {file_type}")
    
    try:
        job_dir = get_job_directory(job_id)
        output_path = get_output_path(job_id)
        
        # Find the original file
        original_files = list(job_dir.glob("original_*"))
        if not original_files:
            raise FileNotFoundError(f"No original file found for job {job_id}")
        original_file = original_files[0]
        
        # Step 1: Extract text
        update_job_progress(job_id, JobStatus.EXTRACTING, "Extracting text", 10)
        
        if file_type == "docx":
            from app.services.extract.docx_extract import extract_docx
            paragraphs = extract_docx(original_file)
        elif file_type == "pdf":
            from app.services.extract.pdf_extract import extract_pdf
            paragraphs = extract_pdf(original_file)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        update_job_progress(job_id, JobStatus.EXTRACTING, "Text extracted", 20)
        logger.info(f"Job {job_id}: Extracted {len(paragraphs)} paragraphs")
        
        # Step 2: Translate
        update_job_progress(job_id, JobStatus.TRANSLATING, "Translating", 30)
        
        from app.services.translation import get_translator
        translator = get_translator()
        
        translated_paragraphs = []
        total = len(paragraphs)
        for i, para in enumerate(paragraphs):
            if para.strip():
                translated = translator.translate(para)
                translated_paragraphs.append(translated)
            else:
                translated_paragraphs.append(para)
            
            # Update progress (30% to 80%)
            progress = 30 + int((i + 1) / total * 50) if total > 0 else 80
            if (i + 1) % 10 == 0 or i == total - 1:
                update_job_progress(job_id, JobStatus.TRANSLATING, f"Translating ({i+1}/{total})", progress)
        
        logger.info(f"Job {job_id}: Translated {len(translated_paragraphs)} paragraphs")
        
        # Step 3: Render PDF
        update_job_progress(job_id, JobStatus.RENDERING, "Building PDF", 85)
        
        from app.services.render.pdf_render import render_pdf
        render_pdf(translated_paragraphs, output_path)
        
        update_job_progress(job_id, JobStatus.RENDERING, "Finalizing", 95)
        
        # Done!
        update_job_progress(job_id, JobStatus.DONE, "Done", 100)
        logger.info(f"Job {job_id}: Translation complete, output at {output_path}")
        
        return {"status": "success", "job_id": job_id}
        
    except Exception as e:
        logger.exception(f"Job {job_id} failed: {e}")
        update_job_progress(job_id, JobStatus.ERROR, "Error", 0, str(e))
        return {"status": "error", "job_id": job_id, "error": str(e)}
