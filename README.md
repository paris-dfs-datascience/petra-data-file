# Petra Vision API

A FastAPI service to upload a PDF, extract its contents with `pdfplumber`, and keep a real analysis stage built from that extracted content and the selected validation rules.

The same run can be reviewed in the UI through tabs that separate the process into three views:

- **Original PDF**
- **Extracted Text and Tables**
- **Analysis Derived From the Extraction**

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
   - Choose providers with `TEXT_PROVIDER` and `VISION_PROVIDER` using `openai` or `claude`.
   - For Claude, configure `ANTHROPIC_API_KEY` (the app also accepts `ANTHROPIC_AI_API_KEY` and `ANTROPIC_AI_API_KEY`).
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
   - field `rules_json`: selected validation rules sent from the UI

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

When enabled, the UI presents the workflow in tabs so the same uploaded document can be reviewed as one continuous process:

- `Original PDF`
  - inspect the uploaded source document directly
- `Extracted Text`
  - review the page-by-page text and tables recovered by `pdfplumber`
- `Analysis`
  - inspect the analysis produced from the extracted text and tables, including rule assessments and page observations

---

## Output format

The pipeline returns results grouped by **page**, and it also returns a dedicated analysis section built from the extracted text and tables. The UI surfaces these parts in separate tabs so the original PDF, the extraction, and the analysis can be compared side by side during the same review:

{
  "document_id": "sample_20260326T140100",
  "page_count": 2,
  "source_filename": "sample.pdf",
  "source_pdf_url": "/public/uploads/originals/sample_abc123.pdf",
  "analysis": {
    "overview": [
      { "label": "Pages", "value": "2", "detail": "Total pages processed from the PDF." },
      { "label": "Selected Rules", "value": "3", "detail": "Rules enabled for this analysis run." }
    ],
    "rule_assessments": [
      {
        "rule_id": "FMT-HEADINGS",
        "rule_name": "All page headers",
        "matched_pages": [1],
        "notes": ["Keyword overlap found on page(s): 1."]
      }
    ],
    "page_observations": [
      {
        "page": 1,
        "observations": ["Starts with: Statement of Financial Position", "1 table(s) detected."]
      }
    ]
  },
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
- **Pipeline**: PDF extraction and derived analysis live in `src/pipeline/`
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
  - text provider selection via `TEXT_PROVIDER`
  - vision provider selection via `VISION_PROVIDER`
  - OpenAI or Claude model selection
  - database backend selection
  - storage backend selection
  - UI enable/disable behavior

## Notes

- This service extracts PDF content with `pdfplumber` and uses that extracted material as the input to a separate analysis stage.
- The UI is designed to expose the process in tabs so operators can review the source PDF, the extracted output, and the resulting analysis independently.
- Ensure you have permission to process the uploaded documents.

---

## License

MIT
