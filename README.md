# Petra Vision API

A FastAPI microservice to **upload and validate PDF financial statements**, render each page as an image, and evaluate configurable rules with **OpenAI Vision**, returning **strict JSON** results per page and per rule.

- **Rule Name**
- **Pass or Fail**
- **Reasoning**
- **Citation** (page numbers / evidence snippets)

Rules live in `rules/*.json`, and the system prompt lives in `config/system_prompt.md`.

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
   - Copy `.env.example` to `.env` and set `OPENAI_API_KEY`.
   - Put your rules into `rules/rules.json` (see the example).
   - Edit `config/system_prompt.md` with your rules validation preamble.
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
   python -m src.main validate --pdf ./tests/sample.pdf --rules ./rules/rules.json --out ./data/reports/report.json
   4. **Run API**
   python -m uvicorn src.main:app --reload --port 8000
      Then use the versioned API under `/api/v1`.
      Main validation route: `POST /api/v1/validations` with `multipart/form-data`:
   - field `pdf`: your PDF file
   - field `rules_json` (optional): raw JSON string of rules; if omitted, file `rules/rules.json` is used.

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

## Rules JSON shape

You can supply **any number of rules**. The pipeline evaluates every page against every rule.

{
  "rules": [
    {
      "id": "rule_bs_current_assets_present",
      "name": "Balance sheet shows current assets",
      "description": "Verify the presence of a line item called 'Current assets' or the equivalent on the balance sheet.",
      "acceptance_criteria": "The image shows a balance sheet section with a 'Current assets' or equivalent heading.",
      "severity": "medium"
    }
  ]
}- You can remove or add rules freely without touching code.

---

## Output format

The pipeline returns results grouped by **page**, with each page containing rule evaluations:

{
  "document_id": "2025-10-29T12-30-15-123Z_ABC123",
  "pages": [
    {
      "page": 2,
      "image_data_url": "data:image/png;base64,...",
      "rules": [
        {
          "rule_id": "rule_bs_current_assets_present",
          "rule_name": "Balance sheet shows current assets",
          "status": "pass",
          "reasoning": "The page includes a section labeled 'Current assets' with line items and totals.",
          "citations": [{ "page": 2, "evidence": "Balance Sheet - Current assets" }],
          "preview_images": [{ "page": 2, "image_data_url": "data:image/png;base64,..." }]
        }
      ]
    }
  ]
}---

## Architecture

- **API**: FastAPI routers under `/api/v1`
- **Pipeline**: PDF rendering and rule evaluation live in `src/pipeline/`
- **Services**: business orchestration lives in `src/services/`
- **Providers**: OpenAI and storage integrations live in `src/providers/`
- **Schemas**: request and response contracts live in `src/schemas/`
- **Models**: SQLAlchemy models live in `src/models/`

---

## Configuration

- `config/app.yaml` controls:
  - vision model (`gpt-4o`), temperature/seed
  - **`concurrent_requests`**: max parallel API calls (default: 4)
  - image rendering DPI (default: 300)
- `config/system_prompt.md` is **injected as a system message**. You can fully rewrite it without code changes.

### Vision provider configuration

vision:
  provider: "openai"
  model_id: "gpt-4o"
  temperature: 0.1
  seed: 42
  max_tokens: 1200
  image_detail: "high"
  concurrent_requests: 4

## Notes

- This service is structured as a small FastAPI microservice with a dedicated validation pipeline.
- Ensure you have permission to process the uploaded documents.

---

## License

MIT
