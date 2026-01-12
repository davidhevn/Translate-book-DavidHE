# Book Translator - English to Vietnamese

A web application to translate PDF and DOCX documents from English to Vietnamese.

## Features

- Upload PDF or DOCX documents
- Automatic text extraction and translation
- Progress tracking with real-time updates
- Download translated document as PDF
- Uses Argos Translate (offline) or pluggable translation providers

## Tech Stack

- **Backend**: Python FastAPI
- **Frontend**: Jinja2 templates + Tailwind CSS + vanilla JS
- **Task Queue**: Celery + Redis
- **Translation**: Argos Translate (offline, en→vi)

## Quick Start

### Prerequisites

- Python 3.10+
- Redis server (for Celery)

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/davidhevn/Translate-book-DavidHE.git
   cd Translate-book-DavidHE
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy environment file:
   ```bash
   cp .env.example .env
   ```

5. Start Redis (in separate terminal):
   ```bash
   redis-server
   ```

6. Start Celery worker (in separate terminal):
   ```bash
   celery -A app.workers.celery_app worker --loglevel=info
   ```

7. Start the application:
   ```bash
   uvicorn app.main:app --reload
   ```

8. Open http://localhost:8000

### Run Tests

```bash
pytest
```

### Docker Compose

```bash
docker-compose up --build
```

## Environment Variables

See `.env.example` for all available options:

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_UPLOAD_SIZE_MB` | `50` | Maximum file upload size in MB |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `TRANSLATOR_BACKEND` | `mock` | Translation backend: `mock`, `argos` |
| `DEBUG` | `false` | Enable debug mode |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/upload` | Upload file, returns `{job_id}` |
| `GET` | `/api/jobs/{job_id}` | Get job status, progress |
| `GET` | `/api/download/{job_id}` | Download translated PDF |
| `GET` | `/health` | Health check |

## Project Structure

```
/app
  main.py              # FastAPI application
  config.py            # Configuration
  /api                 # API routes
  /web/templates       # Jinja2 templates
  /services
    /translation       # Translation providers
    /extract           # Document text extraction
    /render            # PDF rendering
  /workers             # Celery tasks
/tests                 # Test suite
/storage               # Uploaded/translated files
```

## Installing Argos Translate Language Pack

```bash
pip install argostranslate
python -c "
import argostranslate.package
argostranslate.package.update_package_index()
packages = argostranslate.package.get_available_packages()
en_vi = next((p for p in packages if p.from_code == 'en' and p.to_code == 'vi'), None)
if en_vi:
    argostranslate.package.install_from_path(en_vi.download())
    print('English → Vietnamese package installed!')
"
```

## Contributing

1. Create a feature branch from `main`
2. Make changes with tests
3. Run `pytest` to ensure tests pass
4. Submit a Pull Request

## License

MIT
