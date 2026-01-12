"""Job models and file-based store for persistence."""
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
import threading

from app.config import STORAGE_DIR


class JobStatus(str, Enum):
    """Job processing status."""
    QUEUED = "queued"
    EXTRACTING = "extracting"
    TRANSLATING = "translating"
    RENDERING = "rendering"
    DONE = "done"
    ERROR = "error"


@dataclass
class Job:
    """Translation job model."""
    id: str
    original_filename: str
    file_type: str  # pdf or docx
    status: JobStatus = JobStatus.QUEUED
    step: str = "Queued"
    percent: int = 0
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        """Convert job to dictionary for API response."""
        return {
            "id": self.id,
            "original_filename": self.original_filename,
            "file_type": self.file_type,
            "status": self.status.value if isinstance(self.status, JobStatus) else self.status,
            "step": self.step,
            "percent": self.percent,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Job":
        """Create Job from dictionary."""
        status = data.get("status", "queued")
        if isinstance(status, str):
            status = JobStatus(status)
        return cls(
            id=data["id"],
            original_filename=data["original_filename"],
            file_type=data["file_type"],
            status=status,
            step=data.get("step", "Queued"),
            percent=data.get("percent", 0),
            error=data.get("error"),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
        )


class JobStore:
    """File-based job storage for persistence across threads/processes.
    
    Stores job data as JSON files in the storage directory.
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._cache: dict[str, Job] = {}

    def _get_job_file(self, job_id: str) -> Path:
        """Get path to job status file."""
        return STORAGE_DIR / job_id / "job.json"

    def _save_to_file(self, job: Job):
        """Save job to file."""
        job_file = self._get_job_file(job.id)
        job_file.parent.mkdir(parents=True, exist_ok=True)
        with open(job_file, 'w') as f:
            json.dump(job.to_dict(), f)

    def _load_from_file(self, job_id: str) -> Optional[Job]:
        """Load job from file."""
        job_file = self._get_job_file(job_id)
        if job_file.exists():
            try:
                with open(job_file, 'r') as f:
                    data = json.load(f)
                return Job.from_dict(data)
            except Exception:
                return None
        return None

    def create(self, job: Job) -> Job:
        """Store a new job."""
        with self._lock:
            self._cache[job.id] = job
            self._save_to_file(job)
        return job

    def get(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        with self._lock:
            # Try cache first
            if job_id in self._cache:
                # Refresh from file to get latest updates
                file_job = self._load_from_file(job_id)
                if file_job:
                    self._cache[job_id] = file_job
                return self._cache.get(job_id)
            
            # Try loading from file
            job = self._load_from_file(job_id)
            if job:
                self._cache[job_id] = job
            return job

    def update(self, job_id: str, **kwargs) -> Optional[Job]:
        """Update job fields."""
        with self._lock:
            # Load current state from file
            job = self._load_from_file(job_id)
            if not job:
                job = self._cache.get(job_id)
            
            if job:
                for key, value in kwargs.items():
                    if hasattr(job, key):
                        setattr(job, key, value)
                job.updated_at = datetime.utcnow().isoformat()
                self._cache[job_id] = job
                self._save_to_file(job)
            return job

    def delete(self, job_id: str) -> bool:
        """Delete a job."""
        with self._lock:
            if job_id in self._cache:
                del self._cache[job_id]
            job_file = self._get_job_file(job_id)
            if job_file.exists():
                job_file.unlink()
                return True
            return False


# Global job store instance
job_store = JobStore()
