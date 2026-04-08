# Petra Vision API

A FastAPI service to upload a PDF, extract its contents with `pdfplumber`, and keep a real analysis stage built from that extracted content and the selected validation rules.

The same run can be reviewed in the React frontend through tabs that separate the process into three views:

- **Original PDF**
- **Extracted Text and Tables**
- **Analysis Derived From the Extraction**

The operator workflow is protected by Microsoft Entra ID. The React frontend requires a successful Microsoft sign-in, and the FastAPI backend accepts only Azure access tokens issued by the configured tenant, audience, scope, and approved frontend app registration.

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
   - Copy `env.example` to `.env`.
   - Copy `frontend/.env.example` to `frontend/.env`.
   - Choose providers with `TEXT_PROVIDER` and `VISION_PROVIDER` using `openai` or `claude`.
   - For Claude, configure `ANTHROPIC_API_KEY` (the app also accepts `ANTHROPIC_AI_API_KEY` and `ANTROPIC_AI_API_KEY`).
  - Configure Microsoft Entra ID values for the backend API and frontend SPA. The repository templates are already set for:
     - tenant `dce78d1e-e927-4f5a-8d06-0035eaf8cc08`
     - frontend app `fa60a728-3038-450f-ba94-8e89667048a4`
     - API app `f4cb04ea-3fd2-4d6d-83be-a08bb993f9e9`
     - API scope `api://f4cb04ea-3fd2-4d6d-83be-a08bb993f9e9/access_as_user`
     - accepted access token versions `1.0,2.0` in backend validation, so the API works whether your Entra app manifest still emits v1 tokens or has already been moved to v2
   - Optional tunables in `config/app.yaml`.
- Temporary workspace behavior is controlled with `LOCAL_WORKDIR`.

### Frontend

The supported UI now lives in the separate React app under `frontend/`.

- the legacy built-in backend UI under `src/ui/` is deprecated and no longer mounted
- the backend root `/` now returns a JSON service descriptor only
- use the standalone frontend service for operator workflows

### Ephemeral runtime

The service does not persist uploaded PDFs, validation runs, or feedback records.

- uploaded PDFs are copied into a temporary working directory only for the duration of the analysis
- rendered page images are temporary and removed after use
- the React frontend previews the original PDF from the browser's local file object, not from a server-side public URL

3. **Run CLI (one-off PDF validation)**
   python -m src.main validate --pdf ./tests/sample.pdf --out ./data/reports/report.json
4. **Run API**
   python -m uvicorn src.main:app --reload --port 8000
   Then use the versioned API under `/api/v1`.
   Main extraction route: `POST /api/v1/validations` with `multipart/form-data`:
   - field `pdf`: your PDF file
   - field `rules_json`: selected validation rules sent from the frontend

5. **Run Frontend**
   cd frontend
   npm install
   npm run dev

   The browser will show a Microsoft sign-in gate before the workspace loads.

6. **Run with Docker Compose**
   docker compose up --build

The compose file starts two services:

- `petra_vision_api`
- `petra_vision_frontend`

---

## Output format

The pipeline returns results grouped by **page**, and it also returns a dedicated analysis section built from the extracted text and tables. The React frontend surfaces these parts in separate tabs so the original PDF, the extraction, and the analysis can be compared side by side during the same review:

{
  "document_id": "sample_20260326T140100",
  "page_count": 2,
  "source_filename": "sample.pdf",
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
- **Providers**: text and vision integrations live in `src/providers/`
- **Schemas**: request and response contracts live in `src/schemas/`

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
  - Microsoft Entra ID tenant, audience, scope, and allowed SPA client app IDs
  - temporary workspace location via `LOCAL_WORKDIR`
  - legacy `ENABLE_UI` parsing for backward compatibility only; the backend no longer mounts the built-in UI

## Notes

- This service extracts PDF content with `pdfplumber` and uses that extracted material as the input to a separate analysis stage.
- The service runs without persistent storage. Uploaded PDFs and rendered page images are removed after analysis.
- The backend disables public OpenAPI and documentation routes so the API surface is not exposed anonymously.
- The legacy backend UI under `src/ui/` is deprecated and no longer served by FastAPI.
- The supported operator interface is the separate React frontend under `frontend/`.
- Ensure you have permission to process the uploaded documents.

---

## License

MIT
