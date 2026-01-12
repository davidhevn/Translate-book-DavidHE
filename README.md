# Book Translator - English to Vietnamese

A web application to translate PDF and DOCX documents from English to Vietnamese.

## Features

- 📤 Upload PDF or DOCX documents
- 🔄 Automatic text extraction and translation
- 📊 Real-time progress tracking with status updates
- 📥 Download translated document as PDF
- 🌐 Uses Argos Translate (offline) or pluggable translation providers
- 🐳 Docker support for easy deployment

## Tech Stack

- **Backend**: Python FastAPI
- **Frontend**: Jinja2 templates + Tailwind CSS + vanilla JS
- **Task Queue**: Celery + Redis
- **Translation**: Argos Translate (offline, en→vi) or MockTranslator for testing
- **Document Processing**: pypdf, python-docx, reportlab

## Quick Start

### Prerequisites

- Python 3.10+
- Redis server (for Celery background tasks)

### Option 1: Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/davidhevn/Translate-book-DavidHE.git
   cd Translate-book-DavidHE
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

5. **Start Redis** (in separate terminal):
   ```bash
   redis-server
   # Or on Windows with Docker:
   docker run -d -p 6379:6379 redis:7-alpine
   ```

6. **Start Celery worker** (in separate terminal):
   ```bash
   celery -A app.workers.celery_app worker --loglevel=info
   # On Windows, you may need:
   celery -A app.workers.celery_app worker --loglevel=info --pool=solo
   ```

7. **Start the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

8. **Open browser:** http://localhost:8000

### Option 2: Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d --build
```

Open browser: http://localhost:8000

### Run Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_end_to_end_docx.py -v
```

## Environment Variables

See `.env.example` for all available options:

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_UPLOAD_SIZE_MB` | `50` | Maximum file upload size in MB |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `CELERY_BROKER_URL` | Same as REDIS_URL | Celery broker URL |
| `CELERY_RESULT_BACKEND` | Same as REDIS_URL | Celery result backend |
| `TRANSLATOR_BACKEND` | `mock` | Translation backend: `mock` or `argos` |
| `DEBUG` | `false` | Enable debug mode |
| `HOST` | `0.0.0.0` | Server bind host |
| `PORT` | `8000` | Server bind port |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Home page with upload form |
| `GET` | `/job/{job_id}` | Job status page |
| `GET` | `/health` | Health check |
| `POST` | `/api/upload` | Upload file, returns `{job_id}` |
| `GET` | `/api/jobs/{job_id}` | Get job status: `{status, step, percent, error}` |
| `GET` | `/api/download/{job_id}` | Download translated PDF (only when done) |
| `GET` | `/api/health` | API health check |

### Job Status Values

| Status | Description |
|--------|-------------|
| `queued` | Job is waiting to be processed |
| `extracting` | Extracting text from document |
| `translating` | Translating text (shows progress %) |
| `rendering` | Building the output PDF |
| `done` | Translation complete, ready for download |
| `error` | Translation failed (check `error` field) |

## Installing Argos Translate (for real translation)

To use real English→Vietnamese translation instead of the mock translator:

1. **Install Argos Translate:**
   ```bash
   pip install argostranslate
   ```

2. **Download the EN→VI language pack:**
   ```python
   import argostranslate.package
   
   # Update package index
   argostranslate.package.update_package_index()
   
   # Get available packages
   packages = argostranslate.package.get_available_packages()
   
   # Find and install EN→VI
   en_vi = next((p for p in packages if p.from_code == 'en' and p.to_code == 'vi'), None)
   if en_vi:
       argostranslate.package.install_from_path(en_vi.download())
       print('English → Vietnamese package installed!')
   ```

3. **Set environment variable:**
   ```bash
   export TRANSLATOR_BACKEND=argos
   # Or in .env file:
   TRANSLATOR_BACKEND=argos
   ```

4. **Restart the application and worker.**

## Project Structure

```
/app
  main.py              # FastAPI application entry point
  config.py            # Configuration from environment
  /api
    routes.py          # API endpoints (upload, status, download)
  /web
    /templates         # Jinja2 HTML templates
    /static            # Static assets (CSS)
  /services
    file_handler.py    # File validation and storage
    /translation
      base.py          # Translator interface
      mock.py          # Mock translator for testing
      argos.py         # Argos Translate provider
    /extract
      docx_extract.py  # DOCX text extraction
      pdf_extract.py   # PDF text extraction
    /render
      pdf_render.py    # PDF output generation
  /workers
    celery_app.py      # Celery configuration
    tasks.py           # Background translation task
  /models
    job.py             # Job model and in-memory store
/tests                 # Test suite (pytest)
/storage               # Uploaded and translated files
/docker                # Docker configuration
```

## Translation Workflow

1. User uploads PDF/DOCX file
2. File is validated and saved to `./storage/{job_id}/`
3. Celery task is queued for background processing
4. Worker extracts text from document
5. Text is translated paragraph by paragraph (with progress updates)
6. Translated text is rendered to a new PDF
7. User downloads the translated PDF

## Security Notes

- File types are validated (only .pdf and .docx allowed)
- File size is limited (default 50MB)
- Filenames are sanitized to prevent path traversal
- UUIDs are used for job IDs
- Files are stored in isolated job directories

## Contributing

1. Create a feature branch from `main`
2. Make changes with tests
3. Run `pytest` to ensure all tests pass
4. Commit with [Conventional Commits](https://www.conventionalcommits.org/) format
5. Submit a Pull Request

### Commit Message Format

```
feat(scope): add new feature
fix(scope): fix bug description
test(scope): add or update tests
docs(scope): update documentation
chore(scope): maintenance tasks
```

## Creating a Pull Request

After completing your feature:

```bash
# Ensure all tests pass
pytest

# Push your branch
git push origin feat/your-feature-name

# Create PR via GitHub CLI (if installed)
gh pr create --title "feat: your feature" --body "Description of changes"

# Or manually at:
# https://github.com/davidhevn/Translate-book-DavidHE/compare
```

## License

MIT

## Troubleshooting

### Celery worker not starting on Windows

Use the `--pool=solo` option:
```bash
celery -A app.workers.celery_app worker --loglevel=info --pool=solo
```

### Redis connection refused

Ensure Redis is running:
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# Start Redis (Linux/Mac)
redis-server

# Start Redis with Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### Argos Translate not working

1. Verify the package is installed: `pip show argostranslate`
2. Check if language pack is installed (run the Python script above)
3. Ensure `TRANSLATOR_BACKEND=argos` is set
4. Check worker logs for errors
