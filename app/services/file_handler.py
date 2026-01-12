"""File handling utilities."""
import logging
import os
import re
import uuid
from pathlib import Path
from typing import Optional, Tuple

from app.config import STORAGE_DIR, ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE_BYTES

logger = logging.getLogger(__name__)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and special characters."""
    # Get just the filename without path
    filename = os.path.basename(filename)
    # Remove any non-alphanumeric characters except dots, dashes, underscores
    filename = re.sub(r'[^\w\-.]', '_', filename)
    # Ensure no double dots (path traversal attempt)
    while '..' in filename:
        filename = filename.replace('..', '.')
    return filename or "unnamed"


def validate_file(filename: str, content_length: Optional[int]) -> Tuple[bool, str]:
    """Validate uploaded file.
    
    Returns: (is_valid, error_message)
    """
    if not filename:
        return False, "No filename provided"
    
    # Check extension
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type '{ext}' not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Check size if provided
    if content_length and content_length > MAX_UPLOAD_SIZE_BYTES:
        max_mb = MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        return False, f"File too large. Maximum size: {max_mb}MB"
    
    return True, ""


def get_file_type(filename: str) -> str:
    """Get file type from filename."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return "pdf"
    elif ext == ".docx":
        return "docx"
    return "unknown"


def create_job_directory(job_id: str) -> Path:
    """Create directory for job files."""
    job_dir = STORAGE_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created job directory: {job_dir}")
    return job_dir


def get_job_directory(job_id: str) -> Path:
    """Get path to job directory."""
    return STORAGE_DIR / job_id


def save_uploaded_file(job_id: str, filename: str, content: bytes) -> Path:
    """Save uploaded file to job directory.
    
    Returns path to saved file.
    """
    job_dir = create_job_directory(job_id)
    safe_filename = sanitize_filename(filename)
    file_path = job_dir / f"original_{safe_filename}"
    
    with open(file_path, 'wb') as f:
        f.write(content)
    
    logger.info(f"Saved uploaded file: {file_path} ({len(content)} bytes)")
    return file_path


def get_output_path(job_id: str) -> Path:
    """Get path for translated output PDF."""
    return get_job_directory(job_id) / "translated_output.pdf"


def generate_job_id() -> str:
    """Generate a unique job ID."""
    return str(uuid.uuid4())
