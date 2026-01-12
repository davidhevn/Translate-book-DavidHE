"""API routes for the translation service."""
import logging
import threading
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from app.models import Job, JobStatus, job_store
from app.services.file_handler import (
    validate_file,
    get_file_type,
    save_uploaded_file,
    get_output_path,
    get_job_directory,
    generate_job_id,
)
from app.config import REDIS_URL

logger = logging.getLogger(__name__)

router = APIRouter()


def _check_redis_available() -> bool:
    """Check if Redis is available for Celery."""
    try:
        import redis
        r = redis.from_url(REDIS_URL, socket_connect_timeout=1)
        r.ping()
        return True
    except Exception:
        return False


def _process_translation_sync(job_id: str, file_type: str):
    """Process translation synchronously (without Celery)."""
    try:
        logger.info(f"Starting sync translation for job {job_id}")
        
        job_dir = get_job_directory(job_id)
        output_path = get_output_path(job_id)
        
        # Find original file
        original_files = list(job_dir.glob("original_*"))
        if not original_files:
            raise FileNotFoundError(f"No original file found for job {job_id}")
        original_file = original_files[0]
        
        # Step 1: Extract
        job_store.update(job_id, status=JobStatus.EXTRACTING, step="Extracting text", percent=10)
        
        if file_type == "docx":
            from app.services.extract.docx_extract import extract_docx
            paragraphs = extract_docx(original_file)
        elif file_type == "pdf":
            from app.services.extract.pdf_extract import extract_pdf
            paragraphs = extract_pdf(original_file)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        job_store.update(job_id, step="Text extracted", percent=20)
        logger.info(f"Job {job_id}: Extracted {len(paragraphs)} paragraphs")
        
        # Step 2: Translate
        job_store.update(job_id, status=JobStatus.TRANSLATING, step="Translating", percent=30)
        
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
            
            # Update progress
            progress = 30 + int((i + 1) / total * 50) if total > 0 else 80
            if (i + 1) % 5 == 0 or i == total - 1:
                job_store.update(job_id, step=f"Translating ({i+1}/{total})", percent=progress)
        
        logger.info(f"Job {job_id}: Translated {len(translated_paragraphs)} paragraphs")
        
        # Step 3: Render PDF
        job_store.update(job_id, status=JobStatus.RENDERING, step="Building PDF", percent=85)
        
        from app.services.render.pdf_render import render_pdf
        render_pdf(translated_paragraphs, output_path)
        
        job_store.update(job_id, step="Finalizing", percent=95)
        
        # Done!
        job_store.update(job_id, status=JobStatus.DONE, step="Done", percent=100)
        logger.info(f"Job {job_id}: Translation complete!")
        
    except Exception as e:
        logger.exception(f"Job {job_id} failed: {e}")
        job_store.update(job_id, status=JobStatus.ERROR, step="Error", percent=0, error=str(e))


@router.get("/health")
async def api_health():
    """API health check."""
    redis_ok = _check_redis_available()
    return {
        "status": "ok",
        "redis": "connected" if redis_ok else "unavailable (using sync mode)",
    }


@router.post("/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload a file for translation.
    
    Returns job_id to track translation progress.
    Uses Celery if Redis available, otherwise processes synchronously.
    """
    # Validate file
    is_valid, error = validate_file(file.filename, file.size)
    if not is_valid:
        logger.warning(f"Upload validation failed: {error}")
        raise HTTPException(status_code=400, detail=error)
    
    # Generate job ID
    job_id = generate_job_id()
    logger.info(f"Creating job {job_id} for file: {file.filename}")
    
    # Read and save file
    try:
        content = await file.read()
        save_uploaded_file(job_id, file.filename, content)
    except Exception as e:
        logger.error(f"Failed to save file for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")
    
    # Create job record
    file_type = get_file_type(file.filename)
    job = Job(
        id=job_id,
        original_filename=file.filename,
        file_type=file_type,
        status=JobStatus.QUEUED,
        step="Queued",
        percent=0,
    )
    job_store.create(job)
    logger.info(f"Job {job_id} created successfully")
    
    # Try Celery first, fall back to sync processing
    redis_available = _check_redis_available()
    
    if redis_available:
        try:
            from app.workers.tasks import translate_document_task
            translate_document_task.delay(job_id, file_type)
            logger.info(f"Translation task queued via Celery for job {job_id}")
        except Exception as e:
            logger.warning(f"Celery failed: {e}, falling back to sync mode")
            background_tasks.add_task(_process_translation_sync, job_id, file_type)
    else:
        # No Redis - use FastAPI background tasks (synchronous in background thread)
        logger.info(f"Redis unavailable, using sync mode for job {job_id}")
        background_tasks.add_task(_process_translation_sync, job_id, file_type)
    
    return {"job_id": job_id}


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get translation job status and progress."""
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "status": job.status.value,
        "step": job.step,
        "percent": job.percent,
        "error": job.error,
    }


@router.get("/download/{job_id}")
async def download_translated_file(job_id: str):
    """Download the translated PDF file."""
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.DONE:
        raise HTTPException(
            status_code=400, 
            detail=f"Translation not complete. Current status: {job.status.value}"
        )
    
    output_path = get_output_path(job_id)
    if not output_path.exists():
        logger.error(f"Output file not found for job {job_id}: {output_path}")
        raise HTTPException(status_code=404, detail="Translated file not found")
    
    # Generate download filename
    original_name = job.original_filename.rsplit('.', 1)[0]
    download_name = f"{original_name}_vietnamese.pdf"
    
    return FileResponse(
        path=output_path,
        filename=download_name,
        media_type="application/pdf",
    )
