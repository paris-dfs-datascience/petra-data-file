# RAG Vision Pipeline (OpenAI Vision)

An MVP pipeline to **upload a PDF of financial statements**, render each page as an image, and **validate rules** using **OpenAI Vision** returning **strict JSON** per rule:

- **Rule Name**
- **Pass or Fail**
- **Reasoning**
- **Citation** (page numbers / evidence snippets)

Everything is modular: rules live in `rules/*.json`, the system prompt is in `config/system_prompt.md`.

> Uses **LangGraph** to orchestrate: PDF → images → vision eval (all pages) → aggregate report.

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

3. **Run CLI (one-off PDF validation)**
   python -m src.main cli validate --pdf ./tests/sample.pdf --rules ./rules/rules.json --out ./data/reports/report.json
   4. **Run API**
   python -m uvicorn src.main:app --reload --port 8000
      Then `POST /validate` with a `multipart/form-data` upload:
   - field `pdf`: your PDF file
   - field `rules_json` (optional): raw JSON string of rules; if omitted, file `rules/rules.json` is used.

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

- **PDF → images**: `PyMuPDF` renders each page at configurable DPI (default 300) → `data/uploads/<doc_id>/pages/*.png`
- **Vision evaluation**: For each page, evaluate **all rules** against that single page. Each rule evaluation is a separate OpenAI API call.
- **Concurrency**: Uses a bounded thread pool (default 4 concurrent requests, configurable via `vision.concurrent_requests` in `config/app.yaml`) to parallelize API calls while respecting rate limits.
- **LangGraph** orchestrates the stages into a reproducible graph.

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
  concurrent_requests: 4  # Max parallel API calls---

## Notes

- This repo is an MVP—ideal for internal POCs with financial statements. You might enhance it with caching, persistence across runs, Streamlit/Gradio UI, and tracing with LangSmith.
- Ensure you have permission to process the uploaded documents.

---

## License

MIT
