# Petra Vision API

A FastAPI service to upload a PDF and inspect what `pdfplumber` can extract from it, page by page, including raw text and detected tables.

- **Extracted Text**
- **Detected Tables**
- **Per-page Character Count**

---

## Quick Start

1. **Install**
   # Create virtual environment
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # Mac/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   
   # Install dependencies
   python -m pip install -r requirements.txt
2. **Configure**
   - Copy `.env.example` to `.env`.
   - Optional tunables in `config/app.yaml`.

### Storage and database modes

The service supports two common deployment styles:

- Local mode
  - `DATABASE_BACKEND=sqlite`
  - `STORAGE_BACKEND=local`
  - uploaded files are persisted under `public/`
  - public files are served under `/public/...`
- Remote mode
  - `DATABASE_BACKEND=postgresql`
  - `STORAGE_BACKEND=minio` for MinIO or any S3-compatible endpoint
  - `STORAGE_BACKEND=azure_blob` for Azure Blob Storage

If `DATABASE_URL` is set, it takes precedence over the derived database settings.

3. **Run CLI (one-off PDF validation)**
   python -m src.main validate --pdf ./tests/sample.pdf --out ./data/reports/report.json
4. **Run API**
   python -m uvicorn src.main:app --reload --port 8000
   Then use the versioned API under `/api/v1`.
   Main extraction route: `POST /api/v1/validations` with `multipart/form-data`:
   - field `pdf`: your PDF file

5. **Run with Docker Compose**
   docker compose up --build

The compose file starts three services:

- `petra_vision_api`
- `petra_vision_postgres`
- `petra_vision_minio`

The application is intentionally configured to use the simple local mode inside the container:

- `DATABASE_BACKEND=sqlite`
- `STORAGE_BACKEND=local`

PostgreSQL and MinIO are available on the Docker network for future switching, but they are not used by default.

## Optional UI

The service can expose a lightweight built-in UI at `/`.

- `ENABLE_UI=true`
  - `/` renders the Tailwind-based UI
- `ENABLE_UI=false`
  - `/` returns the JSON service descriptor instead

The UI files are organized under:

- `src/ui/templates/`
- `src/ui/static/`

---

## Output format

The pipeline returns results grouped by **page**, with extracted text and normalized tables:

{
  "document_id": "sample_20260326T140100",
  "page_count": 2,
  "pages": [
    {
      "page": 1,
      "text": "Statement of Financial Position ...",
      "char_count": 4210,
      "tables": [
        {
          "index": 1,
          "rows": [
            ["Assets", "2024", "2023"],
            ["Cash", "100", "90"]
          ]
        }
      ]
    }
  ]
}

## Architecture

- **API**: FastAPI routers under `/api/v1`
- **Pipeline**: PDF extraction lives in `src/pipeline/`
- **Services**: business orchestration lives in `src/services/`
- **Providers**: storage integrations live in `src/providers/`
- **Schemas**: request and response contracts live in `src/schemas/`
- **Models**: SQLAlchemy models live in `src/models/`

---

## Configuration

- `config/app.yaml` controls:
  - PDF rendering DPI
  - image format
  - report toggles
- Environment variables control:
  - database backend selection
  - storage backend selection
  - UI enable/disable behavior

## Notes

- This service is focused on local PDF extraction with pdfplumber.
- Ensure you have permission to process the uploaded documents.

---

## License

MIT
