# Book Translator - English to Vietnamese

Translate PDF and DOCX documents from English to Vietnamese.

## Quick Start (2 steps)

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
python run.py
```

That's it! Open http://localhost:8000 in your browser.

## How to Use

1. Open http://localhost:8000
2. Upload a PDF or DOCX file
3. Wait for translation to complete (progress shown on screen)
4. Click "Download" to get your translated PDF

## Features

- ✅ Upload PDF or DOCX files
- ✅ Real-time progress tracking
- ✅ Download translated PDF
- ✅ Works offline (no internet needed for mock translator)
- ✅ No Docker required
- ✅ No Redis required

## Project Structure

```
/app
  main.py           # FastAPI app
  /api/routes.py    # API endpoints
  /services         # Translation, extraction, rendering
  /models           # Job tracking
  /web/templates    # HTML pages
/tests              # Test suite
run.py              # ← Run this file!
```

## Run Tests

```bash
pytest
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/upload` | Upload file, returns job_id |
| `GET` | `/api/jobs/{job_id}` | Get translation progress |
| `GET` | `/api/download/{job_id}` | Download translated PDF |

## Environment Variables (optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_UPLOAD_SIZE_MB` | `50` | Max file size |
| `TRANSLATOR_BACKEND` | `mock` | `mock` or `argos` |

## Using Real Translation (Argos Translate)

To use actual English→Vietnamese translation:

```bash
pip install argostranslate

python -c "
import argostranslate.package
argostranslate.package.update_package_index()
packages = argostranslate.package.get_available_packages()
en_vi = next(p for p in packages if p.from_code == 'en' and p.to_code == 'vi')
argostranslate.package.install_from_path(en_vi.download())
print('Done!')
"

# Then set environment variable before running:
set TRANSLATOR_BACKEND=argos   # Windows
export TRANSLATOR_BACKEND=argos  # Linux/Mac

python run.py
```

## License

MIT
