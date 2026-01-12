"""API routes for the translation service."""
import logging
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse

from app.models import Job, JobStatus, job_store
from app.services.file_handler import (
    validate_file,
    get_file_type,
    save_uploaded_file,
    get_output_path,
    generate_job_id,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def api_health():
    """API health check."""
    return {"status": "ok"}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file for translation.
    
    Returns job_id to track translation progress.
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
    
    # Trigger async translation task
    try:
        from app.workers.tasks import translate_document_task
        translate_document_task.delay(job_id, file_type)
        logger.info(f"Translation task queued for job {job_id}")
    except Exception as e:
        # If Celery/Redis unavailable, log warning but don't fail upload
        # Job will stay in QUEUED state
        logger.warning(f"Failed to queue translation task: {e}. Job {job_id} will need manual processing.")
    
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
