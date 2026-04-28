# Flag Analysis

A small companion tool that reads Petra flag/feedback data and asks Claude to
suggest areas of improvement. It auto-detects two input shapes:

| Input | Source | "Errors" mean |
|---|---|---|
| `feedback.json` | `/app/data/feedback.json` (written by `src/api/routers/feedback.py`) | User-marked `assessment == "incorrect"` |
| Validation report | `python -m src.main validate --out report.json` | Rules with verdict `fail` / `needs_review` |

## Usage

```bash
# Pull feedback.json off the running container app
az containerapp exec --name ai-audit-tool --resource-group PET-RG-03 \
  --command "sh -c 'cat /app/data/feedback.json'" > feedback.json

# Analyze it
python flag_analysis/analyze_flags.py feedback.json

# Save Claude's feedback to a file
python flag_analysis/analyze_flags.py feedback.json --out improvements.md

# Stats only (no LLM call)
python flag_analysis/analyze_flags.py feedback.json --skip-llm
```

## Environment

- `ANTHROPIC_API_KEY` (required unless `--skip-llm`)
- `CLAUDE_TEXT_MODEL` (optional, defaults to `claude-sonnet-4-6`)

## Output

For `feedback.json`:
- Total records, model accuracy, count marked incorrect
- Top rules generating incorrect assessments
- Verdict / analysis-type breakdown of errors
- Markdown feedback from Claude (Overview, Top Failure Modes, Areas for
  Improvement, Quick Wins)

For a validation report:
- Total rule assessments, pass rate, flagged count by verdict and group
- Markdown feedback from Claude (Overview, Top Issues, Areas for Improvement,
  Quick Wins)
