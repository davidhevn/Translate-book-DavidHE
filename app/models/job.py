"""Job models and in-memory store."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import threading


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
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert job to dictionary for API response."""
        return {
            "id": self.id,
            "original_filename": self.original_filename,
            "file_type": self.file_type,
            "status": self.status.value,
            "step": self.step,
            "percent": self.percent,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class JobStore:
    """Thread-safe in-memory job storage.
    
    For production, replace with Redis or database.
    """
    
    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create(self, job: Job) -> Job:
        """Store a new job."""
        with self._lock:
            self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **kwargs) -> Optional[Job]:
        """Update job fields."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                for key, value in kwargs.items():
                    if hasattr(job, key):
                        setattr(job, key, value)
                job.updated_at = datetime.utcnow()
            return job

    def delete(self, job_id: str) -> bool:
        """Delete a job."""
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                return True
            return False


# Global job store instance
job_store = JobStore()
