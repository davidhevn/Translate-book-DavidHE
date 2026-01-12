"""Main FastAPI application."""
import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.api.routes import router as api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Book Translator",
    description="Translate PDF and DOCX documents from English to Vietnamese",
    version="0.1.0"
)

# Setup templates and static files
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "web" / "templates")
app.mount("/static", StaticFiles(directory=BASE_DIR / "web" / "static"), name="static")

# Include API routes
app.include_router(api_router, prefix="/api")


@app.get("/")
async def home(request: Request):
    """Render the home page with file upload form."""
    return templates.TemplateResponse(request, "index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": "book-translator"}


@app.get("/job/{job_id}")
async def job_page(request: Request, job_id: str):
    """Render the job status page."""
    return templates.TemplateResponse(request, "job.html", {"job_id": job_id})
