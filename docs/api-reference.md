# API Reference

All endpoints are prefixed with `/api/v1` (configurable via `API_PREFIX`).

When authentication is enabled, all endpoints except `/health` require a valid Azure AD bearer token in the `Authorization` header.

## Validations

### POST /validations

Synchronous document validation. Blocks until analysis is complete.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pdf` | file | Yes | PDF file to validate |
| `rules_json` | string | No | JSON string of selected rules. If omitted, all rules are used. |

**Response:** `200 OK` - `DocumentValidationResponse`

```json
{
  "document_id": "upload_20240115T143022",
  "page_count": 5,
  "source_filename": "report.pdf",
  "analysis": {
    "overview": [{ "label": "Total Rules", "value": "8" }],
    "selected_rule_count": 8,
    "text_rule_count": 6,
    "vision_rule_count": 2,
    "rule_assessments": [...],
    "text_page_results": [...],
    "visual_page_results": [...],
    "page_observations": [...]
  },
  "pages": [
    {
      "page": 1,
      "text": "Extracted page text...",
      "tables": [{ "index": 1, "rows": [["Header1", "Header2"], ["val1", "val2"]] }],
      "char_count": 1523
    }
  ]
}
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 413 | File exceeds `MAX_UPLOAD_SIZE_MB` (default 50 MB) |
| 415 | File content type is not `application/pdf` |
| 422 | File does not start with PDF magic bytes (`%PDF-`) |

### POST /validations/jobs

Create an asynchronous validation job. Returns immediately with a job ID for polling.

**Request:** Same as `POST /validations`

**Response:** `200 OK` - `ValidationJobResponse`

```json
{
  "job_id": "abc123",
  "status": "running",
  "message": "Validation job started.",
  "progress_current": 0,
  "progress_total": 10
}
```

### GET /validations/jobs/{job_id}

Poll the status of an async validation job.

**Response:** `200 OK` - `ValidationJobResponse`

When the job is complete, the `result` field contains the full `DocumentValidationResponse`:

```json
{
  "job_id": "abc123",
  "status": "completed",
  "message": "Validation complete.",
  "progress_current": 10,
  "progress_total": 10,
  "error": null,
  "result": { ... }
}
```

**Job Statuses:** `pending`, `running`, `completed`, `failed`, `cancelled`

**Error Response:** `404` if `job_id` not found.

### POST /validations/jobs/{job_id}/cancel

Cancel a running validation job.

**Response:** `200 OK` - `ValidationJobResponse` with updated status.

**Error Response:** `404` if `job_id` not found.

## Rules

### GET /rules

List all available validation rules.

**Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `rules_path` | string | Optional path to a custom rules JSON file |

**Response:** `200 OK`

```json
{
  "rules": [
    {
      "id": "FMT-HEADINGS",
      "name": "Heading Alignment and Integrity",
      "analysis_type": "text",
      "query": "Title lines and subtitle lines...",
      "description": "Determine whether title/subtitle lines...",
      "acceptance_criteria": "Title lines should be complete...",
      "severity": "major",
      "group": null,
      "bypassable": false
    }
  ]
}
```

## Export

### POST /export

Generate a PDF audit report from analysis results.

**Request:** `application/json` - `ExportPdfRequest`

The request body contains the full analysis result (the same structure as `DocumentValidationResponse.analysis`).

**Response:** `200 OK` - Streaming PDF file download (`application/pdf`)

## Feedback

### POST /feedbacks

Submit user feedback on a validation result.

**Request:** `application/json`

```json
{
  "document_id": "upload_20240115T143022",
  "rule_id": "FMT-HEADINGS",
  "feedback_type": "incorrect",
  "message": "This heading was flagged incorrectly."
}
```

**Response:** `200 OK`

```json
{
  "success": true
}
```

## Health

### GET /health

Health check endpoint. No authentication required.

**Response:** `200 OK`

```json
{
  "status": "healthy"
}
```

## Data Models

### DocumentValidationResponse

| Field | Type | Description |
|-------|------|-------------|
| `document_id` | string | Unique identifier for the validation run |
| `page_count` | integer | Total pages in the PDF |
| `source_filename` | string | Original uploaded filename |
| `analysis` | DocumentAnalysisSchema | Full analysis results |
| `pages` | PageExtractionSchema[] | Extracted text and tables per page |

### RuleAssessmentSchema

| Field | Type | Description |
|-------|------|-------------|
| `rule_id` | string | Rule identifier (e.g., "FMT-HEADINGS") |
| `rule_name` | string | Human-readable rule name |
| `analysis_type` | "text" \| "vision" | Type of analysis performed |
| `execution_status` | string | "completed", "running", "skipped" |
| `verdict` | string | "pass", "fail", "needs_review", "not_applicable" |
| `summary` | string | Brief description of the assessment |
| `reasoning` | string | Detailed reasoning behind the verdict |
| `findings` | string[] | List of specific findings |
| `citations` | AnalysisCitationSchema[] | Page references with evidence |
| `matched_pages` | integer[] | Pages where the rule was evaluated |
| `notes` | string[] | Additional notes |
| `group` | string \| null | Rule group (e.g., "numerical") |
| `bypassable` | boolean | Whether the rule can be bypassed |
| `bypass` | boolean | Whether the rule was bypassed |

### ValidationJobResponse

| Field | Type | Description |
|-------|------|-------------|
| `job_id` | string | Unique job identifier |
| `status` | string | Job status |
| `message` | string | Human-readable status message |
| `progress_current` | integer | Current progress count |
| `progress_total` | integer | Total items to process |
| `error` | string \| null | Error message if failed |
| `result` | DocumentValidationResponse \| null | Full result when completed |
